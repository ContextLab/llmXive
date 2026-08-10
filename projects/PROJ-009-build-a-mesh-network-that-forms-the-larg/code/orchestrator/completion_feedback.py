"""
Completion Feedback Module for Mesh Network Orchestrator.

Handles the 'completion feedback' loop required by FR-001.
Implements runtime heartbeat monitoring and state updates for the SchedulerState.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Any, Optional, Callable

from orchestrator.logger import get_logger
from orchestrator.models import TaskStatus, PhysicalNode, TaskChunk, ExecutionRun

logger = get_logger(__name__)


class FeedbackError(Exception):
    """Base exception for feedback loop errors."""
    pass


class StateUpdateError(FeedbackError):
    """Raised when scheduler state update fails."""
    pass


class InvalidStatusError(FeedbackError):
    """Raised when an invalid task status is received."""
    pass


class TaskStatusEnum(Enum):
    """Enumeration of possible task statuses for feedback."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    OOM = "oom"
    REASSIGNED = "reassigned"


@dataclass
class TaskFeedback:
    """Container for a single task status update."""
    node_id: str
    task_id: str
    status: TaskStatusEnum
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: Optional[Dict[str, Any]] = None


class CompletionFeedbackManager:
    """
    Manages the receipt of task status updates and updates the central scheduler state.

    This class implements the 'completion feedback' loop required by FR-001.
    It interacts with the SchedulerState object (defined in T008) to update
    task statuses and track runtime heartbeat monitoring.
    """

    def __init__(self, scheduler_state: Optional[Any] = None):
        """
        Initialize the feedback manager.

        Args:
            scheduler_state: The central SchedulerState object to update.
                             If None, a mock state is used for testing.
        """
        self.scheduler_state = scheduler_state
        self._pending_feedbacks: List[TaskFeedback] = []
        self._heartbeat_times: Dict[str, datetime] = {}  # node_id -> last_heartbeat
        self.logger = get_logger(__name__)

    def receive_task_status(
        self,
        node_id: str,
        task_id: str,
        status: str
    ) -> TaskFeedback:
        """
        Receive a task status update from a node.

        This function is the primary entry point for the completion feedback loop.
        It validates the status, updates the heartbeat for the node, and creates
        a feedback record.

        Args:
            node_id: The unique identifier of the node sending the update.
            task_id: The unique identifier of the task being reported on.
            status: The status string (e.g., 'completed', 'failed', 'running').

        Returns:
            TaskFeedback: The created feedback object.

        Raises:
            InvalidStatusError: If the status string is not recognized.
        """
        try:
            status_enum = TaskStatusEnum(status.lower())
        except ValueError:
            raise InvalidStatusError(
                f"Invalid status '{status}' received for task {task_id} on node {node_id}. "
                f"Valid statuses: {[s.value for s in TaskStatusEnum]}"
            )

        feedback = TaskFeedback(
            node_id=node_id,
            task_id=task_id,
            status=status_enum
        )

        # Update heartbeat for the node
        self._heartbeat_times[node_id] = datetime.now(timezone.utc)

        # Log the event
        self.logger.info(
            f"Received task status update: node={node_id}, task={task_id}, status={status_enum.value}"
        )

        # Store in pending list for batch processing or immediate update
        self._pending_feedbacks.append(feedback)

        # Immediately update the scheduler state if available
        if self.scheduler_state is not None:
            self.update_scheduler_state(task_id, status_enum, node_id)

        return feedback

    def update_scheduler_state(
        self,
        task_id: str,
        status: TaskStatusEnum,
        node_id: Optional[str] = None
    ) -> None:
        """
        Update the central scheduler state with the new task status.

        This method modifies the SchedulerState object (from T008) to reflect
        the completion, failure, or other state changes of a task.

        Args:
            task_id: The unique identifier of the task.
            status: The new status of the task.
            node_id: Optional node ID if the status came from a specific node.

        Raises:
            StateUpdateError: If the state update fails.
        """
        if self.scheduler_state is None:
            self.logger.warning(
                "Scheduler state is not set. Cannot update state for task %s",
                task_id
            )
            return

        try:
            # Map our TaskStatusEnum to the model's TaskStatus if needed
            # Assuming the model uses string representations or compatible enums
            model_status = status.value

            # Update the task in the scheduler state
            # This assumes the scheduler_state has a method like update_task_status
            # or a direct attribute access pattern. We implement a generic update here.
            if hasattr(self.scheduler_state, 'update_task_status'):
                self.scheduler_state.update_task_status(task_id, model_status, node_id)
            elif hasattr(self.scheduler_state, 'tasks'):
                # Fallback: direct attribute access if structure is known
                if task_id in self.scheduler_state.tasks:
                    self.scheduler_state.tasks[task_id]['status'] = model_status
                    if node_id:
                        self.scheduler_state.tasks[task_id]['node_id'] = node_id
                    self.scheduler_state.tasks[task_id]['completed_at'] = datetime.now(timezone.utc)
                else:
                    self.logger.warning(f"Task {task_id} not found in scheduler state.")
            else:
                # Generic update attempt
                setattr(self.scheduler_state, 'last_status_update', {
                    'task_id': task_id,
                    'status': model_status,
                    'node_id': node_id,
                    'timestamp': datetime.now(timezone.utc)
                })

            self.logger.debug(
                f"Scheduler state updated: task={task_id}, status={model_status}"
            )

        except Exception as e:
            self.logger.error(
                f"Failed to update scheduler state for task {task_id}: {e}"
            )
            raise StateUpdateError(f"State update failed for task {task_id}: {e}") from e

    def get_heartbeat_status(self, node_id: str, timeout_seconds: float = 60.0) -> bool:
        """
        Check if a node has sent a heartbeat within the timeout window.

        Args:
            node_id: The node to check.
            timeout_seconds: Maximum time since last heartbeat to be considered 'alive'.

        Returns:
            bool: True if heartbeat is recent, False otherwise.
        """
        if node_id not in self._heartbeat_times:
            return False

        last_heartbeat = self._heartbeat_times[node_id]
        now = datetime.now(timezone.utc)
        elapsed = (now - last_heartbeat).total_seconds()

        return elapsed <= timeout_seconds

    def process_pending_feedbacks(self) -> int:
        """
        Process all pending feedbacks and clear the queue.

        Returns:
            int: Number of feedbacks processed.
        """
        count = len(self._pending_feedbacks)
        for fb in self._pending_feedbacks:
            # Ensure state is updated if not done in receive_task_status
            if self.scheduler_state is not None:
                self.update_scheduler_state(fb.task_id, fb.status, fb.node_id)
        
        self._pending_feedbacks.clear()
        return count


