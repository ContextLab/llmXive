"""One substantive personality fixture repo, shared by every lane suite.

Three suites each carried their own `_make_repo` writing a spec of
`"# Spec\\n\\nA placeholder."` — 20-odd bytes. The redesigned lane refuses to
critique that (`select_target` skips anything under
`MIN_SUBSTANTIVE_BYTES`), which is the whole point: the 2026-10-09 audit found
the old lane commenting on 140-character catalog previews. A fixture that is
not substantive therefore tests nothing about a turn, so there is one builder
and it writes a real artifact.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "personality"
PROJECT_ID = "PROJ-001-mechanistic-interpretability-of-ctcf-bin"
FEATURE_DIR = "specs/001-mechanistic-interpretability-of-ctcf-bin"

#: A spec with enough in it to have something to say about.
SUBSTANTIVE_SPEC = (
    "# Spec — CTCF interpretability\n\n## Requirements\n\n"
    + "\n".join(
        f"- **FR-{i:03d}**: The system MUST report an effect direction for each "
        f"claimed motif class at threshold {i}."
        for i in range(1, 12)
    )
    + "\n\n## Success criteria\n\n"
    + "\n".join(
        f"- **SC-{i:03d}**: At least one perturbation per motif class, with a "
        f"pre-registered direction, measured on held-out loci."
        for i in range(1, 8)
    )
    + "\n"
)


def make_repo(tmp_path: Path, *, stage: str = "in_progress",
              spec_body: str | None = None, with_reviews: bool = False) -> Path:
    """A repo skeleton with the personality pool and one substantive project.

    ``spec_body=""`` (or anything thin) deliberately produces a repo with
    NOTHING substantive, for the tests that assert a turn abstains without a
    model call.
    """
    repo = tmp_path / "repo"
    repo.mkdir(exist_ok=True)
    pool = repo / "agents" / "prompts" / "personalities"
    pool.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES / "kahneman.md", pool / "kahneman.md")
    (repo / "agents" / "prompts" / "personality.md").write_text(
        "# Personality umbrella\nReturn JSON.", encoding="utf-8")

    feature = repo / "projects" / PROJECT_ID / FEATURE_DIR
    feature.mkdir(parents=True, exist_ok=True)
    (feature / "spec.md").write_text(
        SUBSTANTIVE_SPEC if spec_body is None else spec_body, encoding="utf-8")
    (feature / "tasks.md").write_text("# Tasks\n\n- [ ] T1\n", encoding="utf-8")
    if with_reviews:
        reviews = repo / "projects" / PROJECT_ID / "reviews" / "research"
        reviews.mkdir(parents=True, exist_ok=True)
        (reviews / "llmxive_reviewer_stats__2026-10-01__specified.md").write_text(
            "---\nreviewer: llmxive_reviewer_stats\n---\n\nThe thresholds are unmotivated.",
            encoding="utf-8")

    state_dir = repo / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / f"{PROJECT_ID}.yaml").write_text(
        yaml.safe_dump({
            "artifact_hashes": {},
            "assigned_agent": None,
            "created_at": "2026-05-01T00:00:00+00:00",
            "current_stage": stage,
            "failed_stage": None,
            "field": "biology",
            "human_escalation_reason": None,
            "id": PROJECT_ID,
            "last_run_id": None,
            "last_run_status": None,
            "points_paper": {},
            "points_research": {},
            "revision_round": 0,
            "speckit_paper_dir": None,
            "speckit_research_dir": FEATURE_DIR,
            "title": "CTCF Interpretability",
            "updated_at": "2026-05-13T00:00:00+00:00",
        }),
        encoding="utf-8",
    )
    return repo


__all__ = ["FEATURE_DIR", "PROJECT_ID", "SUBSTANTIVE_SPEC", "make_repo"]
