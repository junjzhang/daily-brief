#!/usr/bin/env python3
"""Tests for build.py. Run: python -m pytest scripts/test_build.py -v"""

import json
import shutil
import tempfile
from pathlib import Path

import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build


@pytest.fixture
def project(tmp_path):
    """Set up a minimal project directory and point build.py at it."""
    archive = tmp_path / "archive"
    archive.mkdir()

    # Minimal template
    template = tmp_path / "template.html"
    template.write_text(
        '<!DOCTYPE html><html lang="{{LANG}}"><head><title>{{PAGE_TITLE}}</title></head>'
        '<body><h1>{{SITE_TITLE}}</h1><div>{{DATE}}</div>'
        '<div class="{{STATS_CLASS}}">{{STATS}}</div>'
        '{{CONTENT}}<footer>{{FOOTER_SOURCES}}</footer></body></html>'
    )

    # Empty seen.json
    (tmp_path / "seen.json").write_text("{}")

    # Empty manifest
    (archive / "manifest.json").write_text('{"site": {}, "briefs": []}')

    # Monkey-patch paths
    build.ROOT = tmp_path
    build.CONTENT_PATH = tmp_path / "content.json"
    build.SEEN_PATH = tmp_path / "seen.json"
    build.TEMPLATE_PATH = template
    build.MANIFEST_PATH = archive / "manifest.json"
    build.ARCHIVE_DIR = archive

    return tmp_path


def write_content(project, date, entries, site=None):
    site = site or {"title": "Test Brief", "description": "test", "lang": "zh-CN"}
    data = {"date": date, "site": site, "entries": entries}
    (project / "content.json").write_text(json.dumps(data, ensure_ascii=False))


def load_json(path):
    return json.loads(path.read_text())


class TestBasicBuild:
    def test_generates_html(self, project):
        write_content(project, "2026-05-12", [
            {"source": "Src", "url": "https://a.com/1", "title": "Article 1",
             "date": "2026-05-12", "category": "Cat", "summary": "sum",
             "insights": {"problem": "p", "approach": "a", "takeaway": "t"}},
        ])
        build.build()
        html_path = project / "archive" / "2026-05-12.html"
        assert html_path.exists()
        html = html_path.read_text()
        assert "Article 1" in html
        assert "Test Brief" in html

    def test_updates_seen_json(self, project):
        write_content(project, "2026-05-12", [
            {"source": "Src", "url": "https://a.com/new", "title": "New",
             "date": "2026-05-12", "category": "", "summary": "s",
             "insights": {"problem": "p", "approach": "a", "takeaway": "t"}},
        ])
        build.build()
        seen = load_json(project / "seen.json")
        assert "https://a.com/new" in seen
        assert seen["https://a.com/new"]["first_seen"] == "2026-05-12"

    def test_updates_manifest(self, project):
        write_content(project, "2026-05-12", [
            {"source": "Src", "url": "https://a.com/1", "title": "A",
             "date": "2026-05-12", "category": "", "summary": "s",
             "insights": {"problem": "p", "approach": "a", "takeaway": "t"}},
        ])
        build.build()
        manifest = load_json(project / "archive" / "manifest.json")
        assert manifest["site"]["title"] == "Test Brief"
        assert len(manifest["briefs"]) == 1
        assert manifest["briefs"][0]["date"] == "2026-05-12"
        assert manifest["briefs"][0]["new_count"] == 1


class TestDedup:
    def test_new_article_has_insights_card(self, project):
        write_content(project, "2026-05-12", [
            {"source": "Src", "url": "https://a.com/new", "title": "New Article",
             "date": "2026-05-12", "category": "Cat", "summary": "s",
             "insights": {"problem": "the problem", "approach": "the approach", "takeaway": "the takeaway"}},
        ])
        build.build()
        html = (project / "archive" / "2026-05-12.html").read_text()
        assert "the problem" in html
        assert "the approach" in html
        assert "the takeaway" in html
        assert "card" in html

    def test_old_article_is_compact(self, project):
        write_content(project, "2026-05-12", [
            {"source": "Src", "url": "https://a.com/old", "title": "Old Article",
             "date": "2026-05-01", "category": "Cat", "summary": "s",
             "insights": None},
        ])
        build.build()
        html = (project / "archive" / "2026-05-12.html").read_text()
        assert "Old Article" in html
        assert "compact" in html

    def test_old_article_not_added_to_seen(self, project):
        write_content(project, "2026-05-12", [
            {"source": "Src", "url": "https://a.com/old", "title": "Old",
             "date": "2026-05-01", "category": "", "summary": "s",
             "insights": None},
        ])
        build.build()
        seen = load_json(project / "seen.json")
        assert "https://a.com/old" not in seen

    def test_mixed_new_and_old(self, project):
        write_content(project, "2026-05-12", [
            {"source": "Src", "url": "https://a.com/new", "title": "New One",
             "date": "2026-05-12", "category": "A", "summary": "s",
             "insights": {"problem": "p", "approach": "a", "takeaway": "t"}},
            {"source": "Src", "url": "https://a.com/old", "title": "Old One",
             "date": "2026-05-01", "category": "B", "summary": "s",
             "insights": None},
        ])
        build.build()
        html = (project / "archive" / "2026-05-12.html").read_text()
        manifest = load_json(project / "archive" / "manifest.json")
        assert manifest["briefs"][0]["new_count"] == 1
        assert "New One" in html
        assert "Old One" in html


