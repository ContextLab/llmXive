"""
Completion Feedback Manager for US1.

Handles the 'completion feedback' loop required by FR-001.
Implements reception of task status from nodes and updates the central scheduler state.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Any, Optional, Callable

from orchestrator.models import TaskStatus, ExecutionRun, PhysicalNode
from orchestrator.logger import get_logger

logger = get_logger(__name__)


class FeedbackError(Exception):
    """Base exception for feedback processing errors."""
    pass


class StateUpdateError(FeedbackError):
    """Raised when updating the scheduler state fails."""
    pass


class InvalidStatusError(FeedbackError):
    """Raised when an unknown or invalid status string is received."""
    pass


@dataclass
class TaskFeedback:
    """
    Represents a single feedback event from a node.
    """
    node_id: str
    task_id: str
    status: TaskStatus
    timestamp: datetime
    details: Optional[Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.status, TaskStatus):
            # Try to convert string to enum if passed as string
            if isinstance(self.status, str):
                try:
                    self.status = TaskStatus(self.status.upper())
                except ValueError:
                    raise InvalidStatusError(f"Unknown task status: {self.status}")
            else:
                raise InvalidStatusError(f"Invalid status type: {type(self.status)}")
        
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)


class CompletionFeedbackManager:
    """
    Manages the reception of task completion feedback and updates the central scheduler state.
    
    This class acts as the interface between remote node reports and the central
    scheduler's state machine (defined in T008/T015).
    """
    
    def __init__(self, scheduler_state_ref: Optional[Any] = None):
        """
        Initialize the manager.
        
        Args:
            scheduler_state_ref: A reference to the central scheduler state object
                                 (typically an instance of Scheduler from T015 or a shared dict).
                                 If None, this manager operates in a standalone mode for testing.
        """
        self.scheduler_state = scheduler_state_ref
        self.feedback_log: List[TaskFeedback] = []
        self.logger = get_logger(__name__)

    def receive_task_status(
        self, 
        node_id: str, 
        task_id: str, 
        status: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> TaskFeedback:
        """
        Receive a task status update from a node.
        
        This method validates the incoming status, creates a feedback record,
        and triggers the state update.
        
        Args:
            node_id: The unique identifier of the node reporting.
            task_id: The unique identifier of the task being reported on.
            status: A string representation of the TaskStatus (e.g., "COMPLETED", "FAILED").
            details: Optional metadata associated with the status (e.g., error messages, metrics).
        
        Returns:
            The created TaskFeedback object.
        
        Raises:
            InvalidStatusError: If the status string is not recognized.
            StateUpdateError: If the state update fails.
        """
        self.logger.info(f"Received status '{status}' for task {task_id} from node {node_id}")
        
        # Parse status
        try:
            parsed_status = TaskStatus(status.upper())
        except ValueError:
            raise InvalidStatusError(f"Received invalid task status string: '{status}'")

        now = datetime.now(timezone.utc)
        feedback = TaskFeedback(
            node_id=node_id,
            task_id=task_id,
            status=parsed_status,
            timestamp=now,
            details=details or {}
        )

        self.feedback_log.append(feedback)

        # Update central state
        self.update_scheduler_state(task_id, parsed_status, node_id, details)

        return feedback

    def update_scheduler_state(
        self, 
        task_id: str, 
        status: TaskStatus, 
        node_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update the central scheduler state based on the new task status.
        
        This method interacts with the scheduler object (T015) to mark tasks
        as complete, failed, or re-queue them if necessary.
        
        Args:
            task_id: The ID of the task to update.
            status: The new status of the task.
            node_id: The node associated with this update (if known).
            details: Additional context for the state transition.
        
        Raises:
            StateUpdateError: If the scheduler state cannot be updated.
        """
        if self.scheduler_state is None:
            self.logger.warning(
                "No scheduler state reference provided. "
                "Feedback recorded but central state not updated."
            )
            return

        try:
            # Delegate to the scheduler's internal state update mechanism.
            # Assuming the scheduler object exposed by T015 has a method to handle this.
            # If the scheduler is a dict-like structure, we would update it directly.
            # Here we assume a method `handle_task_update` exists on the Scheduler class.
            
            if hasattr(self.scheduler_state, 'handle_task_update'):
                self.scheduler_state.handle_task_update(task_id, status, node_id, details)
            elif hasattr(self.scheduler_state, 'update_task_status'):
                self.scheduler_state.update_task_status(task_id, status, node_id, details)
            else:
                # Fallback: attempt to update a direct attribute if it's a simple dict/object
                if hasattr(self.scheduler_state, 'tasks') and task_id in self.scheduler_state.tasks:
                    self.scheduler_state.tasks[task_id]['status'] = status
                    if node_id:
                        self.scheduler_state.tasks[task_id]['node_id'] = node_id
                    self.scheduler_state.tasks[task_id]['completed_at'] = datetime.now(timezone.utc)
                else:
                    self.logger.warning(
                        f"Scheduler state structure unknown or task {task_id} not found. "
                        "State update skipped."
                    )
            
            self.logger.debug(f"Successfully updated state for task {task_id} to {status}")

        except Exception as e:
            msg = f"Failed to update scheduler state for task {task_id}: {e}"
            self.logger.error(msg, exc_info=True)
            raise StateUpdateError(msg) from e

    def get_pending_tasks(self) -> List[str]:
        """
        Retrieve a list of task IDs that are currently pending or in progress.
        
        Returns:
            List of task IDs.
        """
        if self.scheduler_state is None:
            return []
        
        pending = []
        if hasattr(self.scheduler_state, 'tasks'):
            for tid, tdata in self.scheduler_state.tasks.items():
                if tdata.get('status') in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                    pending.append(tid)
        return pending

    def get_feedback_history(self) -> List[TaskFeedback]:
        """
        Return the history of all received feedback events.
        
        Returns:
            List of TaskFeedback objects.
        """
        return self.feedback_log.copy()


