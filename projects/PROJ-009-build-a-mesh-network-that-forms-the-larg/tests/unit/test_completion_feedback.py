"""
Unit Tests for completion_feedback.py (T013b)
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from orchestrator.completion_feedback import (
    CompletionFeedbackManager,
    TaskFeedback,
    TaskStatusEnum,
    FeedbackError,
    StateUpdateError,
    InvalidStatusError,
    create_feedback_manager,
)
from orchestrator.scheduler_state import (
    SchedulerState,
    TaskStatusEvent,
    SchedulerStateError,
    create_scheduler_state,
)


class TestTaskFeedback:
    def test_valid_status_string(self):
        fb = TaskFeedback(
            node_id="n1",
            task_id="t1",
            status="completed"
        )
        assert fb.status == TaskStatusEnum.COMPLETED

    def test_valid_status_enum(self):
        fb = TaskFeedback(
            node_id="n1",
            task_id="t1",
            status=TaskStatusEnum.FAILED
        )
        assert fb.status == TaskStatusEnum.FAILED

    def test_invalid_status_string(self):
        with pytest.raises(InvalidStatusError):
            TaskFeedback(
                node_id="n1",
                task_id="t1",
                status="unknown_status"
            )

    def test_timestamp_default(self):
        fb = TaskFeedback(
            node_id="n1",
            task_id="t1",
            status="pending"
        )
        assert isinstance(fb.timestamp, datetime)
        assert fb.timestamp.tzinfo == timezone.utc


class TestCompletionFeedbackManager:
    @pytest.fixture
    def mock_state(self):
        return create_scheduler_state()

    @pytest.fixture
    def manager(self, mock_state):
        return create_feedback_manager(mock_state)

    def test_init(self, mock_state):
        mgr = CompletionFeedbackManager(mock_state)
        assert mgr.state is mock_state
        assert len(mgr.get_history()) == 0

    def test_receive_task_status_success(self, manager):
        fb = manager.receive_task_status(
            node_id="node-1",
            task_id="task-1",
            status="running",
            details={"progress": 0.5}
        )
        assert fb.node_id == "node-1"
        assert fb.task_id == "task-1"
        assert fb.status == TaskStatusEnum.RUNNING
        assert fb.details == {"progress": 0.5}
        assert len(manager.get_history()) == 1

    def test_update_scheduler_state_success(self, manager):
        fb = manager.receive_task_status(
            node_id="node-1",
            task_id="task-1",
            status="completed"
        )
        result = manager.update_scheduler_state(fb)
        assert result is True
        # Verify state transition occurred (assuming IDLE -> RUNNING -> COMPLETED logic in state)
        # The exact state depends on the state machine logic in T013d
        # Here we just verify no exception was raised

    def test_update_scheduler_state_failure(self, manager):
        fb = manager.receive_task_status(
            node_id="node-1",
            task_id="task-1",
            status="completed"
        )
        # Mock the state to raise an error
        with patch.object(manager.state, 'handle_task_status_update', side_effect=SchedulerStateError("Simulated error")):
            with pytest.raises(StateUpdateError):
                manager.update_scheduler_state(fb)

    def test_process_feedback_loop(self, manager):
        fb1 = TaskFeedback(node_id="n1", task_id="t1", status="completed")
        fb2 = TaskFeedback(node_id="n2", task_id="t2", status="failed")
        result = manager.process_feedback_loop([fb1, fb2])
        assert len(result) == 2
        assert len(manager.get_history()) == 2

    def test_receive_invalid_status(self, manager):
        with pytest.raises(InvalidStatusError):
            manager.receive_task_status(
                node_id="n1",
                task_id="t1",
                status="invalid_status_string"
            )

    def test_factory_function(self, mock_state):
        mgr = create_feedback_manager(mock_state)
        assert isinstance(mgr, CompletionFeedbackManager)