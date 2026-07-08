#!/usr/bin/env python3
"""
AI Directory — Scraper
Collects new AI tools from free sources and merges into tools.json.

Sources:
  1. Product Hunt API (free tier — today's AI launches)
  2. GitHub trending (AI/ML repos)
  3. Existing AI directory RSS/JSON feeds

The scraper is designed to run via Hermes cron job daily.
It NEVER overwrites existing entries — only appends new ones.

Usage:
  python scraper.py                    # scrape all sources
  python scraper.py --source producthunt  # specific source
  python scraper.py --dry-run          # preview without writing
"""

import json
import hashlib
import time
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError

# ─── Config ───────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data"
TOOLS_FILE = DATA_DIR / "tools.json"
CATEGORIES_FILE = DATA_DIR / "categories.json"

USER_AGENT = "AI-Directory-Bot/1.0 (https://github.com/ai-directory)"
TIMEOUT = 15


def load_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def make_id(name):
    """Create a URL-safe ID from a tool name."""
    return name.lower().strip().replace(" ", "-").replace(".", "")


def fetch_json(url, headers=None):
    """Fetch JSON from a URL with basic error handling."""
    req = Request(url)
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    with urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_text(url, headers=None):
    """Fetch raw text/HTML from a URL."""
    req = Request(url)
    req.add_header("User-Agent", USER_AGENT)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    with urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


# ─── Source: Product Hunt ─────────────────────────────────────────────────────
def scrape_producthunt(api_token=None):
    """
    Scrape Product Hunt for today's AI-related launches.
    Requires a free API token from https://www.producthunt.com/v2/oauth/applications
    """
    if not api_token:
        print("  [producthunt] No API token provided — skipping (set PH_TOKEN env var)")
        return []

    url = "https://api.producthunt.com/v2/api/graphql"
    query = """
    {
      posts(first: 20, topic: "artificial-intelligence", order: VOTES) {
        edges {
          node {
            name
            tagline
            description
            website
            votesCount
            topics { edges { node { name } } }
          }
        }
      }
    }
    """
    try:
        data = fetch_json(url, headers={"Authorization": f"Bearer {api_token}"})
        tools = []
        for edge in data.get("data", {}).get("posts", {}).get("edges", []):
            node = edge["node"]
            tools.append({
                "id": make_id(node["name"]),
                "name": node["name"],
                "tagline": node.get("tagline", ""),
                "description": node.get("description", node.get("tagline", "")),
                "url": node.get("website", ""),
                "category": "ai-tools",  # will be auto-categorized
                "pricing": "unknown",
                "features": [],
                "rating": 0,
                "added": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "tags": [t["node"]["name"] for t in node.get("topics", {}).get("edges", [])],
                "source": "producthunt"
            })
        print(f"  [producthunt] Found {len(tools)} AI tools")
        return tools
    except Exception as e:
        print(f"  [producthunt] Error: {e}")
        return []


# ─── Source: GitHub Trending ──────────────────────────────────────────────────
def scrape_github_trending():
    """Scrape GitHub trending repos for AI/ML topics."""
    tools = []
    topics = ["machine-learning", "ai", "llm"]
    for topic in topics:
        url = f"https://api.github.com/search/repositories?q=topic:{topic}+stars:>500+pushed:>2026-06-01&sort=stars&order=desc&per_page=10"
        try:
            data = fetch_json(url)
            for repo in data.get("items", []):
                name = repo["name"].replace("-", " ").title()
                tools.append({
                    "id": make_id(repo["name"]),
                    "name": name,
                    "tagline": (repo.get("description") or "Open-source AI tool")[:100],
                    "description": repo.get("description") or f"{name} is an open-source project on GitHub.",
                    "url": repo["html_url"],
                    "category": "code",
                    "pricing": "free",
                    "features": ["Open source", "Self-hosted"],
                    "rating": min(5.0, round(repo.get("stargazers_count", 0) / 2000, 1)),
                    "added": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "tags": ["open-source", "github", repo.get("language", "").lower()],
                    "source": "github-trending"
                })
            print(f"  [github] Found {len(data.get('items', []))} repos for topic '{topic}'")
        except Exception as e:
            print(f"  [github] Error fetching topic '{topic}': {e}")
        time.sleep(1)  # be nice to the API
    return tools


