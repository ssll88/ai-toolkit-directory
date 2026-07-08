#!/usr/bin/env python3
"""
AI Directory — Static Site Generator
Reads tools.json + categories.json and generates a complete static website.

Output: site/ directory with index.html, category pages, and all assets.
No frameworks needed — just clean HTML/CSS/JS that works on any free host
(GitHub Pages, Netlify, Cloudflare Pages, Vercel).

Usage:
  python build.py          # build site
  python build.py --serve  # build + start local server on :8000
"""

import json
import os
import argparse
import http.server
import socketserver
from pathlib import Path
from datetime import datetime

# ─── Config ───────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data"
OUT_DIR = Path(__file__).parent.parent / "site"

SITE_NAME = "AI Toolkit"
SITE_TAGLINE = "The AI tools directory for every profession"
SITE_URL = "https://ai-directory.example.com"  # update after deployment


# ─── Data loading ─────────────────────────────────────────────────────────────
def load_data():
    tools_data = json.loads((DATA_DIR / "tools.json").read_text(encoding="utf-8"))
    cats_data = json.loads((DATA_DIR / "categories.json").read_text(encoding="utf-8"))
    return tools_data, cats_data


# ─── HTML templates ───────────────────────────────────────────────────────────
def css():
    return """
:root {
  --bg: #0a0a0f;
  --bg-card: #13131a;
  --bg-hover: #1a1a24;
  --text: #e4e4e7;
  --text-dim: #71717a;
  --accent: #6366f1;
  --accent-hover: #818cf8;
  --border: #27272a;
  --free: #22c55e;
  --paid: #f59e0b;
  --freemium: #3b82f6;
  --radius: 12px;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
}
a { color: var(--accent); text-decoration: none; transition: color 0.2s; }
a:hover { color: var(--accent-hover); }
.container { max-width: 1200px; margin: 0 auto; padding: 0 24px; }

/* Header */
header {
  border-bottom: 1px solid var(--border);
  padding: 20px 0;
  position: sticky; top: 0;
  background: rgba(10,10,15,0.85);
  backdrop-filter: blur(12px);
  z-index: 100;
}
.header-inner { display: flex; justify-content: space-between; align-items: center; }
.logo { font-size: 1.5rem; font-weight: 800; color: var(--text); }
.logo span { color: var(--accent); }
.header-nav { display: flex; gap: 24px; align-items: center; }
.header-nav a { color: var(--text-dim); font-size: 0.9rem; font-weight: 500; }
.header-nav a:hover { color: var(--text); }

/* Search */
.search-wrap { margin: 48px 0 24px; }
.search-wrap h1 { font-size: 2.5rem; font-weight: 800; margin-bottom: 8px; }
.search-wrap p { color: var(--text-dim); margin-bottom: 24px; font-size: 1.1rem; }
.search-box {
  width: 100%; padding: 16px 24px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text); font-size: 1rem;
  transition: border-color 0.2s;
}
.search-box:focus { outline: none; border-color: var(--accent); }
.search-box::placeholder { color: var(--text-dim); }

/* Category pills */
.cat-pills { display: flex; gap: 8px; flex-wrap: wrap; margin: 24px 0; }
.cat-pill {
  padding: 6px 16px; border-radius: 20px; font-size: 0.85rem; font-weight: 500;
  background: var(--bg-card); border: 1px solid var(--border); color: var(--text-dim);
  cursor: pointer; transition: all 0.2s; white-space: nowrap;
}
.cat-pill:hover { border-color: var(--accent); color: var(--text); }
.cat-pill.active { background: var(--accent); border-color: var(--accent); color: white; }

/* Stats bar */
.stats-bar { display: flex; gap: 32px; margin: 24px 0; padding: 16px 0; border-bottom: 1px solid var(--border); }
.stat-item { display: flex; flex-direction: column; }
.stat-num { font-size: 1.5rem; font-weight: 800; color: var(--text); }
.stat-label { font-size: 0.8rem; color: var(--text-dim); }

/* Tool cards */
.tools-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; margin: 24px 0 64px; }
.tool-card {
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 20px;
  transition: all 0.2s; display: flex; flex-direction: column; gap: 8px;
}
.tool-card:hover { background: var(--bg-hover); border-color: var(--accent); transform: translateY(-2px); }
.tool-header { display: flex; justify-content: space-between; align-items: start; gap: 12px; }
.tool-name { font-size: 1.1rem; font-weight: 700; }
.tool-cat { font-size: 0.75rem; color: var(--text-dim); }
.tool-tagline { color: var(--text-dim); font-size: 0.9rem; }
.tool-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px; }
.tool-tag { font-size: 0.7rem; padding: 2px 8px; border-radius: 4px; background: var(--bg); color: var(--text-dim); }
.tool-footer { display: flex; justify-content: space-between; align-items: center; margin-top: auto; padding-top: 8px; }
.tool-link { font-size: 0.85rem; font-weight: 600; }
.pricing-badge { font-size: 0.7rem; padding: 2px 10px; border-radius: 4px; font-weight: 600; text-transform: uppercase; }
.pricing-badge.free { background: rgba(34,197,94,0.15); color: var(--free); }
.pricing-badge.paid { background: rgba(245,158,11,0.15); color: var(--paid); }
.pricing-badge.freemium { background: rgba(59,130,246,0.15); color: var(--freemium); }
.pricing-badge.unknown { background: rgba(113,113,122,0.15); color: var(--text-dim); }

/* Footer */
footer { border-top: 1px solid var(--border); padding: 32px 0; text-align: center; color: var(--text-dim); font-size: 0.85rem; }
footer a { color: var(--text-dim); }

/* Category page */
.cat-header { margin: 48px 0 24px; }
.cat-header h1 { font-size: 2rem; display: flex; align-items: center; gap: 12px; }
.cat-header p { color: var(--text-dim); margin-top: 8px; }

/* Responsive */
@media (max-width: 640px) {
  .tools-grid { grid-template-columns: 1fr; }
  .search-wrap h1 { font-size: 1.8rem; }
  .stats-bar { gap: 16px; }
}

/* No results */
.no-results { text-align: center; padding: 48px; color: var(--text-dim); }
"""


