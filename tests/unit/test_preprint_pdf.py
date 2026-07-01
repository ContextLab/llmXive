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


def test_build_peer_review_tex_renders_reviewers() -> None:
    from types import SimpleNamespace

    recs = [
        SimpleNamespace(
            reviewer_name="paper_reviewer_overreach",
            verdict="minor_revision",
            feedback="The abstract overstates the result.",
            action_items=[
                SimpleNamespace(text="Soften the SOTA claim.", severity="writing")
            ],
        ),
        SimpleNamespace(
            reviewer_name="paper_reviewer_claim_accuracy",
            verdict="accept",
            feedback="Claims are supported.",
            action_items=[],
        ),
    ]
    proj = SimpleNamespace(title="A Paper", id="PROJ-1-x")
    tex = build_peer_review_tex(proj, recs)
    assert r"llmXive Automated Review of A Paper" in tex
    assert "paper\\_reviewer\\_overreach" in tex  # reviewer names escaped
    assert "Soften the SOTA claim." in tex
    assert "advisory" in tex and "automated feedback" in tex


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
