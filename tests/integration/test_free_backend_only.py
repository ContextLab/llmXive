"""Integration test (T104): every v1 backend is `is_paid: false`.

Pure file-fixture-driven; asserts the registry's invariants hold.

The semantic assertion is: with only DARTMOUTH_CHAT_API_KEY (and
optionally HF_TOKEN) configured, every agent invocation produces a
run-log entry with `cost_estimate_usd == 0.0`. The runlog writer's
CostInvariantError guard (T103) makes any non-zero cost fail-fast.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from llmxive.agents import registry as registry_loader
from llmxive.state.runlog import CostInvariantError, append_entry
from llmxive.types import (
    BackendName,
    Outcome,
    RunLogEntry,
)


def test_every_backend_is_free() -> None:
    reg = registry_loader.load()
    for backend in reg.backends:
        assert backend.is_paid is False, (
            f"backend {backend.name!r} has is_paid=True; v1 invariant is False "
            f"(Constitution Principle IV)"
        )


def test_every_agent_is_paid_opt_in_false() -> None:
    reg = registry_loader.load()
    for agent in reg.agents:
        assert agent.paid_opt_in is False, (
            f"agent {agent.name!r} has paid_opt_in=True; v1 invariant is False "
            f"(FR-020)"
        )


def test_runlog_writer_blocks_non_zero_cost(tmp_path: Path) -> None:
    """A run-log entry with cost_estimate_usd > 0 must raise."""
    for sub in ("projects", "run-log", "locks", "citations"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    entry = RunLogEntry(
        run_id="11111111-1111-1111-1111-111111111111",
        entry_id="22222222-2222-2222-2222-222222222222",
        agent_name="test_agent",
        project_id="PROJ-001-cost",
        task_id="33333333-3333-3333-3333-333333333333",
        inputs=[],
        outputs=[],
        backend=BackendName.DARTMOUTH,
        model_name="qwen.qwen3.5-122b",
        prompt_version="1.0.0",
        started_at=now,
        ended_at=now,
        outcome=Outcome.SUCCESS,
        cost_estimate_usd=0.000001,  # any non-zero
    )

    with pytest.raises(CostInvariantError):
        append_entry(entry, repo_root=tmp_path)


def test_zero_cost_runlog_succeeds(tmp_path: Path) -> None:
    """A run-log entry with cost_estimate_usd == 0.0 writes successfully."""
    for sub in ("projects", "run-log", "locks", "citations"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    entry = RunLogEntry(
        run_id="44444444-4444-4444-4444-444444444444",
        entry_id="55555555-5555-5555-5555-555555555555",
        agent_name="test_agent",
        project_id="PROJ-002-zero",
        task_id="66666666-6666-6666-6666-666666666666",
        inputs=[],
        outputs=[],
        backend=BackendName.DARTMOUTH,
        model_name="qwen.qwen3.5-122b",
        prompt_version="1.0.0",
        started_at=now,
        ended_at=now,
        outcome=Outcome.SUCCESS,
        cost_estimate_usd=0.0,
    )

    written = append_entry(entry, repo_root=tmp_path)
    assert written.exists()
    content = written.read_text(encoding="utf-8").strip()
    assert "cost_estimate_usd" in content
    assert '"cost_estimate_usd": 0.0' in content or '"cost_estimate_usd":0.0' in content