def render_header(active_cat=None):
    nav_links = '<a href="/">All Tools</a>'
    return f"""<header>
  <div class="container header-inner">
    <a href="/" class="logo">AI<span>Toolkit</span></a>
    <nav class="header-nav">{nav_links}</nav>
  </div>
</header>"""


def render_footer(tools_count, last_updated):
    return f"""<footer>
  <div class="container">
    <p>{tools_count} AI tools &middot; Updated {last_updated[:10]} &middot;
    <a href="https://github.com">Powered by AI Directory</a></p>
  </div>
</footer>"""


def tool_card_html(tool, cat_name, cat_icon):
    pricing_class = tool.get("pricing", "unknown")
    features_html = "".join(f'<span class="tool-tag">{f}</span>' for f in tool.get("features", [])[:4])
    tags_html = "".join(f'<span class="tool-tag">{t}</span>' for t in tool.get("tags", [])[:3])
    rating_stars = "★" * round(tool.get("rating", 0))
    return f"""<div class="tool-card" data-name="{tool['name'].lower()}" data-category="{tool['category']}" data-tags="{' '.join(tool.get('tags', [])).lower()}">
  <div class="tool-header">
    <div>
      <div class="tool-name">{tool['name']}</div>
      <div class="tool-cat">{cat_icon} {cat_name}</div>
    </div>
    <span class="pricing-badge {pricing_class}">{tool.get('pricing', 'unknown')}</span>
  </div>
  <div class="tool-tagline">{tool.get('tagline', tool.get('description', '')[:80])}</div>
  <div class="tool-tags">{features_html}{tags_html}</div>
  <div class="tool-footer">
    <span class="tool-cat">{rating_stars}</span>
    <a href="{tool.get('url', '#')}" target="_blank" rel="noopener" class="tool-link">Visit →</a>
  </div>
</div>"""


