"""Tests for `scripts/compile_paper.py`.

Covers the pure helpers (no LaTeX engine required):
- `_has_pdf` distinguishes a valid PDF from a 0-byte / stub
- `_entry_tex` picks the right entry-point .tex
- `_clean_partial_outputs` removes the stub family

The full compile path is covered by `tests/test_restyle_arxiv_paper.py`
(existing) and end-to-end on real arXiv submissions by manual runs.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "compile_paper.py"


@pytest.fixture(scope="module")
def cp():
    """Load the script as a module (it's not in src/ to keep import-time
    side effects from leaking into the package)."""
    spec = importlib.util.spec_from_file_location("compile_paper", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["compile_paper"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _make_pdf(path: Path, *, body_size: int, trailer: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = b"%PDF-1.7\n" + (b"x" * body_size)
    if trailer:
        data += b"\n%%EOF\n"
    path.write_bytes(data)


class TestHasPdf:
    def test_real_multi_kb_pdf_counts(self, cp, tmp_path: Path) -> None:
        _make_pdf(tmp_path / "paper" / "pdf" / "main-llmxive.pdf", body_size=20_000)
        assert cp._has_pdf(tmp_path) is True

    def test_tiny_pdf_with_trailer_rejected(self, cp, tmp_path: Path) -> None:
        # lualatex sometimes writes ~2KB stubs WITH a %%EOF — we require
        # both EOF and minimum size to consider it valid.
        _make_pdf(tmp_path / "paper" / "pdf" / "main-llmxive.pdf", body_size=200)
        assert cp._has_pdf(tmp_path) is False

    def test_zero_byte_pdf_rejected(self, cp, tmp_path: Path) -> None:
        p = tmp_path / "paper" / "pdf" / "main-llmxive.pdf"
        p.parent.mkdir(parents=True)
        p.write_bytes(b"")
        assert cp._has_pdf(tmp_path) is False

    def test_no_pdf_dir(self, cp, tmp_path: Path) -> None:
        assert cp._has_pdf(tmp_path) is False


class TestEntryTex:
    def test_picks_from_metadata_toplevel_tex(self, cp, tmp_path: Path) -> None:
        src = tmp_path / "paper" / "source"
        src.mkdir(parents=True)
        (src / "arxiv_anyflow.tex").write_text(r"\documentclass{article}", encoding="utf-8")
        (src / "main.tex").write_text(r"\documentclass{article}", encoding="utf-8")
        entry = cp._entry_tex(tmp_path, {"toplevel_tex": ["arxiv_anyflow.tex"]})
        assert entry == "arxiv_anyflow.tex"

    def test_falls_back_to_single_documentclass(self, cp, tmp_path: Path) -> None:
        src = tmp_path / "paper" / "source"
        src.mkdir(parents=True)
        (src / "only.tex").write_text(r"\documentclass{article}", encoding="utf-8")
        (src / "section.tex").write_text("no class here", encoding="utf-8")
        assert cp._entry_tex(tmp_path, {}) == "only.tex"

    def test_main_tex_preferred_with_multiple_candidates(self, cp, tmp_path: Path) -> None:
        src = tmp_path / "paper" / "source"
        src.mkdir(parents=True)
        for name in ("anonymous.tex", "main.tex", "paper.tex"):
            (src / name).write_text(r"\documentclass{article}", encoding="utf-8")
        assert cp._entry_tex(tmp_path, {}) == "main.tex"

    def test_no_source_returns_none(self, cp, tmp_path: Path) -> None:
        assert cp._entry_tex(tmp_path, {}) is None


class TestRestyleStaleness:
    """Wrapper-regen staleness rule: when `extract_paper_content.py`
    has been updated more recently than an existing wrapper.tex, the
    wrapper must be regenerated. Without this rule, fixes to the
    wrapper-generator silently fail to flow through to old papers
    (PROJ-571 reproduced exactly this — fix landed, old wrapper kept
    compiling 'nedot.' above the title)."""

    def test_existing_wrapper_returned_when_fresh(self, cp, tmp_path: Path, monkeypatch) -> None:
        # Wrapper newer than script → no regen.
        src = tmp_path / "paper" / "source"
        src.mkdir(parents=True)
        wrapper = src / "main-llmxive.tex"
        wrapper.write_text("existing wrapper", encoding="utf-8")
        import os
        # Set wrapper mtime to NOW; restyle script mtime to long ago.
        script = cp.RESTYLE_SCRIPT
        if not script.exists():
            pytest.skip("RESTYLE_SCRIPT not found in test env")
        os.utime(wrapper, (10_000_000_000, 10_000_000_000))  # year 2286
        out = cp._restyle_if_needed(tmp_path, {"arxiv_id": "2099.99999"}, "main.tex")
        assert out == wrapper
        # The "existing wrapper" content must not have been overwritten.
        assert wrapper.read_text(encoding="utf-8") == "existing wrapper"


class TestInstallPrecompiledBbl:
    """When the source has a `.bbl` but no `.bib`, we must copy the
    `.bbl` into pdf_dir, renamed to match the wrapper stem, so lualatex
    can find it. Without this, natbib emits `[?]` for every citation
    (PROJ-576 symptom: the SANA-WM Intro was full of `[? ? ? ?]`)."""

    def test_copies_main_bbl_renamed_to_wrapper_stem(self, cp, tmp_path: Path) -> None:
        src = tmp_path / "source"
        pdf_dir = tmp_path / "pdf"
        src.mkdir()
        (src / "main.bbl").write_text(r"\bibitem{key}A. Author.", encoding="utf-8")
        dst = cp._install_precompiled_bbl(src, pdf_dir, "main-llmxive")
        assert dst is not None
        assert dst.name == "main-llmxive.bbl"
        assert dst.exists()
        assert r"\bibitem{key}" in dst.read_text(encoding="utf-8")

    def test_returns_none_when_no_bbl(self, cp, tmp_path: Path) -> None:
        src = tmp_path / "source"
        pdf_dir = tmp_path / "pdf"
        src.mkdir()
        assert cp._install_precompiled_bbl(src, pdf_dir, "main-llmxive") is None

    def test_prefers_main_bbl_when_multiple_exist(self, cp, tmp_path: Path) -> None:
        src = tmp_path / "source"
        pdf_dir = tmp_path / "pdf"
        src.mkdir()
        (src / "other.bbl").write_text("other-bib", encoding="utf-8")
        (src / "main.bbl").write_text("main-bib", encoding="utf-8")
        dst = cp._install_precompiled_bbl(src, pdf_dir, "main-llmxive")
        assert dst is not None and dst.read_text(encoding="utf-8") == "main-bib"


class TestCleanPartialOutputs:
    def test_removes_stub_family(self, cp, tmp_path: Path) -> None:
        for suffix in (".pdf", ".log", ".aux", ".out", ".toc", ".bbl", ".blg"):
            (tmp_path / f"main-llmxive{suffix}").write_text("stub", encoding="utf-8")
        (tmp_path / "main-llmxive.tex").write_text("keep me", encoding="utf-8")  # not in family
        (tmp_path / "other.pdf").write_text("keep me too", encoding="utf-8")
        cp._clean_partial_outputs(tmp_path, "main-llmxive")
        assert (tmp_path / "main-llmxive.tex").is_file()
        assert (tmp_path / "other.pdf").is_file()
        for suffix in (".pdf", ".log", ".aux", ".out", ".toc", ".bbl", ".blg"):
            assert not (tmp_path / f"main-llmxive{suffix}").exists()
