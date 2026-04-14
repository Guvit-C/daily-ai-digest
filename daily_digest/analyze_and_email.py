#!/usr/bin/env python3
"""
Daily Digest — Analysis + HTML Email

Reads daily_digest_signals.json, formats signals as structured text,
sends to Gemini 2.5 Flash (via OpenRouter) for trend analysis,
generates a clean HTML email, and sends via Gmail.
"""

import os
import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    exit(1)

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# Model: Gemini 2.5 Flash via OpenRouter
# Chosen because: large context window, cheap, fast, handles structured prompts well
MODEL = "google/gemini-2.5-flash"

# -------------------------------------------------------------------
# ANALYSIS PROMPT
#
# We send pre-formatted plain text sections (not raw JSON) so the model
# can read it like a human would. Each section is labeled by source type
# and sorted by signal strength.
# -------------------------------------------------------------------
ANALYSIS_PROMPT = """You are an AI research analyst. Your job is to surface the highest-value AI developments from today's signals — things that save real time, reduce cost, or make AI systems work better.

Below are today's signals from four sources:
- RSS (official blogs: Anthropic, OpenAI, Google DeepMind, HuggingFace, The Batch) — highest trust, breaks news first
- X Posts (industry leaders and researchers) — early signal, sometimes noisy
- GitHub Trending (what developers are actually building) — shows real adoption
- Reddit r/LocalLLaMA & r/MachineLearning (practitioners) — street-level signal, what works in practice

---

{formatted_signals}

---

WHAT COUNTS AS GOLD — prioritize these above everything else:
1. TIME-SAVED: Something that replaces hours of manual work per week through automation
2. COST-REDUCED: Replaces expensive tools, services, or headcount with AI
3. META-AI-ROI: Makes your AI usage itself better — self-improving systems, better context management,
   knowledge bases that compound, agents that improve their own prompts, AutoResearch-style loops,
   memory systems, smarter workflows for using AI. Think Karpathy's AutoResearch or an Obsidian
   knowledge base that makes every future AI query more accurate. These multiply ROI over time.
4. NEW-REVENUE: Opens a new income stream or competitive advantage that didn't exist before

GOLD EXAMPLES (use these to calibrate your scoring):
- An agent that reads papers and rewrites its own prompts to get better answers → gold (meta-ai-roi)
- A system that builds a personal knowledge base so your AI always has context → gold (meta-ai-roi)
- A tool that monitors your inbox and auto-drafts replies → gold (time-saved)
- An open-source model that matches GPT-4 performance at 1/10th the cost → gold (cost-reduced)
- A new fine-tuning technique that makes small models accurate for a niche task → gold (cost-reduced + meta-ai-roi)

NOT GOLD EXAMPLES:
- "GPT-4o now supports 16 more languages" → incremental, no workflow change
- "How to write better prompts" tutorial → not a new capability
- A new AI image generator with no unique business use case → low ROI signal
- A version bump with no new capability → skip unless it crosses a threshold

IMPORTANT: Do NOT filter out research papers or technical posts just because they sound academic.
If a paper or technique crosses a capability threshold or enables a new workflow, it is gold.
A "tutorial" that teaches a genuinely new technique (not just how to use an existing tool) is also gold.

YOUR TASK:
Read all signals. Identify 4 to 6 items that score highest on the GOLD criteria above.
Sort them by gold_score descending — highest value first.

Return a JSON object with this exact structure:
{
  "trends": [
    {
      "title": "Short clear title",
      "gold_score": 4,
      "gold_reason": "One sentence on why this scores high — what specifically it unlocks",
      "roi_category": "time-saved | cost-reduced | meta-ai-roi | new-revenue",
      "simple_explanation": "2-3 sentences in plain English — what this is, no jargon",
      "why_now": "What specifically triggered this right now",
      "business_benefits": ["concrete benefit 1", "concrete benefit 2", "concrete benefit 3"],
      "best_for": "Who benefits most (e.g. solo operators, agencies, content teams, developers)",
      "action_item": "One concrete thing to try or look into this week",
      "sources": [
        {"type": "rss|x|github|reddit", "title": "title or handle", "url": "url"}
      ]
    }
  ],
  "executive_summary": "2-3 sentences on the single biggest shift happening right now, in plain business language"
}

RULES:
- gold_score is 1-5: 5 = immediate, obvious ROI; 1 = weak signal, low impact
- Use simple English. Replace: embeddings→stored knowledge, tokens→words, API→connection, model→AI system
- Business benefits must be specific: "saves 3 hours/week", "replaces $200/month tool", not vague like "increases efficiency"
- Only include sources that directly support the trend
- Return ONLY valid JSON — no markdown, no preamble"""