# ─── Source: There's An AI For That (RSS) ────────────────────────────────────
def scrape_taafd_feed():
    """Scrape the TAAFT directory feed for new AI tools."""
    # This uses their public JSON endpoint (not the official API)
    url = "https://listingbot.de/api/ai-tools"  # placeholder community feed
    try:
        data = fetch_json(url)
        tools = []
        for item in data[:20]:
            tools.append({
                "id": make_id(item.get("name", "unknown")),
                "name": item.get("name", ""),
                "tagline": item.get("tagline", ""),
                "directory/scraper.py": None,
                "description": item.get("description", item.get("tagline", "")),
                "url": item.get("url", ""),
                "category": item.get("category", "ai-tools"),
                "pricing": item.get("pricing", "unknown"),
                "features": item.get("features", []),
                "rating": item.get("rating", 0),
                "added": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "tags": item.get("tags", []),
                "source": "taafd-feed"
            })
        print(f"  [taafd] Found {len(tools)} tools from feed")
        return tools
    except Exception as e:
        print(f"  [taafd] Error (feed may be unavailable): {e}")
        return []


# ─── Dedup & Merge ────────────────────────────────────────────────────────────
def merge_new_tools(existing_tools, new_tools):
    """Merge new tools into existing list, skipping duplicates by ID or URL."""
    existing_ids = {t["id"] for t in existing_tools}
    existing_urls = {t.get("url", "").lower().rstrip("/") for t in existing_tools}
    existing_names = {t["name"].lower() for t in existing_tools}

    added = []
    for tool in new_tools:
        tid = tool["id"]
        url = tool.get("url", "").lower().rstrip("/")
        name = tool.get("name", "").lower()

        if tid in existing_ids or url in existing_urls or name in existing_names:
            continue
        if not tool.get("name") or not tool.get("url"):
            continue

        added.append(tool)
        existing_ids.add(tid)
        existing_urls.add(url)
        existing_names.add(name)

    return existing_tools + added, added


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Scrape AI tools from free sources")
    parser.add_argument("--source", choices=["producthunt", "github", "taafd", "all"], default="all")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--ph-token", default=None, help="Product Hunt API token")
    args = parser.parse_args()

    import os
    ph_token = args.ph_token or os.environ.get("PH_TOKEN")

    print(f"🤖 AI Directory Scraper — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Source: {args.source} | Dry run: {args.dry_run}\n")

    # Load existing
    data = load_json(TOOLS_FILE)
    existing = data.get("tools", [])
    print(f"📂 Existing tools: {len(existing)}\n")

    # Scrape
    new_tools = []
    if args.source in ("all", "producthunt"):
        print("Scraping Product Hunt...")
        new_tools += scrape_producthunt(ph_token)
    if args.source in ("all", "github"):
        print("\nScraping GitHub trending...")
        new_tools += scrape_github_trending()
    if args.source in ("all", "taafd"):
        print("\nScraping TAAFT feed...")
        new_tools += scrape_taafd_feed()

    print(f"\n📊 Total new candidates: {len(new_tools)}")

    # Merge
    merged, added = merge_new_tools(existing, new_tools)
    print(f"✅ New tools added: {len(added)}")
    for t in added:
        print(f"   + {t['name']} ({t['category']}) — {t['url']}")

    if args.dry_run:
        print("\n[DRY RUN] No changes written.")
        return

    # Save
    data["tools"] = merged
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_json(TOOLS_FILE, data)
    print(f"\n💾 Saved {len(merged)} tools to {TOOLS_FILE}")


if __name__ == "__main__":
    main()
