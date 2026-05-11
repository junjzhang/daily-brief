You maintain a daily brief site. The repo is already cloned in your working directory.

## Task

1. Read `sources.yaml` to get the site config and list of sources.

2. For each source, use WebFetch to scrape its URL. Extract all entries: title, date, link, category, summary.

3. For articles published in the last 7 days, fetch full articles via WebFetch. Extract 3-5 key technical takeaways per article.

4. Determine today's date: `TZ=Asia/Shanghai date +%Y-%m-%d`

5. Generate `archive/{date}.html` — a self-contained HTML brief with inline CSS. Requirements:
   - Title from `site.title` in sources.yaml + today's date
   - Section "本周新文章": detailed cards with title, category badge, date, key takeaways (bullets), original link
   - Section "近期概览": compact list of older articles (title + date + one-line summary)
   - Style: dark theme (#0d1117 bg), modern, mobile-friendly, good typography
   - UI text language matches `site.lang` in sources.yaml
   - Back link to `../index.html`
   - Category badges with distinct colors

6. Read `archive/manifest.json`, add/replace today's entry `{"date": "YYYY-MM-DD", "title": "...", "file": "YYYY-MM-DD.html"}`, write back.

7. Git add, commit with message `brief: YYYY-MM-DD`, push to origin main.

## Rules
- If WebFetch fails for an article, skip it and note in the brief
- HTML must be self-contained (inline CSS, no external dependencies)
- Technical terms stay in original language, UI text follows site.lang
