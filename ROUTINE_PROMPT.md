You produce a daily content.json for a brief site. The repo is already cloned.

## Step 1: Setup

```bash
TODAY=$(TZ=Asia/Shanghai date +%Y-%m-%d)
```

Read `sources.yaml` for the site config and source list.
Read `seen.json` for the set of already-covered article URLs.

## Step 2: Scrape Sources

For each source in sources.yaml, use WebFetch on its URL. Extract entries based on the `type` hint:

- **blog-index**: HTML page with links to articles. Extract ALL articles on the page. If the page has category sections with "all posts" or similar sub-page links, follow each sub-page link via additional WebFetch calls to collect every article across all categories. Do not rely on the index page alone if it truncates or only shows recent posts.
- **github-releases**: GitHub releases page. Extract release tag/title, date, URL, and body summary.
- **changelog**: Single page with dated sections. Extract each version's title, date, and summary.
- **rss**: RSS/Atom feed. Extract each item's title, link, pubDate, and description.

Normalize every entry to: `{source, url, title, date, category, summary}`

## Step 3: Identify New Articles

For each entry, check if its URL exists in seen.json:
- **NOT in seen.json** → this is a NEW article
- **IN seen.json** → this is an OLD article

## Step 4: Generate Insights (NEW articles only)

For each NEW article:
1. WebFetch the full article URL to get detailed content
2. Generate three insights guided by the source's `focus` field (if present):
   - **Problem**: What core problem does this article address?
   - **Approach**: What method or technique is used?
   - **Takeaway**: What is the key result or conclusion?
3. Keep insights concise (1-2 sentences each)

For OLD articles: set `insights` to `null`. Do NOT fetch full content.

If WebFetch fails for a new article, set `insights` to `{"error": "fetch failed"}`.

## Step 5: Output content.json

Write `content.json` with this exact structure:

```json
{
  "date": "YYYY-MM-DD",
  "site": {
    "title": "<from sources.yaml site.title>",
    "description": "<from sources.yaml site.description>",
    "lang": "<from sources.yaml site.lang>"
  },
  "entries": [
    {
      "source": "Source Name",
      "url": "https://...",
      "title": "Article Title",
      "date": "YYYY-MM-DD",
      "category": "Category",
      "summary": "One-line summary for compact list display",
      "insights": {
        "problem": "...",
        "approach": "...",
        "takeaway": "..."
      }
    },
    {
      "source": "Source Name",
      "url": "https://...",
      "title": "Old Article",
      "date": "YYYY-MM-DD",
      "category": "Category",
      "summary": "One-line summary",
      "insights": null
    }
  ]
}
```

## Step 6: Push

```bash
git add content.json
git commit -m "content: $TODAY"
git push origin main
```

## Rules

- Only push content.json. Do NOT modify seen.json, manifest.json, archive/, or any other file.
- UI text (summaries, insights) follows `site.lang` from sources.yaml. Technical terms stay in English.
- If a source fetch fails entirely, include zero entries for that source (omit it from entries array).
- Ensure content.json is valid JSON.