def load_signals():
    """Load scraped signals from disk."""
    signal_file = "./daily_digest_signals.json"
    if not os.path.exists(signal_file):
        raise FileNotFoundError(f"Signal file not found: {signal_file} — run scrape.py first")

    with open(signal_file, "r", encoding="utf-8") as f:
        return json.load(f)


def format_signals_as_text(signals):
    """
    Convert raw signals JSON into clean labeled text sections.
    This is much better than dumping raw JSON — the model reads it like a human would.
    Each section has a clear header and compact per-item formatting.
    """
    lines = []

    # --- RSS Feeds ---
    rss = signals.get("rss", [])
    lines.append(f"=== RSS FEEDS — Official Blogs ({len(rss)} articles, last 48h) ===")
    if rss:
        for item in rss:
            lines.append(f"[{item.get('feed_name', 'Unknown')}] {item.get('title', '')}")
            if item.get("excerpt"):
                lines.append(f"  {item['excerpt'][:300]}")
            if item.get("url"):
                lines.append(f"  URL: {item['url']}")
            lines.append("")
    else:
        lines.append("(no articles retrieved)")
        lines.append("")

    # --- X Posts ---
    x_posts = signals.get("x_posts", [])
    lines.append(f"=== X POSTS — Industry Leaders ({len(x_posts)} posts) ===")
    if x_posts:
        for item in x_posts:
            lines.append(f"@{item.get('author', '')}: {item.get('text', '')}")
            lines.append(f"  Likes: {item.get('likes', 0)} | URL: {item.get('url', '')}")
            lines.append("")
    else:
        lines.append("(no posts retrieved)")
        lines.append("")

    # --- GitHub Trending ---
    github = signals.get("github", [])
    lines.append(f"=== GITHUB TRENDING — AI Repos ({len(github)} repos, this week) ===")
    if github:
        for item in github:
            lines.append(f"{item.get('name', '')} (⭐ {item.get('stars', 0):,})")
            lines.append(f"  {item.get('description', '')}")
            lines.append(f"  ROI score: {item.get('roi_score', 0)}/10 — {item.get('roi_reason', '')}")
            lines.append(f"  URL: {item.get('url', '')}")
            lines.append("")
    else:
        lines.append("(no repos retrieved)")
        lines.append("")

    # --- Reddit ---
    reddit = signals.get("reddit", [])
    lines.append(f"=== REDDIT — Practitioners ({len(reddit)} posts, today) ===")
    if reddit:
        for item in reddit:
            lines.append(f"r/{item.get('subreddit', '')} | {item.get('title', '')} (score: {item.get('score', 0)}, {item.get('num_comments', 0)} comments)")
            if item.get("selftext"):
                lines.append(f"  {item['selftext'][:200]}")
            lines.append(f"  URL: {item.get('url', '')}")
            lines.append("")
    else:
        lines.append("(no posts retrieved)")
        lines.append("")

    return "\n".join(lines)


