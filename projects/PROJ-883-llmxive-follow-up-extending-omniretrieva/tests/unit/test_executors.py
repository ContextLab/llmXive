"""Unit tests for the executor implementations."""

import pytest
from executors.base import create_executor, ExecutionResult, TimeoutException

@pytest.mark.parametrize(
    "etype,expected_prefix",
    [
        ("text", "text_plan_"),
        ("relational", "relational_plan_"),
        ("graph", "graph_plan_"),
    ],
)
def test_executor_runs_successfully(etype, expected_prefix):
    ExecutorClass = create_executor(etype)
    executor = ExecutorClass(timeout_seconds=5)
    # Minimal query dict – only the fields required by the executors.
    query = {
        "query_id": f"test_{etype}",
        "source_type": etype,
        "complexity_level": 2,
    }
    result = executor.run(query)
    assert isinstance(result, ExecutionResult)
    assert result.success is True
    assert result.timeout is False
    assert result.executed_plan.startswith(expected_prefix)

def test_timeout_is_enforced(monkeypatch):
    """Force a timeout by patching the concrete ``_run`` method."""

    class SlowExecutor(create_executor("text")):
        def _run(self, query):
            import time

            time.sleep(2)  # longer than the 1‑second timeout we set
            return super()._run(query)

    executor = SlowExecutor(timeout_seconds=1)
    query = {
        "query_id": "slow_test",
        "source_type": "text",
        "complexity_level": 1,
    }
    result = executor.run(query)
    assert result.timeout is True
    assert result.success is False
    assert result.executed_plan is None