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
from typing import ClassVar

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
        _pre, body = ex._slice_document(r"\documentclass{article} no body")
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

    def test_at_internal_macros_captured(self, ex) -> None:
        # `@`-internal macros (e.g. \@noticestring, \@onedot) must round-
        # trip into the forwarded list — `build_wrapper` will then wrap
        # the whole block in \makeatletter so they parse correctly.
        # Without capture, `\@noticestring` from PROJ-578 / `\@onedot`
        # from PROJ-580 silently disappeared, breaking citations and
        # text spacing.
        src = (
            r"\def\@onedot{\ifx\@let@token.\else.\null\fi\xspace}" + "\n"
            r"\renewcommand{\@noticestring}{notice body}"
        )
        out = ex._forwarded_newcommands(src)
        names = [
            line.split("{")[1].split("}")[0]
            for line in out if r"\providecommand" in line
        ]
        assert r"\@onedot" in names
        assert r"\@noticestring" in names


# ──────────────────────────────────────────────────────────────────────
# build_wrapper: must wrap forwarded macros in \makeatletter / \makeatother
# so `\@xxx` macros (CVPR \onedot, NeurIPS \@noticestring, etc.) parse
# correctly. Without this guard `\providecommand{\@noticestring}{...}`
# was interpreted as defining `\@` and leaking "noticestring" as raw
# text into the preamble — which then got typeset at \begin{document}
# above the title block (see PROJ-578 "oticestring", PROJ-580 "nedot.").
# ──────────────────────────────────────────────────────────────────────

class TestBuildWrapperMakeAtLetterGuard:
    def test_forwarded_block_wrapped_in_makeatletter(self, ex) -> None:
        out = ex.build_wrapper(
            title="Test", author="A", arxiv_id="2605.99999",
            forwarded_packages=[],
            forwarded_newcommands=[
                r"\providecommand{\@noticestring}{notice body}",
                r"\providecommand{\@onedot}{\xspace}",
            ],
            body="body content",
        )
        # The forwarded-macros block must be sandwiched between
        # \makeatletter and \makeatother.
        head = out.split("User-defined macros forwarded", 1)[1]
        block = head.split("\\begin{document}", 1)[0]
        assert r"\makeatletter" in block
        assert r"\makeatother" in block
        # And the @-macros must be inside that block (\makeatletter
        # appears BEFORE the macro line).
        at_idx = block.index(r"\makeatletter")
        note_idx = block.index(r"\@noticestring")
        other_idx = block.index(r"\makeatother")
        assert at_idx < note_idx < other_idx

    def test_title_double_plus_broken_with_empty_group(self, ex) -> None:
        # PROJ-580 (Causal Forcing++) rendered "Causal Forcing—," in the
        # display font because Fraunces fuses `+ +` via contextual
        # alternates. Inserting `{}` between consecutive `+` characters
        # blocks the fusion. Text extraction (pdftotext) is unaffected.
        assert ex._break_repeated_plus("Causal Forcing++") == "Causal Forcing+{}+"
        assert ex._break_repeated_plus("C+++") == "C+{}+{}+"
        assert ex._break_repeated_plus("No plus") == "No plus"
        assert ex._break_repeated_plus("a+b") == "a+b"  # single + unaffected

    def test_no_forwarded_block_when_empty(self, ex) -> None:
        # No macros → don't emit an empty makeatletter pair (purely
        # cosmetic, but verifies we don't accidentally always wrap).
        out = ex.build_wrapper(
            title="Test", author="A", arxiv_id="2605.99999",
            forwarded_packages=[], forwarded_newcommands=[],
            body="body content",
        )
        assert "User-defined macros forwarded" not in out


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
        # Options ARE preserved for normal forwarded packages.
        out = ex._forwarded_packages(r"\usepackage[ruled,lined]{algorithm}")
        assert any("[ruled,lined]" in line for line in out)

    def test_natbib_options_stripped(self, ex) -> None:
        # natbib is special-cased: llmxive.cls always loads it with the
        # house options, so forwarding it WITH options causes a fatal
        # `! Option clash for package natbib` (PROJ-603). We forward a
        # bare \usepackage{natbib} instead — a no-op re-request.
        out = ex._forwarded_packages(r"\usepackage[numbers, sort&compress]{natbib}")
        natbib_lines = [line for line in out if "natbib" in line]
        assert natbib_lines == [r"\usepackage{natbib}"]

    def test_dedupe_across_sources(self, ex) -> None:
        out = ex._forwarded_packages(
            r"\usepackage{natbib}", r"\RequirePackage{natbib}"
        )
        # Same package + same opts → dedupe
        assert len([line for line in out if "natbib" in line]) == 1


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


