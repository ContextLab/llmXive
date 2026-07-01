"""Reviewed-Preprints follow-up spawn (2026-07-01, increment 3b).

Each preprint seeds a SEPARATE llmXive brainstorm project (our own study) that
extends + CITES the source. The follow-up drops the original byline (it's ours);
the preprint project is left untouched.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import yaml

from llmxive.paper_reprocess.branch_nocode import spawn_followup_project
from llmxive.types import Project, Stage


def _seed_preprint(tmp_path: Path) -> tuple[Path, Project]:
    repo = tmp_path / "repo"
    pid = "PROJ-601-https-arxiv-org-abs-2605-12882"
    pdir = repo / "projects" / pid
    (pdir / "paper").mkdir(parents=True)
    (pdir / "paper" / "metadata.json").write_text(json.dumps({
        "authors": ["Alice Original", "Bob Author"],
        "arxiv_url": "https://arxiv.org/abs/2605.12882",
        "arxiv_id": "2605.12882",
        "title": "A Third-Party Paper On Widgets",
        "toplevel_tex": [],
    }), encoding="utf-8")
    now = datetime.now(UTC)
    proj = Project(
        id=pid, title="A Third-Party Paper On Widgets", field="computer science",
        current_stage=Stage.REVIEWED_PREPRINT, points_research={}, points_paper={},
        created_at=now, updated_at=now, artifact_hashes={},
    )
    from llmxive.state import project as project_store
    project_store.save(proj, repo_root=repo)
    return repo, proj


def test_spawn_followup_creates_separate_citing_project(tmp_path: Path) -> None:
    repo, preprint = _seed_preprint(tmp_path)
    orig_meta = (repo / "projects" / preprint.id / "paper" / "metadata.json").read_bytes()

    new_id = spawn_followup_project(
        preprint, repo_root=repo,
        _extension_fn=lambda _text: "We propose extending widget analysis to gadgets.",
    )

    # A DIFFERENT, fresh project id.
    assert new_id != preprint.id
    assert new_id.startswith("PROJ-")
    # Exists at BRAINSTORMED.
    from llmxive.state import project as project_store
    followup = project_store.load(new_id, repo_root=repo)
    assert followup.current_stage == Stage.BRAINSTORMED
    # Its idea proposes the extension + CITES the source (title + authors + url),
    # and does NOT claim the original byline as its own authors.
    idea = next((repo / "projects" / new_id / "idea").glob("*.md")).read_text()
    assert "extending widget analysis to gadgets" in idea
    assert "A Third-Party Paper On Widgets" in idea
    assert "Alice Original" in idea  # cited, not as our author
    assert "arxiv.org/abs/2605.12882" in idea
    assert "paper_authors:" not in idea  # the follow-up is ours — no borrowed byline
    # The PREPRINT project is untouched.
    assert (repo / "projects" / preprint.id / "paper" / "metadata.json").read_bytes() == orig_meta
