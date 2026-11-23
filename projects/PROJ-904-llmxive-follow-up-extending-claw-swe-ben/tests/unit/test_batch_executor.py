import pytest
import time
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from experiments.batch_executor import BatchExecutor, TimeoutGuard, ExecutionStatus, BatchExecutionResult
from models.task_instance import TaskInstance
from models.context_config import ContextConfiguration
from models.execution_result import ExecutionResult

class TestBatchSubmit:
    """Tests for the BatchExecutor submit functionality."""

    def test_batch_submit_success(self):
        """Test that a successful execution returns a COMPLETED status."""
        executor = BatchExecutor(max_workers=1, instance_timeout_seconds=30)
        
        def success_func(task: TaskInstance, config: ContextConfiguration) -> ExecutionResult:
            return ExecutionResult(
                task_id=task.task_id,
                status=ExecutionStatus.COMPLETED,
                output="Success"
            )

        task = TaskInstance(task_id="test_001", problem_statement="Test problem")
        result = executor.submit(task, success_func)

        assert result.task_id == "test_001"
        assert result.status == ExecutionStatus.COMPLETED
        assert result.result is not None
        assert result.result.output == "Success"
        assert result.duration_seconds > 0
        assert result.error_message is None

        executor.shutdown()

    def test_batch_submit_timeout(self):
        """Test that a slow execution triggers a TIMEOUT status."""
        executor = BatchExecutor(max_workers=1, instance_timeout_seconds=1)
        
        def slow_func(task: TaskInstance, config: ContextConfiguration) -> ExecutionResult:
            time.sleep(5) # Sleep longer than timeout
            return ExecutionResult(task_id=task.task_id, status=ExecutionStatus.COMPLETED)

        task = TaskInstance(task_id="test_timeout", problem_statement="Slow task")
        result = executor.submit(task, slow_func)

        assert result.task_id == "test_timeout"
        assert result.status == ExecutionStatus.TIMEOUT
        assert "exceeded" in result.error_message.lower()
        assert result.result is None

        executor.shutdown()

    def test_batch_submit_exception(self):
        """Test that an exception in execution triggers a FAILED status."""
        executor = BatchExecutor(max_workers=1, instance_timeout_seconds=30)
        
        def failing_func(task: TaskInstance, config: ContextConfiguration) -> ExecutionResult:
            raise ValueError("Simulated failure")

        task = TaskInstance(task_id="test_fail", problem_statement="Failing task")
        result = executor.submit(task, failing_func)

        assert result.task_id == "test_fail"
        assert result.status == ExecutionStatus.FAILED
        assert "Simulated failure" in result.error_message
        assert result.result is None

        executor.shutdown()

    def test_batch_submit_parallel(self):
        """Test that multiple tasks can be submitted in parallel."""
        executor = BatchExecutor(max_workers=2, instance_timeout_seconds=30)
        
        def fast_func(task: TaskInstance, config: ContextConfiguration) -> ExecutionResult:
            time.sleep(0.5)
            return ExecutionResult(task_id=task.task_id, status=ExecutionStatus.COMPLETED)

        tasks = [
            TaskInstance(task_id=f"parallel_{i}", problem_statement=f"Task {i}")
            for i in range(4)
        ]

        results = executor.submit_batch(tasks, fast_func)

        assert len(results) == 4
        for r in results:
            assert r.status == ExecutionStatus.COMPLETED

        # Check that total time is roughly half of sequential time (2 workers)
        # Sequential would be ~2.0s, parallel should be ~1.0s
        executor.shutdown()

class TestTimeoutGuard:
    """Tests for the TimeoutGuard decorator."""

    def test_timeout_guard_success(self):
        """Test that a function completing within timeout succeeds."""
        guard = TimeoutGuard(timeout_seconds=5)

        @guard
        def quick_func():
            time.sleep(0.1)
            return "done"

        assert quick_func() == "done"

    def test_timeout_guard_fail(self):
        """Test that a function exceeding timeout raises TimeoutError."""
        guard = TimeoutGuard(timeout_seconds=1)

        @guard
        def slow_func():
            time.sleep(5)
            return "done"

        with pytest.raises(TimeoutError):
            slow_func()

    def test_timeout_guard_exception_propagation(self):
        """Test that exceptions within the function are propagated."""
        guard = TimeoutGuard(timeout_seconds=5)

        @guard
        def error_func():
            raise RuntimeError("Internal error")

        with pytest.raises(RuntimeError, match="Internal error"):
            error_func()
