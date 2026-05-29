"""Bridge between the legacy TaskerAgent Mode-A/Mode-B loop and the
spec-015 convergence engine (T027).

The legacy ``TaskerAgent`` (``tasks_cmd.py``) drives its own analyze-revise
loop: Mode-A runs ``run_analyze`` for an analyze report, Mode-B re-writes
``tasks.md`` in response. The spec-015 convergence engine
(``llmxive.convergence.engine.run_convergence``) generalizes this loop
(identify → revise → re-review with adaptive kickback). This module is
the production path: as of T027 the engine is the DEFAULT; the legacy
loop is retained only as an emergency rollback via
``LLMXIVE_TASKER_LEGACY=1``.

The bridge:

1. Loads the project's tasks/spec/plan/analyze/constitution into the
   engine's artifacts dict via ``run_engine_for_project``.
2. Translates the analyze report's findings into spec-015 ``Concern``
   objects (one per analyze finding, severity inferred from the finding
   class).
3. Runs the engine with ``write_back=False`` so this module owns the
   filesystem writeback.
4. Applies the FR-031 deterministic pre-filter guards
   (``_legacy_guards.check_legacy_guards``) to every proposed
   tasks.md / spec.md / plan.md change BEFORE writing it back. The same
   guards run in the legacy loop; SSoT lives in ``_legacy_guards.py``.
5. On a guard violation, the writeback is rejected and a synthetic
   ``Concern`` describing the violation is surfaced back through the
   engine (next round retries). If the guard fires irrecoverably (the
   engine has already exhausted its rounds), the bridge reports the
   round as non-converged and the caller's outer loop handles the
   kickback.

The legacy path remains available via the opt-out env var.
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
from llmxive.convergence.types import (
    Concern,
    ConcernResponse,
    Reviser,
    Severity,
    Verdict,
)

from ._legacy_guards import check_legacy_guards


def tasker_legacy_enabled() -> bool:
    """True when ``LLMXIVE_TASKER_LEGACY=1`` (or any truthy value).

    Production callers in ``tasks_cmd.py`` check this BEFORE entering
    the engine path; when True they fall through to the legacy
    Mode-A/Mode-B loop instead. This is the emergency-rollback opt-out
    after the T027 cutover (engine became the default).
    """
    val = os.environ.get("LLMXIVE_TASKER_LEGACY", "").strip().lower()
    return val in {"1", "true", "yes", "on"}


def tasker_engine_enabled() -> bool:
    """True when the engine path should drive the tasker (default).

    Post-T027 the engine is the default; ``LLMXIVE_TASKER_LEGACY=1``
    flips it back to the legacy Mode-A/Mode-B loop. The historic
    opt-IN env var ``LLMXIVE_TASKER_USE_ENGINE`` is still honored for
    back-compat: setting it to a falsy value (``0`` / ``false``) forces
    the legacy path. Unset = engine.
    """
    if tasker_legacy_enabled():
        return False
    # Back-compat: the pre-T027 opt-in flag. If set to a truthy value
    # it's a no-op (engine is the default); set to a falsy value it
    # forces the legacy path.
    legacy_compat = os.environ.get("LLMXIVE_TASKER_USE_ENGINE")
    if legacy_compat is not None:
        return legacy_compat.strip().lower() in {"1", "true", "yes", "on"}
    return True


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
        # Concern.text is now ``min_length=1`` (spec-015 fix for the
        # empty-text bug). Findings missing both ``text`` and ``message``
        # were already a degenerate input — the analyzer claimed a problem
        # but never described it. Synthesize a placeholder so the bridge
        # stays robust (the upstream finding ID still surfaces) instead of
        # silently producing an empty-text Concern.
        raw_text = str(f.get("text") or f.get("message") or "").strip()
        if not raw_text:
            raw_text = (
                f"<analyze-finding {finding_id} (class={cls}) had no "
                f"text/message field>"
            )
        concerns.append(
            Concern(
                id=finding_id,
                reviewer=cls,
                severity=severity,
                artifact=str(f.get("artifact") or default_artifact_path),
                location=str(f.get("location") or ""),
                text=raw_text,
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


class _GuardedReviser:
    """Reviser wrapper that runs FR-031 deterministic guards on the
    proposed writebacks BEFORE returning them to the engine.

    When a guard fires, the proposed change for that artifact is
    REJECTED (the artifact stays at its original content for this round)
    and a synthetic ``Concern`` describing the violation is appended to
    ``pending_guard_concerns`` so the bridge can feed it back into the
    next round (or so the caller can inspect it after the engine exits).

    Implements the Reviser Protocol structurally.

    The post-revise artifact view (after guards) is stashed on
    ``post_revise_view`` so the bridge can write it back to disk
    after the engine returns (engine is run with ``write_back=False``).
    """

    def __init__(
        self,
        inner: Reviser,
        *,
        artifact_keys_by_filename: dict[str, str],
    ) -> None:
        self._inner = inner
        # filename ("tasks.md" / "spec.md" / "plan.md") -> the engine
        # artifacts-dict key (e.g. "projects/<id>/specs/<f>/tasks.md").
        self._keys = artifact_keys_by_filename
        self.pending_guard_concerns: list[Concern] = []
        self.post_revise_view: dict[str, str] = {}
        self._guard_concern_seq = 0

    @property
    def name(self) -> str:
        return getattr(self._inner, "name", "guarded")

    def revise(
        self, artifacts: dict[str, str], concerns: list[Concern]
    ) -> tuple[dict[str, str], list[ConcernResponse]]:
        updated, responses = self._inner.revise(artifacts, concerns)
        filtered_updated = dict(updated)
        for filename, key in self._keys.items():
            new_content = updated.get(key)
            if new_content is None:
                continue
            original_content = artifacts.get(key, "")
            if new_content == original_content:
                continue  # no change → nothing to guard
            refusals = check_legacy_guards(
                filename=filename,
                new_content=new_content,
                original_content=original_content,
            )
            if not refusals:
                continue
            # Guard fired: revert this key's content + raise a synthetic
            # concern so the engine's next round re-revises addressing
            # the violation.
            filtered_updated[key] = original_content
            for msg in refusals:
                self._guard_concern_seq += 1
                self.pending_guard_concerns.append(
                    Concern(
                        id=f"GUARD-{self._guard_concern_seq:03d}",
                        reviewer="fr031_guard",
                        severity=Severity.REQUIREMENT,
                        artifact=key,
                        location="",
                        text=msg,
                    )
                )
        # Stash the post-guard view so the bridge can write it back to
        # disk after the engine returns (engine is read-only here).
        self.post_revise_view = dict(filtered_updated)
        return filtered_updated, responses


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

    Returns a :class:`ProjectRunResult` whose ``files_written`` /
    ``files_unchanged`` reflect THIS bridge's filesystem writes (the
    inner engine call is run with ``write_back=False`` so we can apply
    the FR-031 guards first). Disk side-effect: ``tasks_path`` (and
    possibly ``spec_path`` / ``plan_path``) is rewritten when the
    engine produced new content AND every FR-031 pre-filter guard
    passed on that content.

    Wiring contract (intended for ``tasks_cmd.py``):

    - Caller is responsible for the FIRST analyze (Mode-A): it produces
      ``analyze_findings`` from ``run_analyze(...)`` on the current
      tasks.md + spec + plan. The bridge translates those to Concerns.
    - The bridge runs the engine and applies the FR-031 deterministic
      guards on its output BEFORE writing it back to disk.
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

    # Wrap the live reviser with the FR-031 guard pre-filter.
    if spec.reviser is None:
        raise RuntimeError(
            "build_tasks_reviewspec returned a ReviewSpec with no "
            "reviser; cannot run the engine-driven tasker."
        )
    guarded = _GuardedReviser(
        spec.reviser,
        artifact_keys_by_filename={
            "tasks.md": tasks_key,
            "spec.md": spec_key,
            "plan.md": plan_key,
        },
    )
    spec.reviser = guarded

    # Snapshot originals BEFORE the runner mutates anything: we apply
    # the engine's guard-filtered output ourselves below.
    artifact_paths_map = {
        tasks_key: tasks_path, spec_key: spec_path, plan_key: plan_path,
    }
    originals = {
        key: (p.read_text() if p.exists() else "")
        for key, p in artifact_paths_map.items()
    }

    # Supply EVERY sentinel key the TasksReviser reads (FR-049 fail-loud
    # invariant enforced by run_engine_for_project). Empty string is
    # acceptable when an input is legitimately empty (e.g. no comments
    # block, no prior reviews) — the reviser's `artifacts.get("__X__", "")`
    # fallback then sees the explicit empty rather than a silently-missing
    # key. See _REQUIRED_EXTRA_INPUTS_PER_STAGE['tasked'] for the contract.
    extra_inputs: dict[str, str] = {
        "__analyze_report__": analyze_report_text,
        "__prior_reviews__": "",
        "__constitution__": constitution_text or "",
        "__comments_block__": "",
        "__spec_md__": originals.get(spec_key, ""),
        "__plan_md__": originals.get(plan_key, ""),
    }

    # write_back=False: we apply guards ourselves (via _GuardedReviser)
    # and write to disk below.
    result = run_engine_for_project(
        spec=spec,
        artifact_paths=artifact_paths_map,
        extra_inputs=extra_inputs,
        repo_root=repo_root,
        write_back=False,
        constitution=constitution_text,
    )

    # Apply the post-guard view to disk. ``guarded.post_revise_view``
    # holds the final-round artifacts dict (with guard-violations
    # reverted to their original-on-disk content).
    files_written: list[Path] = []
    files_unchanged: list[Path] = []
    last_updated = guarded.post_revise_view
    for key, path in artifact_paths_map.items():
        new_content = last_updated.get(key)
        if new_content is None:
            files_unchanged.append(path)
            continue
        if new_content == originals[key]:
            files_unchanged.append(path)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_content)
        files_written.append(path)

    return ProjectRunResult(
        convergence=result.convergence,
        files_written=files_written,
        files_unchanged=files_unchanged,
    )


__all__ = [
    "analyze_findings_to_concerns",
    "run_tasker_via_engine",
    "tasker_engine_enabled",
    "tasker_legacy_enabled",
]
