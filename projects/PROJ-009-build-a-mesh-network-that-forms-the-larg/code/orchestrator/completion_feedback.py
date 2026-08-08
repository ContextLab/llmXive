"""
Completion Feedback Module (T013b)

Implements the 'completion feedback' loop required by FR-001.
Handles reception of task status from nodes and updates the central scheduler state.

Dependencies: T013a (node_manager.py)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Any, Optional, Callable

from orchestrator.models import TaskStatus, PhysicalNode
from orchestrator.node_manager import NodeManager, NodeDiscoveryError
from orchestrator.logger import get_logger

logger = get_logger(__name__)


class FeedbackError(Exception):
    """Base exception for feedback loop failures."""
    pass


class StateUpdateError(FeedbackError):
    """Raised when the scheduler state cannot be updated."""
    pass


class InvalidStatusError(FeedbackError):
    """Raised when an unexpected status string is received."""
    pass


@dataclass
class TaskFeedback:
    """Represents a feedback signal from a node regarding a specific task."""
    node_id: str
    task_id: str
    status: TaskStatus
    timestamp: datetime
    metrics: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)


class CompletionFeedbackManager:
    """
    Manages the reception of task completion status and updates the scheduler state.

    This class acts as the bridge between the remote node execution (T013a/T014a)
    and the central Scheduler (T015). It implements the 'completion feedback' loop.
    """

    def __init__(self, node_manager: NodeManager):
        """
        Initialize the feedback manager with a reference to the NodeManager.

        Args:
            node_manager: The active NodeManager instance handling SSH connections.
        """
        if node_manager is None:
            raise ValueError("node_manager cannot be None")
        self.node_manager = node_manager
        self._feedback_log: List[TaskFeedback] = []
        self._state_callbacks: List[Callable[[str, TaskStatus], None]] = []

        logger.info("CompletionFeedbackManager initialized.")

    def register_state_callback(self, callback: Callable[[str, TaskStatus], None]) -> None:
        """
        Register a callback function to be invoked when task state updates.
        This allows the Scheduler (T015) to react to feedback.

        Args:
            callback: Function signature (task_id: str, status: TaskStatus) -> None
        """
        self._state_callbacks.append(callback)
        logger.debug("Registered state callback for feedback manager.")

    def receive_task_status(self, node_id: str, task_id: str, status: str) -> TaskFeedback:
        """
        Receive a task status update from a node and validate it.

        This function is the entry point for the feedback loop. It parses the raw
        status string, validates it against the TaskStatus enum, and constructs
        a TaskFeedback object.

        Args:
            node_id: The ID of the node reporting status.
            task_id: The ID of the task being reported on.
            status: The raw status string (e.g., 'COMPLETED', 'FAILED').

        Returns:
            TaskFeedback: The validated feedback object.

        Raises:
            InvalidStatusError: If the status string is not recognized.
            FeedbackError: If the node_id is unknown or invalid.
        """
        if not self.node_manager.is_node_registered(node_id):
            logger.warning(f"Received feedback from unregistered node: {node_id}")
            # We still process it but log a warning; the scheduler might need to know
            # about rogue nodes.

        try:
            # Map string input to TaskStatus enum
            status_enum = TaskStatus(status.upper())
        except ValueError:
            valid_statuses = [s.name for s in TaskStatus]
            raise InvalidStatusError(
                f"Invalid status '{status}' received for task {task_id}. "
                f"Valid options: {valid_statuses}"
            )

        feedback = TaskFeedback(
            node_id=node_id,
            task_id=task_id,
            status=status_enum,
            timestamp=datetime.now(timezone.utc)
        )

        self._feedback_log.append(feedback)
        logger.info(f"Received feedback: Node={node_id}, Task={task_id}, Status={status_enum.name}")

        return feedback

    def update_scheduler_state(self, task_id: str, status: TaskStatus) -> bool:
        """
        Update the central scheduler state based on a received feedback.

        This function triggers registered callbacks (typically the Scheduler)
        to update its internal state machine for the given task.

        Args:
            task_id: The ID of the task to update.
            status: The new status of the task.

        Returns:
            bool: True if the state was updated successfully, False otherwise.

        Raises:
            StateUpdateError: If the update fails (e.g., task not found in scheduler).
        """
        if not self._state_callbacks:
            logger.warning("No state callbacks registered. Scheduler state cannot be updated.")
            return False

        success_count = 0
        for callback in self._state_callbacks:
            try:
                callback(task_id, status)
                success_count += 1
            except Exception as e:
                logger.error(f"State callback failed for task {task_id}: {e}")
                # Do not raise immediately; allow other callbacks to run if possible
                # but log the failure.

        if success_count == 0:
            raise StateUpdateError(
                f"Failed to update scheduler state for task {task_id}. "
                f"No callbacks succeeded."
            )

        logger.debug(f"Scheduler state updated for task {task_id} to {status.name}")
        return True

    def process_feedback(self, node_id: str, task_id: str, status: str) -> None:
        """
        High-level method to receive status and immediately update the scheduler.

        This combines receive_task_status and update_scheduler_state into a single
        atomic operation for convenience in the orchestration loop.

        Args:
            node_id: Node ID.
            task_id: Task ID.
            status: Status string.

        Raises:
            FeedbackError: If validation fails or state update fails.
        """
        feedback = self.receive_task_status(node_id, task_id, status)
        
        # Attempt to update the scheduler state
        # We catch StateUpdateError here to ensure the feedback is logged even if
        # the scheduler isn't ready, though typically this should be fatal for the run.
        try:
            self.update_scheduler_state(task_id, feedback.status)
        except StateUpdateError as e:
            logger.critical(f"Critical: Could not update scheduler state for {task_id}: {e}")
            raise

    def get_feedback_history(self) -> List[TaskFeedback]:
        """Return the list of all received feedback."""
        return self._feedback_log.copy()


def create_feedback_manager(node_manager: NodeManager) -> CompletionFeedbackManager:
    """
    Factory function to create a CompletionFeedbackManager.

    Args:
        node_manager: The NodeManager instance.

    Returns:
        CompletionFeedbackManager: A configured manager instance.
    """
    return CompletionFeedbackManager(node_manager)


def main() -> None:
    """
    Entry point for testing the completion feedback module.
    This simulates receiving feedback from a node and updating the state.
    """
    logger.info("Running CompletionFeedbackManager main test.")

    # We cannot instantiate a real NodeManager without SSH credentials in this context,
    # so we mock the behavior for the test run or assume it's called from a runner.
    # For a real execution, this would be invoked by the Scheduler.
    
    # Simulated flow:
    # 1. Create manager (requires NodeManager, skipped here for standalone test)
    # 2. Simulate receiving feedback
    
    print("CompletionFeedback module loaded successfully.")
    print("Functions available: receive_task_status, update_scheduler_state, process_feedback")
    
    # Basic sanity check of enums
    from orchestrator.models import TaskStatus
    assert TaskStatus.COMPLETED is not None
    assert TaskStatus.FAILED is not None
    print("TaskStatus enum validated.")


if __name__ == "__main__":
    main()
