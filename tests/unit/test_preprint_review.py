"""Reviewed-Preprints review-only runner (2026-07-01, increment 4).

`run_preprint_review` runs the SAME paper-review panel the pipeline uses for an
llmXive-authored paper, but ONCE (no convergence, no revise, no accept/reject),
over an ingested preprint. Each lens writes a normal review record under
`paper/reviews/`; the concerns are consolidated into `paper/action_items.md`.

Offline the network boundary (`agents.base.chat_with_fallback`) is stubbed with a
canned review-record response — the REAL PaperReviewerAgent parsing + record
writing + schema validation still run (only the model call is faked). A real-call
sibling in `tests/real_call/` exercises the genuine panel.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.paper_reprocess.preprint_review import (
    consolidate_action_items,
    paper_reviewer_agent_names,
    run_preprint_review,
)
from llmxive.types import Project, Stage

_PROJ_ID = "PROJ-902-preprint-review-test"

# A canned, schema-valid paper-review response (non-accept + one action item).
_REVIEW_RESPONSE = (
    "---\n"
    "verdict: minor_revision\n"
    "score: 0.0\n"
    "action_items:\n"
    "  - text: Clarify the exact evaluation metric used in Section 4.\n"
    "    severity: writing\n"
    "feedback: Well-motivated; a few clarifications needed.\n"
    "---\n\n"
    "The paper is well-motivated. Section 4 should name the exact metric used "
    "so the results can be interpreted.\n"
)


@pytest.fixture
def tmp_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Project]:
    """Hermetic repo: a preprint project + symlinked real agents/ registry.

    Contracts resolve from the real repo (contract_validate freezes CONTRACTS_DIR
    at import), so only agents/ needs to be present under $LLMXIVE_REPO_ROOT.
    """
    repo = tmp_path / "repo"
    pdir = repo / "projects" / _PROJ_ID
    (pdir / "paper" / "source").mkdir(parents=True)
    (pdir / "paper" / "metadata.json").write_text(
        json.dumps(
            {
                "arxiv_id": "2605.99999",
                "arxiv_url": "https://arxiv.org/abs/2605.99999",
                "title": "A Preprint To Review",
                "authors": ["Alice Original", "Bob Author"],
                "abstract": "We study widgets.",
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
        "\\title{A Preprint To Review}\n"
        "\\begin{abstract}\nWe study widgets.\n\\end{abstract}\n"
        "\\section{Method}\nWe do things carefully.\n",
        encoding="utf-8",
    )
    real_repo = Path(__file__).resolve().parents[2]
    (repo / "agents").symlink_to(real_repo / "agents")

    now = datetime.now(UTC)
    proj = Project(
        id=_PROJ_ID,
        title="A Preprint To Review",
        field="computer science",
        current_stage=Stage.REVIEWED_PREPRINT,
        created_at=now,
        updated_at=now,
    )
    from llmxive.state import project as project_store

    project_store.save(proj, repo_root=repo)
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(repo))
    return repo, proj


def _stub_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    from llmxive.backends.base import ChatResponse

    monkeypatch.setattr(
        "llmxive.agents.base.chat_with_fallback",
        lambda *a, **k: ChatResponse(
            text=_REVIEW_RESPONSE, model="openai.gpt-oss-120b", backend="dartmouth"
        ),
    )


def test_panel_names_are_the_paper_reviewers(tmp_repo: tuple[Path, Project]) -> None:
    repo, _ = tmp_repo
    names = paper_reviewer_agent_names(repo)
    # The science specialist lenses, all real registry entries.
    assert "paper_reviewer_claim_accuracy" in names
    assert "paper_reviewer_overreach" in names
    assert "paper_reviewer_scientific_evidence" in names
    # No research-side or non-reviewer entries leak in.
    assert all(n.startswith("paper_reviewer_") for n in names)
    assert len(names) >= 6
    # EXCLUDED for preprints: reproducibility-packaging / house-formatting lenses
    # (mis-fire on third-party papers), the blind text figure_critic (replaced by
    # the vision reviewer), and the flaky generic holistic paper_reviewer.
    assert "paper_reviewer" not in names
    assert "paper_reviewer_code_quality_paper" not in names
    assert "paper_reviewer_data_quality_paper" not in names
    assert "paper_reviewer_text_formatting" not in names
    assert "paper_reviewer_figure_critic" not in names


def test_run_preprint_review_writes_records_and_action_items(
    tmp_repo: tuple[Path, Project], monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, proj = tmp_repo
    _stub_chat(monkeypatch)
    lenses = ["paper_reviewer_claim_accuracy", "paper_reviewer_overreach"]

    result = run_preprint_review(proj, repo_root=repo, agent_names=lenses)

    # Every lens ran and produced a record; none failed.
    assert set(result.reviewers_run) == set(lenses)
    assert result.reviewers_failed == []
    review_dir = repo / "projects" / _PROJ_ID / "paper" / "reviews"
    written = sorted(p.name for p in review_dir.glob("*.md"))
    assert any("paper_reviewer_claim_accuracy" in n for n in written)
    assert any("paper_reviewer_overreach" in n for n in written)

    # Consolidated action items exist and captured the per-lens concern.
    ai = repo / "projects" / _PROJ_ID / "paper" / "action_items.md"
    assert ai.exists()
    text = ai.read_text(encoding="utf-8")
    assert "A Preprint To Review" in text
    assert "Clarify the exact evaluation metric" in text
    assert result.num_action_items == len(lenses)  # one item per lens
    assert result.action_items_path == ai


def test_review_never_modifies_the_original_paper(
    tmp_repo: tuple[Path, Project], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The panel is READ-ONLY over the paper — original bytes are untouched."""
    repo, proj = tmp_repo
    _stub_chat(monkeypatch)
    pdir = repo / "projects" / _PROJ_ID
    orig_tex = (pdir / "paper" / "source" / "main.tex").read_bytes()
    orig_meta = (pdir / "paper" / "metadata.json").read_bytes()

    run_preprint_review(proj, repo_root=repo, agent_names=["paper_reviewer_overreach"])

    assert (pdir / "paper" / "source" / "main.tex").read_bytes() == orig_tex
    assert (pdir / "paper" / "metadata.json").read_bytes() == orig_meta
