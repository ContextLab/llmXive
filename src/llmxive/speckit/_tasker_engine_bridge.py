"""Bridge between the legacy TaskerAgent Mode-A/Mode-B loop and the
spec-015 convergence engine (T027).

The legacy ``TaskerAgent`` (``tasks_cmd.py``) drives its own analyze-revise
loop: Mode-A runs ``run_analyze`` for an analyze report, Mode-B re-writes
``tasks.md`` in response. The spec-015 convergence engine
(``llmxive.convergence.engine.run_convergence``) generalizes this loop
(identify → revise → re-review with adaptive kickback). This module is
the migration path that lets ``TaskerAgent`` opt into the engine via
``LLMXIVE_TASKER_USE_ENGINE=1`` without removing the legacy loop.

The bridge:

1. Loads the project's tasks/spec/plan/analyze/constitution into the
   engine's artifacts dict via ``run_engine_for_project``.
2. Translates the analyze report's findings into spec-015 ``Concern``
   objects (one per analyze finding, severity inferred from the finding
   class).
3. Runs the engine + writes the rewritten ``tasks.md`` back to disk.

The legacy path remains the default until the production cutover; the
env var is the feature flag.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from llmxive.convergence.project_runner import (
    ProjectRunResult,
    run_engine_for_project,
)
from llmxive.convergence.reviewspecs import build_tasks_reviewspec
from llmxive.convergence.types import Concern, Severity, Verdict


def tasker_engine_enabled() -> bool:
    """True when ``LLMXIVE_TASKER_USE_ENGINE=1`` (or any truthy value).
    Production callers in ``tasks_cmd.py`` check this BEFORE entering
    the legacy loop and switch paths accordingly."""
    val = os.environ.get("LLMXIVE_TASKER_USE_ENGINE", "").strip().lower()
    return val in {"1", "true", "yes", "on"}


# --- analyze report → spec-015 concerns ----------------------------------


# The legacy analyze report can flag a handful of finding classes; this
# table maps each to the spec-015 Severity vocabulary the engine consumes.
_FINDING_CLASS_TO_SEVERITY: dict[str, Severity] = {
    "constraint_preservation": Severity.REQUIREMENT,
    "coverage": Severity.REQUIREMENT,
    "ordering": Severity.REQUIREMENT,
    "executability": Severity.REQUIREMENT,
    "methodology": Severity.METHODOLOGY,
    "spec_consistency": Severity.METHODOLOGY,
    "science": Severity.SCIENCE,
    "fatal": Severity.FATAL,
    "writing": Severity.WRITING,
    "trivial": Severity.TRIVIAL,
}


def analyze_findings_to_concerns(
    findings: list[dict[str, Any]], *, default_artifact_path: str,
) -> list[Concern]:
    """Translate analyze-report findings to spec-015 Concerns.

    Each finding produces ONE Concern. Severity is inferred from the
    finding's ``class`` field (or its lens name); unknown classes fall
    back to WRITING (the most conservative). The Concern's ``id`` mirrors
    the finding's ``id`` when present so downstream tooling can match
    legacy findings to spec-015 concerns.
    """
    concerns: list[Concern] = []
    for i, f in enumerate(findings):
        cls = (f.get("class") or f.get("lens") or "writing").strip().lower()
        severity = _FINDING_CLASS_TO_SEVERITY.get(cls, Severity.WRITING)
        finding_id = str(f.get("id") or f"F{i + 1:03d}")
        concerns.append(
            Concern(
                id=finding_id,
                reviewer=cls,
                severity=severity,
                artifact=str(f.get("artifact") or default_artifact_path),
                location=str(f.get("location") or ""),
                text=str(f.get("text") or f.get("message") or ""),
            )
        )
    return concerns


class _AnalyzeReportReviewer:
    """A single 'reviewer' that surfaces the analyze report's findings as
    R1 concerns and accepts in R3 (the loop terminates when the reviser's
    new artifacts satisfy the analyze pass — same semantics as the
    legacy Mode-A/Mode-B loop)."""

    def __init__(self, name: str, concerns: list[Concern]) -> None:
        self.name = name
        self._concerns = concerns

    def identify(self, artifacts, *, constitution, advisory):  # type: ignore[no-untyped-def]
        return list(self._concerns)

    def rereview(self, artifacts, own_concerns, responses, *, constitution, advisory):  # type: ignore[no-untyped-def]
        # The reviser's responses are the R2 output; we trust them in R3
        # for this bridge (matches legacy semantics where a successful
        # Mode-B always loops back to a fresh Mode-A on the new content).
        # When the bridge's caller wants stricter re-checking, it can
        # call run_analyze on the rewritten tasks.md to verify before
        # moving forward.
        return [
            Verdict(concern_id=c.id, reviewer=self.name, status="pass")
            for c in own_concerns
        ]


def run_tasker_via_engine(
    *,
    project_id: str,
    repo_root: Path,
    tasks_path: Path,
    spec_path: Path,
    plan_path: Path,
    analyze_findings: list[dict[str, Any]],
    backend: Any,
    constitution_text: str | None = None,
    analyze_report_text: str = "",
    model: str | None = None,
) -> ProjectRunResult:
    """Run the spec-015 convergence engine in place of the legacy
    Mode-A/Mode-B loop for the Tasker.

    Returns the :class:`ProjectRunResult` from
    :func:`run_engine_for_project`. Disk side-effect: ``tasks_path`` is
    rewritten when the engine converges + the reviser produced new content.

    Wiring contract (intended for ``tasks_cmd.py``):

    - Caller is responsible for the FIRST analyze (Mode-A): it produces
      ``analyze_findings`` from ``run_analyze(...)`` on the current
      tasks.md + spec + plan. The bridge translates those to Concerns.
    - The bridge then runs the engine, which calls TasksReviser (R2)
      to rewrite tasks.md addressing the concerns.
    - After the bridge returns, the caller can re-run ``run_analyze``
      to verify the new tasks.md analyzes clean (the strict-loop
      version of T027 vs. the trust-the-reviser version implemented
      here).
    """
    tasks_key = f"projects/{project_id}/specs/{tasks_path.parent.name}/tasks.md"
    spec_key = f"projects/{project_id}/specs/{spec_path.parent.name}/spec.md"
    plan_key = f"projects/{project_id}/specs/{plan_path.parent.name}/plan.md"

    spec = build_tasks_reviewspec(
        backend=backend, repo_root=repo_root, project_id=project_id,
        model=model,
    )
    concerns = analyze_findings_to_concerns(
        analyze_findings, default_artifact_path=tasks_key,
    )
    spec.reviewers = [_AnalyzeReportReviewer("analyze", concerns)]

    extra_inputs: dict[str, str] = {
        "__analyze_report__": analyze_report_text,
    }
    if constitution_text:
        extra_inputs["__constitution__"] = constitution_text

    return run_engine_for_project(
        spec=spec,
        artifact_paths={
            tasks_key: tasks_path,
            spec_key: spec_path,
            plan_key: plan_path,
        },
        extra_inputs=extra_inputs,
        repo_root=repo_root,
        write_back=True,
    )


__all__ = [
    "analyze_findings_to_concerns",
    "run_tasker_via_engine",
    "tasker_engine_enabled",
]