# ──────────────────────────────────────────────────────────────────────
# Title / author / body cleanup helpers (added in PDF polish pass)
# ──────────────────────────────────────────────────────────────────────

class TestStripChapterPrefix:
    def test_strips_chapter_n_colon(self, ex) -> None:
        assert ex._strip_chapter_prefix("Chapter 41: Some Topic") == "Some Topic"

    def test_strips_chapter_with_period_after_n(self, ex) -> None:
        assert ex._strip_chapter_prefix("Chapter 7. Foo") == "Foo"

    def test_case_insensitive(self, ex) -> None:
        assert ex._strip_chapter_prefix("CHAPTER 3: Bar") == "Bar"

    def test_leaves_normal_titles_alone(self, ex) -> None:
        assert ex._strip_chapter_prefix("MinT: Managed Infrastructure") == "MinT: Managed Infrastructure"

    def test_none_passthrough(self, ex) -> None:
        assert ex._strip_chapter_prefix(None) is None


class TestICMLAuthorLine:
    def test_simple_authors_with_affiliations(self, ex) -> None:
        src = (
            r"\icmlauthor{Alice}{a}" + "\n"
            r"\icmlauthor{Bob}{b}" + "\n"
            r"\icmlaffiliation{a}{Acme U}" + "\n"
            r"\icmlaffiliation{b}{Beta Inc}" + "\n"
        )
        line = ex._build_icml_author_line(src)
        assert "Alice" in line and "Bob" in line
        # Superscripts on the names + affiliations listed
        assert "Acme U" in line and "Beta Inc" in line

    def test_shared_affiliation_dedupes(self, ex) -> None:
        src = (
            r"\icmlauthor{Alice}{ust}" + "\n"
            r"\icmlauthor{Bob}{ust}" + "\n"
            r"\icmlaffiliation{ust}{Hong Kong U}" + "\n"
        )
        line = ex._build_icml_author_line(src)
        # Hong Kong U appears once even though two authors share it
        assert line.count("Hong Kong U") == 1

    def test_no_icml_authors_returns_none(self, ex) -> None:
        assert ex._build_icml_author_line(r"\author{Plain Author}") is None


class TestStripTextcolor:
    def test_unwraps_textcolor(self, ex) -> None:
        out = ex._strip_textcolor(r"hello \textcolor{red}{warm} world")
        assert out == "hello warm world"

    def test_keeps_nested_braces_in_content(self, ex) -> None:
        out = ex._strip_textcolor(r"\textcolor{red}{nested {braces} ok}")
        assert out == "nested {braces} ok"

    def test_strips_optional_model(self, ex) -> None:
        out = ex._strip_textcolor(r"\textcolor[rgb]{1,0,0}{red text}")
        assert out == "red text"

    def test_leaves_other_macros_alone(self, ex) -> None:
        out = ex._strip_textcolor(r"plain \emph{italic} text")
        assert out == r"plain \emph{italic} text"


class TestConvertWrapfigure:
    def test_basic_wrapfigure_becomes_figure(self, ex) -> None:
        src = (
            r"\begin{wrapfigure}{r}{0.5\textwidth}" + "\n"
            r"\includegraphics{foo}" + "\n"
            r"\caption{x}" + "\n"
            r"\end{wrapfigure}"
        )
        out = ex._convert_wrapfigure(src)
        assert "wrapfigure" not in out
        assert r"\begin{figure}" in out and r"\end{figure}" in out
        assert r"\includegraphics{foo}" in out

    def test_with_optional_arg(self, ex) -> None:
        src = (
            r"\begin{wrapfigure}[10]{l}{0.4\linewidth}" + "\n"
            r"content" + "\n"
            r"\end{wrapfigure}"
        )
        out = ex._convert_wrapfigure(src)
        assert "wrapfigure" not in out
        assert "content" in out

    def test_multiple_wrapfigures(self, ex) -> None:
        src = (
            r"\begin{wrapfigure}{r}{0.5\textwidth}A\end{wrapfigure}" + "\n"
            r"middle" + "\n"
            r"\begin{wrapfigure}{l}{0.5\textwidth}B\end{wrapfigure}"
        )
        out = ex._convert_wrapfigure(src)
        # Both converted, middle text preserved
        assert out.count(r"\begin{figure}") == 2
        assert "middle" in out
        assert "wrapfigure" not in out


