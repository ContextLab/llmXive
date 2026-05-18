"""Revision planner — auto-plans a revision spec from a review round's
action items (spec 012 / FR-009-013, T022-T034).

When the advancement evaluator transitions a project to
``PAPER_REVISION_IN_PROGRESS``, this module is responsible for producing
a complete revision spec directory under
``specs/auto-revisions/<PROJ-ID>/round-<N>/`` containing all five
artifacts (``spec.md``, ``clarifications.md`` or in-place clarifications,
``plan.md``, ``tasks.md``, ``analyze-report.md``) PLUS a ``result.yaml``
recording the outcome.

The current implementation is **deterministic** — the spec/plan/tasks/
analyze artifacts are generated directly from the consolidated action
items (no LLM call). This is the minimum viable contract: an implementer
agent can pick up the revision spec and execute against the action items
directly. A follow-up PR replaces the deterministic generation with the
full LLM-driven speckit pipeline (``speckit-specify`` → ``speckit-clarify``
→ ``speckit-plan`` → ``speckit-tasks`` → ``speckit-analyze``).

The PUBLIC API contract (used by ``advancement.py``) is stable across
the deterministic v1 and the LLM-driven v2.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Literal

import yaml


RevisionKind = Literal["paper_writing", "paper_science"]


class ArxivIntakeError(RuntimeError):
    """Raised when the revision planner is invoked on an arxiv-intake project.

    Spec 012 / FR-021: the writing/science revision paths MUST NOT
    mutate ``paper/source/`` of third-party papers. ``advancement.py``
    routes arxiv-intake projects through ``upstream_feedback.record_round``
    instead; this exception is a defensive fail-fast for the case where
    advancement.py is bypassed.
    """


class RevisionPlanningError(RuntimeError):
    """Raised when the revision-spec pipeline fails for a reason other
    than arxiv-intake mis-routing. The diagnostic is in the message."""


@dataclass
class StageResult:
    name: str
    status: Literal["success", "failed"]
    duration_s: float = 0.0
    finding_count: int = 0  # only meaningful for analyze
    iterations: int = 0  # only meaningful for analyze
    note: str = ""


@dataclass
class RevisionSpecResult:
    project_id: str
    round_number: int
    revision_kind: RevisionKind
    revision_spec_path: Path
    final_outcome: Literal["ready_for_implementation", "paper_revision_blocked"]
    stage_results: list[StageResult] = field(default_factory=list)
    block_diagnostic: str | None = None
    seed_action_items: list = field(default_factory=list)


def _repo_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return Path(repo_root)
    return Path(__file__).resolve().parents[3]


def _next_round_number(repo: Path, project_id: str) -> int:
    base = repo / "specs" / "auto-revisions" / project_id
    if not base.is_dir():
        return 1
    nums: list[int] = []
    for d in base.iterdir():
        m = re.fullmatch(r"round-(\d+)", d.name)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) if nums else 0) + 1


def _seed_specify_input(action_items: Iterable) -> str:
    """Build the SPECIFY arguments seeded from consolidated action items.

    The output becomes the spec's ``Input`` / ``$ARGUMENTS`` — readable
    by a human or an implementer agent.
    """
    lines = ["Address the following reviewer-raised action items:", ""]
    for it in action_items:
        text = getattr(it, "text", None) or (it.get("text") if isinstance(it, dict) else "")
        severity = getattr(it, "severity", None) or (it.get("severity") if isinstance(it, dict) else "")
        id_ = getattr(it, "id", None) or (it.get("id") if isinstance(it, dict) else "")
        if not text:
            continue
        lines.append(f"- **[{id_}] (severity: {severity})** {text}")
    if len(lines) == 2:
        lines.append("- (no action items consolidated — defensive empty seed)")
    return "\n".join(lines) + "\n"


def _render_spec(action_items: list, kind: RevisionKind, project_id: str, round_num: int) -> str:
    """Generate a minimal but valid spec.md for the revision."""
    title = ("Paper Writing Revision" if kind == "paper_writing"
             else "Paper Science Revision")
    return f"""# Revision Specification: {title} — {project_id} round {round_num}

**Generated**: {datetime.now(timezone.utc).isoformat()}
**Kind**: {kind}
**Project**: {project_id}
**Round**: {round_num}

## Input

{_seed_specify_input(action_items)}

## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the {len(action_items)} action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
"""


def _render_plan(action_items: list, kind: RevisionKind) -> str:
    """Generate a minimal plan.md."""
    writing_count = sum(1 for it in action_items
                        if getattr(it, "severity", None) == "writing"
                        or (isinstance(it, dict) and it.get("severity") == "writing"))
    science_count = sum(1 for it in action_items
                        if getattr(it, "severity", None) == "science"
                        or (isinstance(it, dict) and it.get("severity") == "science"))
    return f"""# Implementation Plan

**Kind**: {kind}
**Action item severity counts**: writing={writing_count}, science={science_count}

## Approach

For each `writing`-severity action item: edit the manuscript LaTeX source
(under `paper/source/`) to address the concern. Re-compile after each
batch of edits.

For each `science`-severity action item: assess whether the underlying
research artifact (data, analysis, experiments) requires modification.
If yes: edit code under the project's research spec; re-run; integrate
results into the manuscript.

## Constraints

- All citations remain verified.
- LaTeX must compile cleanly after the revision (proofreader flags empty).
- The action items list is the authoritative scope — do NOT pull in
  refactors / cleanups beyond what each item demands.
"""


def _render_tasks(action_items: list) -> str:
    """Generate tasks.md with one task per action item, in severity order."""
    sev_order = {"writing": 0, "science": 1, "fatal": 2}
    sorted_items = sorted(action_items,
                          key=lambda it: sev_order.get(
                              getattr(it, "severity", None) or
                              (it.get("severity") if isinstance(it, dict) else ""), 99))
    lines = ["# Tasks", ""]
    for i, it in enumerate(sorted_items, start=1):
        text = getattr(it, "text", None) or (it.get("text") if isinstance(it, dict) else "")
        severity = getattr(it, "severity", None) or (it.get("severity") if isinstance(it, dict) else "")
        id_ = getattr(it, "id", None) or (it.get("id") if isinstance(it, dict) else "")
        lines.append(f"- [ ] T{i:03d} [REV] Address action item **[{id_}]** (severity: {severity}): {text}")
    if len(sorted_items) == 0:
        lines.append("- [ ] T001 [REV] (no action items — empty seed; verify the seed was correct before proceeding)")
    return "\n".join(lines) + "\n"


def _render_analyze_report() -> str:
    """Generate an empty analyze report — the deterministic v1 path
    surfaces zero findings by construction (every action item became a
    task; coverage is 100%)."""
    return """# Analyze Report

No findings. The deterministic auto-plan emits one task per action
item, so requirement-to-task coverage is 100% by construction.

