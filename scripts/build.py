#!/usr/bin/env python3
"""Render a daily brief HTML from content.json + template.html.

Zero external dependencies. Reads content.json (LLM output), seen.json (dedup index),
and template.html (HTML/CSS skeleton). Produces archive/{date}.html, updates seen.json
and manifest.json.
"""

import json
import sys
from datetime import datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_PATH = ROOT / "content.json"
SEEN_PATH = ROOT / "seen.json"
TEMPLATE_PATH = ROOT / "template.html"
MANIFEST_PATH = ROOT / "archive" / "manifest.json"
ARCHIVE_DIR = ROOT / "archive"


def load_json(path, default=None):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


BADGE_COLORS = [
    ("#3fb950", "rgba(63,185,80,.15)"),    # green
    ("#bc8cff", "rgba(188,140,255,.15)"),   # purple
    ("#d29922", "rgba(210,153,34,.15)"),    # orange
    ("#58a6ff", "rgba(88,166,255,.15)"),    # blue
    ("#f85149", "rgba(248,81,73,.15)"),     # red
    ("#39d2c0", "rgba(57,210,192,.15)"),    # cyan
    ("#f0883e", "rgba(240,136,62,.15)"),    # amber
    ("#db61a2", "rgba(219,97,162,.15)"),    # pink
]


def badge_style(index):
    fg, bg = BADGE_COLORS[index % len(BADGE_COLORS)]
    return f"background:{bg};color:{fg}"


def render_insight_row(tag, label, text, color):
    colors = {"problem": "#d29922", "approach": "#3fb950", "takeaway": "#58a6ff"}
    bg = {"problem": "rgba(210,153,34,.15)", "approach": "rgba(63,185,80,.15)", "takeaway": "rgba(88,166,255,.15)"}
    return (
        f'<div class="insight-row">'
        f'<span class="insight-tag" style="background:{bg[tag]};color:{colors[tag]}">{label}</span>'
        f'<span class="insight-text">{escape(text)}</span>'
        f'</div>'
    )


def render_card(entry, source_idx):
    e = escape
    cat = entry.get("category", "")
    badge = f'<span class="badge" style="{badge_style(source_idx)}">{e(cat)}</span>' if cat else ""

    insights_html = ""
    ins = entry.get("insights")
    if ins and not ins.get("error"):
        insights_html = '<div class="insights">'
        insights_html += render_insight_row("problem", "Problem", ins.get("problem", ""), "problem")
        insights_html += render_insight_row("approach", "Approach", ins.get("approach", ""), "approach")
        insights_html += render_insight_row("takeaway", "Takeaway", ins.get("takeaway", ""), "takeaway")
        insights_html += '</div>'
    elif ins and ins.get("error"):
        insights_html = f'<div class="insights"><div class="insight-row"><span class="insight-text" style="color:var(--muted)">内容获取失败，无法生成 insights</span></div></div>'

    return (
        f'<div class="card">'
        f'<div class="card-head"><span class="card-title">{e(entry["title"])}</span>{badge}</div>'
        f'<div class="card-meta">{e(entry.get("date", ""))}</div>'
        f'{insights_html}'
        f'<a class="card-link" href="{e(entry["url"])}">阅读原文 →</a>'
        f'</div>'
    )


def render_compact_item(entry, source_idx):
    e = escape
    cat = entry.get("category", "")
    badge = f'<span class="badge" style="{badge_style(source_idx)}">{e(cat)}</span>' if cat else ""
    return (
        f'<li>'
        f'<a class="c-title" href="{e(entry["url"])}">{e(entry["title"])}</a>'
        f'<span class="c-meta">{badge} {e(entry.get("date", ""))}</span>'
        f'</li>'
    )


def build():
    content = load_json(CONTENT_PATH)
    if not content:
        print("No content.json found or empty, skipping build.")
        return

    seen = load_json(SEEN_PATH, {})
    template = TEMPLATE_PATH.read_text()

    date = content["date"]
    site = content.get("site", {})
    lang = site.get("lang", "zh-CN")
    site_title = site.get("title", "Daily Brief")
    entries = content.get("entries", [])

    by_source = {}
    for entry in entries:
        src = entry.get("source", "Unknown")
        by_source.setdefault(src, []).append(entry)

    source_names = list(by_source.keys())
    new_count = sum(1 for e in entries if e.get("insights") and not (isinstance(e.get("insights"), dict) and e["insights"].get("error")))
    sources_with_new = set()
    for e in entries:
        if e.get("insights") and not (isinstance(e.get("insights"), dict) and e["insights"].get("error")):
            sources_with_new.add(e.get("source", ""))

    if new_count > 0:
        stats = f"今日 {new_count} 篇新文章 · 来自 {len(sources_with_new)} 个源"
        stats_class = "stats"
    else:
        stats = "今日无新内容"
        stats_class = "stats stats-empty"

    body = ""
    for si, source_name in enumerate(source_names):
        source_entries = by_source[source_name]
        card_entries = [e for e in source_entries if e.get("insights")]
        old_entries = [e for e in source_entries if not e.get("insights")]

        body += f'<div class="section">'
        body += f'<div class="section-title">{escape(source_name)}'
        if card_entries:
            body += f' <span class="count">{len(card_entries)} 篇新文章</span>'
        body += f'</div>'

        for entry in card_entries:
            body += render_card(entry, si)

        if old_entries:
            body += '<ul class="compact">'
            for entry in old_entries:
                body += render_compact_item(entry, si)
            body += '</ul>'

        body += '</div>'

    footer_sources = " · ".join(
        f'<a href="{escape(e.get("url", "#"))}">{escape(src)}</a>'
        for src, entries_list in by_source.items()
        for e in entries_list[:1]
    )

    html = template
    html = html.replace("{{LANG}}", escape(lang))
    html = html.replace("{{PAGE_TITLE}}", f"{escape(site_title)} 每日简报 — {date}")
    html = html.replace("{{SITE_TITLE}}", escape(site_title))
    html = html.replace("{{DATE}}", date)
    html = html.replace("{{STATS_CLASS}}", stats_class)
    html = html.replace("{{STATS}}", stats)
    html = html.replace("{{CONTENT}}", body)
    html = html.replace("{{FOOTER_SOURCES}}", footer_sources)

    ARCHIVE_DIR.mkdir(exist_ok=True)
    out_path = ARCHIVE_DIR / f"{date}.html"
    out_path.write_text(html)
    print(f"Generated {out_path}")

    for entry in entries:
        if entry.get("insights") and not (isinstance(entry.get("insights"), dict) and entry["insights"].get("error")):
            url = entry["url"]
            if url not in seen:
                seen[url] = {
                    "title": entry["title"],
                    "source": entry.get("source", ""),
                    "first_seen": date,
                    "date": entry.get("date", ""),
                }
    save_json(SEEN_PATH, seen)
    print(f"Updated {SEEN_PATH} ({len(seen)} entries)")

    manifest = load_json(MANIFEST_PATH, {"site": {}, "briefs": []})
    manifest["site"] = {
        "title": site_title,
        "description": site.get("description", ""),
        "lang": lang,
        "sources": source_names,
    }
    briefs = manifest.get("briefs", [])
    briefs = [b for b in briefs if b.get("date") != date]
    briefs.append({
        "date": date,
        "file": f"{date}.html",
        "new_count": new_count,
        "sources": source_names,
    })
    briefs.sort(key=lambda b: b["date"], reverse=True)
    manifest["briefs"] = briefs
    save_json(MANIFEST_PATH, manifest)
    print(f"Updated {MANIFEST_PATH}")


if __name__ == "__main__":
    build()
