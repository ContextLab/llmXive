"""Failure-mode tests (T037 + T038, US5).

Parametrize :func:`personality.tick` against fixtures that raise
TimeoutError / signal rate-limit / signal model_error / return malformed
JSON. Asserts each path produces the right outcome enum + the rotation
pointer is unchanged. No real LLM.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llmxive.agents import personality as p


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Minimal repo with one valid persona + pre-set rotation pointer at
    'prior-slug' so we can detect HOLD vs ADVANCE."""
    FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "personality"
    r = tmp_path / "repo"
    r.mkdir()
    (r / "agents" / "prompts" / "personalities").mkdir(parents=True)
    (r / "agents" / "prompts" / "personalities" / "kahneman.md").write_text(
        (FIXTURES / "kahneman.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (r / "agents" / "prompts" / "personality.md").write_text(
        "# Umbrella\nReturn JSON.\n", encoding="utf-8")
    (r / "state" / "projects").mkdir(parents=True)
    # Pre-set the rotation pointer.
    p.write_rotation_state(
        p.RotationState(
            last_used="prior-slug",
            last_used_at="2026-05-13T00:00:00+00:00",
            last_outcome=p.OUTCOME_COMMITTED,
            history=[],
        ),
        r / p.ROTATION_PATH,
    )
    return r


class TestExceptionClassifier:
    def test_timeout_classified(self) -> None:
        assert p._classify_llm_exception(TimeoutError("operation timed out")) == p.OUTCOME_TIMEOUT

    def test_rate_limit_classified(self) -> None:
        for exc in [
            RuntimeError("HTTP 429 Too Many Requests"),
            RuntimeError("rate limit exceeded"),
            RuntimeError("quota exhausted for today"),
        ]:
            assert p._classify_llm_exception(exc) == p.OUTCOME_RATE_LIMITED

    def test_generic_falls_through_to_model_error(self) -> None:
        assert p._classify_llm_exception(ValueError("garbled response")) == p.OUTCOME_MODEL_ERROR
        assert p._classify_llm_exception(ConnectionError("ECONNREFUSED")) == p.OUTCOME_MODEL_ERROR


class TestTickHoldsPointerOnFailure:
    def test_rate_limited_holds_pointer(self, repo: Path, monkeypatch) -> None:
        # Monkeypatch the LLM call to raise a rate-limit-shaped error.
        def fake_call(*a, **kw):
            raise RuntimeError("HTTP 429: rate limit hit")
        monkeypatch.setattr(p, "_call_llm_for_persona", fake_call)
        entry = p.tick(repo)
        assert entry["outcome"] == p.OUTCOME_RATE_LIMITED
        # Pointer HELD at the prior slug per FR-017.
        state = p.load_rotation_state(repo / p.ROTATION_PATH)
        assert state.last_used == "prior-slug"

    def test_timeout_holds_pointer(self, repo: Path, monkeypatch) -> None:
        def fake_call(*a, **kw):
            raise TimeoutError("LLM call exceeded budget")
        monkeypatch.setattr(p, "_call_llm_for_persona", fake_call)
        entry = p.tick(repo)
        assert entry["outcome"] == p.OUTCOME_TIMEOUT
        state = p.load_rotation_state(repo / p.ROTATION_PATH)
        assert state.last_used == "prior-slug"

    def test_model_error_holds_pointer(self, repo: Path, monkeypatch) -> None:
        def fake_call(*a, **kw):
            raise ConnectionError("ECONNREFUSED: backend down")
        monkeypatch.setattr(p, "_call_llm_for_persona", fake_call)
        entry = p.tick(repo)
        assert entry["outcome"] == p.OUTCOME_MODEL_ERROR
        state = p.load_rotation_state(repo / p.ROTATION_PATH)
        assert state.last_used == "prior-slug"


class TestWorkflowDryrunShape:
    """T038: exercise the orchestrator's pre-LLM logic with a fixture pool
    and a mocked LLM, asserting the workflow-shaped path (load pool →
    select → build catalog → call LLM → parse → dispatch) goes through
    without firing the real network."""

    def test_full_dryrun_with_canned_response(self, repo: Path) -> None:
        FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "personality"
        # Use the abstain fixture — minimal, no project creation needed.
        entry = p.tick(repo, llm_fixture=str(FIXTURES / "action_abstain.json"))
        assert entry["agent_name"] == "personality"
        assert entry["personality_slug"] == "kahneman"
        assert entry["action"] == "abstain"
        assert entry["outcome"] == p.OUTCOME_ABSTAINED
        # Pointer advanced on abstain.
        state = p.load_rotation_state(repo / p.ROTATION_PATH)
        assert state.last_used == "kahneman"

    def test_run_log_entry_written_to_disk(self, repo: Path) -> None:
        FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "personality"
        p.tick(repo, llm_fixture=str(FIXTURES / "action_abstain.json"))
        # Find the JSONL file under state/run-log/<YYYY-MM>/.
        log_files = list((repo / "state" / "run-log").rglob("*.jsonl"))
        assert log_files, "expected a run-log JSONL file"
        # Last line must parse as JSON with our agent_name.
        for f in log_files:
            for line in f.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                d = json.loads(line)
                if d.get("agent_name") == "personality":
                    assert d["personality_slug"] == "kahneman"
                    return
        pytest.fail("no personality run-log entry found")
