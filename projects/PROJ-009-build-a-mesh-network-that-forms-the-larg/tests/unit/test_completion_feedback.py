"""
Unit tests for the Completion Feedback Module (T013b).
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from orchestrator.models import TaskStatus, ExecutionRun, TaskChunk
from orchestrator.completion_feedback import (
    CompletionFeedbackManager,
    create_feedback_manager,
    TaskFeedback,
    FeedbackError,
    StateUpdateError,
    InvalidStatusError
)


class TestTaskFeedback:
    """Tests for the TaskFeedback dataclass."""

    def test_task_feedback_creation(self):
        fb = TaskFeedback(
            node_id="node_1",
            task_id="task_1",
            status=TaskStatus.COMPLETED,
            payload={"key": "value"}
        )
        assert fb.node_id == "node_1"
        assert fb.task_id == "task_1"
        assert fb.status == TaskStatus.COMPLETED
        assert fb.payload == {"key": "value"}
        assert fb.timestamp is not None

    def test_task_feedback_to_dict(self):
        fb = TaskFeedback(
            node_id="node_1",
            task_id="task_1",
            status=TaskStatus.COMPLETED
        )
        d = fb.to_dict()
        assert d["node_id"] == "node_1"
        assert d["task_id"] == "task_1"
        assert d["status"] == "completed"
        assert "timestamp" in d


class TestCompletionFeedbackManager:
    """Tests for the CompletionFeedbackManager class."""

    @pytest.fixture
    def mock_state_accessor(self):
        run = ExecutionRun(
            run_id="run_1",
            created_at=datetime.now(timezone.utc),
            status="running",
            task_chunks=[
                TaskChunk(
                    task_id="run_1_task_1",
                    node_id="node_1",
                    status=TaskStatus.PENDING,
                    iterations=100
                )
            ]
        )
        def accessor(run_id: str):
            if run_id == "run_1":
                return run
            return None
        return accessor

    @pytest.fixture
    def mock_state_mutator(self):
        def mutator(run: ExecutionRun) -> bool:
            return True
        return mutator

    def test_init(self, mock_state_accessor, mock_state_mutator):
        manager = create_feedback_manager(mock_state_accessor, mock_state_mutator)
        assert isinstance(manager, CompletionFeedbackManager)

    def test_receive_task_status_valid(self, mock_state_accessor, mock_state_mutator):
        manager = create_feedback_manager(mock_state_accessor, mock_state_mutator)
        fb = manager.receive_task_status("node_1", "run_1_task_1", "completed")
        assert fb.node_id == "node_1"
        assert fb.task_id == "run_1_task_1"
        assert fb.status == TaskStatus.COMPLETED

    def test_receive_task_status_invalid(self, mock_state_accessor, mock_state_mutator):
        manager = create_feedback_manager(mock_state_accessor, mock_state_mutator)
        with pytest.raises(InvalidStatusError):
            manager.receive_task_status("node_1", "run_1_task_1", "zombie")

    def test_update_scheduler_state_success(self, mock_state_accessor, mock_state_mutator):
        manager = create_feedback_manager(mock_state_accessor, mock_state_mutator)
        fb = manager.receive_task_status("node_1", "run_1_task_1", "completed")
        result = manager.update_scheduler_state(fb)
        assert result is True

        # Verify the run was updated
        run = mock_state_accessor("run_1")
        assert run.task_chunks[0].status == TaskStatus.COMPLETED

    def test_update_scheduler_state_run_not_found(self, mock_state_accessor, mock_state_mutator):
        manager = create_feedback_manager(mock_state_accessor, mock_state_mutator)
        fb = manager.receive_task_status("node_1", "run_1_task_999", "completed")
        with pytest.raises(StateUpdateError):
            manager.update_scheduler_state(fb)

    def test_update_scheduler_state_task_not_found(self, mock_state_accessor, mock_state_mutator):
        manager = create_feedback_manager(mock_state_accessor, mock_state_mutator)
        fb = manager.receive_task_status("node_1", "run_1_task_999", "completed")
        with pytest.raises(StateUpdateError):
            manager.update_scheduler_state(fb)

    def test_infer_run_id(self, mock_state_accessor, mock_state_mutator):
        manager = create_feedback_manager(mock_state_accessor, mock_state_mutator)
        # Test valid pattern
        run_id = manager._infer_run_id("run_1_task_1")
        assert run_id == "run_1"
        # Test invalid pattern
        run_id = manager._infer_run_id("invalid_task_1")
        assert run_id is None

    def test_process_feedback_batch(self, mock_state_accessor, mock_state_mutator):
        manager = create_feedback_manager(mock_state_accessor, mock_state_mutator)
        fb1 = manager.receive_task_status("node_1", "run_1_task_1", "completed")
        fb2 = manager.receive_task_status("node_1", "run_1_task_1", "invalid") # Will fail on update

        results = manager.process_feedback_batch([fb1, fb2])
        assert results[0] is True
        assert results[1] is False