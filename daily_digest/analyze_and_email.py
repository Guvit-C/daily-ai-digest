#!/usr/bin/env python3
"""
Daily Digest — GPT-4o Analysis + HTML Email Generation

Reads daily_digest_signals.json, sends to GPT-4o for trend analysis,
generates HTML email, and sends it via Gmail.
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

ANALYSIS_PROMPT = """You are an AI research analyst for business owners and automation professionals. Your job is to explain AI/automation trends in plain English, without jargon.

Read the raw signals below (GitHub repos, X posts, YouTube videos). Find what's ACTUALLY happening in AI automation RIGHT NOW.

FILTER OUT:
- Incremental improvements to existing tools
- Speculative hype without real implementations
- Content that's just "AI is cool"
- Generic tutorials
- Anything requiring 6+ months to understand or deploy

FOCUS ON:
- New ways of working that are fundamentally different
- Tools/patterns that save measurable time or money
- Things non-technical business owners can understand
- Deployable solutions (not research papers)
- Things that matter in the next 30-90 days

For each trend, explain it so a business owner (not a technologist) understands:
- WHAT it is (simple terms, no jargon)
- HOW it works (step-by-step, like explaining to a 10-year-old)
- WHY it matters NOW (what changed recently)
- BUSINESS BENEFITS (how it saves money, time, or opens revenue)
- WHO it helps (what type of business/role benefits most)

Return a JSON object with:
- "trends": array of trend objects with:
  - title: short, clear name
  - simple_explanation: 2-3 sentences explaining WHAT this is, in plain English
  - how_it_works: 3-4 sentences on HOW it works, step by step
  - why_now: what triggered this to appear NOW
  - business_benefits: list of 3-4 concrete benefits (saves X hours/week, reduces cost, etc)
  - best_for: who benefits most (e.g., "agencies managing multiple clients", "content creators", "sales teams")
  - sources: array of source objects with "type", "title", "url", "excerpt"
  - action_item: one concrete step to try or explore
- "executive_summary": 2-3 sentences about biggest shift, in plain business language

SIGNALS DATA:
{signals_data}

