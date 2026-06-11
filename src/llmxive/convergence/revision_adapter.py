"""Engine ↔ auto-revisions directory adapter (spec 015 T042 / FR-034).

The convergence engine emits a native :class:`KickbackRecord` on
non-convergence. The implementer agent (``agents/implementer.py``) reads
the spec-012 directory contract under ``specs/auto-revisions/<PROJ-ID>/round-<N>/``
(``spec.md``, ``plan.md``, ``tasks.md``, ``analyze-report.md``,
``result.yaml``) plus an entry in ``state/revisions/index.yaml``.

This adapter is the SOLE bridge between the two: it takes a
``KickbackRecord`` + a ``project_id`` + a ``round_num`` and writes
exactly the directory shape the implementer expects, so the implementer
read path is UNCHANGED.

The deterministic render helpers (``_render_spec`` / ``_render_plan`` /
``_render_tasks`` / ``_render_analyze_report``) preserve the byte-for-byte
output of the deprecated ``revision_planner`` module — they were lifted
here verbatim and rewired to accept ``Concern`` objects (or any
``severity``-bearing duck) rather than legacy ``ActionItem``-shaped
dicts. The same template lands in the same file because the implementer's
tasks.md / spec.md parsers depend on those exact patterns.

This module REPLACES ``llmxive.agents.revision_planner`` — once every
caller has been migrated, that module is deleted.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

import yaml

from .types import Concern, KickbackRecord, Severity

# --- next-round-number discovery ----------------------------------------

def next_round_number(repo: Path, project_id: str) -> int:
    """Return the next available round number for the project.

    Mirrors the discovery rule from ``revision_planner._next_round_number``
    so existing rounds laid down by the deprecated module are recognised
    and not overwritten. Public: ``advancement.evaluate`` consults it to
    enforce the bounded revision-round cap (spec 023)."""
    base = repo / "specs" / "auto-revisions" / project_id
    if not base.is_dir():
        return 1
    nums: list[int] = []
    for d in base.iterdir():
        m = re.fullmatch(r"round-(\d+)", d.name)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) if nums else 0) + 1


# --- severity normalisation --------------------------------------------

# The implementer's tasks.md parser reads severities in the legacy
# ``writing | science | fatal`` taxonomy (``_read_action_items`` defaults
# any missing severity to ``writing``). To preserve that contract while
# still carrying the engine's richer ``Severity`` enum into the audit
# trail, the spec / tasks markdown files use the legacy values and the
# YAML ``result.yaml`` carries the engine-native severity verbatim.

_ENGINE_TO_LEGACY_SEVERITY: dict[Severity, str] = {
    Severity.TRIVIAL: "writing",
    Severity.CODE: "writing",
    Severity.WRITING: "writing",
    Severity.REQUIREMENT: "writing",
    Severity.METHODOLOGY: "science",
    Severity.SCIENCE: "science",
    Severity.FATAL: "fatal",
}


def _legacy_severity(s: Severity) -> str:
    """Map an engine severity onto the legacy
    ``writing | science | fatal`` taxonomy the implementer agent parses."""
    return _ENGINE_TO_LEGACY_SEVERITY.get(s, "writing")


# --- deterministic render helpers (lifted from revision_planner) -------

def _seed_specify_input(concerns: Iterable[Concern]) -> str:
    """Build the SPECIFY arguments seeded from consolidated concerns.

    The output becomes the spec's ``Input`` / ``$ARGUMENTS`` — readable
    by a human or an implementer agent. Byte-compatible with the
    deprecated revision_planner module's output for an equivalent input
    list."""
    lines = ["Address the following reviewer-raised action items:", ""]
    seen = 0
    for c in concerns:
        sev = _legacy_severity(c.severity)
        if not c.text:
            continue
        lines.append(f"- **[{c.id}] (severity: {sev})** {c.text}")
        seen += 1
    if seen == 0:
        lines.append("- (no action items consolidated — defensive empty seed)")
    return "\n".join(lines) + "\n"


def _render_spec(
    concerns: list[Concern], kind: str, project_id: str, round_num: int,
) -> str:
    """Generate a minimal but valid spec.md for the revision."""
    title = (
        "Paper Writing Revision" if kind == "paper_writing"
        else ("Paper Science Revision" if kind == "paper_science"
              else "Auto Revision")
    )
    return f"""# Revision Specification: {title} — {project_id} round {round_num}

