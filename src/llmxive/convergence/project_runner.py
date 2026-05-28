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
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .engine import run_convergence
from .types import (
    Concern,
    ConcernResponse,
    ConvergenceResult,
    ReviewSpec,
)


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

    Returns a :class:`ProjectRunResult` with the ConvergenceResult plus
    the lists of files that were rewritten / left unchanged.
    """
    # Load on-disk → artifacts dict.
    artifacts: dict[str, str] = {}
    for key, path in artifact_paths.items():
        artifacts[key] = path.read_text() if path.exists() else ""
    if extra_inputs:
        artifacts.update(extra_inputs)

    # Wrap the reviser so we can capture its post-revise output.
    original_reviser = spec.reviser
    capturing = _CapturingReviser(original_reviser) if original_reviser is not None else None
    spec.reviser = capturing
    try:
        result = run_convergence(spec, artifacts)
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


__all__ = ["ProjectRunResult", "run_engine_for_project"]
