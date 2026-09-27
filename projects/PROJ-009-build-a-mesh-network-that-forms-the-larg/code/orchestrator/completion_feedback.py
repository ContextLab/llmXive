"""
Completion Feedback Module (T013b)
Handles the 'completion feedback' loop required by FR-001.
Implements receive_task_status and update_scheduler_state to update
the SchedulerState object defined in T013d.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Any, Optional, Callable

from orchestrator.scheduler_state import (
    SchedulerState,
    TaskStatusEvent,
    SchedulerStateError,
)
from orchestrator.logger import get_logger

logger = get_logger(__name__)


class FeedbackError(Exception):
    """Base exception for feedback processing errors."""
    pass


class StateUpdateError(FeedbackError):
    """Raised when updating the scheduler state fails."""
    pass


class InvalidStatusError(FeedbackError):
    """Raised when an unknown task status is received."""
    pass


class TaskStatusEnum(Enum):
    """Enumeration of valid task completion statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    OOM = "oom"
    CANCELLED = "cancelled"


@dataclass
class TaskFeedback:
    """Container for a single task status update."""
    node_id: str
    task_id: str
    status: TaskStatusEnum
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if isinstance(self.status, str):
            try:
                self.status = TaskStatusEnum(self.status)
            except ValueError:
                raise InvalidStatusError(f"Unknown status string: {self.status}")


class CompletionFeedbackManager:
    """
    Manages the reception of task status updates and the subsequent
    update of the global SchedulerState.
    """

    def __init__(self, scheduler_state: SchedulerState):
        if not isinstance(scheduler_state, SchedulerState):
            raise TypeError("scheduler_state must be an instance of SchedulerState")
        self.state = scheduler_state
        self._logger = get_logger(__name__)
        self._history: List[TaskFeedback] = []

    def receive_task_status(
        self,
        node_id: str,
        task_id: str,
        status: str | TaskStatusEnum,
        details: Optional[Dict[str, Any]] = None
    ) -> TaskFeedback:
        """
        Receives a task status update from a node.

        Args:
            node_id: The identifier of the node reporting status.
            task_id: The identifier of the task being reported on.
            status: The status string or enum value.
            details: Optional metadata (e.g., ops_per_sec, error_msg).

        Returns:
            The constructed TaskFeedback object.

        Raises:
            InvalidStatusError: If the status string is not recognized.
        """
        try:
            if isinstance(status, str):
                status_enum = TaskStatusEnum(status)
            else:
                status_enum = status
        except ValueError:
            raise InvalidStatusError(f"Invalid status received: {status}")

        feedback = TaskFeedback(
            node_id=node_id,
            task_id=task_id,
            status=status_enum,
            details=details
        )

        self._history.append(feedback)
        self._logger.info(
            f"Received feedback: Task {task_id} on Node {node_id} -> {status_enum.value}"
        )

        return feedback

    def update_scheduler_state(
        self,
        feedback: TaskFeedback
    ) -> bool:
        """
        Updates the global SchedulerState based on a received feedback event.

        This method constructs a TaskStatusEvent and delegates to the
        SchedulerState's internal handler.

        Args:
            feedback: The TaskFeedback object containing the update.

        Returns:
            True if the state was updated successfully.

        Raises:
            StateUpdateError: If the state transition is invalid or fails.
        """
        try:
            event = TaskStatusEvent(
                task_id=feedback.task_id,
                node_id=feedback.node_id,
                new_status=feedback.status,
                timestamp=feedback.timestamp,
                details=feedback.details
            )

            # Delegate to the SchedulerState defined in T013d
            self.state.handle_task_status_update(event)

            self._logger.debug(
                f"SchedulerState updated for Task {feedback.task_id} "
                f"to {feedback.status.value}"
            )
            return True

        except SchedulerStateError as e:
            self._logger.error(f"Failed to update SchedulerState: {e}")
            raise StateUpdateError(f"SchedulerState update failed: {e}") from e
        except Exception as e:
            self._logger.error(f"Unexpected error updating state: {e}")
            raise StateUpdateError(f"Unexpected error: {e}") from e

    def process_feedback_loop(
        self,
        feedback_list: List[TaskFeedback]
    ) -> List[TaskFeedback]:
        """
        Processes a batch of feedback updates sequentially.

        Args:
            feedback_list: List of TaskFeedback objects to process.

        Returns:
            List of successfully processed feedback objects.
        """
        processed = []
        for fb in feedback_list:
            try:
                self.update_scheduler_state(fb)
                processed.append(fb)
            except StateUpdateError as e:
                self._logger.warning(f"Skipping feedback due to state error: {e}")
        return processed

    def get_history(self) -> List[TaskFeedback]:
        """Returns the history of received feedback."""
        return self._history.copy()


def create_feedback_manager(scheduler_state: SchedulerState) -> CompletionFeedbackManager:
    """Factory function to create a CompletionFeedbackManager."""
    return CompletionFeedbackManager(scheduler_state)


def main():
    """
    Standalone entry point for testing the feedback loop logic.
    Simulates receiving status updates and updating the state machine.
    """
    from orchestrator.scheduler_state import create_scheduler_state

    # Initialize the state machine (T013d dependency)
    state = create_scheduler_state()
    state.transition_to("RUNNING")

    # Initialize the manager
    manager = create_feedback_manager(state)

    # Simulate receiving a completed task
    try:
        fb = manager.receive_task_status(
            node_id="node-1",
            task_id="task-101",
            status="completed",
            details={"ops_per_sec": 1500}
        )
        manager.update_scheduler_state(fb)
        print(f"State after update: {state.current_state}")

        # Simulate a failure
        fb_fail = manager.receive_task_status(
            node_id="node-2",
            task_id="task-102",
            status="failed",
            details={"error": "Timeout"}
        )
        manager.update_scheduler_state(fb_fail)
        print(f"State after failure: {state.current_state}")

    except (InvalidStatusError, StateUpdateError) as e:
        print(f"Feedback processing error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
