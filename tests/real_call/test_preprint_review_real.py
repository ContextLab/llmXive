"""Real-call verification of the Reviewed-Preprint review-only runner (item 4).

Runs the GENUINE paper-review panel (one lens, to bound cost) against a small
real paper through :func:`run_preprint_review` — no stubs — and asserts it writes
a schema-valid review record + a consolidated ``action_items.md``. Gated by the
``real_call`` directory convention (conftest skips unless ``LLMXIVE_REAL_TESTS=1``);
additionally skipped when no Dartmouth key is resolvable.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.credentials import load_dartmouth_key
from llmxive.paper_reprocess.preprint_review import run_preprint_review
from llmxive.types import Project, Stage

_PROJ_ID = "PROJ-904-preprint-review-realcall"


@pytest.fixture
def tmp_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Project]:
    repo = tmp_path / "repo"
    pdir = repo / "projects" / _PROJ_ID
    (pdir / "paper" / "source").mkdir(parents=True)
    (pdir / "paper" / "metadata.json").write_text(
        json.dumps(
            {
                "arxiv_id": "1706.03762",
                "arxiv_url": "https://arxiv.org/abs/1706.03762",
                "title": "Attention Is All You Need (excerpt)",
                "authors": ["Ashish Vaswani", "Noam Shazeer"],
                "abstract": (
                    "We propose the Transformer, a model architecture relying "
                    "entirely on attention mechanisms, dispensing with recurrence "
                    "and convolutions entirely."
                ),
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
        "\\title{Attention Is All You Need (excerpt)}\n"
        "\\begin{abstract}\nWe propose the Transformer, a model architecture "
        "relying entirely on attention mechanisms.\n\\end{abstract}\n"
        "\\section{Model}\nThe Transformer uses stacked self-attention and "
        "point-wise, fully connected layers for both the encoder and decoder.\n",
        encoding="utf-8",
    )
    real_repo = Path(__file__).resolve().parents[2]
    (repo / "agents").symlink_to(real_repo / "agents")
    now = datetime.now(UTC)
    proj = Project(
        id=_PROJ_ID,
        title="Attention Is All You Need (excerpt)",
        field="computer science",
        current_stage=Stage.REVIEWED_PREPRINT,
        created_at=now,
        updated_at=now,
    )
    from llmxive.state import project as project_store

    project_store.save(proj, repo_root=repo)
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(repo))
    return repo, proj


def test_run_preprint_review_real_panel(tmp_repo: tuple[Path, Project]) -> None:
    if not load_dartmouth_key(prompt_if_missing=False):
        pytest.skip("no Dartmouth key resolvable; set one to run the real panel")
    repo, proj = tmp_repo

    result = run_preprint_review(
        proj, repo_root=repo, agent_names=["paper_reviewer_writing_quality"]
    )

    # The genuine model produced a schema-valid record (or the lens legitimately
    # failed — but if it ran, a record must exist and validate).
    assert "paper_reviewer_writing_quality" in result.reviewers_run
    review_dir = repo / "projects" / _PROJ_ID / "paper" / "reviews"
    recs = list(review_dir.glob("paper_reviewer_writing_quality*.md"))
    assert recs, "the writing-quality lens must have written a review record"

    from llmxive.state import reviews as reviews_store

    loaded = reviews_store.read(recs[0])
    assert loaded.verdict in {
        "accept", "minor_revision", "full_revision", "reject",
        "major_revision_writing", "major_revision_science", "fundamental_flaws",
    }
    assert (repo / "projects" / _PROJ_ID / "paper" / "action_items.md").exists()
