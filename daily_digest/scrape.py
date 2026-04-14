#!/usr/bin/env python3
"""
Daily Digest — Data Collection

Fetches:
  1. RSS feeds — official AI blogs (Anthropic, OpenAI, Google DeepMind, HuggingFace, The Batch)
  2. GitHub trending AI repos (weekly)
  3. X (Twitter) posts from key AI accounts via Apify
  4. Reddit top posts from r/LocalLLaMA and r/MachineLearning

Saves combined data to: daily_digest_signals.json
"""

import os
import json
import requests
import time
import feedparser
from datetime import datetime, timedelta
from dotenv import load_dotenv

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: BeautifulSoup4 not installed. Run: pip install beautifulsoup4")
    exit(1)

load_dotenv()

APIFY_API_KEY = os.getenv("APIFY_API_KEY")

# --- Config ---
GITHUB_TRENDING_URL = "https://github.com/trending?since=weekly"
APIFY_API_URL = "https://api.apify.com/v2"
APIFY_ACTOR = "simoit~x-twitter-profile-scrapper"

AI_KEYWORDS = [
    "ai", "llm", "agent", "automation", "machine-learning", "deep-learning",
    "neural", "nlp", "transformer", "claude", "gpt", "llama", "embeddings",
    "vector", "rag", "langchain", "mcp", "autonomous", "workflow"
]

MAX_GITHUB_REPOS = 15

X_ACCOUNTS = [
    "Google", "nvidia", "AnthropicAI", "geminicli", "antigravity",
    "claudeai", "ylecun", "goodfellow_ian", "demishassabis", "karpathy"
]
POSTS_PER_ACCOUNT = 3

# RSS sources — these are official blogs that break news first
RSS_SOURCES = [
    {"name": "Anthropic",              "url": "https://www.anthropic.com/news/rss.xml"},
    {"name": "OpenAI",                 "url": "https://openai.com/news/rss.xml"},
    {"name": "Google DeepMind",        "url": "https://deepmind.google/blog/rss.xml"},
    {"name": "HuggingFace",            "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "The Batch (DeepLearning.AI)", "url": "https://www.deeplearning.ai/the-batch/feed/"},
]
MAX_ARTICLES_PER_FEED = 3   # max articles per RSS source
RSS_HOURS_CUTOFF = 48       # only include articles from last 48 hours

# Reddit subreddits — practitioner discussion, real signal
REDDIT_SUBREDDITS = ["LocalLLaMA", "MachineLearning"]
REDDIT_POSTS_PER_SUB = 5


def get_rss_feeds():
    """Fetch recent articles from RSS feeds published in the last 48 hours."""
    print("  Fetching RSS feeds...")
    articles = []
    cutoff = datetime.now() - timedelta(hours=RSS_HOURS_CUTOFF)

    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(source["url"])

            if feed.bozo:
                # bozo flag means feedparser had trouble parsing — not always fatal
                print(f"    WARNING [{source['name']}]: Feed parse warning (still trying)")

            count = 0
            for entry in feed.entries[:10]:  # check up to 10 entries per feed
                # Parse published date
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        published = datetime(*entry.published_parsed[:6])
                    except Exception:
                        pass
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    try:
                        published = datetime(*entry.updated_parsed[:6])
                    except Exception:
                        pass

                # Skip entries older than cutoff (skip date check if date unavailable)
                if published and published < cutoff:
                    continue

                # Strip HTML from summary
                summary = ""
                raw_summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
                if raw_summary:
                    try:
                        soup = BeautifulSoup(raw_summary, "html.parser")
                        summary = soup.get_text()[:400].strip()
                    except Exception:
                        summary = raw_summary[:400]

                articles.append({
                    "source": "rss",
                    "feed_name": source["name"],
                    "title": entry.get("title", "No title"),
                    "url": entry.get("link", ""),
                    "published": published.isoformat() if published else "unknown",
                    "excerpt": summary,
                })
                count += 1

                if count >= MAX_ARTICLES_PER_FEED:
                    break

            print(f"    [{source['name']}]: {count} articles")

        except Exception as e:
            print(f"    ERROR [{source['name']}]: {str(e)}")

    print(f"  RSS: {len(articles)} articles total")
    return articles


def get_reddit_posts():
    """
    Fetch top posts from AI subreddits using Reddit's public JSON API.
    No API key or auth needed — just a proper User-Agent header.
    """
    print("  Fetching Reddit posts...")
    posts = []

    headers = {
        # Reddit requires a descriptive User-Agent or it blocks the request
        "User-Agent": "DailyAIDigest/1.0 (automated digest bot; github.com/Guvit-C/daily-ai-digest)"
    }

    for subreddit in REDDIT_SUBREDDITS:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/top.json?limit={REDDIT_POSTS_PER_SUB}&t=day"
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            data = response.json()
            items = data.get("data", {}).get("children", [])

            count = 0
            for item in items:
                post = item.get("data", {})

                # Skip mod posts and empty titles
                if not post.get("title") or post.get("distinguished"):
                    continue

                posts.append({
                    "source": "reddit",
                    "subreddit": subreddit,
                    "title": post.get("title", ""),
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    # selftext is the post body (empty for link posts)
                    "selftext": post.get("selftext", "")[:300].strip(),
                })
                count += 1

            print(f"    [r/{subreddit}]: {count} posts")
            time.sleep(1)  # be polite to Reddit's servers

        except Exception as e:
            print(f"    ERROR [r/{subreddit}]: {str(e)}")

    print(f"  Reddit: {len(posts)} posts total")
    return posts


def calculate_roi_score(description, readme_content):
    """Score a GitHub repo for business/automation relevance."""
    combined_text = (description + " " + readme_content).lower()

    business_keywords = {
        "saves time": 2, "faster": 1.5, "automation": 2, "automate": 2,
        "reduce cost": 2, "cost savings": 2, "efficiency": 1.5, "production": 1.5,
        "production-ready": 2, "enterprise": 1.5, "scale": 1.5, "business": 1,
        "workflow": 1.5, "pipeline": 1.5, "deploy": 1, "client": 1,
        "customer": 1, "revenue": 2, "roi": 3, "measurable": 1.5, "real-world": 1,
    }

    score = 0
    reasons = []

    for keyword, weight in business_keywords.items():
        if keyword in combined_text:
            score += weight
            reasons.append(keyword)

    score = min(score, 10)

    if score < 2:
        reason = "Generic AI tool, limited business context"
    elif score < 4:
        reason = f"Some business relevance: {', '.join(set(reasons[:2]))}"
    else:
        reason = f"Clear business value: {', '.join(set(reasons[:3]))}"

    return score, reason


def fetch_github_readme(repo_url):
    """Fetch first 2000 chars of a repo's README."""
    try:
        parts = repo_url.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1]

        for branch in ["main", "master"]:
            readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
            response = requests.get(readme_url, timeout=10)
            if response.status_code == 200:
                return response.text[:2000]

        return ""
    except Exception:
        return ""


