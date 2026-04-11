#!/usr/bin/env python3
"""
Daily Digest — Phase 1 & 1B Scraping (Clone)

Fetches:
  1. YouTube competitor latest videos (Nateherk, Nick Saraev, Chase H AI)
  2. GitHub trending AI repos (weekly)
  3. X (Twitter) posts from key AI accounts

Saves combined data to: daily_digest_signals.json
"""

import os
import json
import requests
import time
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: BeautifulSoup4 not installed. Run: pip install beautifulsoup4")
    exit(1)

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
APIFY_API_KEY = os.getenv("APIFY_API_KEY")

GITHUB_TRENDING_URL = "https://github.com/trending?since=weekly"
APIFY_API_URL = "https://api.apify.com/v2"
APIFY_ACTOR = "simoit~x-twitter-profile-scrapper"

AI_KEYWORDS = [
    "ai", "llm", "agent", "automation", "machine-learning", "deep-learning",
    "neural", "nlp", "transformer", "claude", "gpt", "llama", "embeddings",
    "vector", "rag", "langchain", "mcp", "autonomous", "workflow"
]

MAX_GITHUB_REPOS = 25
ROI_SCORE_THRESHOLD = 2

X_ACCOUNTS = [
    "Google", "nvidia", "AnthropicAI", "geminicli", "antigravity",
    "claudeai", "ylecun", "goodfellow_ian", "demishassabis", "karpathy"
]
POSTS_PER_ACCOUNT = 3

COMPETITORS = [
    {"name": "Nateherk", "query": "Nateherk AI automation"},
    {"name": "Nick Saraev", "query": "Nick Saraev agentic workflow"},
    {"name": "Chase H AI", "query": "Chase H AI"}
]


def get_youtube_videos():
    """Fetch latest 2 videos from competitor channels."""
    if not YOUTUBE_API_KEY:
        print("ERROR: YOUTUBE_API_KEY not found in .env")
        return []

    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        all_videos = []

        for comp in COMPETITORS:
            print(f"  Fetching YouTube: {comp['name']}...")
            search_response = youtube.search().list(
                q=comp['query'], type="channel", part="id,snippet", maxResults=1
            ).execute()

            if not search_response.get("items"):
                print(f"    Could not find channel for {comp['name']}")
                continue

            channel_id = search_response["items"][0]["id"]["channelId"]

            videos_response = youtube.search().list(
                channelId=channel_id, order="date", part="id,snippet",
                type="video", maxResults=2
            ).execute()

            for item in videos_response.get("items", []):
                video_id = item["id"]["videoId"]

                # Get stats
                video_details = youtube.videos().list(
                    id=video_id, part="statistics"
                ).execute()
                stats = video_details["items"][0]["statistics"] if video_details.get("items") else {}

                # Try transcript
                transcript = ""
                try:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                    transcript = " ".join([t['text'] for t in transcript_list])
                except:
                    transcript = "[Transcript unavailable]"

                all_videos.append({
                    "source": "youtube",
                    "channel": comp['name'],
                    "title": item["snippet"]["title"],
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "published_at": item["snippet"]["publishedAt"],
                    "views": stats.get("viewCount", 0),
                    "likes": stats.get("likeCount", 0),
                    "transcript_excerpt": transcript[:500] if transcript else "[N/A]"
                })

        print(f"  YouTube: fetched {len(all_videos)} videos")
        return all_videos

    except Exception as e:
        print(f"  ERROR: YouTube scrape failed: {str(e)}")
        return []


def calculate_roi_score(description, readme_content):
    """Analyze repo for business ROI signals."""
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
    """Fetch README from GitHub repo."""
    try:
        parts = repo_url.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1]

        for branch in ["main", "master"]:
            readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
            response = requests.get(readme_url, timeout=10)
            if response.status_code == 200:
                return response.text[:2000]

        return ""
    except:
        return ""


def get_github_trending():
    """Scrape GitHub trending AI repos."""
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
                except:
                    stars = 0

                topics = []
                for topic_elem in article.find_all("a", class_="topic-tag"):
                    topics.append(topic_elem.text.strip())

                is_ai = any(
                    keyword in repo_name.lower() or
                    keyword in description.lower() or
                    keyword in " ".join(topics).lower()
                    for keyword in AI_KEYWORDS
                )

                if not is_ai:
                    continue

                print(f"    Analyzing {repo_name}...")
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
            except:
                pass

        repos.sort(key=lambda r: (r["roi_score"], r["stars"]), reverse=True)
        repos = repos[:MAX_GITHUB_REPOS]

        print(f"  GitHub: fetched {len(repos)} repos")
        return repos

    except Exception as e:
        print(f"  ERROR: GitHub scrape failed: {str(e)}")
        return []


def get_x_posts():
    """Fetch X (Twitter) posts via Apify."""
    if not APIFY_API_KEY:
        print("  WARNING: APIFY_API_KEY not set, skipping X posts")
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
                    "endDate": today, "includePinned": False, "includeReplies": False,
                    "includeRetweets": False, "limit": POSTS_PER_ACCOUNT,
                    "maxItems": POSTS_PER_ACCOUNT, "startDate": cutoff, "username": account
                }

                run_url = f"{APIFY_API_URL}/acts/{APIFY_ACTOR}/runs"
                response = requests.post(
                    run_url, json=actor_input, params={"token": APIFY_API_KEY},
                    headers={"Content-Type": "application/json"}, timeout=120
                )
                response.raise_for_status()
                run_id = response.json().get("data", {}).get("id")

                if not run_id:
                    raise RuntimeError("No run ID returned")

                # Poll for completion
                for _ in range(30):
                    status_url = f"{APIFY_API_URL}/acts/{APIFY_ACTOR}/runs/{run_id}"
                    status_response = requests.get(status_url, params={"token": APIFY_API_KEY}, timeout=30)
                    status_response.raise_for_status()
                    run_status = status_response.json().get("data", {})

                    if run_status.get("status") == "SUCCEEDED":
                        break
                    elif run_status.get("status") in ["FAILED", "ABORTED"]:
                        raise RuntimeError(f"Apify run {run_status.get('status')}")
                    time.sleep(2)
                else:
                    raise RuntimeError("Timeout")

                dataset_id = run_status.get("defaultDatasetId")
                if not dataset_id:
                    raise RuntimeError("No dataset ID")

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
                        "created_at": item.get("date", "")
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

    print(f"  X: fetched {len(posts)} posts")
    return posts


def main():
    print("="*60)
    print("DAILY DIGEST — Data Collection (Phase 1 & 1B)")
    print("="*60)

    signals = {
        "collected_at": datetime.now().isoformat(),
        "youtube": get_youtube_videos(),
        "github": get_github_trending(),
        "x_posts": get_x_posts(),
    }

    os.makedirs("./", exist_ok=True)
    output_path = "./daily_digest_signals.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(signals, f, indent=2, ensure_ascii=False)

    total = len(signals["youtube"]) + len(signals["github"]) + len(signals["x_posts"])
    print(f"\n[OK] Data collection complete")
    print(f"  {total} signals saved to {output_path}")


if __name__ == "__main__":
    main()
