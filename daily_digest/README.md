# Daily AI Trends Digest

An autonomous workflow that scrapes AI/automation signals daily and sends you actionable trend insights via email.

## What It Does

1. **Phase 1 & 1B Data Collection** (`scrape.py`)
   - Fetches latest YouTube videos from competitor channels (Nateherk, Nick Saraev)
   - Scrapes GitHub trending AI/automation repos (weekly)
   - Collects X (Twitter) posts from 10 key AI accounts
   - Saves combined signals to `daily_digest_signals.json`

2. **GPT-4o Analysis** (`analyze_and_email.py`)
   - Sends all signals to GPT-4o with a specialized prompt
   - Filters for signal, not noise (ignores hype, generic content)
   - Identifies trends with real ROI/efficiency impact
   - Extracts evidence and actionable next steps
   - Generates a clean HTML email

3. **Email Delivery**
   - Sends email daily to your inbox (ahmedgoatkr@gmail.com)
   - Formatted for easy reading and quick scanning

## Setup

### Local Testing

1. Copy `.env.example` to `.env` and fill in all values:
   ```bash
   cp .env.example .env
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run both scripts manually:
   ```bash
   # Step 1: Collect data
   python scrape.py

   # Step 2: Analyze and send email
   python analyze_and_email.py
   ```

### GitHub Actions (Autonomous Daily Run)

1. Add these secrets to your GitHub repo:
   - `YOUTUBE_API_KEY`
   - `GITHUB_TOKEN` (optional, for higher rate limits)
   - `APIFY_API_KEY`
   - `OPENROUTER_API_KEY`
   - `GMAIL_USER` (ahmedgoatkr@gmail.com)
   - `GMAIL_APP_PASSWORD`

2. The workflow (`.github/workflows/daily_digest.yml`) runs automatically:
   - **When:** Every day at 9 AM UTC (adjust the cron schedule if needed)
   - **Trigger:** Runs automatically OR manually via GitHub UI → Actions → "Daily AI Trends Digest" → Run workflow

## Required API Keys

| API | Purpose | Cost | Required? |
|---|---|---|---|
| **YouTube Data API v3** | Competitor video research | Free (up to 10k quota/day) | Yes |
| **OpenRouter (GPT-4o)** | AI trend analysis | ~$0.005-0.01 per run | Yes |
| **GitHub API** | Trending repos | Free (or $0 with token) | Yes (free) |
| **Apify** | X (Twitter) scraping | Free tier available, ~$0.001/run paid | Optional |
| **Gmail** | Email delivery | Free | Yes |

## Cost Per Run

- **Data collection:** ~$0.001 (GitHub + YouTube, mostly free)
- **GPT-4o analysis:** ~$0.008-0.012 per run
- **Total:** ~$0.01 per day = ~$0.30/month

## File Structure

```
daily_digest/
├── scrape.py                    # Phase 1 & 1B data collection
├── analyze_and_email.py         # GPT-4o + email generation
├── requirements.txt
├── .env.example
└── README.md

.github/workflows/
└── daily_digest.yml             # GitHub Actions trigger
```

## Output

**Email Subject:** Daily AI Trends — [Date]

**Content:**
1. Executive summary (2–3 sentences)
2. 5–8 actionable trends:
   - What's happening
   - Why now
   - ROI potential
   - Evidence (which signals point to this)
   - Concrete action item for your agency

## Prompt Strategy

The GPT-4o prompt is designed to:
- **Filter noise:** Ignore incremental tool updates, speculative hype, generic tutorials
- **Identify signal:** Focus on paradigm shifts, measurable efficiency gains, deployable-today solutions
- **Drive ROI:** What can your agency build/offer around this trend?
- **Surface evidence:** Show which GitHub repo, X post, or YouTube video triggered the insight

You can modify `analyze_and_email.py` to customize the prompt behavior.

## Troubleshooting

### Email not sending
- Check `GMAIL_APP_PASSWORD` is an [app-specific password](https://support.google.com/accounts/answer/185833), not your account password
- Verify `GMAIL_USER` is set to ahmedgoatkr@gmail.com

### No data collected
- Ensure all API keys are valid
- Check `daily_digest_signals.json` was created by `scrape.py`
- If X posts fail, it's optional — GitHub + YouTube will still work

### GitHub Actions failing
- View logs: GitHub → Actions → "Daily AI Trends Digest" → latest run
- Check that all secrets are added to the repo
- Ensure `.github/workflows/daily_digest.yml` is in the correct path

## Next Steps

1. **Test locally** with `python scrape.py` + `python analyze_and_email.py`
2. **Add GitHub secrets** once working
3. **Enable workflow** — it will run at 9 AM UTC daily
4. **Adjust cron schedule** in `.github/workflows/daily_digest.yml` if needed
5. **Iterate on the prompt** based on email quality — modify `ANALYSIS_PROMPT` in `analyze_and_email.py`
