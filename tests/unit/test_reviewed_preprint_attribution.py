"""Reviewed-Preprint attribution ethics (2026-07-01).

A review-only ingested paper must credit ONLY (1) original authors, (2) the
submitter, and (3) the UNDERLYING review models — never a modifier
(implementer/planner/tasker/reviser). This pins that `web_data._project_authors`
filters the run-log to reviewer runs when `paper/preprint.json` marks the project.
"""

from __future__ import annotations

import json
from pathlib import Path

from llmxive.paper_reprocess.preprint import write_preprint_manifest
from llmxive.web_data import _project_authors


def _repo_with_runlog(tmp_path: Path, *, preprint: bool) -> tuple[Path, str]:
    """A minimal repo: one project with metadata authors + a run-log holding a
    REVIEWER run (claude-sonnet-4.7) and an IMPLEMENTER run (qwen-impl)."""
    repo = tmp_path / "repo"
    pid = "PROJ-601-preprint"
    proj = repo / "projects" / pid
    (proj / "paper").mkdir(parents=True)
    # real agents/ so registry/alias helpers behave as in production (no mocks)
    real_agents = Path(__file__).resolve().parents[2] / "agents"
    (repo / "agents").symlink_to(real_agents)
    (proj / "paper" / "metadata.json").write_text(
        json.dumps({"authors": ["Alice Original", "Bob Author"],
                    "arxiv_url": "https://arxiv.org/abs/2605.12882"}),
        encoding="utf-8",
    )
    if preprint:
        write_preprint_manifest(
            proj, source_url="https://arxiv.org/abs/2605.12882",
            ingested_via="scrape", submitter="github-actions[bot]",
            ingested_at="2026-07-01",
        )
    rl = repo / "state" / "run-log" / "2026-07"
    rl.mkdir(parents=True)
    (rl / "runs.jsonl").write_text(
        json.dumps({"project_id": pid, "agent_name": "research_reviewer_idea_quality",
                    "model_name": "claude-sonnet-4.7", "outcome": "success"}) + "\n"
        + json.dumps({"project_id": pid, "agent_name": "implementer",
                      "model_name": "qwen-impl", "outcome": "success"}) + "\n",
        encoding="utf-8",
    )
    return repo, pid


def test_preprint_credits_reviewer_model_not_implementer(tmp_path: Path) -> None:
    repo, pid = _repo_with_runlog(tmp_path, preprint=True)
    authors = _project_authors(repo, pid)
    names = {a["name"] for a in authors}
    # original authors credited
    assert any("Alice" in n for n in names)
    assert any("Bob" in n for n in names)
    # the UNDERLYING review model credited (by model_name, not the prompt name)
    assert any("claude-sonnet-4.7" in n for n in names)
    assert "research_reviewer_idea_quality" not in names  # role is never the identity
    # the IMPLEMENTER (modifier) is NOT credited on a preprint
    assert not any("qwen-impl" in n for n in names), (
        "a modifier run must never be credited on a review-only preprint"
    )


def test_non_preprint_still_credits_implementer(tmp_path: Path) -> None:
    # Control: without preprint.json the normal rules apply — the implementer IS an
    # author (this is a real llmXive project, not a third party's paper).
    repo, pid = _repo_with_runlog(tmp_path, preprint=False)
    names = {a["name"] for a in _project_authors(repo, pid)}
    assert any("qwen-impl" in n for n in names)
    assert any("claude-sonnet-4.7" in n for n in names)
