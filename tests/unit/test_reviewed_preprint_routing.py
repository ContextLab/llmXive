"""Reviewed-Preprints routing (2026-07-01 ethics change).

Intake must NEVER modify an ingested paper. `reprocess_ingested_paper` marks the
project a review-only Reviewed Preprint (writes provenance, parks it terminal) and
leaves the original paper bytes + metadata.json untouched — it no longer runs the
branch_code modify path.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import yaml

from llmxive.paper_reprocess.preprint import load_preprint_manifest
from llmxive.paper_reprocess.reprocess import reprocess_ingested_paper
from llmxive.types import Project, Stage


def _seed_ingested(tmp_path: Path) -> tuple[Path, Project]:
    repo = tmp_path / "repo"
    pid = "PROJ-601-https-arxiv-org-abs-2605-12882"
    pdir = repo / "projects" / pid
    (pdir / "paper").mkdir(parents=True)
    (pdir / "idea").mkdir(parents=True)
    (pdir / "paper" / "metadata.json").write_text(json.dumps({
        "authors": ["Alice Original", "Bob Author"],
        "arxiv_url": "https://arxiv.org/abs/2605.12882",
        "submitted_via": "llmXive dashboard, GitHub issue #208",
        "submitter": "github-actions[bot]",
        "title": "A Third-Party Paper",
    }), encoding="utf-8")
    (pdir / "paper" / "main.pdf").write_bytes(b"%PDF-1.5 original body bytes\n%%EOF")
    now = datetime.now(UTC).isoformat()
    state = {
        "id": pid, "title": "A Third-Party Paper", "field": "computer science",
        "current_stage": Stage.PAPER_INGESTED.value, "points_research": {},
        "points_paper": {}, "created_at": now, "updated_at": now,
        "last_run_id": None, "last_run_status": None, "failed_stage": None,
        "artifact_hashes": {}, "assigned_agent": None,
        "speckit_research_dir": None, "speckit_paper_dir": None,
        "revision_round": 0, "human_escalation_reason": None,
        "revision_spec_path": None,
    }
    sp = repo / "state" / "projects" / f"{pid}.yaml"
    sp.parent.mkdir(parents=True)
    sp.write_text(yaml.safe_dump(state, sort_keys=True), encoding="utf-8")
    from llmxive.state import project as project_store
    return repo, project_store.load(pid, repo_root=repo)


def test_reprocess_marks_preprint_and_never_modifies(tmp_path: Path) -> None:
    repo, project = _seed_ingested(tmp_path)
    pdir = repo / "projects" / project.id
    orig_meta = (pdir / "paper" / "metadata.json").read_bytes()
    orig_pdf = (pdir / "paper" / "main.pdf").read_bytes()

    result = reprocess_ingested_paper(project, repo_root=repo)

    # Parked at the terminal review-only stage (never advances, never modified).
    assert result.current_stage == Stage.REVIEWED_PREPRINT
    # Provenance manifest written.
    m = load_preprint_manifest(pdir)
    assert m is not None and m["is_reviewed_preprint"] is True
    assert m["source_url"] == "https://arxiv.org/abs/2605.12882"
    assert m["ingested_via"] == "llmXive dashboard, GitHub issue #208"
    assert m["submitter"] == "github-actions[bot]"
    # The original paper + metadata are BYTE-IDENTICAL — we did not modify it.
    assert (pdir / "paper" / "metadata.json").read_bytes() == orig_meta
    assert (pdir / "paper" / "main.pdf").read_bytes() == orig_pdf
    # No backfilled specs / no llmXive modification of the work.
    assert not list(pdir.glob("specs/*/spec.md"))
