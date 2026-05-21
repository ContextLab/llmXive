"""Spec 013 — unit tests for the post-paper-appendix renderer (FR-034..FR-036).

Closes finding F5: assert the spacer page links to the GitHub
project-directory URL, NOT the dashboard root (FR-033).
"""

from __future__ import annotations

from pathlib import Path

from llmxive.pipeline import post_paper_appendix as ppa


class TestRenderSpacer:
    def test_contains_github_project_url(self) -> None:
        """FR-033: the spacer URL points to the GitHub project directory,
        not the dashboard root. Closes finding F5."""
        out = ppa.render_spacer("PROJ-578-https-arxiv-org-abs-2605-14906")
        assert (
            "https://github.com/ContextLab/llmXive/tree/main/projects/"
            "PROJ-578-https-arxiv-org-abs-2605-14906/"
        ) in out

    def test_contains_end_of_paper_text(self) -> None:
        out = ppa.render_spacer("PROJ-X")
        assert "End of paper" in out

    def test_clears_page_styles(self) -> None:
        out = ppa.render_spacer("PROJ-X")
        # Spacer must suppress page numbering / headers (FR-036).
        assert r"\thispagestyle{empty}" in out

    def test_does_not_contain_dashboard_url(self) -> None:
        out = ppa.render_spacer("PROJ-X")
        # FR-033 explicitly says NOT the dashboard root.
        assert "context-lab.com/llmXive" not in out


class TestRenderInline:
    def test_preserves_ref_macro(self) -> None:
        """LaTeX commands like \\ref must pass through verbatim so
        downstream cross-references resolve (FR-033 + earlier gen_appendix
        fix). Closes finding F5 at the renderer level."""
        out = ppa.render_inline(r"See Appendix \ref{app:image_release} for details.")
        assert r"\ref{app:image_release}" in out
        # No double-escaping.
        assert r"\textbackslash{}ref" not in out

    def test_preserves_cite_macro(self) -> None:
        out = ppa.render_inline(r"As shown in \cite{foo2024}.")
        assert r"\cite{foo2024}" in out

    def test_math_span_preserved(self) -> None:
        out = ppa.render_inline(r"Cohen's $\kappa = 0.86$ shows agreement.")
        assert r"$\kappa = 0.86$" in out

    def test_bold_renders_to_textbf(self) -> None:
        out = ppa.render_inline("This is **important**.")
        assert r"\textbf{important}" in out
