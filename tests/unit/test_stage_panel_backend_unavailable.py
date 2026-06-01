"""The circuit-breaker's BackendUnavailable must ABORT a stage panel cleanly.

When the Dartmouth endpoint is persistently down the breaker raises
BackendUnavailable (a PermanentBackendError). At the stage-panel boundary this
must propagate AS-IS — NOT be wrapped into a StagePanelEscalation (which writes
human_input_needed.yaml: a human cannot fix a dead endpoint) and NOT be treated
as a convergence kickback. The run loop's existing `except Exception` then aborts
the run with the project's stage state preserved for the next scheduled tick.
"""

from __future__ import annotations

import pytest

from llmxive.backends.base import BackendUnavailable
from llmxive.speckit import _stage_panel
from llmxive.speckit._stage_panel import (
    StagePanelEscalation,
    StagePanelKickback,
    run_stage_panel,
)


def _spec():
    # A minimal object standing in for a ReviewSpec — run_engine_for_project is
    # patched out, so its internals are never inspected.
    return object()


def test_backend_unavailable_propagates_as_is(tmp_path, monkeypatch):
    memory_dir = tmp_path / "memory"

    def boom(**_kwargs):
        raise BackendUnavailable(
            "circuit open: Dartmouth endpoint persistently unavailable "
            "after 3 consecutive failures / 30 min"
        )

    monkeypatch.setattr(_stage_panel, "run_engine_for_project", boom)

    with pytest.raises(BackendUnavailable):
        run_stage_panel(
            stage_label="research_review",
            spec=_spec(),  # type: ignore[arg-type]
            artifact_paths={},
            extra_inputs={},
            repo_root=tmp_path,
            memory_dir=memory_dir,
        )

    # Must NOT have written the human-escalation marker (a dead endpoint is not
    # human-actionable) and must NOT have raised StagePanelEscalation/Kickback.
    assert not (memory_dir / "human_input_needed.yaml").exists()


def test_backend_unavailable_is_not_escalation_or_kickback(tmp_path, monkeypatch):
    """Explicitly: the propagated type is BackendUnavailable itself, not one of
    the panel's control-flow exceptions."""

    def boom(**_kwargs):
        raise BackendUnavailable("circuit open: ... after 3 consecutive failures / 30 min")

    monkeypatch.setattr(_stage_panel, "run_engine_for_project", boom)

    try:
        run_stage_panel(
            stage_label="spec",
            spec=_spec(),  # type: ignore[arg-type]
            artifact_paths={},
            extra_inputs={},
            repo_root=tmp_path,
            memory_dir=tmp_path / "m",
        )
    except BackendUnavailable as exc:
        assert not isinstance(exc, (StagePanelEscalation, StagePanelKickback))
    else:  # pragma: no cover - the call must raise
        raise AssertionError("expected BackendUnavailable to propagate")
