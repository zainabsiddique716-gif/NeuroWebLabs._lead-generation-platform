# Architecture Write-Up
### Local Lead Generation & Outreach Platform

## 1. One-Sentence Summary

Google Maps-style search → scrape business + website → extract email →
qualify the lead → store it → send outreach email → track what happened —
all visible and controllable from one dashboard.

## 2. Module Boundaries

The backend is split into five independent modules, each hidden behind an
abstract base class. The pipeline (`app/main.py`) never depends on a
specific implementation — only on the interface. This means any module can
be swapped or extended later without touching the rest of the codebase.

| Module | Interface | Current Implementation | Swap-in Examples Later |
|---|---|---|---|
| Lead Source | `lead_sources/base.py` → `BaseLeadSource.search()` | `openstreetmap.py` (Nominatim + Overpass) | Google Places, LinkedIn, Yelp |
| Scraper | `scrapers/base.py` → `BaseScraper.scrape()` | `email_extractor.py` (homepage → contact page, robots.txt-aware) | Social media scraper, phone-number scraper |
| Qualification | `qualification/base.py` → `BaseRule.check()` | `rules.py` — `HasEmailRule`, `WebsiteLiveRule`, `MinRatingRule` | Industry-specific rules, ML-based scoring |
| Outreach | `outreach/base.py` → `BaseChannel.send()` | `email_channel.py` (SMTP) | WhatsApp, LinkedIn DM |
| Scheduler | `core/scheduler.py` | APScheduler, interval-based | Celery + Redis (if scale grows) |

Adding a new lead source, for example, means writing one new file
(`lead_sources/linkedin.py`) that implements `search()` — no other file
needs to change.

## 3. Data Flow

Search (query + location)
│
▼
Lead Source module ──► Business rows saved to DB
│
▼
Scraper module ──► Lead row created/updated with email
│
▼
Qualification engine ──► Lead.status = qualified / rejected
│
▼
Dashboard review (human can edit email / status)
│
▼
Outreach module ──► Email sent, OutreachLog row created
│
▼
Lead.status = contacted



The Scheduler runs this same flow automatically on a timer for every saved
search, so the system keeps discovering new leads without anyone opening
the dashboard.

## 4. Stack Choices & Reasoning

| Layer | Choice | Why |
|---|---|---|
| Backend framework | FastAPI | Async-friendly, automatic OpenAPI docs (`/docs`), matches intern's existing stack |
| Database | PostgreSQL (Neon) | Free tier fits $50 budget, standard SQL, easy to scale later; SQLite fallback for local dev |
| ORM | SQLAlchemy | Type-safe models, works identically against Postgres or SQLite |
| Lead source | OpenStreetMap (Nominatim + Overpass) | Zero cost — Google Places charges past free thresholds; acceptable trade-off in data completeness for a $50 budget |
| Scraper | BeautifulSoup + requests | Lightweight, no headless browser needed for static contact pages |
| Scheduler | APScheduler (in-process) | No Redis/Celery infrastructure cost; sufficient for this workload |
| Outreach | SMTP (smtplib) | No paid transactional email service needed for the sending volume in scope |
| Frontend | React + Vite + TypeScript + Tailwind | Matches intern's existing internship stack; fast dev server, typed components |

## 5. Reliability & Failure Handling

Every external call (geocoding, website fetch, email send) is wrapped so a
single failure never crashes the pipeline:

- No website listed → lead marked, not scraped
- Website unreachable/timeout → `error_reason: website_unreachable`
- robots.txt disallows crawling → scrape skipped, respectfully
- No email found on any checked page → `error_reason: no_email_found`
- SMTP failure → logged in `OutreachLog.error_message`, lead status untouched

## 6. Qualification Rules (Adjustable, Not Hardcoded)

Rules live in a single list (`QUALIFICATION_RULES` in `qualification/rules.py`).
Adding, removing, or reordering a rule is a one-line change and does not
require touching the pipeline logic. Current rules: has a found email, has a
live website, meets a minimum rating (skipped gracefully when rating data is
unavailable, since OpenStreetMap often lacks it).

## 7. Safety Design (Outreach)

- `OUTREACH_DRY_RUN` environment flag (default `true`) simulates sends
  without contacting real businesses — satisfies the brief's
  "review before sending" requirement.
- `DAILY_SEND_LIMIT` environment variable caps sends per day to protect
  sender reputation and avoid spam flags.
- Every send attempt (success or failure) is logged to `OutreachLog` for
  full auditability.
