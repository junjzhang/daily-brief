# Daily Brief

LLM-powered daily digest deployed to GitHub Pages — powered by [Claude Code Routines](https://claude.ai/code/routines).

Fork this repo, edit `sources.yaml`, create a routine, and get a daily auto-updating brief site.

## How it works

1. A Claude Code Routine runs daily on a cron schedule
2. It reads `sources.yaml` to know what to scrape
3. For each source, it fetches the page, extracts entries, and summarizes new content
4. It generates an HTML brief in `archive/`, updates `manifest.json`, and pushes to the repo
5. GitHub Pages serves the site — `index.html` reads the manifest and lists all briefs

## Setup

### 1. Fork this repo

### 2. Edit `sources.yaml`

```yaml
site:
  title: "My Daily Brief"
  lang: zh-CN           # or en, ja, etc.

sources:
  - name: PyTorch DevLogs
    url: https://docs.pytorch.org/devlogs/
    type: blog-index     # page with links to articles
    focus: "key technical progress"

  - name: Rust Blog
    url: https://blog.rust-lang.org/
    type: blog-index
    focus: "language features and toolchain changes"
```

### 3. Enable GitHub Pages

Settings → Pages → Source: Deploy from branch `main`, directory `/`.

### 4. Create a Claude Code Routine

Go to [claude.ai/code/routines](https://claude.ai/code/routines) and create a routine with:

- **Schedule**: `0 1 * * *` (daily at 9am Asia/Shanghai, adjust for your timezone)
- **Repo**: your fork's URL
- **Prompt**: see `ROUTINE_PROMPT.md`

## Structure

```
├── index.html              # landing page, reads manifest.json
├── sources.yaml            # configure your information sources
├── archive/
│   ├── manifest.json       # index of all briefs [{date, title, file}]
│   ├── 2026-05-11.html     # daily brief
│   └── ...
└── ROUTINE_PROMPT.md        # the prompt to use for your routine
```

## License

MIT