def get_github_trending():
    """Scrape GitHub trending page for AI repos, score by business relevance."""
    print("  Fetching GitHub trending...")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(GITHUB_TRENDING_URL, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        repos = []
        seen = set()

        for article in soup.find_all("article", class_="Box-row"):
            try:
                link = article.find("h2", class_="h3").find("a")
                if not link:
                    continue

                repo_path = link.get("href", "").strip("/")
                repo_url = f"https://github.com{repo_path}"
                repo_name = repo_path.strip("/")

                if repo_name in seen:
                    continue
                seen.add(repo_name)

                description_elem = article.find("p", class_="col-9")
                description = description_elem.text.strip() if description_elem else ""

                stars_elem = article.find("span", class_="d-inline-block float-sm-right")
                stars_str = stars_elem.text.strip() if stars_elem else "0"
                try:
                    stars = int(stars_str.replace(",", "").split()[0])
                except Exception:
                    stars = 0

                topics = [t.text.strip() for t in article.find_all("a", class_="topic-tag")]

                # Only keep repos related to AI
                is_ai = any(
                    keyword in repo_name.lower() or
                    keyword in description.lower() or
                    keyword in " ".join(topics).lower()
                    for keyword in AI_KEYWORDS
                )

                if not is_ai:
                    continue

                readme = fetch_github_readme(repo_url)
                roi_score, roi_reason = calculate_roi_score(description, readme)

                repos.append({
                    "source": "github",
                    "name": repo_name,
                    "description": description,
                    "stars": stars,
                    "url": repo_url,
                    "topics": topics,
                    "roi_score": roi_score,
                    "roi_reason": roi_reason,
                })
            except Exception:
                pass

        # Sort by ROI score first, then stars
        repos.sort(key=lambda r: (r["roi_score"], r["stars"]), reverse=True)
        repos = repos[:MAX_GITHUB_REPOS]

        if not repos:
            print("  WARNING: GitHub trending returned 0 AI repos — GitHub may have changed their HTML structure. Check class names in get_github_trending().")
        else:
            print(f"  GitHub: {len(repos)} repos")
        return repos

    except Exception as e:
        print(f"  ERROR: GitHub scrape failed: {str(e)}")
        return []


def get_x_posts():
    """Fetch X (Twitter) posts via Apify actor."""
    if not APIFY_API_KEY:
        print("  WARNING: APIFY_API_KEY not set — skipping X posts")
        return []

    posts = []
    today = datetime.now().strftime("%Y-%m-%d")
    cutoff = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")

    for account in X_ACCOUNTS:
        success = False

        for attempt in range(2):
            try:
                print(f"  Scraping X: @{account} (attempt {attempt + 1}/2)...")

                actor_input = {
                    "endDate": today,
                    "includePinned": False,
                    "includeReplies": False,
                    "includeRetweets": False,
                    "limit": POSTS_PER_ACCOUNT,
                    "maxItems": POSTS_PER_ACCOUNT,
                    "startDate": cutoff,
                    "username": account,
                }

                run_url = f"{APIFY_API_URL}/acts/{APIFY_ACTOR}/runs"
                response = requests.post(
                    run_url,
                    json=actor_input,
                    params={"token": APIFY_API_KEY},
                    headers={"Content-Type": "application/json"},
                    timeout=120,
                )
                response.raise_for_status()
                run_id = response.json().get("data", {}).get("id")

                if not run_id:
                    raise RuntimeError("No run ID returned from Apify")

                # Poll until the Apify run finishes
                run_status = {}
                for _ in range(30):
                    status_url = f"{APIFY_API_URL}/acts/{APIFY_ACTOR}/runs/{run_id}"
                    status_response = requests.get(status_url, params={"token": APIFY_API_KEY}, timeout=30)
                    status_response.raise_for_status()
                    run_status = status_response.json().get("data", {})

                    if run_status.get("status") == "SUCCEEDED":
                        break
                    elif run_status.get("status") in ["FAILED", "ABORTED"]:
                        raise RuntimeError(f"Apify run ended with: {run_status.get('status')}")
                    time.sleep(2)
                else:
                    raise RuntimeError("Apify run timed out after 60 seconds")

                dataset_id = run_status.get("defaultDatasetId")
                if not dataset_id:
                    raise RuntimeError("No dataset ID in Apify run result")

                dataset_url = f"{APIFY_API_URL}/datasets/{dataset_id}/items"
                dataset_response = requests.get(dataset_url, params={"token": APIFY_API_KEY}, timeout=30)
                dataset_response.raise_for_status()
                items = dataset_response.json()

                for item in items[:POSTS_PER_ACCOUNT]:
                    if isinstance(item, str):
                        continue
                    text = item.get("rawContent")
                    if not text:
                        continue

                    posts.append({
                        "source": "x",
                        "author": account,
                        "text": text,
                        "url": item.get("url", f"https://x.com/{account}"),
                        "likes": item.get("likeCount", 0),
                        "created_at": item.get("date", ""),
                    })

                print(f"    [OK] @{account}: {len(items)} posts")
                success = True
                break

            except Exception as e:
                print(f"    [FAIL] @{account}: {str(e)}")
                if attempt < 1:
                    time.sleep(3)

        if not success:
            print(f"    SKIPPED @{account}")

    print(f"  X: {len(posts)} posts total")
    return posts


def main():
    print("=" * 60)
    print("DAILY DIGEST — Data Collection")
    print("=" * 60)

    signals = {
        "collected_at": datetime.now().isoformat(),
        "rss":     get_rss_feeds(),
        "github":  get_github_trending(),
        "x_posts": get_x_posts(),
        "reddit":  get_reddit_posts(),
    }

    output_path = "./daily_digest_signals.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(signals, f, indent=2, ensure_ascii=False)

    total = sum(len(signals[k]) for k in ["rss", "github", "x_posts", "reddit"])
    print(f"\n[OK] Collection complete — {total} signals saved to {output_path}")
    print(f"  RSS: {len(signals['rss'])} | GitHub: {len(signals['github'])} | X: {len(signals['x_posts'])} | Reddit: {len(signals['reddit'])}")


if __name__ == "__main__":
    main()