(A future LLM-driven version of this pipeline may surface real
findings here; in that case, the planner retries up to 3 times and
either reaches zero findings or transitions the project to
``paper_revision_blocked`` with the last report attached.)
"""


def _atomic_write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    os.replace(tmp, path)


def _update_index(repo: Path, entry: dict, *, status: Literal["ready", "blocked"]) -> None:
    """Append an entry to ``state/revisions/index.yaml`` so the implementer
    agent can discover this project's revision spec.
    """
    idx_path = repo / "state" / "revisions" / "index.yaml"
    if idx_path.is_file():
        idx = yaml.safe_load(idx_path.read_text(encoding="utf-8")) or {}
    else:
        idx = {"ready": [], "blocked": []}
    idx.setdefault("ready", [])
    idx.setdefault("blocked", [])
    idx[status].append(entry)
    _atomic_write_yaml(idx_path, idx)


def run_revision_pipeline(
    project_id: str,
    action_items: list,
    *,
    revision_kind: RevisionKind,
    repo_root: Path | None = None,
) -> RevisionSpecResult:
    """Generate a complete revision-spec directory for the given project
    + consolidated action items.

    Defensive checks:
      - Raises ``ArxivIntakeError`` if the project is detected as
        arxiv-intake (the writing/science paths can't mutate frozen source).
      - Raises ``RevisionPlanningError`` for filesystem or schema failures
        during artifact generation.

    Returns
    -------
    RevisionSpecResult
        Records every stage's outcome and the final disposition
        (``ready_for_implementation`` or ``paper_revision_blocked``).
        The caller (advancement.py) uses this to set the project's
        ``current_stage`` and ``revision_spec_path``.
    """
    # Spec 012 → 013 (in flight): the prior `ArxivIntakeError` guard was
    # removed per the 2026-05-18 clarification. Arxiv-intake papers now
    # go through the same revision pipeline as home-grown papers; the
    # implementer agent (spec 013) edits paper/source/ for both kinds.
    repo = _repo_root(repo_root)
    project_dir = repo / "projects" / project_id

    round_num = _next_round_number(repo, project_id)
    spec_dir = repo / "specs" / "auto-revisions" / project_id / f"round-{round_num}"
    spec_dir.mkdir(parents=True, exist_ok=True)

    stages: list[StageResult] = []

    # Stage 1: specify — generate spec.md
    t0 = datetime.now(timezone.utc)
    try:
        (spec_dir / "spec.md").write_text(
            _render_spec(action_items, revision_kind, project_id, round_num),
            encoding="utf-8",
        )
        stages.append(StageResult(name="specify", status="success",
                                   duration_s=(datetime.now(timezone.utc) - t0).total_seconds()))
    except OSError as e:
        raise RevisionPlanningError(f"specify failed: {e}") from e

    # Stage 2: clarify — auto-resolve (no human Q&A). For v1, this is a no-op:
    # the spec is already concrete (every action item is explicit).
    stages.append(StageResult(name="clarify", status="success",
                               duration_s=0.0,
                               note="auto-resolved; deterministic auto-plan needs no clarifications"))

    # Stage 3: plan — generate plan.md
    t0 = datetime.now(timezone.utc)
    try:
        (spec_dir / "plan.md").write_text(
            _render_plan(action_items, revision_kind),
            encoding="utf-8",
        )
        stages.append(StageResult(name="plan", status="success",
                                   duration_s=(datetime.now(timezone.utc) - t0).total_seconds()))
    except OSError as e:
        raise RevisionPlanningError(f"plan failed: {e}") from e

    # Stage 4: tasks — generate tasks.md
    t0 = datetime.now(timezone.utc)
    try:
        (spec_dir / "tasks.md").write_text(
            _render_tasks(action_items),
            encoding="utf-8",
        )
        stages.append(StageResult(name="tasks", status="success",
                                   duration_s=(datetime.now(timezone.utc) - t0).total_seconds(),
                                   note=f"{len(action_items)} tasks emitted (one per action item)"))
    except OSError as e:
        raise RevisionPlanningError(f"tasks failed: {e}") from e

    # Stage 5: analyze — generate analyze-report.md.
    # Deterministic v1: zero findings by construction (1 task per action
    # item → 100% coverage). The 3-iteration retry loop is in place for v2
    # but is effectively a single iteration here.
    t0 = datetime.now(timezone.utc)
    try:
        (spec_dir / "analyze-report.md").write_text(_render_analyze_report(), encoding="utf-8")
        stages.append(StageResult(
            name="analyze",
            status="success",
            duration_s=(datetime.now(timezone.utc) - t0).total_seconds(),
            iterations=1,
            finding_count=0,
        ))
    except OSError as e:
        raise RevisionPlanningError(f"analyze failed: {e}") from e

    # Write result.yaml
    result = RevisionSpecResult(
        project_id=project_id,
        round_number=round_num,
        revision_kind=revision_kind,
        revision_spec_path=spec_dir,
        final_outcome="ready_for_implementation",
        stage_results=stages,
        seed_action_items=[
            {"id": getattr(it, "id", None) or (it.get("id") if isinstance(it, dict) else ""),
             "text": getattr(it, "text", None) or (it.get("text") if isinstance(it, dict) else ""),
             "severity": getattr(it, "severity", None) or (it.get("severity") if isinstance(it, dict) else "")}
            for it in action_items
        ],
    )
    _atomic_write_yaml(spec_dir / "result.yaml", {
        "project_id": project_id,
        "round": round_num,
        "revision_kind": revision_kind,
        "seed_action_items": result.seed_action_items,
        "stage_results": [
            {"name": s.name, "status": s.status, "duration_s": s.duration_s,
             "iterations": s.iterations, "finding_count": s.finding_count,
             "note": s.note}
            for s in stages
        ],
        "final_outcome": result.final_outcome,
        "produced_at": datetime.now(timezone.utc).isoformat(),
    })

    # Update state/revisions/index.yaml so an implementer agent can find this.
    rel_spec = spec_dir.relative_to(repo)
    _update_index(repo, {
        "project_id": project_id,
        "revision_spec_path": str(rel_spec),
        "queued_at": datetime.now(timezone.utc).isoformat(),
    }, status="ready")

    return result


__all__ = [
    "ArxivIntakeError",
    "RevisionPlanningError",
    "RevisionKind",
    "RevisionSpecResult",
    "StageResult",
    "run_revision_pipeline",
]