def analyze_with_gemini(signals):
    """Send formatted signals to Gemini 2.5 Flash via OpenRouter for trend analysis."""
    if not OPENROUTER_API_KEY:
        raise ValueError("ERROR: OPENROUTER_API_KEY not found in .env")

    print(f"  Model: {MODEL}")
    print(f"  API key: {OPENROUTER_API_KEY[:20]}...")

    formatted = format_signals_as_text(signals)
    prompt = ANALYSIS_PROMPT.replace("{formatted_signals}", formatted)

    print(f"  Prompt size: ~{len(prompt.split()):,} words")

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,   # lower = more factual, less hallucination
        "max_tokens": 3000,
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Guvit-C/daily-ai-digest",
        "X-Title": "Daily AI Digest",
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=90,
        )

        # Save full response for debugging
        with open("gemini_full_response.txt", "w", encoding="utf-8") as f:
            f.write(response.text)

        response.raise_for_status()
        result = response.json()

        if "choices" not in result or not result["choices"]:
            raise ValueError(f"No choices in response. Full response saved to gemini_full_response.txt")

        content = result["choices"][0]["message"]["content"]

        # Save raw content for debugging
        with open("gemini_response.txt", "w", encoding="utf-8") as f:
            f.write(content)

        # Strip markdown code fences if the model added them
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        analysis = json.loads(content)
        return analysis

    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"OpenRouter API error {response.status_code}: {response.text[:500]}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Request failed: {str(e)}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse model response as JSON: {str(e)}\nRaw: {content[:500]}")


