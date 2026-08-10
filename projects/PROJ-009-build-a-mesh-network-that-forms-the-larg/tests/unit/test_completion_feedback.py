"""
Unit tests for the Completion Feedback Module (T013b).
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from orchestrator.completion_feedback import (
    CompletionFeedbackManager,
    TaskStatusEnum,
    FeedbackError,
    StateUpdateError,
    InvalidStatusError,
    create_feedback_manager,
    TaskFeedback
)


class MockSchedulerState:
    """Mock scheduler state for testing."""
    def __init__(self):
        self.tasks = {}
        self.update_log = []

    def update_task_status(self, task_id: str, status: str, node_id: str = None):
        self.tasks[task_id] = {
            'status': status,
            'node_id': node_id,
            'updated_at': datetime.now(timezone.utc)
        }
        self.update_log.append({
            'task_id': task_id,
            'status': status,
            'node_id': node_id
        })


class TestCompletionFeedbackManager:
    """Tests for CompletionFeedbackManager class."""

    def test_receive_task_status_completed(self):
        """Test receiving a completed task status."""
        mock_state = MockSchedulerState()
        manager = CompletionFeedbackManager(scheduler_state=mock_state)

        feedback = manager.receive_task_status("node_01", "task_101", "completed")

        assert feedback.node_id == "node_01"
        assert feedback.task_id == "task_101"
        assert feedback.status == TaskStatusEnum.COMPLETED
        assert feedback.details is None

        # Verify state was updated
        assert "task_101" in mock_state.tasks
        assert mock_state.tasks["task_101"]["status"] == "completed"
        assert mock_state.tasks["task_101"]["node_id"] == "node_01"

    def test_receive_task_status_failed(self):
        """Test receiving a failed task status."""
        mock_state = MockSchedulerState()
        manager = CompletionFeedbackManager(scheduler_state=mock_state)

        feedback = manager.receive_task_status("node_02", "task_102", "failed")

        assert feedback.status == TaskStatusEnum.FAILED
        assert mock_state.tasks["task_102"]["status"] == "failed"

    def test_receive_task_status_timeout(self):
        """Test receiving a timeout task status."""
        mock_state = MockSchedulerState()
        manager = CompletionFeedbackManager(scheduler_state=mock_state)

        feedback = manager.receive_task_status("node_03", "task_103", "timeout")

        assert feedback.status == TaskStatusEnum.TIMEOUT

    def test_receive_task_status_oom(self):
        """Test receiving an OOM task status."""
        mock_state = MockSchedulerState()
        manager = CompletionFeedbackManager(scheduler_state=mock_state)

        feedback = manager.receive_task_status("node_04", "task_104", "oom")

        assert feedback.status == TaskStatusEnum.OOM

    def test_receive_task_status_invalid(self):
        """Test receiving an invalid status raises InvalidStatusError."""
        mock_state = MockSchedulerState()
        manager = CompletionFeedbackManager(scheduler_state=mock_state)

        with pytest.raises(InvalidStatusError) as exc_info:
            manager.receive_task_status("node_05", "task_105", "invalid_status")

        assert "Invalid status" in str(exc_info.value)
        assert "invalid_status" in str(exc_info.value)

    def test_update_scheduler_state_no_manager(self):
        """Test update_scheduler_state when manager is None."""
        manager = CompletionFeedbackManager(scheduler_state=None)
        
        # Should not raise, just log warning
        manager.update_scheduler_state("task_999", TaskStatusEnum.COMPLETED, "node_01")
        
        # Verify no state was updated (since there was none)
        assert len(manager._pending_feedbacks) == 0 # Wait, receive_task_status isn't called here
        # But the method itself shouldn't crash

    def test_update_scheduler_state_with_custom_update(self):
        """Test update_scheduler_state with a custom update method."""
        mock_state = MagicMock()
        mock_state.update_task_status = MagicMock()
        
        manager = CompletionFeedbackManager(scheduler_state=mock_state)
        
        manager.update_scheduler_state("task_123", TaskStatusEnum.RUNNING, "node_01")
        
        mock_state.update_task_status.assert_called_once_with("task_123", "running", "node_01")

    def test_get_heartbeat_status_alive(self):
        """Test heartbeat status when node is alive."""
        mock_state = MockSchedulerState()
        manager = CompletionFeedbackManager(scheduler_state=mock_state)
        
        # Receive a status to set heartbeat
        manager.receive_task_status("node_01", "task_101", "running")
        
        # Check immediately
        assert manager.get_heartbeat_status("node_01", timeout_seconds=60.0) is True

    def test_get_heartbeat_status_dead(self):
        """Test heartbeat status when node is dead (timeout exceeded)."""
        mock_state = MockSchedulerState()
        manager = CompletionFeedbackManager(scheduler_state=mock_state)
        
        # Manually set an old heartbeat time
        manager._heartbeat_times["node_01"] = datetime.now(timezone.utc) - timedelta(seconds=120)
        
        # Check with 60s timeout
        assert manager.get_heartbeat_status("node_01", timeout_seconds=60.0) is False

    def test_get_heartbeat_status_never_heartbeat(self):
        """Test heartbeat status when node has never sent a heartbeat."""
        mock_state = MockSchedulerState()
        manager = CompletionFeedbackManager(scheduler_state=mock_state)
        
        assert manager.get_heartbeat_status("node_01", timeout_seconds=60.0) is False

    def test_process_pending_feedbacks(self):
        """Test processing pending feedbacks."""
        mock_state = MockSchedulerState()
        manager = CompletionFeedbackManager(scheduler_state=mock_state)
        
        # Receive multiple statuses without immediate update (if logic allowed)
        # In current implementation, receive_task_status updates immediately if state exists.
        # But let's test the queue mechanism if we bypassed immediate update or if we add logic.
        # For now, we test that the list is cleared.
        
        manager.receive_task_status("node_01", "task_101", "completed")
        manager.receive_task_status("node_02", "task_102", "completed")
        
        # The list might be empty if immediate update clears it, but let's check the method
        # In current code, _pending_feedbacks is appended to in receive_task_status
        # and cleared in process_pending_feedbacks.
        # Wait, receive_task_status does NOT clear _pending_feedbacks.
        # So we should have 2 items.
        
        assert len(manager._pending_feedbacks) == 2
        
        count = manager.process_pending_feedbacks()
        
        assert count == 2
        assert len(manager._pending_feedbacks) == 0

    def test_create_feedback_manager_factory(self):
        """Test the factory function."""
        mock_state = MockSchedulerState()
        manager = create_feedback_manager(scheduler_state=mock_state)
        
        assert isinstance(manager, CompletionFeedbackManager)
        assert manager.scheduler_state is mock_state

    def test_task_feedback_creation(self):
        """Test TaskFeedback dataclass creation."""
        fb = TaskFeedback(
            node_id="node_01",
            task_id="task_101",
            status=TaskStatusEnum.COMPLETED,
            details={"result": 3.14}
        )
        
        assert fb.node_id == "node_01"
        assert fb.task_id == "task_101"
        assert fb.status == TaskStatusEnum.COMPLETED
        assert fb.details == {"result": 3.14}
        assert isinstance(fb.timestamp, datetime)