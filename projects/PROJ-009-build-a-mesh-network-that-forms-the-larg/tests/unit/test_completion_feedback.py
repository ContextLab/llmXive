"""
Unit tests for T013b: completion_feedback.py

Tests the receive_task_status and update_scheduler_state functions
and the CompletionFeedbackManager class.
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
from orchestrator.models import TaskStatus, ExecutionRun

class MockExecutionRun:
    """Mock ExecutionRun for testing state updates."""
    def __init__(self):
        self.task_statuses = {}
        self.tasks = []
        self.status_updates = {}

@pytest.fixture
def manager():
    return create_feedback_manager()

@pytest.fixture
def mock_run():
    return MockExecutionRun()

def test_receive_task_status_valid(manager):
    """Test receiving a valid task status update."""
    feedback = manager.receive_task_status("node_1", "task_1", "completed")
    
    assert feedback.node_id == "node_1"
    assert feedback.task_id == "task_1"
    assert feedback.status == TaskStatusEnum.COMPLETED
    assert feedback.task_id in manager._feedback_log

def test_receive_task_status_invalid(manager):
    """Test that an invalid status raises InvalidStatusError."""
    with pytest.raises(InvalidStatusError):
        manager.receive_task_status("node_1", "task_1", "invalid_status")

def test_update_scheduler_state_completed(manager, mock_run):
    """Test updating scheduler state for a completed task."""
    # First receive the feedback
    manager.receive_task_status("node_1", "task_1", "completed")
    
    # Then update the state
    result = manager.update_scheduler_state("task_1", "completed", mock_run)
    
    assert result is True
    assert mock_run.task_statuses["task_1"] == TaskStatus.COMPLETED

def test_update_scheduler_state_failed(manager, mock_run):
    """Test updating scheduler state for a failed task."""
    manager.receive_task_status("node_2", "task_2", "failed", {"error": "timeout"})
    
    result = manager.update_scheduler_state("task_2", "failed", mock_run)
    
    assert result is True
    assert mock_run.task_statuses["task_2"] == TaskStatus.FAILED

def test_update_scheduler_state_no_run(manager):
    """Test updating state without providing an ExecutionRun (should log warning but return True)."""
    manager.receive_task_status("node_1", "task_1", "completed")
    result = manager.update_scheduler_state("task_1", "completed", None)
    assert result is True

def test_callback_registration(manager):
    """Test that callbacks are invoked on status updates."""
    callback_called = False
    received_feedback = None

    def my_callback(feedback):
        nonlocal callback_called, received_feedback
        callback_called = True
        received_feedback = feedback

    manager.register_callback(my_callback)
    manager.receive_task_status("node_1", "task_1", "running")

    assert callback_called is True
    assert received_feedback.task_id == "task_1"
    assert received_feedback.status == TaskStatusEnum.RUNNING

def test_feedback_to_dict(manager):
    """Test serialization of TaskFeedback."""
    feedback = manager.receive_task_status("node_1", "task_1", "completed", {"key": "value"})
    data = feedback.to_dict()

    assert data["node_id"] == "node_1"
    assert data["task_id"] == "task_1"
    assert data["status"] == "completed"
    assert data["details"]["key"] == "value"
    assert "timestamp" in data

def test_multiple_statuses(manager, mock_run):
    """Test updating the same task with multiple statuses."""
    manager.receive_task_status("node_1", "task_1", "running")
    manager.update_scheduler_state("task_1", "running", mock_run)
    
    assert mock_run.task_statuses["task_1"] == TaskStatus.RUNNING

    manager.receive_task_status("node_1", "task_1", "completed")
    manager.update_scheduler_state("task_1", "completed", mock_run)
    
    assert mock_run.task_statuses["task_1"] == TaskStatus.COMPLETED