class TestBodyCleanupPasses:
    def test_strips_keywords(self, ex) -> None:
        out = ex._body_cleanup_passes(r"\keywords{a, b, c} after")
        assert r"\keywords" not in out
        assert "after" in out

    def test_strips_icmlkeywords(self, ex) -> None:
        out = ex._body_cleanup_passes(r"x \icmlkeywords{ML, ICML} y")
        assert "icmlkeywords" not in out
        assert "x" in out and "y" in out

    def test_strips_textcolor(self, ex) -> None:
        out = ex._body_cleanup_passes(r"\textcolor{blue}{label} text")
        assert r"\textcolor" not in out
        assert "label text" in out

    def test_strips_bare_color(self, ex) -> None:
        out = ex._body_cleanup_passes(r"\color{red} pink text")
        assert r"\color" not in out
        assert "pink text" in out

    def test_converts_wrapfigure(self, ex) -> None:
        out = ex._body_cleanup_passes(
            r"\begin{wrapfigure}{r}{4cm}fig\end{wrapfigure}"
        )
        assert "wrapfigure" not in out
        assert r"\begin{figure}" in out


# ──────────────────────────────────────────────────────────────────────
# General paper-rendering fixes (PROJ-579/598/605, 580/606, 603, 570/572)
# ──────────────────────────────────────────────────────────────────────

class TestWrapfigureWidthCrash:
    """Fix A: a wrapfigure width like `\\columnwidth` / `\\linewidth` must not
    crash the conversion — it was used as a regex *replacement template* and
    raised `re.error: bad escape \\c` (PROJ-579/598/605 all fell back to the
    raw arXiv PDF)."""

    def test_columnwidth_wrapfigure_does_not_crash(self, ex) -> None:
        body = (r"\begin{wrapfigure}{r}{\columnwidth}"
                r"\includegraphics[width=\linewidth]{fig.pdf}"
                r"\end{wrapfigure}")
        out = ex._body_cleanup_passes(body)  # must not raise
        assert "wrapfigure" not in out
        assert r"\begin{figure}" in out

    def test_linewidth_wraptable_does_not_crash(self, ex) -> None:
        body = (r"\begin{wraptable}{l}{0.4\linewidth}"
                r"\includegraphics[width=\columnwidth]{t.pdf}"
                r"\end{wraptable}")
        out = ex._body_cleanup_passes(body)  # must not raise
        assert "wraptable" not in out


class TestCleanTitle:
    """Fix B: a styled \\title with a baked-in subtitle / decorations falls
    back to the clean metadata.json title (PROJ-580, PROJ-606)."""

    def _md(self, tmp_path: Path, title: str) -> Path:
        src = tmp_path / "paper" / "source"
        src.mkdir(parents=True)
        (tmp_path / "paper" / "metadata.json").write_text(
            f'{{"title": "{title}"}}', encoding="utf-8")
        return src

    def test_subtitle_title_uses_metadata(self, ex, tmp_path: Path) -> None:
        src = self._md(tmp_path, "Code as Agent Harness")
        styled = (r"\textbf{Code as Agent Harness}\\ "
                  r"$\lozenge$~Toward Executable Systems~$\lozenge$")
        assert ex._clean_title(styled, src) == "Code as Agent Harness"

    def test_plain_title_unchanged(self, ex, tmp_path: Path) -> None:
        src = self._md(tmp_path, "Whatever")
        assert ex._clean_title("Co-Evolving Policy Distillation", src) == \
            "Co-Evolving Policy Distillation"

    def test_no_metadata_keeps_raw(self, ex, tmp_path: Path) -> None:
        src = tmp_path / "paper" / "source"
        src.mkdir(parents=True)  # no metadata.json
        styled = r"Title\\ subtitle"
        assert ex._clean_title(styled, src) == styled


