"""Reviewed-Preprint manifest (2026-07-01 ethics change) — foundation tests.

A `paper/preprint.json` marks a project as a review-only Reviewed Preprint and
carries the provenance the UI + attribution need. These pin the writer/reader,
the terminal-stage flag helper, and the human-readable ingestion statement.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.paper_reprocess.preprint import (
    ingestion_statement,
    is_reviewed_preprint,
    load_preprint_manifest,
    write_preprint_manifest,
)


def test_write_and_load_roundtrip(tmp_path: Path) -> None:
    proj = tmp_path / "projects" / "PROJ-601-x"
    proj.mkdir(parents=True)
    path = write_preprint_manifest(
        proj,
        source_url="https://arxiv.org/abs/2605.12882",
        ingested_via="llmXive dashboard, GitHub issue #208",
        submitter="github-actions[bot]",
        ingested_at="2026-07-01T12:00:00+00:00",
        followup_project_id="PROJ-999-followup",
    )
    assert path == proj / "paper" / "preprint.json"
    m = load_preprint_manifest(proj)
    assert m is not None
    assert m["is_reviewed_preprint"] is True
    assert m["source_url"] == "https://arxiv.org/abs/2605.12882"
    assert m["followup_project_id"] == "PROJ-999-followup"


def test_is_reviewed_preprint_flag(tmp_path: Path) -> None:
    proj = tmp_path / "projects" / "PROJ-601-x"
    proj.mkdir(parents=True)
    assert is_reviewed_preprint(proj) is False  # no manifest yet
    write_preprint_manifest(
        proj, source_url="https://arxiv.org/abs/x", ingested_via="v",
        submitter="s", ingested_at="2026-07-01",
    )
    assert is_reviewed_preprint(proj) is True


def test_load_missing_returns_none(tmp_path: Path) -> None:
    proj = tmp_path / "projects" / "PROJ-none"
    proj.mkdir(parents=True)
    assert load_preprint_manifest(proj) is None


def test_ingestion_statement_arxiv_and_hf() -> None:
    arx = ingestion_statement({
        "source_url": "https://arxiv.org/abs/2605.12882",
        "ingested_via": "llmXive dashboard, GitHub issue #208",
        "submitter": "github-actions[bot]",
        "ingested_at": "2026-07-01T12:00:00+00:00",
    })
    assert "scraped from arXiv" in arx
    assert "2026-07-01" in arx
    assert "submitted by github-actions[bot]" in arx

    hf = ingestion_statement({
        "source_url": "https://huggingface.co/papers/2605.12882",
        "ingested_via": "user submission",
        "submitter": "jane",
        "ingested_at": "2026-07-01",
    })
    assert "scraped from HuggingFace papers" in hf
    assert "submitted by jane" in hf
