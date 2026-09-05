"""
Contract test for ExecutionOutcome schema validation.
"""
import pytest
import sys
from pathlib import Path
import json

# Ensure src is importable
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.executor import ExecutionOutcome


class TestExecutionOutcomeContract:
    """Tests for ExecutionOutcome schema compliance."""

    def test_execution_outcome_structure(self):
        """Verify ExecutionOutcome has required fields."""
        outcome = ExecutionOutcome(
            task_id="test_001",
            success=True,
            failure_mode=None,
            execution_time=1.5
        )

        # Convert to dict to check structure
        data = outcome.__dict__
        assert "task_id" in data
        assert "success" in data
        assert "failure_mode" in data
        assert "execution_time" in data

    def test_execution_outcome_serialization(self):
        """Verify ExecutionOutcome can be serialized to JSON."""
        outcome = ExecutionOutcome(
            task_id="test_002",
            success=False,
            failure_mode="Controller Execution Failure",
            execution_time=2.0
        )

        try:
            json_str = json.dumps(outcome.__dict__)
            assert "failure_mode" in json_str
        except TypeError:
            pytest.fail("ExecutionOutcome is not JSON serializable")