def create_feedback_manager(
    scheduler_state: Optional[Any] = None
) -> CompletionFeedbackManager:
    """
    Factory function to create a CompletionFeedbackManager.
    
    Args:
        scheduler_state: Reference to the central scheduler state.
    
    Returns:
        Configured CompletionFeedbackManager instance.
    """
    return CompletionFeedbackManager(scheduler_state_ref=scheduler_state)


def main() -> None:
    """
    Entry point for standalone testing of the feedback manager.
    """
    logger.info("Starting completion feedback manager test.")
    
    # Mock a simple scheduler state for testing
    class MockSchedulerState:
        def __init__(self):
            self.tasks = {
                "task_001": {"status": TaskStatus.PENDING, "node_id": None},
                "task_002": {"status": TaskStatus.RUNNING, "node_id": "node_A"}
            }
        
        def handle_task_update(self, task_id, status, node_id, details):
            self.tasks[task_id]['status'] = status
            self.tasks[task_id]['completed_at'] = datetime.now(timezone.utc)
            logger.info(f"Mock Scheduler: Updated {task_id} -> {status}")

    mock_scheduler = MockSchedulerState()
    manager = create_feedback_manager(mock_scheduler)

    # Simulate receiving feedback
    try:
        fb1 = manager.receive_task_status("node_A", "task_001", "COMPLETED")
        print(f"Received feedback: {fb1}")
        
        fb2 = manager.receive_task_status("node_B", "task_002", "FAILED", {"error": "Timeout"})
        print(f"Received feedback: {fb2}")
        
        # Verify state
        print(f"Task 001 status: {mock_scheduler.tasks['task_001']['status']}")
        print(f"Task 002 status: {mock_scheduler.tasks['task_002']['status']}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)

    logger.info("Test complete.")


if __name__ == "__main__":
    main()