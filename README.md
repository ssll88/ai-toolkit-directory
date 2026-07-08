# AI Toolkit — Agent-Maintained AI Tools Directory

A multi-niche AI tools directory website that's automatically maintained by AI agents via Hermes cron jobs.

## What It Does

- **Curates** AI tools across 14+ professional categories (construction, design, code, marketing, etc.)
- **Auto-updates** daily via Hermes cron job — scrapes new tools, rebuilds the site, pushes to GitHub Pages
- **Monetization ready** — affiliate links, sponsored listings, display ads
- **Zero framework** — pure HTML/CSS/JS, deploys free on GitHub Pages

## Quick Start

```bash
# Build the site from data
python scripts/build.py

# Preview locally
python scripts/build.py --serve

# Scrape new tools (GitHub trending is free, no API key needed)
python scripts/scraper.py --source github
```

## Project Structure

```
ai-directory/
├── data/
│   ├── categories.json    # Category definitions
│   └── tools.json         # Tool database (read/written by agents)
├── scripts/
│   ├── scraper.py         # Collects new tools from sources
│   └── build.py           # Generates static HTML site
├── docs/                  # Generated static site (GitHub Pages deploys from here)
│   ├── index.html
│   ├── sitemap.xml
│   └── robots.txt
└── README.md
```

## Deployment (GitHub Pages — Free)

1. Create a new GitHub repo (public)
2. Push this code: `git push origin main`
3. Go to repo Settings → Pages → Source: `main` branch, `/site` folder
4. Your site goes live at `https://YOUR_USERNAME.github.io/REPO_NAME`

## Auto-Update (Hermes Cron Job)

The Hermes agent runs daily to:
1. Run the scraper to find new AI tools
2. Rebuild the static site
3. Commit and push to GitHub (auto-deploys)

See CRON.md for cron job configuration.

## License

MIT
