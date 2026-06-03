"""Bridge between the convergence engine and an on-disk project tree (spec 015 T021).

The engine's :func:`llmxive.convergence.engine.run_convergence` operates on
an in-memory ``artifacts: dict[str, str]`` mapping — it does NOT load from
or write to disk. That's deliberate: the engine is pure, deterministic, and
easy to test. But every production caller needs to:

1. Load the right files off disk into ``artifacts``.
2. Run the engine.
3. Persist the engine's revised artifacts back to disk where the graph +
   downstream tooling expect to find them.

This module is the SSoT for that bridging. It's used by:

- ``tests/integration/test_convergence_tasks_step.py`` (T021 proving ground).
- Eventually (T027) — ``src/llmxive/pipeline/graph.py`` when the engine
  becomes the sole revision driver for reviewable stages.

The captured-artifacts mechanism is a small but load-bearing hack: the
engine doesn't expose updated_artifacts in its ``ConvergenceResult``, so
we wrap the configured Reviser in :class:`_CapturingReviser` that records
every revise() output. The captured artifacts are the post-final-round
state the runner writes back to disk.

Required-extras invariant (FR-049 fail-loud)
--------------------------------------------

Every reviser pulls its supporting context from sentinel ``__X__`` keys in
the artifacts dict (e.g. ``__constitution__``, ``__spec_md__``). If a
production caller forgets to supply one of these the reviser silently
falls back to ``""``, and the panel emits "X not provided" concerns that
look like real findings — that's the production bug the spec-015
calibration repro uncovered (panels reporting "spec.md not provided",
"constitution.md not provided" on real-call calibration runs).

The :data:`_REQUIRED_EXTRA_INPUTS_PER_STAGE` map encodes each stage's
contract; :func:`run_engine_for_project` checks ``extra_inputs`` against
it BEFORE entering the engine and raises ``ValueError`` if any required
key is missing. Callers that legitimately need to opt out (e.g. unit
tests that exercise only a subset of the artifacts dict) pass
``require_full_extra_inputs=False``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .engine import AbortHook, RoundHook, run_convergence
from .types import (
    Concern,
    ConcernResponse,
    ConvergenceResult,
    ReviewSpec,
)

# Required sentinel-key contract per stage. Keys MUST be present (even
# with empty content is allowed for legitimately-empty inputs like
# ``__comments_block__`` when there are no comments — but the caller
# MUST supply the key so the reviser sees it explicitly rather than
# silently defaulting to ``""``). The reviewer-contract source of truth
# is the individual reviser modules in
# :mod:`llmxive.convergence.revisers`; keep this table in sync with
# them when adding new revisers.
_REQUIRED_EXTRA_INPUTS_PER_STAGE: dict[str, set[str]] = {
    # spec_reviser pulls idea + comments + spec_template
    "clarified": {"__idea_md__", "__comments_block__", "__spec_template__"},
    # plan_reviser pulls constitution + comments + spec
    "planned": {"__constitution__", "__comments_block__", "__spec_md__"},
    # tasks_reviser pulls analyze + prior reviews + constitution + comments + spec + plan
    "tasked": {
        "__analyze_report__", "__prior_reviews__", "__constitution__",
        "__comments_block__", "__spec_md__", "__plan_md__",
    },
    # implementer_reviser pulls analyze + comments + constitution + plan + spec + tasks
    "research_review": {
        "__analyze_report__", "__comments_block__", "__constitution__",
        "__plan_md__", "__spec_md__", "__tasks_md__",
    },
    # paper_spec_reviser pulls code + data summaries + constitution + comments
    "paper_clarified": {
        "__code_summary__", "__data_summary__", "__comments_block__",
        "__constitution__",
    },
    # PaperPlanReviser (shares plan_reviser.py): same contract as planned
    "paper_planned": {"__constitution__", "__comments_block__", "__spec_md__"},
    # PaperTasksReviser (shares tasks_reviser.py): same contract as tasked
    "paper_tasked": {
        "__analyze_report__", "__prior_reviews__", "__constitution__",
        "__comments_block__", "__spec_md__", "__plan_md__",
    },
    # paper_implement_reviser pulls paper spec/plan + results + tasks + constitution + comments
    "paper_review": {
        "__paper_spec_md__", "__paper_plan_md__", "__results_md__",
        "__tasks_md__", "__constitution__", "__comments_block__",
    },
}


@dataclass
class ProjectRunResult:
    """What ``run_engine_for_project`` returns. Wraps the engine's
    :class:`ConvergenceResult` plus the on-disk write outcome."""

    convergence: ConvergenceResult
    files_written: list[Path]
    files_unchanged: list[Path]


class _CapturingReviser:
    """Wraps a real Reviser, recording every revise() call's output.

    Implements the :class:`Reviser` protocol structurally (no inheritance)
    so the engine's type checks pass. The last captured ``updated``
    artifacts are what gets written back to disk by
    :func:`run_engine_for_project`.
    """

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.last_updated: dict[str, str] = {}
        self.calls = 0

    @property
    def name(self) -> str:
        return getattr(self._inner, "name", "captured")

    def revise(
        self, artifacts: dict[str, str], concerns: list[Concern]
    ) -> tuple[dict[str, str], list[ConcernResponse]]:
        self.calls += 1
        updated, responses = self._inner.revise(artifacts, concerns)
        # Record the cumulative artifact view (the engine merges
        # progressively across rounds; we want the post-final-round
        # state to write back to disk).
        self.last_updated = dict(updated)
        return updated, responses


def run_engine_for_project(
    *,
    spec: ReviewSpec,
    artifact_paths: dict[str, Path],
    extra_inputs: dict[str, str] | None = None,
    repo_root: Path,
    write_back: bool = True,
    require_full_extra_inputs: bool = True,
    constitution: str | None = None,
    on_round: RoundHook | None = None,
    on_abort: AbortHook | None = None,
) -> ProjectRunResult:
    """Drive the engine for one reviewable step against a REAL project tree.

    Args:
        spec: a live ``ReviewSpec`` from ``build_*_reviewspec(...)``.
        artifact_paths: map from a key the reviser will read (e.g.
            ``"projects/<id>/specs/<f>/tasks.md"``) to its absolute Path on
            disk. The runner reads every entry into the artifacts dict
            before running the engine.
        extra_inputs: optional non-file inputs that go directly into the
            artifacts dict (e.g. ``__constitution__`` /
            ``__analyze_report__`` keys the revisers consume).
        repo_root: repo root path (used by the spec's reviser for prompt
            file resolution).
        write_back: if True (default), the engine's revised artifacts are
            written back to disk via ``Path.write_text()``. Set False to
            run the engine read-only (useful for dry-runs).
        require_full_extra_inputs: if True (default), assert that every
            sentinel key in :data:`_REQUIRED_EXTRA_INPUTS_PER_STAGE` for
            this stage is present in ``extra_inputs``. Fail-loud (FR-049)
            so a production caller can't silently under-supply context.
            Set False for unit-test fixtures that legitimately only
            exercise a partial artifacts dict.
        constitution: explicit constitution text forwarded to
            :func:`run_convergence` via the ``constitution=`` kwarg. When
            given AND ``extra_inputs`` does NOT already contain
            ``__constitution__``, this value is ALSO injected as
            ``__constitution__`` so the reviser's prompt consumes it.
        on_round: optional per-round inspection hook forwarded to
            :func:`run_convergence` (FR-015). Called once per round with
            ``(round_index, concerns, responses, verdicts)`` so callers can
            persist a complete provenance trail.

    Returns a :class:`ProjectRunResult` with the ConvergenceResult plus
    the lists of files that were rewritten / left unchanged.

    Raises:
        ValueError: when ``require_full_extra_inputs`` is True and one
            of the stage's required sentinel keys is missing from
            ``extra_inputs`` (after the optional ``constitution=``
            backfill). The error message lists the missing keys + stage
            so operators can fix the call-site under-supply.
    """
    # Backfill __constitution__ from the explicit kwarg if the caller
    # passed it but didn't put it in extra_inputs (the common case for
    # the calibration harness, which loads the constitution from
    # `.specify/memory/constitution.md` and supplies it via kwarg).
    extras = dict(extra_inputs) if extra_inputs else {}
    if constitution is not None and "__constitution__" not in extras:
        extras["__constitution__"] = constitution

    # Fail-loud required-keys check (FR-049): production callers MUST
    # supply every key the stage's reviser reads. Missing keys cause
    # the panel to report "X not provided" concerns that look like real
    # findings (the spec-015 calibration repro symptom).
    if require_full_extra_inputs:
        required = _REQUIRED_EXTRA_INPUTS_PER_STAGE.get(spec.stage, set())
        missing = sorted(k for k in required if k not in extras)
        if missing:
            raise ValueError(
                f"run_engine_for_project: stage {spec.stage!r} requires "
                f"sentinel keys {missing!r} in extra_inputs but they are "
                "missing. Supply them (empty string is acceptable if a "
                "specific input is legitimately empty, e.g. no comments) "
                "or pass require_full_extra_inputs=False for partial "
                "test fixtures. See _REQUIRED_EXTRA_INPUTS_PER_STAGE in "
                "llmxive.convergence.project_runner for the contract."
            )

    # Load on-disk → artifacts dict.
    artifacts: dict[str, str] = {}
    for key, path in artifact_paths.items():
        artifacts[key] = path.read_text() if path.exists() else ""
    if extras:
        artifacts.update(extras)

    # Wrap the reviser so we can capture its post-revise output.
    original_reviser = spec.reviser
    capturing = _CapturingReviser(original_reviser) if original_reviser is not None else None
    spec.reviser = capturing
    try:
        result = run_convergence(
            spec, artifacts, constitution=constitution, on_round=on_round,
            on_abort=on_abort,
        )
    finally:
        spec.reviser = original_reviser  # restore

    # Write back what the reviser actually changed (engine doesn't expose
    # post-final-round artifacts; the capturing wrapper holds them).
    files_written: list[Path] = []
    files_unchanged: list[Path] = []
    if write_back and capturing is not None and capturing.last_updated:
        for key, path in artifact_paths.items():
            new_content = capturing.last_updated.get(key)
            if new_content is None:
                files_unchanged.append(path)
                continue
            original_content = artifacts[key]
            if new_content == original_content:
                files_unchanged.append(path)
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(new_content)
            files_written.append(path)
    else:
        files_unchanged = list(artifact_paths.values())

    return ProjectRunResult(
        convergence=result,
        files_written=files_written,
        files_unchanged=files_unchanged,
    )


__all__ = [
    "_REQUIRED_EXTRA_INPUTS_PER_STAGE",
    "ProjectRunResult",
    "run_engine_for_project",
]
