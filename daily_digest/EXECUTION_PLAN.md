# Daily Digest Execution Plan

## Overview

You have a fully functional daily AI trends pipeline that will:
1. Scrape YouTube, GitHub, and X data daily
2. Send it to GPT-4o for intelligent analysis
3. Generate a clean HTML email summarizing trends
4. Run autonomously on GitHub Actions (no cost to you)

**Total cost:** ~$0.30/month (GPT-4o analysis)

---

## Phase 1: Local Testing (Do This First)

### Step 1a — Prepare Environment

1. Navigate to the daily_digest folder:
   ```bash
   cd daily_digest
   ```

2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and fill in these values:

   ```
   YOUTUBE_API_KEY=your_key_here
   GITHUB_TOKEN=your_token_here  (optional)
   APIFY_API_KEY=your_key_here
   OPENROUTER_API_KEY=your_key_here
   GMAIL_USER=ahmedgoatkr@gmail.com
   GMAIL_APP_PASSWORD=your_app_password_here
   ```

### Step 1b — Get API Keys

You need 5 things. Here's the fastest path for each:

**1. YouTube Data API v3** (free)
- Go to: https://console.cloud.google.com/
- Create new project (or use existing)
- Enable "YouTube Data API v3"
- Create API key: Credentials → Create Credentials → API Key
- Copy the key to `.env`

**2. GitHub Token** (optional, but recommended)
- Go to: https://github.com/settings/tokens
- Click "Generate new token (classic)"
- Check `public_repo` scope
- Copy the token to `.env`

**3. Apify API Key** (free tier available)
- Go to: https://apify.com/
- Sign up → Dashboard → Settings → API tokens
- Copy the token to `.env`
- Note: Free tier lets you scrape ~30 profiles/month. If you hit limits, upgrade to pay-as-you-go (~$0.001/run)

**4. OpenRouter API Key** (costs money, but cheap)
- Go to: https://openrouter.ai/
- Sign up → Settings → API Keys
- Create new key
- Copy to `.env`
- You need to set up a payment method and have credits (~$1-5 should last months at this volume)

**5. Gmail App Password** (free)
- Go to: https://myaccount.google.com/security
- Scroll to "App passwords"
- Select "Mail" + "Windows Computer" (or your device)
- Google generates a 16-char password
- Copy to `.env`

### Step 1c — Install and Run

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Test data collection (Phase 1 & 1B):
   ```bash
   python scrape.py
   ```
   
   **Expected output:**
   - Fetches 2 YouTube videos
   - Fetches ~25 GitHub repos
   - Fetches X posts from 10 accounts
   - Creates `daily_digest_signals.json`
   
   **Troubleshooting:**
   - If X posts fail (connection timeout, etc.), that's OK — GitHub + YouTube will still work
   - Apify can be flaky; if it times out, run again

3. Test analysis and email:
   ```bash
   python analyze_and_email.py
   ```
   
   **Expected output:**
   - Sends all signals to GPT-4o
   - GPT-4o returns 5-8 trends (as JSON)
   - Generates HTML email
   - Sends email to ahmedgoatkr@gmail.com
   - Check your inbox in 30 seconds
   
   **Troubleshooting:**
   - If Gmail fails: check that GMAIL_APP_PASSWORD is 16 chars (not your account password)
   - If GPT-4o fails: verify OPENROUTER_API_KEY is valid and you have credits
   - Check `daily_digest_signals.json` exists before running step 3

---

## Phase 2: GitHub Actions Setup (Autonomous Daily Runs)

Once local testing works, set up automation.

### Step 2a — Add GitHub Secrets

1. Go to your repo → Settings → Secrets and variables → Actions

2. Click "New repository secret" and add these 6 secrets:
   - `YOUTUBE_API_KEY` = [your YouTube API key]
   - `GITHUB_TOKEN` = [your GitHub token, or leave blank if not using]
   - `APIFY_API_KEY` = [your Apify key]
   - `OPENROUTER_API_KEY` = [your OpenRouter key]
   - `GMAIL_USER` = ahmedgoatkr@gmail.com
   - `GMAIL_APP_PASSWORD` = [your Gmail app password]

### Step 2b — Verify Workflow File

Check that `.github/workflows/daily_digest.yml` exists in your repo.

It should:
- Run daily at 9 AM UTC
- Trigger `scrape.py` → `analyze_and_email.py`
- Upload signals as artifact for debugging

### Step 2c — Test the Workflow