def esc(text):
    """Escape special HTML characters to prevent broken email rendering."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def generate_source_feed_html(signals):
    """Generate the full raw source listing at the bottom of the email."""

    rss_rows = ""
    for item in signals.get("rss", []):
        rss_rows += f"""
        <tr>
            <td style="padding:8px 0;border-bottom:1px solid #f0f0f0;">
                <a href="{item.get('url','#')}" style="color:#0066cc;text-decoration:none;font-size:13px;font-weight:500;">{esc(item.get('title',''))}</a>
                <span style="color:#999;font-size:11px;display:block;margin-top:2px;">{esc(item.get('feed_name',''))} &mdash; {item.get('published','')[:10]}</span>
            </td>
        </tr>"""

    github_rows = ""
    for repo in signals.get("github", []):
        github_rows += f"""
        <tr>
            <td style="padding:8px 0;border-bottom:1px solid #f0f0f0;">
                <a href="{repo.get('url','#')}" style="color:#0066cc;text-decoration:none;font-size:13px;font-weight:500;">{esc(repo.get('name',''))}</a>
                <span style="color:#999;font-size:11px;display:block;margin-top:2px;">{esc(repo.get('description','')[:100])} &mdash; &#x2B50; {repo.get('stars',0):,}</span>
            </td>
        </tr>"""

    x_rows = ""
    for post in signals.get("x_posts", []):
        preview = esc(post.get("text", "")[:120])
        x_rows += f"""
        <tr>
            <td style="padding:8px 0;border-bottom:1px solid #f0f0f0;">
                <a href="{post.get('url','#')}" style="color:#0066cc;text-decoration:none;font-size:13px;font-weight:500;">@{esc(post.get('author',''))}</a>
                <span style="color:#555;font-size:12px;display:block;margin-top:2px;">{preview}...</span>
            </td>
        </tr>"""

    reddit_rows = ""
    for post in signals.get("reddit", []):
        reddit_rows += f"""
        <tr>
            <td style="padding:8px 0;border-bottom:1px solid #f0f0f0;">
                <a href="{post.get('url','#')}" style="color:#0066cc;text-decoration:none;font-size:13px;font-weight:500;">{esc(post.get('title',''))}</a>
                <span style="color:#999;font-size:11px;display:block;margin-top:2px;">r/{esc(post.get('subreddit',''))} &mdash; {post.get('score',0):,} upvotes &mdash; {post.get('num_comments',0)} comments</span>
            </td>
        </tr>"""

    return f"""
    <div style="margin-top:40px;border-top:2px solid #e0e0e0;padding-top:30px;">
        <h2 style="color:#333;font-size:18px;margin-bottom:6px;">Full Source Feed</h2>
        <p style="color:#666;font-size:13px;margin:0 0 24px 0;">Everything collected today. Browse at your own pace.</p>

        <h3 style="color:#d44000;font-size:14px;margin:0 0 8px 0;text-transform:uppercase;letter-spacing:1px;">
            RSS — Official Blogs ({len(signals.get('rss', []))} articles)
        </h3>
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">{rss_rows}</table>

        <h3 style="color:#333;font-size:14px;margin:0 0 8px 0;text-transform:uppercase;letter-spacing:1px;">
            GitHub Trending ({len(signals.get('github', []))} repos)
        </h3>
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">{github_rows}</table>

        <h3 style="color:#1da1f2;font-size:14px;margin:0 0 8px 0;text-transform:uppercase;letter-spacing:1px;">
            X Posts ({len(signals.get('x_posts', []))} posts)
        </h3>
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">{x_rows}</table>

        <h3 style="color:#ff4500;font-size:14px;margin:0 0 8px 0;text-transform:uppercase;letter-spacing:1px;">
            Reddit ({len(signals.get('reddit', []))} posts)
        </h3>
        <table width="100%" cellpadding="0" cellspacing="0">{reddit_rows}</table>
    </div>
    """


def generate_html_email(analysis, signals=None):
    """Build the full HTML email from trend analysis."""
    trends_html = ""

    for i, trend in enumerate(analysis.get("trends", []), 1):
        # Sources
        sources_html = ""
        sources = trend.get("sources", [])
        if sources:
            sources_html = '<div style="margin-top:12px;padding-top:12px;border-top:1px solid #e0e0e0;">'
            sources_html += '<p style="margin:0 0 8px 0;color:#666;font-size:12px;font-weight:600;text-transform:uppercase;">Sources:</p>'
            for s in sources:
                label = s.get("type", "").upper()
                title = s.get("title", "Link")
                url = s.get("url", "#")
                sources_html += f'<div style="margin-bottom:6px;"><a href="{url}" style="color:#0066cc;text-decoration:none;font-size:12px;">&#8594; [{label}] {title}</a></div>'
            sources_html += "</div>"

        # Benefits list
        benefits = trend.get("business_benefits", [])
        benefits_html = ""
        if benefits:
            benefits_html = '<ul style="margin:8px 0;padding-left:20px;color:#333;font-size:13px;">'
            for b in benefits:
                benefits_html += f"<li style='margin-bottom:4px;'>{b}</li>"
            benefits_html += "</ul>"

        # Gold score bar — filled dots out of 5
        gold_score = int(trend.get("gold_score", 0))
        gold_score = max(1, min(5, gold_score))  # clamp to 1-5
        score_dots = ("&#9679;" * gold_score) + ("&#9675;" * (5 - gold_score))

        # ROI category badge colors
        roi_colors = {
            "time-saved":    "#e67e22",
            "cost-reduced":  "#8e44ad",
            "meta-ai-roi":   "#0066cc",
            "new-revenue":   "#27ae60",
        }
        roi_category = trend.get("roi_category", "").lower().strip()
        roi_color = roi_colors.get(roi_category, "#888")
        roi_label = roi_category.replace("-", " ").upper() if roi_category else "UNCATEGORIZED"

        trends_html += f"""
        <div style="background:#f8f9fa;border-left:4px solid #0066cc;padding:20px;margin-bottom:20px;border-radius:4px;">

            <!-- Title row with ROI badge -->
            <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:10px;flex-wrap:wrap;gap:8px;">
                <h3 style="margin:0;color:#0066cc;font-size:16px;font-weight:600;">{i}. {trend.get('title','')}</h3>
                <span style="background:{roi_color};color:white;font-size:10px;font-weight:700;padding:3px 8px;border-radius:20px;white-space:nowrap;letter-spacing:0.5px;">{roi_label}</span>
            </div>

            <!-- Gold score -->
            <p style="margin:0 0 12px 0;font-size:12px;color:#888;">
                Gold score: <span style="color:#f39c12;letter-spacing:2px;">{score_dots}</span>
                <span style="color:#999;margin-left:6px;font-style:italic;">{trend.get('gold_reason','')}</span>
            </p>

            <!-- Simple explanation -->
            <div style="background:white;padding:12px;border-radius:3px;margin-bottom:12px;border-left:3px solid #27ae60;">
                <p style="margin:0 0 4px 0;color:#27ae60;font-size:13px;font-weight:600;">In simple terms:</p>
                <p style="margin:0;color:#555;font-size:13px;line-height:1.6;">{trend.get('simple_explanation','')}</p>
            </div>

            <p style="margin:8px 0;color:#333;font-size:13px;">
                <strong>Why now:</strong> {trend.get('why_now','')}
            </p>

            <p style="margin:8px 0 4px 0;color:#333;font-size:13px;font-weight:600;">Concrete benefits:</p>
            {benefits_html}

            <p style="margin:8px 0;color:#666;font-size:12px;font-style:italic;">
                <strong>Best for:</strong> {trend.get('best_for','')}
            </p>

            <p style="margin:12px 0 0 0;background:#fff;padding:10px;border-radius:3px;border-left:2px solid #27ae60;color:#27ae60;font-size:13px;font-weight:500;">
                &#8594; This week: {trend.get('action_item','')}
            </p>

            {sources_html}
        </div>
        """

    source_feed = generate_source_feed_html(signals) if signals else ""

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;color:#333;margin:0;padding:0;background:#f4f4f4;">
    <div style="max-width:620px;margin:20px auto;padding:0;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

        <!-- Header -->
        <div style="background:linear-gradient(135deg,#0066cc 0%,#0052a3 100%);color:white;padding:32px 30px;text-align:center;">
            <h1 style="margin:0;font-size:26px;font-weight:700;">Daily AI Digest</h1>
            <p style="margin:8px 0 0 0;font-size:14px;opacity:0.85;">{datetime.now().strftime('%B %d, %Y')}</p>
        </div>

        <div style="padding:30px;">

            <!-- Executive Summary -->
            <div style="background:#e8f4f8;border-left:4px solid #0066cc;padding:16px;margin-bottom:28px;border-radius:4px;">
                <p style="margin:0 0 6px 0;color:#0066cc;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Today's Big Picture</p>
                <p style="margin:0;color:#333;font-size:14px;line-height:1.7;">{analysis.get('executive_summary','')}</p>
            </div>

            <!-- Trends -->
            <h2 style="color:#333;font-size:18px;margin:0 0 20px 0;">Top Trends</h2>
            {trends_html}

            <!-- Full source feed -->
            {source_feed}

        </div>

        <!-- Footer -->
        <div style="border-top:1px solid #eee;padding:20px 30px;text-align:center;color:#aaa;font-size:11px;background:#fafafa;">
            Daily AI Digest &mdash; {datetime.now().strftime('%Y-%m-%d %H:%M UTC')} &mdash; Model: {MODEL}
        </div>
    </div>
</body>
</html>"""

    return html