def build_index(tools_data, cats_data):
    tools = tools_data["tools"]
    categories = cats_data["categories"]
    cat_map = {c["id"]: c for c in categories}
    last_updated = tools_data.get("last_updated", "recently")

    # Category pills
    pills = '<button class="cat-pill active" data-filter="all">All</button>\n'
    for c in categories:
        count = sum(1 for t in tools if t["category"] == c["id"])
        if count > 0:
            pills += f'      <button class="cat-pill" data-filter="{c["id"]}">{c["icon"]} {c["name"].split("&")[0].strip()} ({count})</button>\n'

    # Tool cards
    cards = []
    for t in sorted(tools, key=lambda x: x.get("rating", 0), reverse=True):
        cat = cat_map.get(t["category"], {"name": "AI Tool", "icon": "🤖"})
        cards.append(tool_card_html(t, cat["name"], cat["icon"]))
    cards_html = "\n".join(cards)

    free_count = sum(1 for t in tools if t.get("pricing") == "free")
    paid_count = sum(1 for t in tools if t.get("pricing") == "paid")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{SITE_NAME} — {SITE_TAGLINE}</title>
  <meta name="description" content="Discover the best AI tools for construction, project management, design, coding, marketing and more. Updated daily.">
  <style>{css()}</style>
</head>
<body>
{render_header()}
<div class="container">
  <div class="search-wrap">
    <h1>AI Tools for Every Profession</h1>
    <p>{len(tools)} curated tools across {len(categories)} categories — updated daily by AI</p>
    <input type="text" class="search-box" id="search" placeholder="Search AI tools... (e.g. 'construction', 'writing', 'code')">
  </div>
  <div class="cat-pills" id="catPills">
    {pills}
  </div>
  <div class="stats-bar">
    <div class="stat-item"><span class="stat-num">{len(tools)}</span><span class="stat-label">Total Tools</span></div>
    <div class="stat-item"><span class="stat-num">{len(categories)}</span><span class="stat-label">Categories</span></div>
    <div class="stat-item"><span class="stat-num">{free_count}</span><span class="stat-label">Free</span></div>
    <div class="stat-item"><span class="stat-num">{paid_count}</span><span class="stat-label">Paid</span></div>
  </div>
  <div class="tools-grid" id="toolsGrid">
    {cards_html}
  </div>
</div>
{render_footer(len(tools), last_updated)}
<script>
// Live search
const search = document.getElementById('search');
const grid = document.getElementById('toolsGrid');
const cards = grid.querySelectorAll('.tool-card');
search.addEventListener('input', e => {{
  const q = e.target.value.toLowerCase();
  cards.forEach(c => {{
    const match = c.dataset.name.includes(q) || c.dataset.tags.includes(q) || c.dataset.category.includes(q);
    c.style.display = match ? '' : 'none';
  }});
}});

// Category filter pills
const pills = document.querySelectorAll('.cat-pill');
pills.forEach(pill => {{
  pill.addEventListener('click', () => {{
    pills.forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    const filter = pill.dataset.filter;
    cards.forEach(c => {{
      const match = filter === 'all' || c.dataset.category === filter;
      c.style.display = match ? '' : 'none';
    }});
  }});
}});
</script>
</body>
</html>"""


def build_category_page(tool, categories):
    """Generate individual category page (for SEO)."""
    pass  # Future: generate /category/construction.html etc.


def build_site():
    tools_data, cats_data = load_data()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Index page
    index_html = build_index(tools_data, cats_data)
    (OUT_DIR / "index.html").write_text(index_html, encoding="utf-8")

    # Sitemap
    urls = [f"<url><loc>{SITE_URL}/</loc><lastmod>{tools_data.get('last_updated', '')[:10]}</lastmod></url>"]
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""
    (OUT_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    # robots.txt
    (OUT_DIR / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml", encoding="utf-8")

    print(f"✅ Built site with {len(tools_data['tools'])} tools")
    print(f"   Output: {OUT_DIR}")
    print(f"   Open: {(OUT_DIR / 'index.html').resolve()}")


def serve(port=8000):
    build_site()
    os.chdir(OUT_DIR)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"🌐 Serving at http://localhost:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build AI Directory static site")
    parser.add_argument("--serve", action="store_true", help="Build and serve locally")
    parser.add_argument("--port", type=int, default=8000, help="Port for local server")
    args = parser.parse_args()
    if args.serve:
        serve(args.port)
    else:
        build_site()
