# Local Lead Generation & Outreach Platform

Full pipeline: **Search (OpenStreetMap) → Scrape email → Qualify → Review → Send outreach → Track**

100% free data source (OpenStreetMap), Neon Postgres database, SMTP email outreach (safe dry-run by default).

---
##Try It Live:https://neuro-web-labs-lead-generation-plat.vercel.app/
## Project Structure

```
lead-platform/
├── app/                              # FastAPI backend
│   ├── main.py                       # All API endpoints
│   ├── core/database.py              # Neon Postgres connection (SQLite fallback)
│   ├── models/models.py              # Search, Business, Lead, OutreachLog tables
│   ├── lead_sources/                 # Module 4.1 - Google Maps style search (OSM)
│   ├── scrapers/                     # Module 4.2 - website email scraping
│   ├── qualification/                # Module 4.3 - lead qualification rules
│   └── outreach/                     # Module 4.4 - email sending
├── dashboard/                        # React + Vite + TypeScript + Tailwind frontend
│   └── src/
│       ├── App.tsx                   # Tab navigation (Search / Leads / Outreach Log)
│       ├── api.ts                    # Backend API client
│       ├── types.ts                  # Shared TypeScript types
│       └── components/               # SearchPanel, LeadsTable, PipelineTrack, OutreachLogView
├── requirements.txt
├── .env.example
└── README.md
```

---

## Step 1: Neon Database Setup

1. Go to **https://neon.tech**, sign up (free tier), create a new project
2. Copy the **connection string** from the Neon dashboard — it looks like:
   ```
   postgresql://user:password@ep-xxxx.region.aws.neon.tech/dbname?sslmode=require
   ```
3. In the `lead-platform` folder, copy `.env.example` to a new file named `.env`
4. Paste the connection string into `.env` as `DATABASE_URL`, but change
   `postgresql://` to `postgresql+psycopg2://`:
   ```
   DATABASE_URL=postgresql+psycopg2://user:password@ep-xxxx.region.aws.neon.tech/dbname?sslmode=require
   ```

**Skip this step for now?** No problem — if you don't set `DATABASE_URL`, the app
automatically uses a local SQLite file (`local_dev.db`) instead, so you can test
everything before Neon is ready.

---

## Step 2: Backend Setup

Open a terminal inside the `lead-platform` folder:

```
python -m venv venv
```

Activate it:
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

Install dependencies:
```
pip install -r requirements.txt
```

Run the backend:
```
uvicorn app.main:app --reload
```

You should see:
```
Uvicorn running on http://127.0.0.1:8000
```

Check it worked: open `http://127.0.0.1:8000/docs` in your browser — you should
see the Swagger API documentation with all endpoints.

---

## Step 3: Frontend Setup (React Dashboard)

Open a **second terminal**, navigate into the `dashboard` folder:

```
cd dashboard
npm install
npm run dev
```

Terminal will show something like:
```
Local:   http://localhost:5173/
```

Open that URL in your browser. **Keep both terminals running** (backend on 8000, frontend on 5173).

---

## Step 4: Using the Dashboard

1. **Search tab** — enter a query (e.g. "dentists") and location (e.g. "Lahore, Pakistan"), click "Run search". Results save to the database automatically.
2. Click **"Scrape email"** next to any business with a website — this extracts the email and automatically runs it through qualification rules.
3. **Leads tab** — see the pipeline stage counts at the top, filter leads by status, click any email to edit it, and click **"Send outreach"** on qualified leads.
4. **Outreach Log tab** — see every email attempt and its result.

---

## Important: Email Sending is Safe by Default

In `.env`, `OUTREACH_DRY_RUN=true` by default. This means clicking "Send outreach"
**does not actually send an email** — it simulates it and logs `dry_run` status.
This protects you from accidentally emailing real businesses while testing.

To actually send emails:
1. Set up a Gmail **App Password** (Google Account → Security → 2-Step Verification → App Passwords)
2. Fill in `SMTP_USER`, `SMTP_PASSWORD`, `FROM_EMAIL` in `.env`
3. Set `OUTREACH_DRY_RUN=false`

There's also a `DAILY_SEND_LIMIT` (default 50) to protect your sender reputation.

---

## Module Status (Client Brief Sections)

| Section | Status |
|---|---|
| 4.1 Lead Discovery | Done — OpenStreetMap (free, no API key) |
| 4.2 Website & Email Scraping | Done — homepage → contact page, robots.txt respected |
| 4.3 Lead Qualification | Done — adjustable rules in `app/qualification/rules.py` |
| 4.4 Email Outreach | Done — SMTP, dry-run safe, daily limit, template personalization |
| 4.5 Dashboard | Done — React + Vite + TS + Tailwind, 3 tabs |
| Database | Done — Neon Postgres (SQLite fallback for local testing) |
| Scheduling (24/7 background jobs) | Not yet — currently manual trigger only |

## Modularity (for your write-up)

Each pipeline stage lives behind an abstract base class:
- `lead_sources/base.py` → swap in Google Places, LinkedIn, etc. later
- `scrapers/base.py` → swap in a smarter scraper later
- `qualification/base.py` → add/remove rules without touching the pipeline
- `outreach/base.py` → add WhatsApp/LinkedIn channels later

The FastAPI backend never hardcodes which implementation it's using — it only
depends on these interfaces, satisfying the brief's modularity requirement.

## Next Step (Not Yet Built)

**Scheduling** — right now searches only run when you click the button. To make
it run 24/7 automatically, the next step is adding a scheduler (APScheduler or
Celery + Redis) that re-runs saved searches on a timer, calling the same
`/api/search` → `/api/scrape` pipeline in the background.
