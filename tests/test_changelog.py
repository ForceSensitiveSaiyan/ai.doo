"""Tests for build-changelog.py markdown-to-HTML renderer."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import importlib

build_changelog = importlib.import_module("build-changelog")
render_changelog = build_changelog.render_changelog
inline = build_changelog.inline


class TestInline:
    def test_bold(self):
        assert inline("**hello**") == "<strong>hello</strong>"

    def test_code(self):
        assert inline("`foo`") == "<code>foo</code>"

    def test_link(self):
        result = inline("[text](https://example.com)")
        assert 'href="https://example.com"' in result
        assert ">text</a>" in result

    def test_escapes_html(self):
        assert "&amp;" in inline("&")
        assert "&lt;" in inline("<script>")

    def test_combined(self):
        result = inline("**bold** and `code`")
        assert "<strong>bold</strong>" in result
        assert "<code>code</code>" in result


class TestRenderChangelog:
    SAMPLE = """# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-03-01

### Added

- First feature
- **Bold feature** with `code`

### Fixed

- A bug fix

## [0.1.0] - 2026-01-01

### Added

- Initial release

[1.0.0]: https://github.com/example/repo/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/example/repo/releases/tag/v0.1.0
"""

    def test_renders_version_headings(self):
        html = render_changelog(self.SAMPLE)
        assert "<h2>1.0.0 - 2026-03-01</h2>" in html

    def test_renders_section_headings(self):
        html = render_changelog(self.SAMPLE)
        assert "<h3>Added</h3>" in html
        assert "<h3>Fixed</h3>" in html

    def test_renders_list_items(self):
        html = render_changelog(self.SAMPLE)
        assert "<li>First feature</li>" in html
        assert "<li>A bug fix</li>" in html

    def test_renders_inline_formatting(self):
        html = render_changelog(self.SAMPLE)
        assert "<strong>Bold feature</strong>" in html
        assert "<code>code</code>" in html

    def test_skips_preamble(self):
        html = render_changelog(self.SAMPLE)
        assert "Changelog" not in html.split("<h2>")[0]
        assert "All notable" not in html

    def test_skips_link_references(self):
        html = render_changelog(self.SAMPLE)
        assert "github.com/example" not in html

    def test_strips_version_brackets(self):
        html = render_changelog(self.SAMPLE)
        assert "[1.0.0]" not in html
        assert "1.0.0 - 2026-03-01" in html

    def test_closes_lists(self):
        html = render_changelog(self.SAMPLE)
        assert html.count("<ul>") == html.count("</ul>")

    def test_empty_input(self):
        assert render_changelog("") == ""

    def test_no_list_items(self):
        html = render_changelog("## [1.0.0] - 2026-03-01\n\nSome text\n")
        assert "<h2>" in html
        assert "<ul>" not in html