class TestEmptyAndEdgeCases:
    def test_no_entries_generates_empty_brief(self, project):
        write_content(project, "2026-05-12", [])
        build.build()
        html = (project / "archive" / "2026-05-12.html").read_text()
        assert "2026-05-12" in html
        manifest = load_json(project / "archive" / "manifest.json")
        assert manifest["briefs"][0]["new_count"] == 0

    def test_no_content_json_exits_cleanly(self, project):
        build.build()

    def test_insight_error_renders_fallback(self, project):
        write_content(project, "2026-05-12", [
            {"source": "Src", "url": "https://a.com/err", "title": "Error Article",
             "date": "2026-05-12", "category": "", "summary": "s",
             "insights": {"error": "fetch failed"}},
        ])
        build.build()
        html = (project / "archive" / "2026-05-12.html").read_text()
        assert "内容获取失败" in html

    def test_insight_error_not_counted_as_new(self, project):
        write_content(project, "2026-05-12", [
            {"source": "Src", "url": "https://a.com/err", "title": "Err",
             "date": "2026-05-12", "category": "", "summary": "s",
             "insights": {"error": "fetch failed"}},
        ])
        build.build()
        manifest = load_json(project / "archive" / "manifest.json")
        assert manifest["briefs"][0]["new_count"] == 0


class TestMultipleSources:
    def test_groups_by_source(self, project):
        write_content(project, "2026-05-12", [
            {"source": "Alpha", "url": "https://a.com/1", "title": "A1",
             "date": "2026-05-12", "category": "", "summary": "s",
             "insights": {"problem": "p", "approach": "a", "takeaway": "t"}},
            {"source": "Beta", "url": "https://b.com/1", "title": "B1",
             "date": "2026-05-11", "category": "", "summary": "s",
             "insights": {"problem": "p", "approach": "a", "takeaway": "t"}},
        ])
        build.build()
        html = (project / "archive" / "2026-05-12.html").read_text()
        assert "Alpha" in html
        assert "Beta" in html
        manifest = load_json(project / "archive" / "manifest.json")
        assert set(manifest["briefs"][0]["sources"]) == {"Alpha", "Beta"}
        assert manifest["briefs"][0]["new_count"] == 2

    def test_stats_bar_shows_source_count(self, project):
        write_content(project, "2026-05-12", [
            {"source": "A", "url": "https://a.com/1", "title": "X",
             "date": "2026-05-12", "category": "", "summary": "s",
             "insights": {"problem": "p", "approach": "a", "takeaway": "t"}},
            {"source": "B", "url": "https://b.com/1", "title": "Y",
             "date": "2026-05-12", "category": "", "summary": "s",
             "insights": {"problem": "p", "approach": "a", "takeaway": "t"}},
        ])
        build.build()
        html = (project / "archive" / "2026-05-12.html").read_text()
        assert "2 篇新文章" in html
        assert "2 个源" in html


class TestManifestManagement:
    def test_replaces_same_date(self, project):
        (project / "archive" / "manifest.json").write_text(json.dumps({
            "site": {}, "briefs": [
                {"date": "2026-05-12", "file": "2026-05-12.html", "new_count": 99, "sources": []},
            ]
        }))
        write_content(project, "2026-05-12", [])
        build.build()
        manifest = load_json(project / "archive" / "manifest.json")
        assert len(manifest["briefs"]) == 1
        assert manifest["briefs"][0]["new_count"] == 0

    def test_preserves_other_dates(self, project):
        (project / "archive" / "manifest.json").write_text(json.dumps({
            "site": {}, "briefs": [
                {"date": "2026-05-10", "file": "2026-05-10.html", "new_count": 3, "sources": ["X"]},
            ]
        }))
        write_content(project, "2026-05-12", [])
        build.build()
        manifest = load_json(project / "archive" / "manifest.json")
        assert len(manifest["briefs"]) == 2
        dates = {b["date"] for b in manifest["briefs"]}
        assert dates == {"2026-05-10", "2026-05-12"}

    def test_briefs_sorted_reverse_chronological(self, project):
        (project / "archive" / "manifest.json").write_text(json.dumps({
            "site": {}, "briefs": [
                {"date": "2026-05-10", "file": "2026-05-10.html", "new_count": 1, "sources": []},
                {"date": "2026-05-08", "file": "2026-05-08.html", "new_count": 2, "sources": []},
            ]
        }))
        write_content(project, "2026-05-12", [])
        build.build()
        manifest = load_json(project / "archive" / "manifest.json")
        dates = [b["date"] for b in manifest["briefs"]]
        assert dates == ["2026-05-12", "2026-05-10", "2026-05-08"]


class TestHtmlEscaping:
    def test_xss_in_title_escaped(self, project):
        write_content(project, "2026-05-12", [
            {"source": "Src", "url": "https://a.com/1", "title": "<script>alert(1)</script>",
             "date": "2026-05-12", "category": "", "summary": "s",
             "insights": {"problem": "p", "approach": "a", "takeaway": "t"}},
        ])
        build.build()
        html = (project / "archive" / "2026-05-12.html").read_text()
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
