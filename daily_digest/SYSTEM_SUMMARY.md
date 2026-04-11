# Daily Digest System — Complete Overview

## What You Now Have

A complete **autonomous AI trend analysis pipeline** that runs on GitHub Actions daily and sends you actionable insights via email.

---

## The Flow (3 Steps)

```
STEP 1: Scrape Data              STEP 2: Analyze with GPT-4o      STEP 3: Send Email
┌─────────────────────┐         ┌──────────────────────┐         ┌────────────────┐
│ YouTube scrape      │ ──────> │ Filter for signal    │ ──────> │ Clean HTML     │
│ GitHub trending     │         │ Identify ROI levers  │         │ email with      │
│ X (Twitter) posts   │         │ Extract trends       │         │ 5-8 insights   │
│                     │         │ Generate JSON        │         │                │
│ → signals.json      │         │ → analysis.json      │         │ → ahmedgoatkr  │
└─────────────────────┘         └──────────────────────┘         │   @gmail.com   │
                                                                  └────────────────┘
    (runs daily 9 AM UTC on GitHub Actions)
```

---

## Files Created

### Core Scripts
- **`scrape.py`** — Clones Phase 1 & 1B; collects YouTube, GitHub, X data
- **`analyze_and_email.py`** — Sends signals to GPT-4o, generates HTML email, sends via Gmail

### Configuration
- **`.env.example`** — Template for all API keys (copy to `.env` locally)
- **`requirements.txt`** — Python dependencies (requests, google-api, beautifulsoup4, etc.)

### Automation
- **`.github/workflows/daily_digest.yml`** — GitHub Actions workflow (runs daily at 9 AM UTC)

### Documentation
- **`README.md`** — Quick start guide
- **`EXECUTION_PLAN.md`** — Step-by-step setup (do this first)
- **`PROMPT_BREAKDOWN.md`** — How the GPT-4o prompt works and why
- **`SYSTEM_SUMMARY.md`** — This file

---

## The Prompt (The Secret Sauce)

The GPT-4o prompt is designed to **filter noise and extract signal**:

### Filters Out:
- Incremental tool updates
- Speculative hype
- Generic tutorials
- Things that aren't "deploy today"

### Focuses On:
- Paradigm shifts (how automation is fundamentally changing)
- Measurable ROI (time/cost savings)
- Deploy-today solutions
- 30-day horizon (actionable soon)

### Output:
For each trend, GPT-4o extracts:
1. **Title** — Scannable trend name
2. **Description** — One sentence explaining what's happening
3. **Why now** — What triggered this trend to emerge
4. **ROI potential** — How you can make money on this
5. **Evidence** — Which GitHub/X/YouTube signals prove this
6. **Action item** — Concrete next step for your agency

---

## Cost & Budget

| Item | Cost/Run | Cost/Month |
|---|---|---|
| Data collection | Free | Free |
| GPT-4o analysis | $0.008–0.012 | ~$0.25–0.30 |
| **Total** | **~$0.01** | **~$0.30** |

**Your budget:** $5 in OpenRouter credits = 500 days of operation (1.3 years)

---

## The GPT-4o Model Choice

**Why GPT-4o?**
- Reliable structured output (JSON)
- Fast (2-5 seconds per run)
- Cheap ($0.008/run)
- Excellent at signal/noise filtering

**Alternatives:**
- Claude Sonnet: $0.015/run (same quality, 2x cost)
- GPT-4 Turbo: $0.01/run (more expensive, overkill for this task)
- GPT-3.5 Turbo: $0.002/run (too unreliable for filtering)

---

## Local Testing Checklist

Do this FIRST before enabling GitHub Actions:

- [ ] Have all 6 API keys (YouTube, GitHub, Apify, OpenRouter, Gmail user, Gmail app password)
- [ ] Created `.env` file in `daily_digest/` folder
- [ ] Filled in all values in `.env`
- [ ] Ran `pip install -r requirements.txt`
- [ ] Ran `python scrape.py` successfully
- [ ] Saw `daily_digest_signals.json` created
- [ ] Ran `python analyze_and_email.py` successfully
- [ ] Received email at ahmedgoatkr@gmail.com

---

## GitHub Actions Setup Checklist

Once local testing works:

- [ ] Added all 6 secrets to GitHub repo Settings → Secrets
- [ ] Verified `.github/workflows/daily_digest.yml` exists
- [ ] Ran workflow manually from Actions tab
- [ ] Waited 2-3 minutes for completion
- [ ] Checked email inbox for digest
- [ ] Checked GitHub Actions logs for any errors

---

## What Gets Sent to GPT-4o

