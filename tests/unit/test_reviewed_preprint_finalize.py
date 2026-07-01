"""Reviewed-Preprints full intake orchestration (2026-07-01, increment 4).

`finalize_reviewed_preprint` ties the three ethics-safe effects together: mark
(never modify) → peer-review once → spawn a SEPARATE citing follow-up, recording
its id in `preprint.json`. Offline, the review network boundary is stubbed and the
follow-up extension is injected; the REAL marking / review-record writing / spawn
all run.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.paper_reprocess.reprocess import finalize_reviewed_preprint
from llmxive.types import Project, Stage

_PROJ_ID = "PROJ-903-preprint-finalize-test"

_REVIEW_RESPONSE = (
    "---\n"
    "verdict: minor_revision\n"
    "score: 0.0\n"
    "action_items:\n"
    "  - text: State the sample size used in the main experiment.\n"
    "    severity: writing\n"
    "feedback: Interesting; report the sample size.\n"
    "---\n\n"
    "Please report the sample size for the main experiment in Section 3.\n"
)


@pytest.fixture
def tmp_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Project]:
    repo = tmp_path / "repo"
    pdir = repo / "projects" / _PROJ_ID
    (pdir / "paper" / "source").mkdir(parents=True)
    (pdir / "idea").mkdir(parents=True)
    (pdir / "idea" / "stub.md").write_text("---\nfield: other\n---\n\n# Stub\n", encoding="utf-8")
    (pdir / "paper" / "metadata.json").write_text(
        json.dumps(
            {
                "arxiv_id": "2605.42424",
                "arxiv_url": "https://arxiv.org/abs/2605.42424",
                "title": "A Preprint To Finalize",
                "authors": ["Carol Author", "Dave Writer"],
                "abstract": "We study gizmos.",
                "submitted_via": "llmXive dashboard, GitHub issue #321",
                "submitter": "github-actions[bot]",
                "toplevel_tex": ["main.tex"],
                "source_files": ["main.tex"],
                "code": [],
                "data": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (pdir / "paper" / "source" / "main.tex").write_text(
        "\\title{A Preprint To Finalize}\n\\begin{abstract}\nWe study gizmos.\n"
        "\\end{abstract}\n\\section{Method}\nWe measure gizmos.\n",
        encoding="utf-8",
    )
    real_repo = Path(__file__).resolve().parents[2]
    (repo / "agents").symlink_to(real_repo / "agents")

    now = datetime.now(UTC)
    proj = Project(
        id=_PROJ_ID,
        title="A Preprint To Finalize",
        field="computer science",
        current_stage=Stage.PAPER_INGESTED,
        created_at=now,
        updated_at=now,
    )
    from llmxive.state import project as project_store

    project_store.save(proj, repo_root=repo)
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(repo))
    return repo, proj


def test_finalize_marks_reviews_and_spawns_followup(
    tmp_repo: tuple[Path, Project], monkeypatch: pytest.MonkeyPatch
) -> None:
    from llmxive.backends.base import ChatResponse

    repo, proj = tmp_repo
    monkeypatch.setattr(
        "llmxive.agents.base.chat_with_fallback",
        lambda *a, **k: ChatResponse(
            text=_REVIEW_RESPONSE, model="openai.gpt-oss-120b", backend="dartmouth"
        ),
    )
    pdir = repo / "projects" / _PROJ_ID
    orig_meta = (pdir / "paper" / "metadata.json").read_bytes()

    result = finalize_reviewed_preprint(
        proj,
        repo_root=repo,
        review_agent_names=["paper_reviewer_claim_accuracy"],
        _extension_fn=lambda _text: "We propose extending gizmo analysis to gadgets.",
    )

    # (1) Marked terminal; original metadata byte-identical (never modified).
    assert result.current_stage == Stage.REVIEWED_PREPRINT
    assert (pdir / "paper" / "metadata.json").read_bytes() == orig_meta

    # (2) Peer review ran → record + consolidated action items.
    from llmxive.paper_reprocess.preprint import load_preprint_manifest

    assert list((pdir / "paper" / "reviews").glob("paper_reviewer_claim_accuracy*.md"))
    ai = (pdir / "paper" / "action_items.md").read_text(encoding="utf-8")
    assert "sample size" in ai

    # (3) A SEPARATE follow-up brainstorm project was spawned + linked.
    manifest = load_preprint_manifest(pdir)
    assert manifest is not None
    followup_id = manifest["followup_project_id"]
    assert followup_id and followup_id != _PROJ_ID
    from llmxive.state import project as project_store

    followup = project_store.load(followup_id, repo_root=repo)
    assert followup.current_stage == Stage.BRAINSTORMED
    idea = next((repo / "projects" / followup_id / "idea").glob("*.md")).read_text()
    assert "gizmo analysis to gadgets" in idea
    assert "Carol Author" in idea  # cited, not re-authored
    assert "paper_authors:" not in idea
