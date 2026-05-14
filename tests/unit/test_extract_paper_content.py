"""Tests for `scripts/extract_paper_content.py` — the content-extractor
that produces a fresh llmXive wrapper from arXiv source.

Strategy: load the script as a module and exercise its pure helpers.
A full integration test (real lualatex compile) would require a TeX
distribution; those are covered by the paper-compile workflow on real
projects in CI rather than here.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "extract_paper_content.py"


@pytest.fixture(scope="module")
def ex():
    spec = importlib.util.spec_from_file_location("extract_paper_content", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["extract_paper_content"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


# ──────────────────────────────────────────────────────────────────────
# Comment stripping (a real bug we hit: \title{} inside a `% Note: ...`
# comment was being captured as an empty title and the real \title{...}
# never got extracted).
# ──────────────────────────────────────────────────────────────────────

class TestStripComments:
    def test_line_comment_removed(self, ex) -> None:
        out = ex._strip_tex_comments("hello % comment here\nworld")
        assert "% comment" not in out
        assert "hello" in out and "world" in out

    def test_escaped_percent_kept(self, ex) -> None:
        out = ex._strip_tex_comments(r"50\% off")
        assert r"50\%" in out

    def test_title_in_comment_does_not_mask_real_title(self, ex) -> None:
        src = (
            r"% Note: use \title{} and \workshoptitle{} in the preamble" + "\n"
            + r"\title{The Real Title}" + "\n"
        )
        assert ex._extract_macro(src, "title") == "The Real Title"

    def test_no_newline_at_end(self, ex) -> None:
        # `% rest of file` with no trailing newline must still strip the rest
        out = ex._strip_tex_comments("foo % trailing comment")
        assert out == "foo "


# ──────────────────────────────────────────────────────────────────────
# Brace-balanced argument capture
# ──────────────────────────────────────────────────────────────────────

class TestCaptureBracedArg:
    def test_simple_arg(self, ex) -> None:
        arg, _ = ex._capture_braced_arg(r"\foo{hello}", 4)
        assert arg == "hello"

    def test_nested_braces(self, ex) -> None:
        arg, _ = ex._capture_braced_arg(r"\foo{a{b}c}", 4)
        assert arg == "a{b}c"

    def test_escaped_brace_inside(self, ex) -> None:
        # \{ is an escaped brace, not a nesting delimiter
        arg, _ = ex._capture_braced_arg(r"\foo{a\{b\}c}", 4)
        assert arg == r"a\{b\}c"

    def test_no_brace_returns_none(self, ex) -> None:
        arg, _ = ex._capture_braced_arg(r"\foo hello", 4)
        assert arg is None


# ──────────────────────────────────────────────────────────────────────
# Document slicing
# ──────────────────────────────────────────────────────────────────────

class TestSliceDocument:
    def test_basic_split(self, ex) -> None:
        tex = r"""\documentclass{article}
