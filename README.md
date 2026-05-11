# Daily Brief

LLM-powered daily digest deployed to GitHub Pages — powered by [Claude Code Routines](https://claude.ai/code/routines).

Fork this repo, edit `sources.yaml`, create a routine, done.

## How it works

```
Claude Code Routine (daily cron)
  → reads sources.yaml + seen.json
  → scrapes each source, generates insights for new articles
  → outputs content.json, pushes to repo

GitHub Action (triggered by content.json change)
  → runs scripts/build.py
  → renders archive/{date}.html from template.html
  → updates seen.json + manifest.json
  → pushes, GitHub Pages deploys
```

## Setup

### 1. Fork this repo

### 2. Edit `sources.yaml`

```yaml
site:
  title: "My Daily Brief"
  description: "What I'm following"
  lang: zh-CN

sources:
  - name: PyTorch DevLogs
    url: https://docs.pytorch.org/devlogs/
    type: blog-index
    focus: "key technical progress"

  - name: Rust Releases
    url: https://github.com/rust-lang/rust/releases
    type: github-releases

  - name: Tailwind CSS
    url: https://tailwindcss.com/changelog
    type: changelog
```

Supported `type` values: `blog-index`, `github-releases`, `changelog`, `rss`

### 3. Enable GitHub Pages

Settings → Pages → Source: Deploy from branch `main`, directory `/`.

### 4. Create a Claude Code Routine

Go to [claude.ai/code/routines](https://claude.ai/code/routines):

- **Repo**: your fork's URL
- **Schedule**: `0 1 * * *` (9am Asia/Shanghai — adjust for your timezone)
- **Prompt**: copy the contents of `ROUTINE_PROMPT.md`

## Structure

```
├── index.html              # landing page (reads manifest.json)
├── sources.yaml            # your information sources (edit this)
├── template.html           # HTML/CSS template (customize look here)
├── seen.json               # dedup index (auto-managed)
├── content.json            # LLM output (auto-managed)
├── scripts/
│   └── build.py            # renders HTML from content.json
├── .github/workflows/
│   └── build.yml           # action: content.json → build → deploy
├── ROUTINE_PROMPT.md        # prompt for the routine
└── archive/
    ├── manifest.json       # brief index
    └── {date}.html         # daily briefs
```

## Customization

- **Sources**: edit `sources.yaml`
- **Appearance**: edit `template.html` (CSS variables, layout)
- **Language**: set `site.lang` in `sources.yaml`
- **Insight focus**: set `focus` per source to guide what the LLM highlights

## License

MIT
