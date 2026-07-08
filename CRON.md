# Cron Job Configuration

This document describes how the Hermes cron job auto-updates the directory.

## What the Cron Job Does

Every day at 9:00 AM the agent:
1. Runs `python scripts/scraper.py --source github` to find new AI tools
2. Runs `python scripts/build.py` to rebuild the website
3. Commits and pushes changes to GitHub (triggers GitHub Pages redeploy)

## How to Set Up

### Option A: Hermes Cron (Recommended)

In Hermes, create a cron job with this prompt:

```
Update the AI tools directory:

1. cd to ~/ai-directory
2. Run: python scripts/scraper.py --source github
3. Run: python scripts/build.py
4. If tools.json changed, commit and push:
   git add -A && git commit -m "auto-update: $(date +%Y-%m-%d)" && git push
5. Report how many new tools were added
```

Set schedule to `0 9 * * *` (daily at 9am).

### Option B: GitHub Actions (Alternative)

Create `.github/workflows/update.yml`:

```yaml
name: Daily Update
on:
  schedule:
    - cron: '0 9 * * *'
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: python scripts/scraper.py --source github
      - run: python scripts/build.py
      - run: |
          git config user.name "AI Bot"
          git config user.email "bot@example.com"
          git add -A
          git diff --staged --quiet || git commit -m "auto-update: $(date +%Y-%m-%d)"
          git push
```

## Sources

| Source | Free? | API Key Needed? | Quality |
|--------|-------|-----------------|---------|
| GitHub Trending | ✅ | ❌ (60 req/hr) | High (open-source tools) |
| Product Hunt | ✅ | ✅ (free tier) | High (new launches) |
| TAAFD Feed | ✅ | ❌ | Medium |

## Adding More Sources

Edit `scripts/scraper.py` and add a new `scrape_yoursource()` function following
the same pattern as the existing scrapers.