\usepackage{xcolor}
\begin{document}
Hello world.
\end{document}"""
        pre, body = ex._slice_document(tex)
        assert r"\usepackage{xcolor}" in pre
        assert "Hello world." in body
        assert r"\begin{document}" not in body
        assert r"\end{document}" not in body

    def test_no_document_returns_empty_body(self, ex) -> None:
        pre, body = ex._slice_document(r"\documentclass{article} no body")
        assert body == ""


# ──────────────────────────────────────────────────────────────────────
# Title aliasing: ICML (\icmltitle) maps to standard title slot
# ──────────────────────────────────────────────────────────────────────

class TestVenueTitles:
    def test_icmltitle_extracted_when_no_title(self, ex, tmp_path: Path) -> None:
        src = tmp_path / "paper.tex"
        src.write_text(
            r"\documentclass[icml2026]{article}" + "\n"
            r"\icmltitle{The ICML Paper Title}" + "\n"
            r"\begin{document}body\end{document}",
            encoding="utf-8",
        )
        result = ex.extract(tmp_path, "paper.tex", arxiv_id="0000.0")
        assert result["ok"] is True
        assert result["title"] == "The ICML Paper Title"

    def test_standard_title_preferred(self, ex, tmp_path: Path) -> None:
        src = tmp_path / "paper.tex"
        src.write_text(
            r"\title{Standard Title}" + "\n"
            r"\icmltitle{ICML Variant}" + "\n"
            r"\begin{document}body\end{document}",
            encoding="utf-8",
        )
        result = ex.extract(tmp_path, "paper.tex", arxiv_id="0000.0")
        assert result["title"] == "Standard Title"


# ──────────────────────────────────────────────────────────────────────
# \input{} inlining — preamble in a separate file must come through
# ──────────────────────────────────────────────────────────────────────

class TestResolveTex:
    def test_input_inlined_recursively(self, ex, tmp_path: Path) -> None:
        (tmp_path / "section.tex").write_text("Body text.", encoding="utf-8")
        (tmp_path / "main.tex").write_text(
            r"\documentclass{article}\begin{document}" + "\n"
            + r"\input{section}" + "\n"
            + r"\end{document}",
            encoding="utf-8",
        )
        full = ex._resolve_tex(tmp_path, tmp_path / "main.tex")
        assert "Body text." in full
        # The \input{} call itself is replaced.
        assert r"\input{section}" not in full

    def test_missing_input_becomes_comment(self, ex, tmp_path: Path) -> None:
        (tmp_path / "main.tex").write_text(
            r"\input{nope}", encoding="utf-8",
        )
        full = ex._resolve_tex(tmp_path, tmp_path / "main.tex")
        assert "missing input" in full

    def test_cycle_safe(self, ex, tmp_path: Path) -> None:
        # a.tex inputs b.tex which inputs a.tex — should NOT loop
        (tmp_path / "a.tex").write_text(r"A:\input{b}", encoding="utf-8")
        (tmp_path / "b.tex").write_text(r"B:\input{a}", encoding="utf-8")
        full = ex._resolve_tex(tmp_path, tmp_path / "a.tex")
        assert "A:" in full and "B:" in full
        # And the recursion message appears
        assert "recursive" in full or "missing input" in full


# ──────────────────────────────────────────────────────────────────────
# Layout-directive stripping
# ──────────────────────────────────────────────────────────────────────

class TestStripLayoutDirectives:
    def test_drops_twocolumn(self, ex) -> None:
        out = ex._strip_layout_directives(r"before \twocolumn after")
        assert r"\twocolumn" not in out
        assert "before" in out and "after" in out

    def test_drops_geometry(self, ex) -> None:
        out = ex._strip_layout_directives(r"\geometry{margin=1in,top=2cm}")
        assert r"\geometry" not in out

    def test_drops_layout_setlength_but_keeps_math_lengths(self, ex) -> None:
        out = ex._strip_layout_directives(
            r"\setlength{\textwidth}{6in} \setlength{\arrayrulewidth}{0.5pt}"
        )
        # textwidth is in _LAYOUT_LENGTH_NAMES → dropped
        # arrayrulewidth is NOT → kept
        assert r"\textwidth" not in out
        assert r"\arrayrulewidth" in out

    def test_drops_font_redirect(self, ex) -> None:
        out = ex._strip_layout_directives(r"\renewcommand{\rmdefault}{phv}")
        assert r"\rmdefault" not in out


# ──────────────────────────────────────────────────────────────────────
# `\definecolor` capture
# ──────────────────────────────────────────────────────────────────────

class TestForwardedDefinecolor:
    def test_extracts_definecolor(self, ex) -> None:
        out = ex._forwarded_definecolor(r"\definecolor{mindlabfg}{HTML}{0E4DA4}")
        assert any("mindlabfg" in line for line in out)
        assert any("0E4DA4" in line for line in out)

    def test_dedupes_repeats(self, ex) -> None:
        out = ex._forwarded_definecolor(
            r"\definecolor{a}{rgb}{1,0,0} \definecolor{a}{rgb}{0,1,0}"
        )
        assert len(out) == 1   # second mention deduped


# ──────────────────────────────────────────────────────────────────────
# Forwarded `\newcommand` capture with arity / nested-skip
# ──────────────────────────────────────────────────────────────────────

class TestForwardedNewcommands:
    def test_simple_newcommand_forwarded_as_providecommand(self, ex) -> None:
        out = ex._forwarded_newcommands(r"\newcommand{\foo}{bar}")
        assert any(r"\providecommand{\foo}{bar}" == line for line in out)

    def test_arity_preserved(self, ex) -> None:
        out = ex._forwarded_newcommands(r"\newcommand{\foo}[2]{a#1b#2}")
        assert any(r"\providecommand{\foo}[2]{a#1b#2}" == line for line in out)

    def test_nested_inner_newcommand_skipped(self, ex) -> None:
        # `\renewcommand{\title}[2]{\newcommand{\titlelist}{#2}}` — the
        # inner \newcommand uses #2 referring to the OUTER arity. Hoisting
        # it standalone would emit `\providecommand{\titlelist}{#2}` which
        # crashes ("Illegal parameter number"). We must skip it.
        src = r"\renewcommand{\title}[2]{\newcommand{\titlelist}{{#2}}}"
        out = ex._forwarded_newcommands(src)
        # \title should appear; \titlelist should NOT (it's nested)
        names = [
            line.split("{")[1].split("}")[0]
            for line in out if r"\providecommand" in line
        ]
        assert r"\title" in names
        assert r"\titlelist" not in names


# ──────────────────────────────────────────────────────────────────────
# Forwarded packages: dedupe, safe-list filter
# ──────────────────────────────────────────────────────────────────────

class TestForwardedPackages:
    def test_safe_packages_kept(self, ex) -> None:
        out = ex._forwarded_packages(r"\usepackage{natbib}\usepackage{amsmath}")
        assert any("natbib" in line for line in out)
        assert any("amsmath" in line for line in out)

    def test_unsafe_dropped(self, ex) -> None:
        out = ex._forwarded_packages(r"\usepackage{geometry}\usepackage{nv}")
        # Neither geometry nor `nv` (the bundled NVIDIA class) is on the safe list
        assert not any("geometry" in line for line in out)

    def test_options_preserved(self, ex) -> None:
        out = ex._forwarded_packages(r"\usepackage[round,authoryear]{natbib}")
        assert any("[round,authoryear]" in line for line in out)

    def test_dedupe_across_sources(self, ex) -> None:
        out = ex._forwarded_packages(
            r"\usepackage{natbib}", r"\RequirePackage{natbib}"
        )
        # Same package + same opts → dedupe
        assert len([l for l in out if "natbib" in l]) == 1


# ──────────────────────────────────────────────────────────────────────
# Body command stripping
# ──────────────────────────────────────────────────────────────────────

class TestStripBodyCommands:
    def test_maketitle_removed(self, ex) -> None:
        out = ex._strip_body_commands(r"before \maketitle after")
        assert r"\maketitle" not in out
        assert "before" in out and "after" in out

    def test_icmlauthorlist_environment_removed(self, ex) -> None:
        src = (
            r"before "
            r"\begin{icmlauthorlist}\icmlauthor{A}{aa}\end{icmlauthorlist}"
            r" after"
        )
        out = ex._strip_body_commands(src)
        assert "icmlauthorlist" not in out
        assert "before" in out and "after" in out

    def test_icmltitle_with_arg_removed(self, ex) -> None:
        out = ex._strip_body_commands(r"x \icmltitle{The Title} y")
        assert r"\icmltitle" not in out
        assert "The Title" not in out
