"""Tests for `llmxive.agents.submission_intake.heal_paper_metadata`.

Real-world failure mode (PROJ-578/579/580/581 on 2026-05-16): when
arXiv returns a 429 at submission-intake time, the intake's
`_arxiv_metadata` returns `(None, None, ...)` and the project gets:
  - `title` = the issue title (which is the arXiv URL the user pasted)
  - `metadata.json::abstract` = null
  - paper card shows the URL as title and the issue-body boilerplate
    ("A paper was submitted via the website...") as the description.

The heal pass auto-recovers on the next hourly tick: if metadata.json
has `arxiv_id` but title looks like an arXiv URL (or abstract is empty),
re-fetch and patch both metadata.json and state YAML.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml


@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    """Minimal repo skeleton: state/projects/, projects/.../paper/."""
    state_dir = tmp_path / "state" / "projects"
    state_dir.mkdir(parents=True)
    return tmp_path


def _make_broken_paper_project(
    repo: Path, project_id: str, arxiv_id: str, *, also_state: bool = True,
) -> None:
    """Set up a paper project whose metadata.json mirrors the
    PROJ-578-style broken state."""
    pdir = repo / "projects" / project_id
    paper_dir = pdir / "paper"
    paper_dir.mkdir(parents=True)
    (paper_dir / "metadata.json").write_text(json.dumps({
        "arxiv_id": arxiv_id,
        "arxiv_url": f"https://arxiv.org/abs/{arxiv_id}",
        "title": f"https://arxiv.org/abs/{arxiv_id}",
        "authors": [],
        "abstract": None,
        "submitter": "github-actions[bot]",
        "source_files": ["main.tex"],
    }, indent=2), encoding="utf-8")
    if also_state:
        (repo / "state" / "projects" / f"{project_id}.yaml").write_text(yaml.safe_dump({
            "id": project_id,
            "title": f"https://arxiv.org/abs/{arxiv_id}",
            "field": "other",
            "current_stage": "paper_review",
            "created_at": "2026-05-16T00:00:00+00:00",
            "updated_at": "2026-05-16T00:00:00+00:00",
            "artifact_hashes": {},
            "points_research": {},
            "points_paper": {},
        }), encoding="utf-8")


def test_heal_updates_title_authors_abstract(fake_repo: Path) -> None:
    from llmxive.agents.submission_intake import heal_paper_metadata
    _make_broken_paper_project(fake_repo, "PROJ-999-https-arxiv-org-abs-2605-99999", "2605.99999")
    with patch(
        "llmxive.agents.submission_intake._arxiv_metadata",
        return_value=(["Alice", "Bob"], "Real Paper Title", "computer science",
                      "Real abstract text."),
    ):
        summary = heal_paper_metadata(fake_repo)
    assert summary["scanned"] == 1
    assert len(summary["healed"]) == 1
    healed = summary["healed"][0]
    assert healed["project"].startswith("PROJ-999-")
    assert healed["new_title"] == "Real Paper Title"
    assert healed["abstract_filled"] is True
    assert healed["authors_filled"] is True
    # Verify metadata.json
    meta = json.loads((fake_repo / "projects"
                       / "PROJ-999-https-arxiv-org-abs-2605-99999"
                       / "paper" / "metadata.json").read_text())
    assert meta["title"] == "Real Paper Title"
    assert meta["authors"] == ["Alice", "Bob"]
    assert meta["abstract"] == "Real abstract text."
    # Verify state YAML
    state = yaml.safe_load((fake_repo / "state" / "projects"
                            / "PROJ-999-https-arxiv-org-abs-2605-99999.yaml").read_text())
    assert state["title"] == "Real Paper Title"
    assert state["field"] == "computer science"


def test_heal_skips_already_complete(fake_repo: Path) -> None:
    """A project with a real title + abstract must not be touched."""
    from llmxive.agents.submission_intake import heal_paper_metadata
    pdir = fake_repo / "projects" / "PROJ-998-multabench"
    (pdir / "paper").mkdir(parents=True)
    (pdir / "paper" / "metadata.json").write_text(json.dumps({
        "arxiv_id": "2605.10616",
        "title": "MulTaBench: Real Title",
        "authors": ["Alice"],
        "abstract": "Real abstract.",
    }, indent=2), encoding="utf-8")
    with patch(
        "llmxive.agents.submission_intake._arxiv_metadata",
        return_value=(["Should", "Not"], "Should Not Override", "computer science",
                      "Should not override either."),
    ) as mock_fetch:
        summary = heal_paper_metadata(fake_repo)
    assert summary["scanned"] == 1
    assert summary["healed"] == []
    # The mock must not have been called — nothing to heal.
    assert mock_fetch.call_count == 0


def test_heal_handles_missing_paper_dir(fake_repo: Path) -> None:
    """A research project (no paper/ dir) is silently ignored."""
    from llmxive.agents.submission_intake import heal_paper_metadata
    (fake_repo / "projects" / "PROJ-997-no-paper").mkdir(parents=True)
    summary = heal_paper_metadata(fake_repo)
    assert summary["scanned"] == 0
    assert summary["healed"] == []


def test_heal_handles_arxiv_fetch_failure(fake_repo: Path) -> None:
    """When arXiv re-fetch returns nothing, project stays broken
    (so the next tick can retry)."""
    from llmxive.agents.submission_intake import heal_paper_metadata
    _make_broken_paper_project(fake_repo, "PROJ-996-https-arxiv-org-abs-2605-96666", "2605.96666")
    with patch(
        "llmxive.agents.submission_intake._arxiv_metadata",
        return_value=([], None, None, None),
    ):
        summary = heal_paper_metadata(fake_repo)
    assert summary["scanned"] == 1
    assert summary["healed"] == []
    assert len(summary["skipped"]) == 1


def test_heal_skips_project_without_arxiv_id(fake_repo: Path) -> None:
    """A paper project missing arxiv_id can't be healed — silently skip."""
    from llmxive.agents.submission_intake import heal_paper_metadata
    pdir = fake_repo / "projects" / "PROJ-995-non-arxiv"
    (pdir / "paper").mkdir(parents=True)
    (pdir / "paper" / "metadata.json").write_text(json.dumps({
        "title": "Some Paper", "abstract": None, "authors": [],
    }, indent=2), encoding="utf-8")
    summary = heal_paper_metadata(fake_repo)
    assert summary["scanned"] == 1
    assert summary["healed"] == []  # no arxiv_id → can't heal
