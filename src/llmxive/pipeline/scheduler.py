"""Project scheduler — picks the next project to act on per FR-001 priority order.

Priority tiers (T060 / FR-001):
  in_progress > analyzed > clarified > specified > flesh_out_complete >
  brainstormed > paper_in_progress > paper_analyzed > paper_clarified >
  paper_specified > paper_drafting_init > research_complete

Within a tier, oldest updated_at wins.

Projects with active locks are skipped (FR-005). Projects in
human_input_needed or terminal stages are skipped silently.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.pipeline import lock as lockmod
from llmxive.state import project as project_store
from llmxive.types import Project, Stage


# Higher priority first. The Implementer's bias toward in_progress /
# analyzed satisfies FR-006.
PRIORITY: list[Stage] = [
    Stage.IN_PROGRESS,
    Stage.ANALYZED,
    Stage.CLARIFIED,
    Stage.SPECIFIED,
    Stage.FLESH_OUT_COMPLETE,
    Stage.BRAINSTORMED,
    Stage.PAPER_IN_PROGRESS,
    Stage.PAPER_ANALYZED,
    Stage.PAPER_CLARIFIED,
    Stage.PAPER_SPECIFIED,
    Stage.PAPER_DRAFTING_INIT,
    Stage.RESEARCH_COMPLETE,
    # Other intermediate / review states are picked up by their dedicated
    # workflows; the scheduler does not gate on them here.
]


def pick_next(*, repo_root: Path | None = None) -> Project | None:
    projects = project_store.list_all(repo_root=repo_root)
    by_stage: dict[Stage, list[Project]] = {s: [] for s in PRIORITY}
    for p in projects:
        if p.current_stage in {Stage.HUMAN_INPUT_NEEDED, Stage.BLOCKED, Stage.POSTED}:
            continue
        if lockmod.is_locked(p.id, repo_root=repo_root):
            continue
        if p.current_stage in by_stage:
            by_stage[p.current_stage].append(p)
        # Stages outside PRIORITY (e.g., RESEARCH_REVIEW, PAPER_REVIEW) are
        # handled by their reviewer agents on a different cadence.

    for stage in PRIORITY:
        bucket = by_stage[stage]
        if not bucket:
            continue
        bucket.sort(key=lambda p: p.updated_at)
        return bucket[0]
    return None


__all__ = ["pick_next", "PRIORITY"]
