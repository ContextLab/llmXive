"""Unit tests for `scripts/restyle_arxiv_paper.py`.

These tests cover the pure-Python helpers (URL extraction, markdown→tex
conversion, artifact rendering) — they don't require LaTeX. The LaTeX
compile path is exercised manually on PROJ-562 and verified visually.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# The script lives in `scripts/`, not on the package path; import by filepath.
_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "restyle_arxiv_paper.py"
sys.path.insert(0, str(_SCRIPT.parent))
import restyle_arxiv_paper as r  # noqa: E402


class TestTexEscape:
    """The plain-text → LaTeX escape used for artifact labels."""

    def test_handles_all_specials(self):
        assert r._tex_escape("&%$#_{}~^") == r"\&\%\$\#\_\{\}\textasciitilde{}\textasciicircum{}"

    def test_passes_through_letters_digits_punctuation(self):
        assert r._tex_escape("Hello, world 2026!") == "Hello, world 2026!"


class TestMdToTexSummary:
    """Markdown → LaTeX conversion for editorial summaries."""

    def test_heading_becomes_edsection(self):
        out = r._md_to_tex_summary("## Significance\nSome prose.")
        assert "\\edsection{Significance}" in out
        assert "Some prose." in out

    def test_bold_and_italic(self):
        out = r._md_to_tex_summary("**bold** and *italic* together.")
        assert "\\textbf{bold}" in out
        assert "\\textit{italic}" in out

    def test_bold_spans_newlines(self):
        out = r._md_to_tex_summary("A **multi\nline** bold span.")
        assert "\\textbf{multi\nline}" in out

    def test_italic_spans_newlines(self):
        out = r._md_to_tex_summary("Has *cross-line\nitalic* text.")
        assert "\\textit{cross-line\nitalic}" in out

    def test_link_renders_href(self):
        out = r._md_to_tex_summary("See [the project](https://example.com).")
        assert "\\href{https://example.com}{the project}" in out

    def test_escapes_specials_in_prose(self):
        out = r._md_to_tex_summary("100% of authors with #hashtag and a $5 budget.")
        assert "100\\%" in out
        assert "\\#hashtag" in out
        assert "\\$5" in out

    def test_escapes_specials_in_link_label_but_not_url(self):
        out = r._md_to_tex_summary("[A & B](https://example.com/a&b)")
        assert "\\href{https://example.com/a&b}{A \\& B}" in out


class TestExtractArtifactUrls:
    """URL extraction from tex source — what the publication agent uses to
    avoid hallucinating links."""

    def test_finds_github_repo(self):
        tex = r"Code is available at \url{https://github.com/ContextLab/llm-stylometry}."
        urls = r.extract_artifact_urls(tex)
        assert any(u["url"] == "https://github.com/ContextLab/llm-stylometry" for u in urls)

    def test_finds_osf_project(self):
        tex = "Materials are on OSF: https://osf.io/abc123/."
        urls = r.extract_artifact_urls(tex)
        # Trailing slash + period get stripped.
        urls_only = {u["url"] for u in urls}
        assert "https://osf.io/abc123/" in urls_only or "https://osf.io/abc123" in urls_only

    def test_finds_huggingface_model(self):
        tex = "Model: https://huggingface.co/contextlab/example-model"
        urls = r.extract_artifact_urls(tex)
        assert any("huggingface.co/contextlab/example-model" in u["url"] for u in urls)

    def test_dedupes_urls(self):
        tex = (
            "First mention: https://github.com/org/repo. "
            "Then again: \\url{https://github.com/org/repo}."
        )
        urls = r.extract_artifact_urls(tex)
        assert sum(1 for u in urls if u["url"] == "https://github.com/org/repo") == 1

    def test_strips_trailing_punctuation(self):
        tex = "See https://github.com/org/repo, please."
        urls = r.extract_artifact_urls(tex)
        assert urls[0]["url"] == "https://github.com/org/repo"

    def test_assigns_label_by_host(self):
        tex = "https://github.com/o/r and https://doi.org/10.1234/foo"
        urls = r.extract_artifact_urls(tex)
        by_host = {u["url"]: u["label"] for u in urls}
        assert by_host["https://github.com/o/r"] == "Code (GitHub)"
        assert by_host["https://doi.org/10.1234/foo"] == "DOI"

    def test_returns_empty_when_no_urls(self):
        assert r.extract_artifact_urls("Plain text, no urls.") == []


class TestRenderArtifacts:
    """The `\\edartifact{}{}` line-block generator."""

    def test_renders_each_entry(self):
        out = r._render_artifacts([
            {"label": "Project page", "url": "https://example.com/a"},
            {"label": "Reviews", "url": "https://example.com/b"},
        ])
        assert "\\edartifact{Project page}{https://example.com/a}" in out
        assert "\\edartifact{Reviews}{https://example.com/b}" in out

    def test_escapes_label_specials(self):
        out = r._render_artifacts([{"label": "Code & data", "url": "https://example.com"}])
        assert "\\edartifact{Code \\& data}" in out

    def test_skips_empty_entries(self):
        out = r._render_artifacts([
            {"label": "", "url": "https://example.com"},
            {"label": "Reviews", "url": ""},
            {"label": "OK", "url": "https://example.com"},
        ])
        assert out.count("\\edartifact") == 1


class TestLoadArtifacts:
    """JSON loader for artifact lists."""

    def test_loads_well_formed(self, tmp_path: Path):
        p = tmp_path / "artifacts.json"
        p.write_text(json.dumps([
            {"label": "Project page", "url": "https://example.com"},
        ]))
        out = r._load_artifacts(p)
        assert out == [{"label": "Project page", "url": "https://example.com"}]

    def test_returns_empty_for_missing_file(self, tmp_path: Path):
        assert r._load_artifacts(tmp_path / "nope.json") == []

    def test_raises_on_non_list_root(self, tmp_path: Path):
        p = tmp_path / "bad.json"
        p.write_text('{"label": "x", "url": "y"}')
        with pytest.raises(ValueError):
            r._load_artifacts(p)

    def test_filters_entries_missing_keys(self, tmp_path: Path):
        p = tmp_path / "partial.json"
        p.write_text(json.dumps([
            {"label": "ok", "url": "https://x"},
            {"label": "missing-url"},
            {"url": "missing-label"},
            "wrong type",
        ]))
        out = r._load_artifacts(p)
        assert out == [{"label": "ok", "url": "https://x"}]


class TestStripUsepackageLines:
    """The conflicting-package stripper."""

    def test_strips_class_provided(self):
        new, stripped = r._strip_usepackage_lines("\\usepackage{geometry}\n")
        assert "geometry" in stripped
        assert "% [llmxive-restyle] stripped" in new

    def test_preserves_non_conflicting(self):
        new, stripped = r._strip_usepackage_lines("\\usepackage{natbib}\n")
        assert stripped == []
        assert "\\usepackage{natbib}" in new

    def test_strips_multi_name_when_any_conflicts(self):
        # Conservative: if ANY name in a multi-name \usepackage line conflicts,
        # the whole line is stripped — caller would otherwise have to know how to
        # split the line and re-emit just the safe entries.
        new, stripped = r._strip_usepackage_lines(
            "\\usepackage{natbib,geometry,inputenc}\n"
        )
        assert "geometry" in stripped


class TestExtractMetadata:
    """Title/author/date extraction from the original preamble."""

    def test_pulls_title_author_date(self):
        pre = "\\title{Hello World}\n\\author{A. Person}\n\\date{2026}\n"
        meta = r._extract_metadata(pre)
        assert meta == {"title": "Hello World", "author": "A. Person", "date": "2026"}

    def test_handles_multi_line_title(self):
        pre = "\\title{Hello\nWorld}\n"
        meta = r._extract_metadata(pre)
        assert "Hello" in meta.get("title", "")


class TestStripTitleBlock:
    """The \\title/\\author/\\date scrubbing — guards against the regex
    `\\d` / `\\t` escape pitfall noted in the script."""

    def test_no_regex_escape_corruption(self):
        # `\d` and `\t` in a replacement template would explode as regex escapes.
        # The bug to guard against: `re.sub` interprets the replacement string,
        # so `\\date` and `\\title` (or `\\author`) in a replacement raise
        # "bad escape" errors if not used as a lambda. We just need to confirm
        # the substitution runs without raising and removes the COMMAND.
        pre = "\\date{January 2026}\n\\title{Test Title}\n"
        out = r._strip_title_block(pre)
        # The original `\title{...}` and `\date{...}` are replaced with
        # comment lines (which mention the names in prose). The actual
        # command-with-braces no longer appears.
        assert "\\title{Test Title}" not in out
        assert "\\date{January 2026}" not in out
        # And the replacement comments are present.
        assert "moved to wrapper preamble" in out
        assert "dropped" in out
