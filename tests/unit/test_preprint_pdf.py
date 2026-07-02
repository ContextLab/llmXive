"""Reviewed-Preprint PDFs (2026-07-01, increment 5).

Fast deterministic tests (no LaTeX) for the cover/review LaTeX builders + the
pypdf prepend (byte-preservation). A ``slow``-marked test compiles a real cover
through lualatex and prepends it to a real original PDF to prove the toolchain
path end-to-end.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from llmxive.paper_reprocess.preprint_pdf import (
    build_cover_tex,
    build_peer_review_tex,
    prepend_cover_to_pdf,
    render_llmxive_pdf,
    tex_escape,
)


def test_tex_escape_handles_specials() -> None:
    assert tex_escape("a_b & c% $d# {e}") == r"a\_b \& c\% \$d\# \{e\}"
    assert tex_escape("") == ""


def test_build_cover_tex_has_provenance_blurb_and_links() -> None:
    meta = {
        "title": "Widgets & Gadgets: A 100% Study",
        "authors": ["Alice Original", "Bob Author"],
        "abstract": "We study widgets_and_gadgets.",
        "arxiv_url": "https://arxiv.org/abs/2605.12882",
    }
    tex = build_cover_tex(
        meta,
        "Ingested by llmXive on 2026-07-01 — scraped from arXiv.",
        review_report_name="peer-review-llmxive.pdf",
        followup_project_id="PROJ-999-followup",
    )
    assert r"\documentclass{llmxive}" in tex
    assert r"\paperstatus{Reviewed Preprint}" in tex
    # LaTeX specials in the title are escaped (never raw).
    assert r"Widgets \& Gadgets: A 100\% Study" in tex
    assert "Alice Original, Bob Author" in tex
    assert "never modified" in tex
    assert "Ingested by llmXive on 2026-07-01" in tex
    assert "https://arxiv.org/abs/2605.12882" in tex
    assert "github.com/ContextLab/llmXive" in tex
    assert "peer-review-llmxive.pdf" in tex
    assert "PROJ-999-followup" in tex
    # About-llmXive blurb reflects the real provenance: third-party papers from
    # Hugging Face / human submissions, reviewed AND used to seed a follow-up —
    # not "this paper was brainstormed".
    assert "Hugging Face" in tex
    assert "seed a new llmXive follow-up" in tex
    assert "did not write it" in tex


def test_build_peer_review_tex_renders_reviewers() -> None:
    from types import SimpleNamespace

    recs = [
        SimpleNamespace(
            reviewer_name="paper_reviewer_overreach",
            verdict="minor_revision",
            model_name="qwen.qwen3.5-122b",
            # Markdown body: bold, inline code, and a bullet list must render as
            # LaTeX, not as literal ** / backtick / - source.
            feedback=(
                'The **abstract** overstates the result in `main.tex`, calling '
                'it "state of the art".\n\n'
                "1. First concern\n\n2. Second concern\n"
            ),
            action_items=[
                SimpleNamespace(text="Soften the SOTA claim.", severity="writing")
            ],
        ),
        SimpleNamespace(
            reviewer_name="paper_reviewer_claim_accuracy",
            verdict="accept",
            model_name="openai.gpt-oss-120b",
            feedback="Claims are supported.",
            action_items=[],
        ),
    ]
    proj = SimpleNamespace(title="A Paper", id="PROJ-1-x")
    tex = build_peer_review_tex(proj, recs)
    assert r"llmXive Automated Review of A Paper" in tex
    # Reviewer names are prettified for a clean header (not raw snake_case).
    assert r"\section*{Overreach}" in tex
    assert r"\section*{Claim Accuracy}" in tex
    assert "Soften the SOTA claim." in tex
    assert "advisory" in tex and "automated feedback" in tex
    # Opening section describes the process + a panel ROSTER (names only — the
    # per-reviewer descriptions are NOT duplicated in the overview).
    assert r"\section*{How this review was produced}" in tex
    assert "This paper's panel" in tex
    assert tex.count("over-claiming") == 1  # overreach blurb appears ONCE (its section)
    assert tex.count("citations") == 1  # claim_accuracy blurb appears ONCE
    # Each reviewer section carries its pre-written focus blurb.
    assert "over-claiming" in tex  # overreach focus blurb
    assert "citations" in tex  # claim_accuracy focus blurb
    # The prompts-folder link renders as a real \href (single backslash), never
    # as literal "\\href" text.
    assert r"\href{https://github.com/ContextLab/llmXive/tree/main/agents/prompts}" in tex
    assert "\\\\href" not in tex
    assert r"\textbf{Reviewer model:}" in tex
    assert r"\texttt{qwen.qwen3.5-122b}" in tex
    assert r"\texttt{openai.gpt-oss-120b}" in tex
    # Links: the overview links the prompt library folder; each reviewer links
    # its own prompt file.
    assert r"\usepackage{hyperref}" in tex
    assert "github.com/ContextLab/llmXive/tree/main/agents/prompts" in tex
    assert (
        r"\href{https://github.com/ContextLab/llmXive/blob/main/agents/prompts/"
        r"paper_reviewer_overreach.md}" in tex
    )
    # Markdown feedback renders as LaTeX, never as raw markdown source.
    assert r"\textbf{abstract}" in tex
    assert r"\texttt{main.tex}" in tex
    assert "First concern" in tex
    assert "**" not in tex  # no literal markdown emphasis leaks through
    # A loose numbered list stays ONE enumerate (items number 1,2,3 — not 1,1).
    assert tex.count(r"\begin{enumerate}") == 1 and tex.count(r"\item") >= 2
    # Straight quotes render as directional LaTeX quotes (open ``, close '').
    assert "``state of the art''" in tex
    # Prominent, human-not-checked disclaimer at the top.
    assert "not checked by any human" in tex
    assert "errors, misreadings, and inaccuracies are likely" in tex


def test_build_peer_review_tex_renders_math() -> None:
    from types import SimpleNamespace

    rec = SimpleNamespace(
        reviewer_name="paper_reviewer_statistical_analysis",
        verdict="minor_revision",
        model_name="qwen.qwen3.5-122b",
        feedback=(
            r"The bound $\Delta_{\cos} \in [0.02, 0.05]$ is tight; also "
            r"$$E = mc^2$$ and \(a_i\)."
        ),
        action_items=[],
    )
    proj = SimpleNamespace(title="P", id="PROJ-x")
    tex = build_peer_review_tex(proj, [rec])
    # LaTeX math passes through verbatim (rendered as math), not escaped.
    assert r"$\Delta_{\cos} \in [0.02, 0.05]$" in tex
    assert r"$$E = mc^2$$" in tex
    assert r"\(a_i\)" in tex
    assert r"\usepackage{amsmath,amssymb}" in tex
    # The compile-fallback (render_math=False) escapes the math to literal text.
    tex_fallback = build_peer_review_tex(proj, [rec], render_math=False)
    assert r"$\Delta" not in tex_fallback
    assert r"\$" in tex_fallback


def test_control_chars_stripped_from_review() -> None:
    """A stray control character (e.g. BEL 0x07) in an LLM review body must be
    stripped — lualatex rejects it with "invalid character" and fails the whole
    report (seen: PROJ-647)."""
    from types import SimpleNamespace

    from llmxive.paper_reprocess.preprint_pdf import strip_control_chars

    assert strip_control_chars("ho_t\x07 and\x00 params\x1f") == "ho_t and params"
    assert strip_control_chars("keep\ttab\nand\r\n") == "keep\ttab\nand\r\n"
    rec = SimpleNamespace(
        reviewer_name="paper_reviewer_writing_quality",
        verdict="minor_revision",
        model_name="qwen.qwen3.5-122b",
        feedback="A claim about \x07 parameters $x_i$ is unclear.",
        action_items=[SimpleNamespace(text="Fix \x07 wording.", severity="writing")],
    )
    proj = SimpleNamespace(title="P", id="PROJ-y")
    tex = build_peer_review_tex(proj, [rec])
    assert "\x07" not in tex and "\x00" not in tex
    # A Reviewed Preprint is advisory only — NO accept/reject verdict is shown,
    # so the report never contradicts its own "nothing is accepted or rejected".
    assert "Verdict" not in tex
    # the verdict *values* never surface (the disclaimer's "accepted" is fine)
    assert "minor_revision" not in tex


def test_prepend_preserves_original_pages_and_file(tmp_path: Path) -> None:
    from pypdf import PdfReader, PdfWriter

    # A 1-page "cover" and a 3-page "original".
    cover_path = tmp_path / "cover.pdf"
    w = PdfWriter()
    w.add_blank_page(width=200, height=200)
    with cover_path.open("wb") as fh:
        w.write(fh)

    orig_path = tmp_path / "orig.pdf"
    w = PdfWriter()
    for _ in range(3):
        w.add_blank_page(width=300, height=400)
    with orig_path.open("wb") as fh:
        w.write(fh)
    orig_bytes = orig_path.read_bytes()

    out = tmp_path / "merged.pdf"
    prepend_cover_to_pdf(cover_path, orig_path, out)

    merged = PdfReader(str(out))
    assert len(merged.pages) == 4  # 1 cover + 3 original
    # The original file on disk is never rewritten by the prepend.
    assert orig_path.read_bytes() == orig_bytes
    # The body pages keep the original's dimensions (300x400), not the cover's.
    assert round(float(merged.pages[1].mediabox.width)) == 300


@pytest.mark.slow
def test_real_cover_compile_and_prepend(tmp_path: Path) -> None:
    """Genuinely compile a cover via lualatex + prepend to a real original PDF."""
    import shutil

    from pypdf import PdfReader

    repo = Path(__file__).resolve().parents[2]
    if not (repo / "papers" / ".style" / "llmxive.cls").is_file():
        pytest.skip("llmxive.cls not present")
    if shutil.which("lualatex") is None:
        pytest.skip("lualatex not on PATH")

    meta = {
        "title": "A Reviewed Preprint",
        "authors": ["Alice Original"],
        "abstract": "We study the review of preprints.",
        "arxiv_url": "https://arxiv.org/abs/2605.00001",
    }
    tex = build_cover_tex(meta, "Ingested by llmXive on 2026-07-01.")
    cover = render_llmxive_pdf(tex, tmp_path / "cover", repo_root=repo, basename="cover")
    assert len(PdfReader(str(cover)).pages) == 1

    # Build a 5-page synthetic "original" and prepend.
    from pypdf import PdfWriter

    orig = tmp_path / "orig.pdf"
    w = PdfWriter()
    for _ in range(5):
        w.add_blank_page(width=300, height=400)
    with orig.open("wb") as fh:
        w.write(fh)

    out = tmp_path / "original-llmxive.pdf"
    prepend_cover_to_pdf(cover, orig, out)
    assert len(PdfReader(str(out)).pages) == 6
