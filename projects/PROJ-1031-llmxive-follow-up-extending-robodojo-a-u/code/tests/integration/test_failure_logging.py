"""
Integration test for failure mode logging in executor.
"""
import pytest
import sys
from pathlib import Path
import tempfile
import json

# Ensure src is importable
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.executor import ExecutionOutcome, Executor
from src.state_mapper import SymbolicState


class TestFailureLoggingIntegration:
    """Integration tests for failure logging."""

    def test_failure_mode_logged(self):
        """Verify that failure modes are correctly recorded in outcomes."""
        outcome_success = ExecutionOutcome(
            task_id="log_test_001",
            success=True,
            failure_mode=None,
            execution_time=1.0
        )

        outcome_fail = ExecutionOutcome(
            task_id="log_test_002",
            success=False,
            failure_mode="Planner Infeasibility",
            execution_time=0.5
        )

        # Verify serialization
        data_success = outcome_success.__dict__
        data_fail = outcome_fail.__dict__

        assert data_success["failure_mode"] is None
        assert data_fail["failure_mode"] == "Planner Infeasibility"
        assert data_fail["success"] is False
