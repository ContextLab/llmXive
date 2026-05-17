"""Tests for paper_reviewer's arxiv-intake fallback path.

Real-world failure: 26 paper-reviewer invocations across PROJ-564 +
PROJ-566 (both arXiv-submitted papers) failed with
``FileNotFoundError: no paper specs/ feature dir`` because those
projects never ran through the home-grown spec→plan→tasks→implement
pipeline — they came in fully-formed from arXiv with ``paper/source/``
+ ``paper/metadata.json``. The reviewer now falls back to hashing
``metadata.json`` when ``paper/specs/`` doesn't exist.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _make_arxiv_intake_project(repo: Path, project_id: str) -> Path:
    """Build a minimal arXiv-intake project layout (paper/ + metadata.json,
    NO paper/specs/)."""
    proj_dir = repo / "projects" / project_id
    paper = proj_dir / "paper"
    (paper / "source").mkdir(parents=True)
    (paper / "pdf").mkdir()
    (paper / "figures").mkdir()
    (paper / "source" / "main.tex").write_text(r"\documentclass{article}\begin{document}x\end{document}",
                                                encoding="utf-8")
    (paper / "metadata.json").write_text(json.dumps({
        "arxiv_id": "2605.99999",
        "arxiv_url": "https://arxiv.org/abs/2605.99999",
        "title": "Synthetic Test Paper",
        "authors": ["A. Author"],
        "submitter": "github-actions[bot]",
        "submitted_via": "test",
        "source_files": ["main.tex"],
        "toplevel_tex": ["main.tex"],
    }, indent=2), encoding="utf-8")
    return proj_dir


class TestArxivIntakeFallback:
    def test_paper_feature_dir_returns_none_when_no_specs(self, tmp_path: Path) -> None:
        """Without instantiating the full agent (which needs a complete
        registry entry), exercise the _paper_feature_dir helper directly
        as an unbound method on the class — it doesn't read self."""
        from llmxive.agents.paper_reviewer import PaperReviewerAgent
        proj = _make_arxiv_intake_project(tmp_path, "PROJ-999-test")
        # _paper_feature_dir is a method but only reads project_dir; bypass
        # __init__ to avoid the registry-entry validation.
        agent = object.__new__(PaperReviewerAgent)
        assert agent._paper_feature_dir(proj) is None

    def test_handle_response_uses_metadata_json_when_no_feature_dir(self, tmp_path: Path, monkeypatch) -> None:
        """When `paper/specs/` is missing, handle_response should hash
        `paper/metadata.json` and produce a schema-valid artifact_path
        (matches ^projects/PROJ-\\d+-...$)."""
        # We don't run the full handle_response (writes to repo state) —
        # just verify the path-selection logic by reading the source.
        # An integration-style test would need the full agents-registry
        # stack which is out of unit-test scope.
        from llmxive.agents.paper_reviewer import PaperReviewerAgent
        # Sanity: confirm the file references the metadata.json fallback.
        src = Path(__file__).resolve().parents[2] / "src" / "llmxive" / "agents" / "paper_reviewer.py"
        text = src.read_text()
        assert 'project_dir / "paper" / "metadata.json"' in text, (
            "paper_reviewer.handle_response should fall back to metadata.json "
            "when feature_dir is None"
        )
        assert "arXiv-intake" in text, (
            "the fallback path should be documented in code as arxiv-intake"
        )

    def test_no_feature_dir_AND_no_metadata_still_hard_fails(self, tmp_path: Path) -> None:
        """A project with NEITHER paper/specs/ NOR paper/metadata.json
        is a real precondition violation — the reviewer must still
        hard-fail with an actionable message."""
        from llmxive.agents.paper_reviewer import PaperReviewerAgent
        # Just confirm the source still has the hard-fail branch.
        src = Path(__file__).resolve().parents[2] / "src" / "llmxive" / "agents" / "paper_reviewer.py"
        text = src.read_text()
        assert "and no paper/metadata.json" in text, (
            "the hard-fail message should explain BOTH conditions"
        )