IMPORTANT: Use simple English. Avoid: embeddings, tokens, vectors, APIs, frameworks, models (replace with "AI system").
Explain benefits in business terms: time saved per week, cost reduction, new revenue opportunity, customer satisfaction, etc.
For each source, include the actual URL so links work.
Return ONLY valid JSON. No markdown."""


def load_signals():
    """Load the scraped signals."""
    signal_file = "./daily_digest_signals.json"
    if not os.path.exists(signal_file):
        raise FileNotFoundError(f"Signal file not found: {signal_file}")

    with open(signal_file, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_with_gpt4o(signals_data):
    """Send signals to GPT-4o for analysis via OpenRouter."""
    if not OPENROUTER_API_KEY:
        raise ValueError("ERROR: OPENROUTER_API_KEY not found in .env")

    print("  Sending signals to GPT-4o...")
    print(f"    API Key check: {OPENROUTER_API_KEY[:20]}...")

    signals_json = json.dumps(signals_data, indent=2, ensure_ascii=False)
    prompt = ANALYSIS_PROMPT.replace("{signals_data}", signals_json)

    payload = {
        "model": "openai/gpt-4o",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()

        # Debug: save full response
        with open("gpt4o_full_response.txt", "w", encoding="utf-8") as f:
            f.write(json.dumps(result, indent=2))

        if "choices" not in result or not result["choices"]:
            raise ValueError(f"No choices in GPT-4o response. Full response: {result}")

        content = result["choices"][0]["message"]["content"]

        # Debug: save the response
        with open("gpt4o_response.txt", "w", encoding="utf-8") as f:
            f.write(content)

        # Parse JSON from response (handle markdown code blocks)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        analysis = json.loads(content)
        return analysis

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"GPT-4o API call failed: {str(e)}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse GPT-4o response as JSON: {str(e)}\nRaw response: {content[:500]}")


def generate_html_email(analysis):
    """Generate clean HTML email from analysis."""
    trends_html = ""

    for i, trend in enumerate(analysis.get("trends", []), 1):
        sources = trend.get('sources', [])
        sources_html = ""

        if sources:
            sources_html = '<div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #e0e0e0;">'
            sources_html += '<p style="margin: 0 0 8px 0; color: #666; font-size: 12px; font-weight: 600; text-transform: uppercase;">Sources:</p>'
            for source in sources:
                source_type = source.get('type', 'N/A').upper()
                source_title = source.get('title', 'Link')
                source_url = source.get('url', '#')

                sources_html += f'<div style="margin-bottom: 6px;"><a href="{source_url}" style="color: #0066cc; text-decoration: none; font-size: 12px;">→ [{source_type}] {source_title}</a></div>'

            sources_html += '</div>'

        benefits = trend.get('business_benefits', [])
        benefits_html = ""
        if benefits:
            benefits_html = '<ul style="margin: 8px 0; padding-left: 20px; color: #333; font-size: 13px;">'
            for benefit in benefits:
                benefits_html += f'<li style="margin-bottom: 4px;">{benefit}</li>'
            benefits_html += '</ul>'

        trends_html += f"""
        <div style="background: #f8f9fa; border-left: 4px solid #0066cc; padding: 20px; margin-bottom: 20px; border-radius: 4px;">
            <h3 style="margin: 0 0 12px 0; color: #0066cc; font-size: 16px; font-weight: 600;">
                {i}. {trend.get('title', 'N/A')}
            </h3>

            <div style="background: white; padding: 12px; border-radius: 3px; margin-bottom: 12px; border-left: 3px solid #27ae60;">
                <p style="margin: 0 0 6px 0; color: #333; font-size: 13px;">
                    <strong style="color: #27ae60;">In simple terms:</strong>
                </p>
                <p style="margin: 0; color: #555; font-size: 13px; line-height: 1.5;">
                    {trend.get('simple_explanation', 'N/A')}
                </p>
            </div>

            <p style="margin: 8px 0; color: #333; font-size: 13px; line-height: 1.5;">
                <strong>How it works:</strong><br>
                {trend.get('how_it_works', 'N/A')}
            </p>

            <p style="margin: 8px 0; color: #333; font-size: 13px;">
                <strong>Why now:</strong> {trend.get('why_now', 'N/A')}
            </p>

            <div>
                <p style="margin: 8px 0 4px 0; color: #333; font-size: 13px; font-weight: 600;">
                    Concrete benefits:
                </p>
                {benefits_html}
            </div>

            <p style="margin: 8px 0; color: #666; font-size: 12px; font-style: italic;">
                <strong>Best for:</strong> {trend.get('best_for', 'N/A')}
            </p>

            <p style="margin: 12px 0 0 0; background: #fff; padding: 10px; border-radius: 3px; border-left: 2px solid #27ae60; color: #27ae60; font-size: 13px; font-weight: 500;">
                → Next step: {trend.get('action_item', 'N/A')}
            </p>

            {sources_html}
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%); color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 28px; font-weight: 700; }}
            .header p {{ margin: 8px 0 0 0; font-size: 14px; opacity: 0.9; }}
            .summary {{ background: #e8f4f8; border-left: 4px solid #0066cc; padding: 16px; margin-bottom: 25px; border-radius: 4px; }}
            .summary p {{ margin: 0; color: #333; font-size: 14px; line-height: 1.6; }}
            .footer {{ border-top: 1px solid #ddd; margin-top: 30px; padding-top: 20px; text-align: center; color: #999; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Daily AI Trends</h1>
                <p>{datetime.now().strftime('%B %d, %Y')}</p>
            </div>

            <div class="summary">
                <p><strong>Executive Summary:</strong></p>
                <p>{analysis.get('executive_summary', 'Analysis complete.')}</p>
            </div>

            <h2 style="color: #333; font-size: 18px; margin-bottom: 20px;">Top Trends This Week</h2>

            {trends_html}

            <div class="footer">
                <p>Generated by Daily Digest Analyzer | {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


def send_email(html_content, recipient_email):
    """Send HTML email via Gmail."""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        raise ValueError("ERROR: GMAIL_USER or GMAIL_APP_PASSWORD not found in .env")

    print(f"  Sending email to {recipient_email}...")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Daily AI Trends — {datetime.now().strftime('%B %d, %Y')}"
    msg["From"] = GMAIL_USER
    msg["To"] = recipient_email

    part = MIMEText(html_content, "html")
    msg.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, recipient_email, msg.as_string())
        print(f"  [OK] Email sent successfully")
    except smtplib.SMTPAuthenticationError:
        raise RuntimeError("Gmail authentication failed. Check GMAIL_USER and GMAIL_APP_PASSWORD.")
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {str(e)}")


def main():
    print("="*60)
    print("DAILY DIGEST — Analysis & Email")
    print("="*60)

    try:
        print("\n[1/3] Loading signals...")
        signals = load_signals()
        print(f"  [OK] Loaded {len(signals.get('youtube', []))} YouTube, {len(signals.get('github', []))} GitHub, {len(signals.get('x_posts', []))} X posts")

        print("\n[2/3] Analyzing with GPT-4o...")
        analysis = analyze_with_gpt4o(signals)
        print(f"  [OK] Analysis complete ({len(analysis.get('trends', []))} trends identified)")

        print("\n[3/3] Generating and sending email...")
        html_email = generate_html_email(analysis)

        # Send email (both sender and receiver are the same as per user request)
        send_email(html_email, GMAIL_USER)

        print("\n" + "="*60)
        print("[OK] DAILY DIGEST COMPLETE")
        print("="*60)

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
