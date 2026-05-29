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
   NOT converged (kickback) → write ``human_input_needed.yaml`` in the stage's
   memory dir and signal non-advancement by raising
   :class:`StagePanelKickback`.
   Engine exception → escalate via ``human_input_needed.yaml`` and re-raise as
   :class:`StagePanelEscalation`.

The on-disk artifact write-back is owned by ``run_engine_for_project``; this
module supplies the ``artifact_paths`` map keyed by the SAME repo-relative key
the stage's reviser reads, so the revised content lands at the canonical Spec
Kit path.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from llmxive.convergence.project_runner import run_engine_for_project
from llmxive.convergence.types import ReviewSpec
from llmxive.speckit._comments_context import render_recent_comments_block


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
        memory_dir: where ``human_input_needed.yaml`` is written on kickback.
        producer: producing-agent name for self-review prevention (FR-018).
        constitution: explicit constitution text forwarded to the engine.

    Returns the list of absolute Paths the engine rewrote (may be empty when
    the panel accepted with no edits).

    Raises:
        StagePanelKickback: panel did not converge (marker written first).
        StagePanelEscalation: engine path failed (marker written first).
    """
    try:
        run_result = run_engine_for_project(
            spec=spec,
            artifact_paths=artifact_paths,
            extra_inputs=extra_inputs,
            repo_root=repo_root,
            constitution=constitution,
        )
    except Exception as exc:  # engine failure — escalate, do not swallow.
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
        _write_human_input_needed(
            memory_dir,
            {
                "reason": result.kickback.reason,
                "kickback_to_stage": result.kickback.to_stage,
                "worst_severity": result.kickback.worst_severity.value,
                "stage": stage_label,
            },
        )
        raise StagePanelKickback(
            f"{stage_label} panel did not converge: {result.kickback.reason} "
            f"(kickback → {result.kickback.to_stage})"
        )

    return list(run_result.files_written)


__all__ = [
    "StagePanelEscalation",
    "StagePanelKickback",
    "_constitution",
    "_idea_md",
    "_read",
    "_spec_template",
    "render_recent_comments_block",
    "run_stage_panel",
]
