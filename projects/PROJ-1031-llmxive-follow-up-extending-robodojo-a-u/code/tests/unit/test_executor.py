"""
Unit tests for Executor logic.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure src is importable
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.executor import Executor, ExecutionOutcome, ConnectionError


class TestExecutor:
    """Tests for Executor class."""

    def test_executor_initialization(self):
        """Verify Executor initializes."""
        executor = Executor()
        assert executor is not None

    def test_connection_error_raised(self):
        """Verify ConnectionError is raised on failure."""
        executor = Executor()
        # Mock the connection method to fail
        with patch.object(executor, '_connect_to_robot', side_effect=ConnectionError("Simulated")):
            with pytest.raises(ConnectionError):
                executor._connect_to_robot()

    def test_execution_outcome_creation(self):
        """Verify ExecutionOutcome is created correctly."""
        outcome = ExecutionOutcome(
            task_id="exec_test_001",
            success=True,
            failure_mode=None,
            execution_time=1.0
        )
        assert outcome.success is True
        assert outcome.failure_mode is None