**Generated**: {datetime.now(UTC).isoformat()}
**Kind**: {kind}
**Project**: {project_id}
**Round**: {round_num}

## Input

{_seed_specify_input(concerns)}

## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the {len(concerns)} action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
"""


def _render_plan(concerns: list[Concern], kind: str) -> str:
    """Generate a minimal plan.md. Severity counts use the legacy taxonomy
    so the format is identical to the deprecated revision_planner output."""
    writing_count = sum(
        1 for c in concerns if _legacy_severity(c.severity) == "writing"
    )
    science_count = sum(
        1 for c in concerns if _legacy_severity(c.severity) == "science"
    )
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


def _render_tasks(concerns: list[Concern]) -> str:
    """Generate tasks.md with one task per concern, in severity order.

    The output is byte-compatible with the deprecated revision_planner
    module so the implementer's tasks.md parser (``_TASK_RE`` +
    ``alt_pat``) keeps working unchanged."""
    sev_order = {"writing": 0, "science": 1, "fatal": 2}
    sorted_items = sorted(
        concerns,
        key=lambda c: sev_order.get(_legacy_severity(c.severity), 99),
    )
    lines = ["# Tasks", ""]
    for i, c in enumerate(sorted_items, start=1):
        sev = _legacy_severity(c.severity)
        lines.append(
            f"- [ ] T{i:03d} [REV] Address action item **[{c.id}]** "
            f"(severity: {sev}): {c.text}"
        )
    if len(sorted_items) == 0:
        lines.append(
            "- [ ] T001 [REV] (no action items — empty seed; "
            "verify the seed was correct before proceeding)"
        )
    return "\n".join(lines) + "\n"


def _render_analyze_report() -> str:
    """Generate an empty analyze report — the deterministic adapter
    surfaces zero findings by construction (every concern becomes a
    task; coverage is 100%)."""
    return """# Analyze Report

No findings. The deterministic auto-plan emits one task per action
item, so requirement-to-task coverage is 100% by construction.

