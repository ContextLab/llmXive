import pytest
import sys
from pathlib import Path
import tempfile
import json
import os
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from executor import ExecutionOutcome, Executor, RobotController

class TestFailureLoggingIntegration:
    @pytest.fixture
    def temp_log_path(self, tmp_path):
        """Create a temporary log file path."""
        log_dir = tmp_path / "data" / "interim"
        log_dir.mkdir(parents=True, exist_ok=True)
        return str(log_dir / "execution_logs.parquet")

    @pytest.fixture
    def mock_controller(self):
        """Create a mock robot controller."""
        controller = RobotController()
        controller.connected = True
        return controller

    def test_failure_mode_planner_infeasibility(self, temp_log_path, mock_controller):
        """Test that Planner Infeasibility is correctly logged."""
        executor = Executor(mock_controller)
        executor.execution_logs_path = temp_log_path

        # Simulate a planner infeasibility failure
        outcome = ExecutionOutcome(
            task_id="task_001",
            success=False,
            failure_mode="Planner Infeasibility",
            timestamp="2024-01-01T00:00:00"
        )
        executor._log_outcome(outcome)

        # Verify the log file was created and contains the correct data
        assert os.path.exists(temp_log_path)
        df = pd.read_parquet(temp_log_path)

        assert len(df) == 1
        assert df.iloc[0]["task_id"] == "task_001"
        assert df.iloc[0]["success"] == False
        assert df.iloc[0]["failure_mode"] == "Planner Infeasibility"

    def test_failure_mode_controller_execution_failure(self, temp_log_path, mock_controller):
        """Test that Controller Execution Failure is correctly logged."""
        executor = Executor(mock_controller)
        executor.execution_logs_path = temp_log_path

        outcome = ExecutionOutcome(
            task_id="task_002",
            success=False,
            failure_mode="Controller Execution Failure",
            timestamp="2024-01-01T00:00:01"
        )
        executor._log_outcome(outcome)

        assert os.path.exists(temp_log_path)
        df = pd.read_parquet(temp_log_path)

        assert len(df) == 1
        assert df.iloc[0]["failure_mode"] == "Controller Execution Failure"

    def test_multiple_outcomes_logged(self, temp_log_path, mock_controller):
        """Test that multiple outcomes can be logged to the same file."""
        executor = Executor(mock_controller)
        executor.execution_logs_path = temp_log_path

        outcomes = [
            ExecutionOutcome(
                task_id="task_001",
                success=False,
                failure_mode="Planner Infeasibility",
                timestamp="2024-01-01T00:00:00"
            ),
            ExecutionOutcome(
                task_id="task_002",
                success=True,
                failure_mode=None,
                timestamp="2024-01-01T00:00:01"
            ),
            ExecutionOutcome(
                task_id="task_003",
                success=False,
                failure_mode="Controller Execution Failure",
                timestamp="2024-01-01T00:00:02"
            )
        ]

        for outcome in outcomes:
            executor._log_outcome(outcome)

        assert os.path.exists(temp_log_path)
        df = pd.read_parquet(temp_log_path)

        assert len(df) == 3
        assert list(df["task_id"]) == ["task_001", "task_002", "task_003"]
        assert list(df["failure_mode"]) == [
            "Planner Infeasibility",
            None,
            "Controller Execution Failure"
        ]

    def test_schema_compliance(self, temp_log_path, mock_controller):
        """Test that logged data complies with ExecutionOutcome schema."""
        executor = Executor(mock_controller)
        executor.execution_logs_path = temp_log_path

        outcome = ExecutionOutcome(
            task_id="task_schema_test",
            success=False,
            failure_mode="Planner Infeasibility",
            timestamp="2024-01-01T00:00:00"
        )
        executor._log_outcome(outcome)

        df = pd.read_parquet(temp_log_path)
        expected_columns = [
            "task_id", "success", "failure_mode", "timestamp",
            "replan_attempted", "replan_success"
        ]

        assert all(col in df.columns for col in expected_columns)
        assert df["task_id"].dtype == object
        assert df["success"].dtype == bool
        assert df["failure_mode"].dtype == object  # Can be null
        assert df["timestamp"].dtype == object

    def test_log_file_persistence(self, temp_log_path, mock_controller):
        """Test that log file persists across multiple executions."""
        executor = Executor(mock_controller)
        executor.execution_logs_path = temp_log_path

        # First execution
        outcome1 = ExecutionOutcome(
            task_id="task_persist_1",
            success=False,
            failure_mode="Planner Infeasibility",
            timestamp="2024-01-01T00:00:00"
        )
        executor._log_outcome(outcome1)

        # Second execution with new executor instance
        executor2 = Executor(mock_controller)
        executor2.execution_logs_path = temp_log_path

        outcome2 = ExecutionOutcome(
            task_id="task_persist_2",
            success=True,
            failure_mode=None,
            timestamp="2024-01-01T00:00:01"
        )
        executor2._log_outcome(outcome2)

        df = pd.read_parquet(temp_log_path)
        assert len(df) == 2
        assert "task_persist_1" in df["task_id"].values
        assert "task_persist_2" in df["task_id"].values