class TestResourceLines:
    """Fix C: Keywords:/Github:/Code: metadata + bare link lines are stripped
    from the abstract / leading body, while real prose and structure stay."""

    def test_keyword_line_dropped_prose_kept(self, ex) -> None:
        text = ("Real abstract prose.\n\n"
                r"\vspace{5mm}"
                "\n"
                r"\textbf{Keywords}: A, B, C \\"
                "\n"
                r"\textbf{Github}: \url{https://github.com/x/y}")
        text = ex._strip_icons_and_emoji(text)
        text = ex._strip_textcolor(text)
        out = ex._strip_resource_lines(text)
        assert "Real abstract prose." in out
        assert "Keywords" not in out
        assert "github.com" not in out

    def test_structural_command_never_dropped(self, ex) -> None:
        seg = r"\faGithub~\textbf{Github}: \url{https://x}" + "\n" + r"\end{abstract}"
        assert ex._is_resource_line(seg) is False

    def test_bare_link_line_in_leading_body_dropped(self, ex) -> None:
        body = (r"\textbf{Project Page}: \url{https://github.com/CiteVQA/lab}\\"
                "\n\n" r"\section{Introduction}" "\nReal body text.")
        out = ex._strip_resource_lines(body, only_leading_chars=2500)
        assert "CiteVQA" not in out
        assert r"\section{Introduction}" in out
        assert "Real body text." in out


class TestDisabledMacroForwarding:
    """Fix (PROJ-603): a \\providecommand whose body is entirely commented out
    must not leak an unclosed brace ("File ended while scanning \\@argdef")."""

    def test_commented_body_macro_balanced(self, ex) -> None:
        source = (
            r"\providecommand{\authornames}[1]{%" "\n"
            r"%   {\noindent #1\par}" "\n"
            r"% }" "\n"
            r"\providecommand{\vect}[1]{\bm{#1}}" "\n"
        )
        out = ex._forwarded_newcommands(source)
        # Every emitted line must be brace-balanced.
        for line in out:
            nb = __import__("re").sub(r"\\[{}]", "", line)
            assert nb.count("{") == nb.count("}"), line
        # The good macro still comes through.
        assert any(r"\vect" in line for line in out)


class TestAlgorithmConflict:
    """Fix (PROJ-571): algorithm2e must never be forwarded alongside
    algpseudocode/algorithmic — the clash leaks a ~1-inch text column over
    the whole document (107-page blowup). Keep the family the body uses."""

    PKGS: ClassVar[list] = [r"\usepackage{algorithm}", r"\usepackage{algpseudocode}",
            r"\usepackage[ruled]{algorithm2e}"]

    def test_algorithmicx_body_drops_algorithm2e(self, ex) -> None:
        body = r"\State x \For{i}{} \EndFor \Require y \Return z"
        out = ex._resolve_algorithm_conflict(self.PKGS, body)
        assert not any("algorithm2e" in p for p in out)
        assert any("algpseudocode" in p for p in out)

    def test_algorithm2e_body_drops_algpseudocode(self, ex) -> None:
        body = r"\KwIn{x}\SetAlgoLined\DontPrintSemicolon\eIf{a}{b}{c}\BlankLine"
        out = ex._resolve_algorithm_conflict(self.PKGS, body)
        assert any("algorithm2e" in p for p in out)
        assert not any("algpseudocode" in p for p in out)

    def test_no_conflict_passthrough(self, ex) -> None:
        pkgs = [r"\usepackage{algorithm}", r"\usepackage{algpseudocode}"]
        out = ex._resolve_algorithm_conflict(pkgs, r"\State x")
        assert out == pkgs


class TestResourceEnvs:
    """Fix (PROJ-581): a centered row of resource links (Project Page · Code
    · Models) under the title/abstract is removed; figure/prose centers stay."""

    def test_center_link_row_removed(self, ex) -> None:
        block = (r"\begin{center}\vspace{-1em}"
                 r"~\projectpage~\href{http://x.io/SU}{{\text{Project Page}}}"
                 r"\quad~\github~\href{https://github.com/x/SU}{{\text{Code}}}"
                 r"\end{center}")
        out = ex._strip_resource_envs("Intro.\n\n" + block + "\n\nBody.")
        assert "Project Page" not in out and "github" not in out
        assert "Intro." in out and "Body." in out

    def test_figure_center_kept(self, ex) -> None:
        fig = r"\begin{center}\includegraphics[width=\linewidth]{fig.pdf}\end{center}"
        assert ex._strip_resource_envs(fig) == fig

    def test_prose_center_kept(self, ex) -> None:
        prose = r"\begin{center}\textbf{Table 1: Results across benchmarks}\end{center}"
        assert ex._strip_resource_envs(prose) == prose