(A future LLM-driven version of this pipeline may surface real
findings here; in that case, the planner retries up to 3 times and
either reaches zero findings or transitions the project to
``agent_blocked`` with the last report attached.)
"""


def _atomic_write_yaml(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    os.replace(tmp, path)


def _update_index(repo: Path, entry: dict[str, object]) -> None:
    """Append an entry to ``state/revisions/index.yaml`` so the
    implementer agent can discover this project's revision spec.

    Spec 015 T042: only the ``ready`` bucket is written — the engine no
    longer produces a ``blocked`` bucket entry from this path (the
    diagnostic-mode failsafe goes through ``Stage.AGENT_BLOCKED`` +
    ``human_input_needed.yaml`` instead)."""
    idx_path = repo / "state" / "revisions" / "index.yaml"
    if idx_path.is_file():
        idx = yaml.safe_load(idx_path.read_text(encoding="utf-8")) or {}
    else:
        idx = {"ready": [], "blocked": []}
    idx.setdefault("ready", [])
    idx.setdefault("blocked", [])
    idx["ready"].append(entry)
    _atomic_write_yaml(idx_path, idx)


# --- public adapter API ------------------------------------------------


def kickback_to_revision_spec(
    kickback: KickbackRecord,
    *,
    project_id: str,
    repo_root: Path,
    round_num: int | None = None,
    revision_kind: str | None = None,
) -> Path:
    """Write a complete auto-revisions directory from a ``KickbackRecord``.

    The directory contract is:
      ``specs/auto-revisions/<project_id>/round-<N>/spec.md``
      ``                                          /plan.md``
      ``                                          /tasks.md``
      ``                                          /analyze-report.md``
      ``                                          /result.yaml``
    PLUS an entry appended to ``state/revisions/index.yaml`` under the
    ``ready`` bucket so the implementer's polling loop picks it up.

    Parameters
    ----------
    kickback : KickbackRecord
        The engine's emitted record. ``unresolved_concerns`` drive the
        synthetic spec/tasks content (1 task per concern; 100% coverage
        by construction).
    project_id : str
        The target project's PROJ-ID. Validated upstream by the engine.
    repo_root : Path
        Repository root; all on-disk writes are rooted here.
    round_num : int | None
        If supplied, used as-is. If None, the next available round
        number is computed by scanning the project's existing
        ``round-*/`` dirs (defensive against partial state from prior
        runs).
    revision_kind : str | None
        One of ``paper_writing`` / ``paper_science`` / ``auto`` — the
        worst severity determines this when None: SCIENCE/METHODOLOGY/
        FATAL → ``paper_science``; everything else → ``paper_writing``.

    Returns
    -------
    Path
        The absolute path to the produced round directory. The caller
        (advancement.py / implementer.py failsafe) records its repo-
        relative form on ``project.revision_spec_path``.
    """
    repo = Path(repo_root)
    if round_num is None:
        round_num = next_round_number(repo, project_id)
    if revision_kind is None:
        revision_kind = (
            "paper_science"
            if kickback.worst_severity in {
                Severity.METHODOLOGY, Severity.SCIENCE, Severity.FATAL,
            }
            else "paper_writing"
        )

    spec_dir = (
        repo / "specs" / "auto-revisions" / project_id / f"round-{round_num}"
    )
    spec_dir.mkdir(parents=True, exist_ok=True)

    concerns = list(kickback.unresolved_concerns)

    (spec_dir / "spec.md").write_text(
        _render_spec(concerns, revision_kind, project_id, round_num),
        encoding="utf-8",
    )
    (spec_dir / "plan.md").write_text(
        _render_plan(concerns, revision_kind),
        encoding="utf-8",
    )
    (spec_dir / "tasks.md").write_text(
        _render_tasks(concerns),
        encoding="utf-8",
    )
    (spec_dir / "analyze-report.md").write_text(
        _render_analyze_report(),
        encoding="utf-8",
    )

    _atomic_write_yaml(spec_dir / "result.yaml", {
        "project_id": project_id,
        "round": round_num,
        "revision_kind": revision_kind,
        "from_stage": kickback.from_stage,
        "to_stage": kickback.to_stage,
        "worst_severity": kickback.worst_severity.value,
        "seed_action_items": [
            {
                "id": c.id,
                "text": c.text,
                "severity": _legacy_severity(c.severity),
                # The engine-native severity is retained so consumers that
                # want the full Severity ladder can pick it up.
                "engine_severity": c.severity.value,
                "reviewer": c.reviewer,
                "artifact": c.artifact,
                "location": c.location,
            }
            for c in concerns
        ],
        "kickback_reason": kickback.reason,
        "kickback_artifact_links": list(kickback.artifact_links),
        "stage_results": [
            {"name": "specify", "status": "success"},
            {"name": "clarify", "status": "success",
             "note": "auto-resolved; deterministic adapter needs no clarifications"},
            {"name": "plan", "status": "success"},
            {"name": "tasks", "status": "success",
             "note": f"{len(concerns)} tasks emitted (one per concern)"},
            {"name": "analyze", "status": "success",
             "iterations": 1, "finding_count": 0},
        ],
        "final_outcome": "ready_for_implementation",
        "produced_at": datetime.now(UTC).isoformat(),
    })

    rel_spec = spec_dir.relative_to(repo)
    _update_index(repo, {
        "project_id": project_id,
        "revision_spec_path": str(rel_spec),
        "queued_at": datetime.now(UTC).isoformat(),
    })

    return spec_dir


__all__ = [
    "_legacy_severity",
    "_render_analyze_report",
    "_render_plan",
    "_render_spec",
    "_render_tasks",
    "_seed_specify_input",
    "kickback_to_revision_spec",
    "next_round_number",
]