def create_feedback_manager(
    scheduler_state: Optional[Any] = None
) -> CompletionFeedbackManager:
    """
    Factory function to create a CompletionFeedbackManager instance.

    Args:
        scheduler_state: The central scheduler state object to update.

    Returns:
        CompletionFeedbackManager: Configured manager instance.
    """
    return CompletionFeedbackManager(scheduler_state=scheduler_state)


def main() -> None:
    """
    Main entry point for testing the completion feedback module.
    Simulates receiving task statuses and updating the scheduler state.
    """
    logger = get_logger(__name__)
    logger.info("Starting Completion Feedback Manager test...")

    # Create a mock scheduler state for testing
    class MockSchedulerState:
        def __init__(self):
            self.tasks = {}
            self.update_log = []

        def update_task_status(self, task_id: str, status: str, node_id: Optional[str] = None):
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
            logger.info(f"Mock State Updated: Task {task_id} -> {status} on {node_id}")

    mock_state = MockSchedulerState()
    manager = create_feedback_manager(scheduler_state=mock_state)

    # Simulate receiving task statuses
    test_cases = [
        ("node_01", "task_101", "completed"),
        ("node_02", "task_102", "running"),
        ("node_01", "task_103", "failed"),
        ("node_03", "task_104", "timeout"),
        ("node_02", "task_105", "invalid_status"), # Should raise error
    ]

    for node_id, task_id, status in test_cases:
        try:
            feedback = manager.receive_task_status(node_id, task_id, status)
            logger.info(f"Feedback received: {feedback}")
            
            # Check heartbeat
            is_alive = manager.get_heartbeat_status(node_id, timeout_seconds=10.0)
            logger.info(f"Node {node_id} heartbeat status: {is_alive}")
            
        except InvalidStatusError as e:
            logger.error(f"Invalid status error (expected): {e}")
        except StateUpdateError as e:
            logger.error(f"State update error: {e}")

    # Process any remaining pending feedbacks
    processed = manager.process_pending_feedbacks()
    logger.info(f"Processed {processed} pending feedbacks.")

    logger.info("Completion Feedback Manager test completed.")


if __name__ == "__main__":
    main()
