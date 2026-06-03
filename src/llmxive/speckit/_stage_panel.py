"""Shared per-stage convergence-panel invocation for the reviewable DOC stages.

Spec-015 / #239 core deliverable. The reviewable DOC stages (spec / plan /
paper_spec / paper_plan / paper_tasks) each run their agent and historically
advanced with NO panel review — the multi-lens LLM panels built by
``build_*_reviewspec`` were real but never INVOKED for these stages.

This module is the single place the ``*_cmd.py`` ``write_artifacts`` hooks
call AFTER they have produced + written their artifact(s) to disk. It mirrors
the in-cmd engine path that ``paper_implement_cmd.py`` already implements:

1. Resolve a backend (None → offline; skip the panel gracefully — the agent
   already produced the artifact, so a missing backend must not crash the
   stage).
2. Build the LIVE ReviewSpec via the stage's ``build_*_reviewspec`` helper.
3. Source the stage's required sentinel ``__X__`` extra inputs from the REAL
   project artifacts (fail-loud contract enforced by
   :func:`llmxive.convergence.project_runner.run_engine_for_project`).
4. Run the engine through the project-runner bridge (loads artifacts, writes
   back any revised artifact, returns a :class:`ProjectRunResult`).
5. converged → return normally (stage advances as today).
   NOT converged (panel kickback) → write a generic ``convergence_kickback.yaml``
   record (``{to_stage, worst_severity, reason, unresolved_concerns, stage}``) in
   the stage's memory dir and signal non-advancement by raising
   :class:`StagePanelKickback`. The graph's ``_decide_next_stage`` consumes that
   sentinel and performs the ADAPTIVE auto-kickback to ``to_stage`` (F-14/F-20
   Part B) — bounded by a per-project kickback cap that escalates to
   ``human_input_needed`` after repeated kickbacks at the same stage.
   Engine exception (a genuine failure, NOT a panel non-convergence) → escalate
   via ``human_input_needed.yaml`` (real human is required) and re-raise as
   :class:`StagePanelEscalation`.

Per-round inspection trail (F-14a / FR-015): ``run_stage_panel`` supplies the
engine an ``on_round`` hook that appends every round's ``(concerns, responses,
verdicts)`` to a persistent JSONL trail under
``<memory_dir>/convergence_trail/<stage>-<counter>.jsonl`` so a kickback has
full provenance. Trail-write failures never crash the panel (log + continue).

The on-disk artifact write-back is owned by ``run_engine_for_project``; this
module supplies the ``artifact_paths`` map keyed by the SAME repo-relative key
the stage's reviser reads, so the revised content lands at the canonical Spec
Kit path.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import yaml

from llmxive.backends.base import BackendUnavailable, TransientBackendError
from llmxive.convergence.project_runner import run_engine_for_project
from llmxive.convergence.types import (
    Concern,
    ConcernResponse,
    KickbackRecord,
    ReviewSpec,
    Verdict,
)
from llmxive.speckit._comments_context import render_recent_comments_block

logger = logging.getLogger(__name__)

#: Filename of the generic adaptive-kickback sentinel written on panel
#: non-convergence. Consumed by ``graph._decide_next_stage`` (F-14/F-20 B).
CONVERGENCE_KICKBACK_FILENAME = "convergence_kickback.yaml"


class StagePanelKickback(RuntimeError):
    """Raised when the panel did NOT converge (a kickback was produced).

    The stage MUST NOT advance; a ``human_input_needed.yaml`` marker has
    been written in the stage's memory dir before this is raised so the
    graph routes the project back to the kickback target stage.
    """


class StagePanelEscalation(RuntimeError):
    """Raised when the engine path failed entirely (an unexpected exception).

    A ``human_input_needed.yaml`` marker describing the failure has been
    written before this is raised. We do NOT swallow the failure (the next
    tick can retry) — mirrors ``paper_implement_cmd``'s escalation handling.
    """


def _read(path: Path) -> str:
    """Read a file's text, returning ``""`` when it is absent.

    Empty string is the contract-acceptable value for a legitimately-absent
    input: it keeps the sentinel key present so the reviser sees an explicit
    empty rather than emitting a false "X not provided" concern (FR-049).
    """
    try:
        return path.read_text(encoding="utf-8") if path.exists() else ""
    except OSError:
        return ""


def _first_glob(root: Path, pattern: str) -> Path | None:
    matches = sorted(root.glob(pattern))
    return matches[0] if matches else None


def _idea_md(project_dir: Path) -> str:
    idea = _first_glob(project_dir, "idea/*.md")
    return _read(idea) if idea is not None else ""


def _spec_template(project_dir: Path, repo_root: Path) -> str:
    """Resolve the spec template, preferring the per-project copy and falling
    back to the repo-level one (matches ``_real_only_guard``/calibration use)."""
    proj_tpl = project_dir / ".specify" / "templates" / "spec-template.md"
    if proj_tpl.exists():
        return _read(proj_tpl)
    return _read(repo_root / ".specify" / "templates" / "spec-template.md")


def _constitution(memory_dir: Path) -> str:
    return _read(memory_dir / "constitution.md")


def _write_human_input_needed(
    memory_dir: Path, payload: dict[str, object]
) -> Path:
    memory_dir.mkdir(parents=True, exist_ok=True)
    out = memory_dir / "human_input_needed.yaml"
    out.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return out


def _write_convergence_kickback(
    memory_dir: Path, payload: dict[str, object]
) -> Path:
    """Persist the ADAPTIVE-kickback record (F-14/F-20 Part B).

    Distinct from ``human_input_needed.yaml`` (reserved for genuine human
    escalation): this sentinel triggers the graph's auto-kickback to the
    content stage named by ``payload['to_stage']``.
    """
    memory_dir.mkdir(parents=True, exist_ok=True)
    out = memory_dir / CONVERGENCE_KICKBACK_FILENAME
    out.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return out


def emit_convergence_kickback(
    memory_dir: Path, kickback: KickbackRecord, *, stage_label: str
) -> Path:
    """Build + persist the adaptive convergence-kickback sentinel from a
    ``KickbackRecord``.

    Single source of truth for the sentinel payload SHAPE — used by both
    :func:`run_stage_panel` (spec / plan / paper panels) and the research-tasks
    engine-bridge path (``tasks_cmd``). The ``stage`` key is the per-panel label
    that keys the kickback-count file, so each panel's cap is independent.
    """
    return _write_convergence_kickback(
        memory_dir,
        {
            "reason": kickback.reason,
            "to_stage": kickback.to_stage,
            "worst_severity": kickback.worst_severity.value,
            "stage": stage_label,
            "unresolved_concerns": [
                c.model_dump(mode="json") for c in kickback.unresolved_concerns
            ],
            "artifact_links": list(kickback.artifact_links),
        },
    )


def _next_trail_path(memory_dir: Path, stage_label: str) -> Path:
    """Resolve a fresh per-run JSONL trail path under ``convergence_trail/``.

    Uses a monotonically increasing counter per stage so successive panel
    runs (e.g. across kickback cycles) each get their own trail file rather
    than clobbering the prior provenance.
    """
    trail_dir = memory_dir / "convergence_trail"
    trail_dir.mkdir(parents=True, exist_ok=True)
    safe = stage_label.replace("/", "_")
    existing = list(trail_dir.glob(f"{safe}-*.jsonl"))
    idx = len(existing) + 1
    return trail_dir / f"{safe}-{idx:03d}.jsonl"


def _make_round_hook(trail_path: Path):  # type: ignore[no-untyped-def]
    """Build an engine ``on_round`` hook that appends each round's records to
    ``trail_path`` as one JSON line (F-14a / FR-015).

    Robust by contract: a trail-write failure is logged and swallowed so it can
    NEVER crash the panel — provenance is best-effort, advancement is not.
    """

    def _hook(
        round_index: int,
        concerns: list[Concern],
        responses: list[ConcernResponse],
        verdicts: list[Verdict],
    ) -> None:
        try:
            record = {
                "round": round_index,
                "concerns": [c.model_dump(mode="json") for c in concerns],
                "responses": [r.model_dump(mode="json") for r in responses],
                "verdicts": [v.model_dump(mode="json") for v in verdicts],
            }
            with trail_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")
        except Exception as exc:  # provenance is best-effort — never crash.
            logger.warning(
                "convergence trail-write failed for %s: %s", trail_path, exc
            )

    return _hook


def _make_abort_hook(trail_path: Path):  # type: ignore[no-untyped-def]
    """Build an engine ``on_abort`` hook that appends a CLEAN-ABORT record
    ``{"round": idx, "aborted": reason}`` to the SAME ``trail_path`` the round hook
    writes (FR-015 provenance).

    A circuit-breaker / deadline abort otherwise propagates with NO trail (the
    PROJ-552 plan-stage CI aborts committed nothing and looked like "did nothing");
    this makes WHERE + WHY observable in committed state so an unattended run is
    diagnosable. Best-effort by contract: a trail-write failure is logged and
    swallowed — it must NEVER mask the backend abort already propagating.
    """

    def _hook(round_index: int, reason: str) -> None:
        try:
            record = {"round": round_index, "aborted": reason}
            with trail_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")
        except Exception as exc:  # provenance is best-effort — never crash/mask.
            logger.warning(
                "convergence abort-trail write failed for %s: %s", trail_path, exc
            )

    return _hook


def run_stage_panel(
    *,
    stage_label: str,
    spec: ReviewSpec,
    artifact_paths: dict[str, Path],
    extra_inputs: dict[str, str],
    repo_root: Path,
    memory_dir: Path,
    producer: str | None = None,
    constitution: str | None = None,
) -> list[Path]:
    """Run the convergence engine for one reviewable DOC stage.

    Args:
        stage_label: human-readable stage name used in escalation messages.
        spec: a LIVE ``ReviewSpec`` from ``build_*_reviewspec(...)``.
        artifact_paths: map from the reviser's artifact key → absolute Path.
        extra_inputs: the stage's required sentinel ``__X__`` inputs.
        repo_root: repo root (used by the reviser for prompt resolution).
        memory_dir: where the ``convergence_kickback.yaml`` record (panel
            non-convergence) or ``human_input_needed.yaml`` (engine failure) is
            written, and the root of the ``convergence_trail/`` provenance dir.
        producer: producing-agent name for self-review prevention (FR-018).
        constitution: explicit constitution text forwarded to the engine.

    Returns the list of absolute Paths the engine rewrote (may be empty when
    the panel accepted with no edits).

    Raises:
        StagePanelKickback: panel did not converge (marker written first).
        StagePanelEscalation: engine path failed (marker written first).
    """
    trail_path = _next_trail_path(memory_dir, stage_label)
    on_round = _make_round_hook(trail_path)
    on_abort = _make_abort_hook(trail_path)
    try:
        run_result = run_engine_for_project(
            spec=spec,
            artifact_paths=artifact_paths,
            extra_inputs=extra_inputs,
            repo_root=repo_root,
            constitution=constitution,
            on_round=on_round,
            on_abort=on_abort,
        )
    except BackendUnavailable:
        # The backend's circuit breaker is OPEN: the Dartmouth endpoint is
        # PERSISTENTLY down (sustained outage). This is NOT a human-actionable
        # engine failure (a human cannot revive a dead endpoint) and NOT a panel
        # non-convergence kickback. Re-raise AS-IS (do NOT write
        # human_input_needed.yaml, do NOT wrap in StagePanelEscalation) so the
        # run aborts cleanly and the project STAYS at its current stage to resume
        # on the next scheduled tick once the endpoint recovers. The run loop's
        # `except Exception` catches it and fails the run with state preserved.
        # NOTE: must precede the generic `except Exception` below — and the
        # TransientBackendError clause — because BackendUnavailable subclasses
        # PermanentBackendError, not TransientBackendError.
        raise
    except TransientBackendError:
        # A TRANSIENT backend failure (endpoint hung past its deadline / 5xx /
        # connection dropped — the backend's own retry+backoff already
        # exhausted) is NOT a human-actionable engine failure: a human cannot
        # fix a transiently-degraded model endpoint. Re-raise it AS-IS (do NOT
        # write human_input_needed.yaml, do NOT wrap in StagePanelEscalation) so
        # the run fails transiently and the project STAYS at its current stage
        # to retry on the next scheduler tick when the endpoint recovers.
        # run_one_step does not catch TransientBackendError, so it surfaces to
        # the CLI as a transient FAIL with no stage change.
        raise
    except Exception as exc:  # genuine engine failure — escalate, do not swallow.
        _write_human_input_needed(
            memory_dir,
            {
                "reason": (
                    f"{stage_label} panel engine failure: "
                    f"{type(exc).__name__}: {exc}"
                ),
                "stage": stage_label,
            },
        )
        raise StagePanelEscalation(
            f"{stage_label} panel engine failure: {type(exc).__name__}: {exc}"
        ) from exc

    result = run_result.convergence
    if not result.converged and result.kickback is not None:
        kb = result.kickback
        # ADAPTIVE auto-kickback (F-14/F-20 Part B): write the generic
        # convergence_kickback.yaml record (NOT human_input_needed.yaml) so the
        # graph routes the project back to the content stage and auto-retries,
        # bounded by the per-project kickback cap. The record carries the full
        # provenance the next worker needs.
        emit_convergence_kickback(memory_dir, kb, stage_label=stage_label)
        raise StagePanelKickback(
            f"{stage_label} panel did not converge: {kb.reason} "
            f"(kickback → {kb.to_stage})"
        )

    return list(run_result.files_written)


__all__ = [
    "CONVERGENCE_KICKBACK_FILENAME",
    "StagePanelEscalation",
    "StagePanelKickback",
    "_constitution",
    "_idea_md",
    "_read",
    "_spec_template",
    "emit_convergence_kickback",
    "render_recent_comments_block",
    "run_stage_panel",
]