```json
{
  "collected_at": "2024-04-11T14:30:00",
  "youtube": [
    {
      "channel": "Nateherk",
      "title": "Building Autonomous Agents with Claude",
      "url": "...",
      "views": 12000,
      "transcript_excerpt": "..."
    }
  ],
  "github": [
    {
      "name": "anthropics/agents",
      "description": "Framework for building autonomous agents",
      "stars": 850,
      "roi_score": 8,
      "roi_reason": "Clear automation + enterprise use"
    }
  ],
  "x_posts": [
    {
      "author": "AnthropicAI",
      "text": "Agents are the future of automation...",
      "likes": 5000,
      "created_at": "2024-04-10"
    }
  ]
}
```

GPT-4o reads this and returns structured trends.

---

## Email Output Example

**Subject:** Daily AI Trends — April 11, 2024

**Body:**
```
Executive Summary:
The biggest shift happening in AI automation right now is the move 
from static, pre-programmed workflows to autonomous agents that can 
decide their own execution path. This is driven by new APIs from 
major labs and rising client demand for "set it and forget it" 
automation.

──────────────────────────────────────────

Top Trends This Week:

1. Workflows → Agents Paradigm Shift
   What: Automation moving from step-by-step workflows to 
         autonomous agents that decide next steps
   Why now: Anthropic, Google, OpenAI all released agent frameworks
   ROI: 60-70% faster setup. Charge 2x premium for "autonomous"
   Evidence: GitHub (agent-framework-js trending), 
            X (@AnthropicAI), YouTube (Nick Saraev video)
   → Action: Build n8n "agent launcher" template for clients

2. Structured Output Over Embeddings
   [similar format...]
   
[... 5-8 total trends ...]
```

---

## Customization Points

### 1. Change Email Content
- Edit `generate_html_email()` in `analyze_and_email.py`
- Modify HTML colors, headers, footer

### 2. Change Analysis Prompt
- Edit `ANALYSIS_PROMPT` in `analyze_and_email.py`
- Adjust filters, focus areas, output structure
- Test locally before deploying

### 3. Change Scraping Sources
- Edit `X_ACCOUNTS` list in `scrape.py` (add/remove Twitter accounts)
- Edit `COMPETITORS` list (add/remove YouTube channels)
- Adjust `MAX_GITHUB_REPOS` if you want more/fewer repos

### 4. Change Schedule
- Edit `.github/workflows/daily_digest.yml`
- Change cron: `0 9 * * *` (currently 9 AM UTC daily)
- [Cron cheat sheet](https://crontab.guru/)

### 5. Change Email Recipient
- Edit `GMAIL_USER` in `.env` (currently both sender and receiver)
- Modify email delivery logic in `analyze_and_email.py` if needed

---

## Monitoring & Debugging

### Check If It's Running
1. Go to GitHub repo → Actions tab
2. Look for "Daily AI Trends Digest" workflow
3. Check the last run time and status

### View Logs
1. Click on the latest run
2. Expand "Analyze with GPT-4o" step
3. See full output and errors

### Download Signals (for debugging)
1. Click on the run
2. Scroll to "Artifacts"
3. Download `daily_digest_signals.json`
4. Use to test locally with `analyze_and_email.py`

### Test Locally First
Always test changes locally before committing:
```bash
python scrape.py          # Collect data
python analyze_and_email.py  # Analyze and send
```

---

## Next 24 Hours

### Before You Sleep (Today)
1. Read `EXECUTION_PLAN.md` completely
2. Gather your 6 API keys (YouTube, GitHub, Apify, OpenRouter, Gmail)
3. Copy `.env.example` to `.env` and fill in values
4. Run `pip install -r requirements.txt`

### Tomorrow Morning
1. Run `python scrape.py` (2-3 minutes)
2. Run `python analyze_and_email.py` (1 minute)
3. Check your email — you should have a digest!
4. Review the trends — do they make sense?

### Tomorrow Afternoon
1. Add all 6 secrets to GitHub repo
2. Manually trigger the workflow from Actions tab
3. Wait 3 minutes and check email again
4. If it worked, you're done! It will run daily at 9 AM UTC

### This Week
1. Get 2-3 emails and see if the trends match your expectations
2. If quality is good, you can ignore it and let it run autonomously
3. If you want different trends, edit the prompt and re-test locally

---

## Support & Troubleshooting

| Problem | Solution |
|---|---|
| Scraping timeout | Run again (Apify can be flaky) |
| Gmail auth fails | Ensure 16-char app password, not account password |
| GPT-4o error | Check OpenRouter balance; add credits if needed |
| No GitHub output | Check workflow logs; verify all secrets added |
| X posts missing | Optional; GitHub + YouTube still work without it |

---

## Success Criteria

You'll know it's working when:
1. ✅ Local `scrape.py` creates `daily_digest_signals.json`
2. ✅ Local `analyze_and_email.py` sends you an email
3. ✅ GitHub Actions manual run succeeds
4. ✅ You wake up tomorrow and have a new email digest
5. ✅ The trends make sense and are actionable

---

## That's It!

You now have a complete autonomous system. Start with **EXECUTION_PLAN.md** and follow the steps.

The hardest part is done — just need to add your API keys and run.