def send_email(html_content, recipient_email):
    """Send HTML email via Gmail SMTP."""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        raise ValueError("ERROR: GMAIL_USER or GMAIL_APP_PASSWORD not found in .env")

    print(f"  Sending email to {recipient_email}...")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Daily AI Digest — {datetime.now().strftime('%B %d, %Y')}"
    msg["From"] = GMAIL_USER
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, recipient_email, msg.as_string())
        print("  [OK] Email sent")
    except smtplib.SMTPAuthenticationError:
        raise RuntimeError("Gmail authentication failed — check GMAIL_USER and GMAIL_APP_PASSWORD in .env")
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {str(e)}")


def main():
    print("=" * 60)
    print("DAILY DIGEST — Analysis & Email")
    print("=" * 60)

    try:
        print("\n[1/3] Loading signals...")
        signals = load_signals()
        print(f"  RSS: {len(signals.get('rss',[]))} | GitHub: {len(signals.get('github',[]))} | X: {len(signals.get('x_posts',[]))} | Reddit: {len(signals.get('reddit',[]))}")

        print(f"\n[2/3] Analyzing with {MODEL} via OpenRouter...")
        analysis = analyze_with_gemini(signals)
        print(f"  [OK] {len(analysis.get('trends',[]))} trends identified")

        print("\n[3/3] Generating and sending email...")
        html_email = generate_html_email(analysis, signals)
        send_email(html_email, GMAIL_USER)

        print("\n" + "=" * 60)
        print("[OK] DAILY DIGEST COMPLETE")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
