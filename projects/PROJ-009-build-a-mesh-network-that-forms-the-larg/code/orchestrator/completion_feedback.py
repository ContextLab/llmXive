"""
Completion Feedback Module for US1.
Handles the 'completion feedback' loop required by FR-001.
Implements receive_task_status and update_scheduler_state.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Any, Optional, Callable

from orchestrator.logger import get_logger
from orchestrator.scheduler_state import SchedulerState, StateTransitionError

# Import NodeStatus and TaskStatus from models to ensure consistency
# Note: T008 defined these, and T013d uses them in SchedulerState.
from orchestrator.models import NodeStatus, TaskStatus


class FeedbackError(Exception):
    """Base exception for feedback handling errors."""
    pass


class StateUpdateError(FeedbackError):
    """Raised when updating the scheduler state fails."""
    pass


class InvalidStatusError(FeedbackError):
    """Raised when an unknown status string is received."""
    pass


class TaskStatusEnum(Enum):
    """
    Enum representing the possible statuses a task can report back.
    Matches the logical states used in the scheduler and models.
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

    @classmethod
    def from_string(cls, status_str: str) -> TaskStatusEnum:
        """Convert a string status to the Enum value."""
        try:
            return cls(status_str.lower())
        except ValueError:
            raise InvalidStatusError(f"Unknown status string: {status_str}")


@dataclass
class TaskFeedback:
    """
    Represents a single feedback event from a node.
    """
    node_id: str
    task_id: str
    status: TaskStatusEnum
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.status, TaskStatusEnum):
            try:
                self.status = TaskStatusEnum(self.status)
            except ValueError:
                raise InvalidStatusError(f"Invalid status value: {self.status}")


class CompletionFeedbackManager:
    """
    Manages the reception of task status updates and updates the central
    SchedulerState object accordingly.
    """
    def __init__(self, scheduler_state: SchedulerState, logger: Optional[logging.Logger] = None):
        self.scheduler_state = scheduler_state
        self.logger = logger or get_logger(__name__)
        self._feedback_history: List[TaskFeedback] = []

    def receive_task_status(
        self,
        node_id: str,
        task_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TaskFeedback:
        """
        Receives a raw status string from a node, validates it, and creates
        a TaskFeedback object.
        """
        self.logger.info(f"Receiving feedback for task {task_id} on node {node_id}: {status}")

        try:
            status_enum = TaskStatusEnum.from_string(status)
        except InvalidStatusError as e:
            self.logger.error(f"Invalid status received: {e}")
            raise

        feedback = TaskFeedback(
            node_id=node_id,
            task_id=task_id,
            status=status_enum,
            metadata=metadata or {}
        )

        self._feedback_history.append(feedback)
        return feedback

    def update_scheduler_state(
        self,
        task_id: str,
        status: TaskStatusEnum,
        node_id: Optional[str] = None
    ) -> None:
        """
        Updates the central SchedulerState based on the task completion status.
        This is the core logic for FR-001 feedback loop.
        """
        self.logger.debug(f"Updating state for task {task_id} to {status.value}")

        try:
            # Map our internal TaskStatusEnum to the SchedulerState expected inputs
            # The SchedulerState (T013d) expects specific transitions.
            # We assume the SchedulerState has a method like `update_task_status`
            # or we trigger a state transition based on the task result.

            # If the task is completed successfully, mark it as such in the state.
            # If failed/timeout, mark as failed.
            # The SchedulerState object is thread-safe as per T013d spec.

            if status == TaskStatusEnum.COMPLETED:
                self.scheduler_state.handle_task_completion(task_id, node_id)
            elif status in (TaskStatusEnum.FAILED, TaskStatusEnum.TIMEOUT):
                self.scheduler_state.handle_task_failure(task_id, node_id)
            elif status == TaskStatusEnum.CANCELLED:
                self.scheduler_state.handle_task_cancelled(task_id, node_id)
            elif status == TaskStatusEnum.RUNNING:
                # Ensure the state knows the task is active
                self.scheduler_state.handle_task_started(task_id, node_id)
            else:
                self.logger.warning(f"Status {status.value} does not trigger a state update.")

        except StateTransitionError as e:
            self.logger.error(f"Failed to update scheduler state: {e}")
            raise StateUpdateError(f"State update failed for task {task_id}: {e}") from e
        except AttributeError as e:
            # This should not happen if T013d is implemented correctly
            self.logger.critical(f"SchedulerState missing expected method: {e}")
            raise StateUpdateError(f"SchedulerState interface mismatch: {e}") from e

    def get_feedback_history(self) -> List[TaskFeedback]:
        """Returns the list of all received feedback events."""
        return self._feedback_history


def create_feedback_manager(scheduler_state: SchedulerState) -> CompletionFeedbackManager:
    """Factory function to create a CompletionFeedbackManager."""
    return CompletionFeedbackManager(scheduler_state)


def main():
    """
    Main entry point for testing the completion feedback loop.
    Simulates receiving feedback and updating state.
    """
    # Mock scheduler state for standalone testing
    # In real usage, this would be the actual instance from T013d
    class MockSchedulerState:
        def __init__(self):
            self.tasks: Dict[str, str] = {}

        def handle_task_completion(self, task_id: str, node_id: Optional[str] = None):
            self.tasks[task_id] = "COMPLETED"
            print(f"[MOCK STATE] Task {task_id} marked COMPLETED on {node_id}")

        def handle_task_failure(self, task_id: str, node_id: Optional[str] = None):
            self.tasks[task_id] = "FAILED"
            print(f"[MOCK STATE] Task {task_id} marked FAILED on {node_id}")

        def handle_task_cancelled(self, task_id: str, node_id: Optional[str] = None):
            self.tasks[task_id] = "CANCELLED"
            print(f"[MOCK STATE] Task {task_id} marked CANCELLED on {node_id}")

        def handle_task_started(self, task_id: str, node_id: Optional[str] = None):
            self.tasks[task_id] = "RUNNING"
            print(f"[MOCK STATE] Task {task_id} marked RUNNING on {node_id}")

    mock_state = MockSchedulerState()
    manager = create_feedback_manager(mock_state)

    # Simulate receiving feedback
    try:
        fb1 = manager.receive_task_status("node-1", "task-101", "running")
        manager.update_scheduler_state("task-101", fb1.status)

        fb2 = manager.receive_task_status("node-1", "task-101", "completed")
        manager.update_scheduler_state("task-101", fb2.status)

        fb3 = manager.receive_task_status("node-2", "task-102", "failed")
        manager.update_scheduler_state("task-102", fb3.status)

        print("\nFeedback History:")
        for fb in manager.get_feedback_history():
            print(f"  Node: {fb.node_id}, Task: {fb.task_id}, Status: {fb.status.value}")

        print("\nFinal State:")
        for tid, state in mock_state.tasks.items():
            print(f"  {tid}: {state}")

    except Exception as e:
        print(f"Error during feedback simulation: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