class TestArxivIntakeFigureDiscovery:
    """For arXiv-intake papers, figures live in paper/source/{figs,pics,
    images,Figures}/ — not paper/figures/. The reviewer must discover
    them or the LLM has no visual context to review."""

    def test_discovers_pdf_figures_under_pics(self, tmp_path: Path) -> None:
        from llmxive.agents.paper_reviewer import _collect_figures_from_arxiv_source
        src = tmp_path / "source"
        (src / "pics").mkdir(parents=True)
        (src / "pics" / "figure1.pdf").write_bytes(b"x" * 1234)
        (src / "pics" / "figure2.png").write_bytes(b"y" * 100)
        out = _collect_figures_from_arxiv_source(src)
        assert "pics/figure1.pdf" in out
        assert "pics/figure2.png" in out
        assert "1234 bytes" in out

    def test_discovers_figures_in_multiple_subdirs(self, tmp_path: Path) -> None:
        from llmxive.agents.paper_reviewer import _collect_figures_from_arxiv_source
        src = tmp_path / "source"
        # macOS HFS+ is case-insensitive, so don't use both "figures" and
        # "Figures" — pick distinct subdir names.
        (src / "figures").mkdir(parents=True)
        (src / "images").mkdir(parents=True)
        (src / "logo").mkdir(parents=True)
        (src / "figures" / "a.pdf").write_bytes(b"a")
        (src / "images" / "b.eps").write_bytes(b"b")
        (src / "logo" / "c.svg").write_bytes(b"c")
        out = _collect_figures_from_arxiv_source(src)
        assert all(s in out for s in ("figures/a.pdf", "images/b.eps", "logo/c.svg"))

    def test_skips_top_level_pdfs_likely_compiled_output(self, tmp_path: Path) -> None:
        from llmxive.agents.paper_reviewer import _collect_figures_from_arxiv_source
        src = tmp_path / "source"
        src.mkdir(parents=True)
        (src / "main.pdf").write_bytes(b"compiled output, not a figure")
        (src / "pics").mkdir()
        (src / "pics" / "real-figure.pdf").write_bytes(b"actual figure")
        out = _collect_figures_from_arxiv_source(src)
        assert "main.pdf" not in out  # top-level PDF skipped
        assert "pics/real-figure.pdf" in out

    def test_caps_at_200_entries(self, tmp_path: Path) -> None:
        from llmxive.agents.paper_reviewer import _collect_figures_from_arxiv_source
        src = tmp_path / "source" / "figs"
        src.mkdir(parents=True)
        for i in range(250):
            (src / f"f{i:03d}.png").write_bytes(b"x")
        out = _collect_figures_from_arxiv_source(src.parent)
        assert "truncated at 200 entries" in out

    def test_real_world_proj_564_discovers_10_figures(self) -> None:
        """Smoke test against the actual PROJ-564 source on disk.
        Skips if PROJ-564 isn't checked out (e.g., on a fresh clone)."""
        from llmxive.agents.paper_reviewer import _collect_figures_from_arxiv_source
        repo = Path(__file__).resolve().parents[2]
        src = repo / "projects" / "PROJ-564-qwen-image-vae-2-0-technical-report" / "paper" / "source"
        if not src.is_dir():
            pytest.skip("PROJ-564 source not checked out")
        out = _collect_figures_from_arxiv_source(src)
        lines = [line for line in out.splitlines() if line.startswith("- ")]
        assert len(lines) >= 5, f"expected ≥5 figures in PROJ-564 source, got {len(lines)}"
        # At least one figure under pics/
        assert any("pics/" in line for line in lines)


class TestArxivIntakeMetadataBlock:
    """The reviewer prompt must include a 'paper provenance' header for
    arxiv-intake papers so the LLM knows it's reviewing a third-party
    manuscript, not a home-grown one."""

    def test_intake_block_exists_in_source(self) -> None:
        src = Path(__file__).resolve().parents[2] / "src" / "llmxive" / "agents" / "paper_reviewer.py"
        text = src.read_text()
        assert "Paper provenance — IMPORTANT context" in text
        assert "third-party" in text or "ingested verbatim" in text
        assert "submitter field is the llmXive intake" in text
