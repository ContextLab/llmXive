"""
Unit tests for T013b: completion_feedback.py

Tests the receive_task_status and update_scheduler_state functions
and the CompletionFeedbackManager class.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from orchestrator.completion_feedback import (
    CompletionFeedbackManager,
    TaskFeedback,
    TaskStatusEnum,
    InvalidStatusError,
    StateUpdateError,
    create_feedback_manager
)
from orchestrator.models import ExecutionRun, TaskStatus


class TestTaskStatusEnum:
    def test_valid_status(self):
        assert TaskStatusEnum("completed") == TaskStatusEnum.COMPLETED
        assert TaskStatusEnum("COMPLETED") == TaskStatusEnum.COMPLETED
        assert TaskStatusEnum("failed") == TaskStatusEnum.FAILED

    def test_invalid_status(self):
        with pytest.raises(ValueError):
            TaskStatusEnum("unknown_status")


class TestCompletionFeedbackManager:
    @pytest.fixture
    def mock_execution_run(self):
        return ExecutionRun(
            run_id="test-run-1",
            start_time=datetime.now(timezone.utc),
            end_time=None,
            status=TaskStatus.PENDING,
            task_states={}
        )

    def test_init(self, mock_execution_run):
        manager = create_feedback_manager(mock_execution_run)
        assert manager.execution_run == mock_execution_run
        assert manager._processed_feedbacks == []
        assert manager._pending_feedbacks == []

    def test_receive_task_status_success(self, mock_execution_run):
        manager = create_feedback_manager(mock_execution_run)
        
        # First call creates the task state
        feedback = manager.receive_task_status(
            node_id="10.0.0.1",
            task_id="task-1",
            status="running"
        )
        
        assert isinstance(feedback, TaskFeedback)
        assert feedback.task_id == "task-1"
        assert feedback.status == TaskStatusEnum.RUNNING
        assert feedback.node_id == "10.0.0.1"
        
        # Verify state was updated in ExecutionRun
        assert "task-1" in mock_execution_run.task_states
        assert mock_execution_run.task_states["task-1"]["status"] == TaskStatusEnum.RUNNING

    def test_receive_task_status_invalid(self, mock_execution_run):
        manager = create_feedback_manager(mock_execution_run)
        
        with pytest.raises(InvalidStatusError):
            manager.receive_task_status(
                node_id="10.0.0.1",
                task_id="task-1",
                status="invalid_status"
            )

    def test_update_scheduler_state_missing_task(self, mock_execution_run):
        manager = create_feedback_manager(mock_execution_run)
        
        # Ensure task is not in states
        if "missing-task" in mock_execution_run.task_states:
            del mock_execution_run.task_states["missing-task"]
        
        with pytest.raises(StateUpdateError):
            manager.update_scheduler_state(
                task_id="missing-task",
                status=TaskStatusEnum.RUNNING
            )

    def test_state_transitions(self, mock_execution_run):
        manager = create_feedback_manager(mock_execution_run)
        
        # 1. Pending -> Running
        manager.receive_task_status("n1", "t1", "running")
        assert mock_execution_run.task_states["t1"]["status"] == TaskStatusEnum.RUNNING
        
        # 2. Running -> Completed
        manager.receive_task_status("n1", "t1", "completed")
        assert mock_execution_run.task_states["t1"]["status"] == TaskStatusEnum.COMPLETED
        
        # 3. Verify end_time is set
        assert mock_execution_run.task_states["t1"]["end_time"] is not None

    def test_get_run_summary(self, mock_execution_run):
        manager = create_feedback_manager(mock_execution_run)
        
        manager.receive_task_status("n1", "t1", "completed")
        manager.receive_task_status("n2", "t2", "failed")
        manager.receive_task_status("n3", "t3", "running")
        
        summary = manager.get_run_summary()
        
        assert summary["total_tasks"] == 3
        assert summary["run_id"] == "test-run-1"
        assert summary["status_counts"]["completed"] == 1
        assert summary["status_counts"]["failed"] == 1
        assert summary["status_counts"]["running"] == 1

    def test_empty_states(self, mock_execution_run):
        manager = create_feedback_manager(mock_execution_run)
        summary = manager.get_run_summary()
        
        assert summary["total_tasks"] == 0
        assert all(v == 0 for v in summary["status_counts"].values())