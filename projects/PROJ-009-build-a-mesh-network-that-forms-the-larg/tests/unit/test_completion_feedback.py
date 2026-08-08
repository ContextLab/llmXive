"""
Unit tests for CompletionFeedbackManager (T013b).

Tests the feedback loop logic: receiving status, validating enums, and updating state.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from orchestrator.completion_feedback import (
    CompletionFeedbackManager,
    TaskFeedback,
    FeedbackError,
    StateUpdateError,
    InvalidStatusError,
    create_feedback_manager
)
from orchestrator.models import TaskStatus
from orchestrator.node_manager import NodeManager


class TestTaskFeedback:
    """Tests for the TaskFeedback dataclass."""

    def test_creation(self):
        feedback = TaskFeedback(
            node_id="node_1",
            task_id="task_123",
            status=TaskStatus.COMPLETED,
            timestamp=datetime.now(timezone.utc)
        )
        assert feedback.node_id == "node_1"
        assert feedback.task_id == "task_123"
        assert feedback.status == TaskStatus.COMPLETED
        assert feedback.timestamp.tzinfo == timezone.utc

    def test_timestamp_default_utc(self):
        # Test that if we didn't set tzinfo, it would be handled, 
        # but here we explicitly pass it.
        dt = datetime.now(timezone.utc)
        feedback = TaskFeedback(
            node_id="node_1",
            task_id="task_123",
            status=TaskStatus.RUNNING,
            timestamp=dt
        )
        assert feedback.timestamp == dt


class TestCompletionFeedbackManager:
    """Tests for the CompletionFeedbackManager class."""

    @pytest.fixture
    def mock_node_manager(self):
        """Create a mock NodeManager."""
        mock = MagicMock(spec=NodeManager)
        mock.is_node_registered.return_value = True
        return mock

    @pytest.fixture
    def manager(self, mock_node_manager):
        """Create a FeedbackManager with the mock node manager."""
        return CompletionFeedbackManager(mock_node_manager)

    def test_init_with_none_node_manager(self):
        with pytest.raises(ValueError, match="node_manager cannot be None"):
            CompletionFeedbackManager(None)

    def test_receive_task_status_valid(self, manager):
        feedback = manager.receive_task_status("node_1", "task_1", "COMPLETED")
        
        assert feedback.node_id == "node_1"
        assert feedback.task_id == "task_1"
        assert feedback.status == TaskStatus.COMPLETED
        assert len(manager.get_feedback_history()) == 1

    def test_receive_task_status_case_insensitive(self, manager):
        # Test that "completed" works same as "COMPLETED"
        feedback = manager.receive_task_status("node_1", "task_1", "completed")
        assert feedback.status == TaskStatus.COMPLETED

    def test_receive_task_status_invalid(self, manager):
        with pytest.raises(InvalidStatusError):
            manager.receive_task_status("node_1", "task_1", "INVALID_STATUS")

    def test_update_scheduler_state_no_callbacks(self, manager):
        # No callbacks registered
        result = manager.update_scheduler_state("task_1", TaskStatus.COMPLETED)
        assert result is False

    def test_update_scheduler_state_success(self, manager):
        # Register a mock callback
        mock_callback = MagicMock()
        manager.register_state_callback(mock_callback)

        result = manager.update_scheduler_state("task_1", TaskStatus.COMPLETED)
        
        assert result is True
        mock_callback.assert_called_once_with("task_1", TaskStatus.COMPLETED)

    def test_update_scheduler_state_failure(self, manager):
        # Register a callback that raises an exception
        def failing_callback(task_id, status):
            raise RuntimeError("Update failed")
        
        manager.register_state_callback(failing_callback)

        with pytest.raises(StateUpdateError):
            manager.update_scheduler_state("task_1", TaskStatus.COMPLETED)

    def test_process_feedback(self, manager):
        mock_callback = MagicMock()
        manager.register_state_callback(mock_callback)

        manager.process_feedback("node_1", "task_1", "COMPLETED")

        # Verify feedback was logged
        assert len(manager.get_feedback_history()) == 1
        # Verify callback was called
        mock_callback.assert_called_once_with("task_1", TaskStatus.COMPLETED)

    def test_process_feedback_invalid_status(self, manager):
        with pytest.raises(InvalidStatusError):
            manager.process_feedback("node_1", "task_1", "BAD_STATUS")

    def test_register_multiple_callbacks(self, manager):
        cb1 = MagicMock()
        cb2 = MagicMock()
        manager.register_state_callback(cb1)
        manager.register_state_callback(cb2)

        manager.update_scheduler_state("task_1", TaskStatus.RUNNING)

        cb1.assert_called_once_with("task_1", TaskStatus.RUNNING)
        cb2.assert_called_once_with("task_1", TaskStatus.RUNNING)


class TestFactoryFunction:
    """Tests for create_feedback_manager."""

    def test_create_feedback_manager(self):
        mock_nm = MagicMock(spec=NodeManager)
        fm = create_feedback_manager(mock_nm)
        
        assert isinstance(fm, CompletionFeedbackManager)
        assert fm.node_manager == mock_nm