1. Go to your repo → Actions → "Daily AI Trends Digest"

2. Click "Run workflow" → "Run workflow" (manual trigger)

3. Wait 2-3 minutes for it to complete

4. Check:
   - Workflow status (green = success)
   - Your email inbox (you should receive a new digest email)
   - Artifacts tab (should have `daily_digest_signals.json` for debugging)

### Step 2d — Adjust Schedule (Optional)

The workflow runs daily at 9 AM UTC. If you want a different time:

1. Edit `.github/workflows/daily_digest.yml`

2. Change the cron line:
   ```yaml
   - cron: '0 9 * * *'  # 9 AM UTC, every day
   ```
   
   **Common schedules:**
   - `0 9 * * 1-5` = Weekdays only at 9 AM
   - `0 9 * * 0` = Sundays only
   - `0 9,15 * * *` = 9 AM and 3 PM UTC daily
   - [Cron cheat sheet](https://crontab.guru/)

3. Commit and push to main branch

---

## Phase 3: Iterate and Customize

Once the pipeline is running, you can refine it.

### Customizing the Prompt

The GPT-4o prompt lives in `analyze_and_email.py` as `ANALYSIS_PROMPT`.

**Current filtering rules:**
- Ignore incremental tool updates
- Ignore generic tutorials
- Focus on paradigm shifts (workflow → agent-based, etc.)
- Focus on deployed-today solutions with measurable ROI

**To change behavior:**

Edit the `ANALYSIS_PROMPT` variable and modify:
- What to filter out (e.g., add "budget too high")
- What to focus on (e.g., "free tools only")
- Output structure (add/remove fields)

Re-run locally to test, then commit to main branch.

### Email Template Customization

The email HTML is generated in `analyze_and_email.py` in the `generate_html_email()` function.

You can:
- Change colors (currently blue `#0066cc`)
- Add your logo
- Change header text
- Reorder fields
- Add footer links

---

## Cost Breakdown

| Component | Cost/Run | Cost/Month |
|---|---|---|
| YouTube API | Free | Free |
| GitHub API | Free | Free |
| Apify (X scraping) | ~$0.001 | ~$0.03 |
| OpenRouter (GPT-4o) | ~$0.01 | ~$0.30 |
| Gmail | Free | Free |
| **Total** | ~$0.011 | **~$0.33** |

**Budget:** You can run this indefinitely on ~$5 OpenRouter credits (at current volume).

---

## Troubleshooting Checklist

### Local Testing Issues

- [ ] All 6 API keys filled in `.env`?
- [ ] API keys valid and have credits/quota?
- [ ] `pip install -r requirements.txt` completed?
- [ ] Running from `daily_digest/` folder?
- [ ] `daily_digest_signals.json` created by `scrape.py`?

### GitHub Actions Issues

- [ ] All 6 secrets added to repo?
- [ ] Secrets spelled exactly as in the workflow file?
- [ ] `.github/workflows/daily_digest.yml` in correct path?
- [ ] Workflow file syntax valid (check in GitHub UI)?
- [ ] Check "Actions" tab for error messages?

### Email Not Arriving

- [ ] `GMAIL_APP_PASSWORD` is 16-char app password (not account password)?
- [ ] Check spam folder?
- [ ] Try manually running analyze_and_email.py locally?

### GPT-4o Failing

- [ ] Check OpenRouter dashboard for credits balance?
- [ ] Try updating `analyze_and_email.py` to use `openai/gpt-4-turbo` instead (cheaper, slightly slower)?
- [ ] Check error message in GitHub Actions logs?

---

## What's Next

1. **Test locally** (Phase 1)
2. **Enable GitHub Actions** (Phase 2)
3. **Review first 2-3 emails** and refine the prompt if needed
4. **Set up a read-only Supabase table** (optional) to log all trends for future reference
5. **Create a Slack integration** (optional) to also post digests to Slack

---

## Quick Reference

- **Local scraping only:** `python scrape.py`
- **Local analysis only:** `python analyze_and_email.py` (requires `daily_digest_signals.json`)
- **Full local pipeline:** `python scrape.py && python analyze_and_email.py`
- **GitHub Actions dashboard:** Actions tab → Daily AI Trends Digest
- **Manual workflow trigger:** Actions → Daily AI Trends Digest → Run workflow
- **View logs:** Click the latest run → see step-by-step output

---

## Questions?

Check `README.md` in this folder for API setup details, or refer back to this plan.
