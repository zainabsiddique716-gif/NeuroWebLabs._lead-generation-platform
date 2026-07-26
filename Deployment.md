# Deployment Notes & Cost Breakdown
### Local Lead Generation & Outreach Platform

## 1. What Runs Where

| Component | Where It Runs | Notes |
|---|---|---|
| Backend API + Scheduler | Render or Railway (recommended) | Needs an always-on process for APScheduler to keep firing; not suitable for serverless/Vercel |
| Database | Neon (Postgres, serverless) | Free tier; connection via `DATABASE_URL` env var |
| Dashboard (frontend) | Vercel | Static React build, connects to backend via its public URL |
| Lead source data | OpenStreetMap public APIs (Nominatim + Overpass) | No hosting needed — external free service |
| Outreach email | Gmail SMTP (App Password) | No separate email service needed at this sending volume |

Local development currently uses SQLite as a zero-setup fallback when
`DATABASE_URL` is not set; production should always set `DATABASE_URL` to
the Neon connection string.

## 2. Environment Variables Required in Production

Set these in the hosting platform's dashboard (Render/Railway "Environment"
tab) — never commit them to GitHub:

DATABASE_URL=postgresql+psycopg2://<user>:<password>@<neon-host>/<db>?sslmode=require
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<sending gmail address>
SMTP_PASSWORD=<gmail app password>
FROM_EMAIL=<sending gmail address>
OUTREACH_DRY_RUN=true # set to false only when ready to send real emails
DAILY_SEND_LIMIT=50
SCHEDULE_INTERVAL_HOURS=24


## 3. Monthly Cost Breakdown (Target: under $50/month)

| Item | Provider | Cost |
|---|---|---|
| Backend hosting | Render (free tier) or Railway ($5 starter) | $0–5 |
| Database | Neon (free tier — 0.5 GB storage, enough for early scale) | $0 |
| Frontend hosting | Vercel (free tier — hobby plan) | $0 |
| Lead source data | OpenStreetMap (Nominatim + Overpass, public, free) | $0 |
| Email sending | Gmail SMTP (free, under Google's daily sending limits) | $0 |
| **Total** | | **$0–5/month** |

This is well within the $50/month budget, leaving headroom to later upgrade
to a paid lead-source API (e.g. SerpApi/Outscraper) or a paid email service
(e.g. Resend/Brevo) if volume grows, while still staying under budget.

## 4. Deployment Steps (Summary)

1. **Neon**: create project → copy connection string → set as `DATABASE_URL`
2. **Backend (Render/Railway)**: connect GitHub repo → set root directory
   to repo root → build command `pip install -r requirements.txt` → start
   command `uvicorn app.main:app --host 0.0.0.0 --port $PORT` → add all
   environment variables from Section 2
3. **Frontend (Vercel)**: connect GitHub repo → set root directory to
   `dashboard/` → framework preset "Vite" → set `VITE_API_URL` (if the
   codebase is updated to read the backend URL from an env var instead of
   the current hardcoded `http://127.0.0.1:8000`) to the deployed backend URL
4. Push to `main` → both platforms auto-deploy on every push

## 5. Known Limitation to Flag Before Going Live

The frontend (`dashboard/src/api.ts`) currently points to
`http://127.0.0.1:8000` (hardcoded for local development). Before deploying
the dashboard to Vercel, this must be changed to the live backend URL (or
read from an environment variable) — otherwise the deployed dashboard will
try to reach `localhost` and fail.