class TestShipoutAndCodeFences:
    """General handling of venue page-overlay banners (PROJ-603) and embedded
    markdown code fences (PROJ-601)."""

    def test_shipout_banner_stripped(self, ex) -> None:
        banner = (r"\AddToShipoutPictureFG*{%"
                  r"\AtPageLowerLeft{\makebox[\paperwidth][c]{"
                  r"\begin{minipage}{0.9\textwidth}Preprint\end{minipage}}}}")
        out = ex._strip_shipout_overlays("Before.\n" + banner + "\nAfter.")
        assert "AddToShipoutPicture" not in out and "Preprint" not in out
        assert "Before." in out and "After." in out

    def test_background_setup_stripped(self, ex) -> None:
        out = ex._strip_shipout_overlays(r"x \backgroundsetup{scale=1,contents={DRAFT}} y")
        assert "backgroundsetup" not in out and "DRAFT" not in out
        assert "x" in out and "y" in out

    def test_markdown_fence_to_lstlisting(self, ex) -> None:
        md = ("Text.\n\n```json\n{\"k\": \"a very long value that overflows\"}\n```\n\nMore.")
        out = ex._convert_markdown_code_fences(md)
        assert r"\begin{lstlisting}" in out and r"\end{lstlisting}" in out
        assert "```" not in out
        assert "a very long value" in out and "Text." in out and "More." in out

    def test_fence_without_language(self, ex) -> None:
        out = ex._convert_markdown_code_fences("```\nplain code\n```")
        assert r"\begin{lstlisting}" in out and "plain code" in out

    def test_non_fence_backticks_left_alone(self, ex) -> None:
        # A single inline backtick run is not a fenced block.
        txt = "Use the `foo` function here."
        assert ex._convert_markdown_code_fences(txt) == txt


class TestTcolorboxForwarding:
    """Fix (PROJ-565/601/606): custom tcolorbox callout/prompt boxes defined
    in the discarded preamble are forwarded so content stays boxed/wrapped."""

    def test_forwards_library_set_and_def(self, ex) -> None:
        src = (r"\tcbuselibrary{skins,breakable}" "\n"
               r"\tcbset{agentscope/.style={colback=blue!5,colframe=blue}}" "\n"
               r"\newtcolorbox[auto counter]{promptbox}[2][]{colback=gray!5,title=#2,#1}")
        out = ex._forwarded_tcolorbox(src)
        joined = "\n".join(out)
        assert r"\tcbuselibrary{skins,breakable}" in joined
        assert "agentscope/.style" in joined
        assert r"\newtcolorbox[auto counter]{promptbox}[2][]" in joined
        # library must come before the definition that may rely on it
        assert out.index(next(p for p in out if "tcbuselibrary" in p)) < \
               out.index(next(p for p in out if "newtcolorbox" in p))

    def test_scoped_bare_tcbset_not_forwarded(self, ex) -> None:
        # Bare \tcbset option-setting (often scoped inside another macro)
        # must NOT be forwarded globally (PROJ-601 set these in \mymaketitle).
        src = r"\newcommand{\mymaketitle}{\tcbset{enhanced,frame hidden}\tcbset{colback=odlbg}}"
        out = ex._forwarded_tcolorbox(src)
        assert out == []

    def test_no_tcolorbox_returns_empty(self, ex) -> None:
        assert ex._forwarded_tcolorbox(r"\section{x} plain text") == []

    def test_balanced_body_capture(self, ex) -> None:
        # nested braces in the body must be captured fully
        src = r"\newtcolorbox{b}{colback=red, title={A {nested} title}}"
        out = ex._forwarded_tcolorbox(src)
        assert len(out) == 1 and out[0].count("{") == out[0].count("}")
