"""
Unit tests for completion_feedback.py (T013b).
"""
import pytest
from datetime import datetime, timezone

from orchestrator.completion_feedback import (
    CompletionFeedbackManager,
    TaskFeedback,
    TaskStatusEnum,
    InvalidStatusError,
    StateUpdateError,
    create_feedback_manager
)
from orchestrator.scheduler_state import SchedulerState


class MockSchedulerState:
    """
    Mock implementation of SchedulerState for unit testing.
    Tracks calls to verify update_scheduler_state logic.
    """
    def __init__(self):
        self.state_log = []
        self.tasks = {}

    def handle_task_completion(self, task_id: str, node_id: str = None):
        self.state_log.append(("COMPLETED", task_id, node_id))
        self.tasks[task_id] = "COMPLETED"

    def handle_task_failure(self, task_id: str, node_id: str = None):
        self.state_log.append(("FAILED", task_id, node_id))
        self.tasks[task_id] = "FAILED"

    def handle_task_cancelled(self, task_id: str, node_id: str = None):
        self.state_log.append(("CANCELLED", task_id, node_id))
        self.tasks[task_id] = "CANCELLED"

    def handle_task_started(self, task_id: str, node_id: str = None):
        self.state_log.append(("RUNNING", task_id, node_id))
        self.tasks[task_id] = "RUNNING"


@pytest.fixture
def mock_state():
    return MockSchedulerState()


@pytest.fixture
def feedback_manager(mock_state):
    return create_feedback_manager(mock_state)


def test_receive_task_status_valid(feedback_manager, mock_state):
    """Test receiving a valid status string."""
    feedback = feedback_manager.receive_task_status(
        node_id="node-1",
        task_id="task-1",
        status="completed"
    )

    assert feedback.node_id == "node-1"
    assert feedback.task_id == "task-1"
    assert feedback.status == TaskStatusEnum.COMPLETED
    assert feedback.timestamp.tzinfo == timezone.utc

    # Verify it was added to history
    history = feedback_manager.get_feedback_history()
    assert len(history) == 1
    assert history[0] == feedback


def test_receive_task_status_invalid_string(feedback_manager):
    """Test that an invalid status string raises InvalidStatusError."""
    with pytest.raises(InvalidStatusError):
        feedback_manager.receive_task_status(
            node_id="node-1",
            task_id="task-1",
            status="unknown_status"
        )


def test_update_scheduler_state_completed(feedback_manager, mock_state):
    """Test that updating state for COMPLETED calls the correct handler."""
    # First receive the feedback
    feedback = feedback_manager.receive_task_status("node-1", "task-1", "completed")

    # Then update the state
    feedback_manager.update_scheduler_state("task-1", feedback.status)

    # Verify the mock state was updated
    assert mock_state.tasks["task-1"] == "COMPLETED"
    assert ("COMPLETED", "task-1", "node-1") in mock_state.state_log


def test_update_scheduler_state_failed(feedback_manager, mock_state):
    """Test that updating state for FAILED calls the correct handler."""
    feedback = feedback_manager.receive_task_status("node-1", "task-1", "failed")
    feedback_manager.update_scheduler_state("task-1", feedback.status)

    assert mock_state.tasks["task-1"] == "FAILED"
    assert ("FAILED", "task-1", "node-1") in mock_state.state_log


def test_update_scheduler_state_timeout(feedback_manager, mock_state):
    """Test that TIMEOUT is treated as a failure."""
    feedback = feedback_manager.receive_task_status("node-1", "task-1", "timeout")
    feedback_manager.update_scheduler_state("task-1", feedback.status)

    assert mock_state.tasks["task-1"] == "FAILED"
    assert ("FAILED", "task-1", "node-1") in mock_state.state_log


def test_update_scheduler_state_running(feedback_manager, mock_state):
    """Test that RUNNING updates the state to running."""
    feedback = feedback_manager.receive_task_status("node-1", "task-1", "running")
    feedback_manager.update_scheduler_state("task-1", feedback.status)

    assert mock_state.tasks["task-1"] == "RUNNING"
    assert ("RUNNING", "task-1", "node-1") in mock_state.state_log


def test_state_update_error_propagation(feedback_manager):
    """Test that StateUpdateError is raised if the state update fails."""
    # Create a manager with a state that raises an error
    class BrokenState:
        def handle_task_completion(self, task_id, node_id=None):
            raise Exception("Intentional break")

    broken_manager = create_feedback_manager(BrokenState())
    feedback = broken_manager.receive_task_status("node-1", "task-1", "completed")

    with pytest.raises(StateUpdateError):
        broken_manager.update_scheduler_state("task-1", feedback.status)


def test_feedback_history_accumulation(feedback_manager):
    """Test that multiple feedbacks are accumulated in history."""
    feedback_manager.receive_task_status("node-1", "task-1", "running")
    feedback_manager.receive_task_status("node-1", "task-1", "completed")
    feedback_manager.receive_task_status("node-2", "task-2", "failed")

    history = feedback_manager.get_feedback_history()
    assert len(history) == 3
    assert history[0].task_id == "task-1"
    assert history[1].task_id == "task-1"
    assert history[2].task_id == "task-2"