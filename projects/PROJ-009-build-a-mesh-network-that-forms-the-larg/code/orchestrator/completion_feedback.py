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
    """Base exception for completion feedback errors."""
    pass


class StateUpdateError(FeedbackError):
    """Raised when updating scheduler state fails."""
    pass


class InvalidStatusError(FeedbackError):
    """Raised when an invalid status string is provided."""
    pass


class TaskStatusEnum(Enum):
    """Enum representing valid task statuses for feedback."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    REASSIGNED = "reassigned"


@dataclass
class TaskFeedback:
    """Data structure holding feedback from a node about a task."""
    node_id: str
    task_id: str
    status: TaskStatusEnum
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "task_id": self.task_id,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details
        }


class CompletionFeedbackManager:
    """
    Manages the completion feedback loop required by FR-001.
    Handles receiving task status updates and updating the scheduler state.
    """

    def __init__(self, state_accessor: Callable[[str], Optional[ExecutionRun]], state_mutator: Callable[[ExecutionRun], None]):
        """
        Initialize the manager with accessors for the scheduler state.

        Args:
            state_accessor: A callable that takes a task_id and returns the current ExecutionRun object.
            state_mutator: A callable that takes an updated ExecutionRun object and persists it.
        """
        self.state_accessor = state_accessor
        self.state_mutator = state_mutator
        self._feedback_history: List[TaskFeedback] = []
        logger.info("CompletionFeedbackManager initialized.")

    def receive_task_status(
        self,
        node_id: str,
        task_id: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> TaskFeedback:
        """
        Receive a status update from a node.

        Validates the status string and creates a TaskFeedback object.

        Args:
            node_id: The ID of the node reporting.
            task_id: The ID of the task being reported on.
            status: The status string (must match TaskStatusEnum).
            details: Optional additional context.

        Returns:
            TaskFeedback: The validated feedback object.

        Raises:
            InvalidStatusError: If the status string is not valid.
        """
        # Validate and normalize status
        try:
            status_enum = TaskStatusEnum(status)
        except ValueError:
            raise InvalidStatusError(f"Invalid status '{status}' for task {task_id}. Valid values: {[s.value for s in TaskStatusEnum]}")

        # Check if task exists in the current run context
        # The ExecutionRun model tracks tasks; we look it up in task_states
        if self.execution_run.task_states is None:
            self.execution_run.task_states = {}
        
        if task_id not in self.execution_run.task_states:
            # Depending on strictness, this might be an error or just a log
            # For now, we log a warning but allow the state to be created if it's new
            logger.warning(f"Task {task_id} not found in execution run states. Creating new entry.")
            self.execution_run.task_states[task_id] = {
                "node_id": node_id,
                "status": TaskStatus.PENDING,
                "start_time": None,
                "end_time": None
            }

        current_state = self.execution_run.task_states[task_id]
        
        # Create feedback object
        feedback = TaskFeedback(
            node_id=node_id,
            task_id=task_id,
            status=status_enum,
            details=details
        )

        self._feedback_history.append(feedback)
        logger.info(f"Received feedback: Task {task_id} on Node {node_id} -> {status_enum.value}")
        return feedback

    def update_scheduler_state(self, task_id: str, status: TaskStatusEnum) -> None:
        """
        Update the SchedulerState (ExecutionRun) object defined in T008.

        This method fetches the current state for the task, updates the status,
        and persists the change. It does not manage the full T015b instance,
        only the specific state update for this task.

        Args:
            task_id: The ID of the task to update.
            status: The new TaskStatusEnum value.

        Raises:
            StateUpdateError: If the state cannot be fetched or updated.
        """
        try:
            # Fetch current state (ExecutionRun) for the task
            # In a real implementation, this might query a database or shared memory
            run = self.state_accessor(task_id)

            if run is None:
                logger.warning(f"No state found for task {task_id}. Creating new state.")
                # If state doesn't exist, we might need to create a placeholder or fail
                # For this implementation, we assume state exists or we handle creation externally
                raise StateUpdateError(f"Cannot update state for task {task_id}: State not found.")

            # Update the task status in the run object
            # Assuming ExecutionRun has a tasks dict or list mapping task_id to status
            # Based on T008 models.py context, we assume a structure like run.tasks[task_id].status
            if hasattr(run, 'tasks') and task_id in run.tasks:
                run.tasks[task_id].status = status.value
                run.tasks[task_id].completed_at = datetime.now(timezone.utc)
            else:
                # Fallback if structure is different or task_id not in tasks dict
                # Log a warning but attempt to update a general status if possible
                logger.warning(f"Task {task_id} not found in run.tasks for ExecutionRun. Attempting general update.")
                if hasattr(run, 'overall_status'):
                     run.overall_status = status.value

            # Persist the update
            self.state_mutator(run)
            logger.info(f"Scheduler state updated for task {task_id}: {status.value}")

        except Exception as e:
            logger.error(f"Failed to update scheduler state for task {task_id}: {e}")
            raise StateUpdateError(f"State update failed for task {task_id}: {e}") from e


def create_feedback_manager(
    state_accessor: Callable[[str], Optional[ExecutionRun]],
    state_mutator: Callable[[ExecutionRun], None]
) -> CompletionFeedbackManager:
    """
    Factory function to create a CompletionFeedbackManager.

    Args:
        state_accessor: Function to get current ExecutionRun by task_id.
        state_mutator: Function to save updated ExecutionRun.

    Returns:
        CompletionFeedbackManager instance.
    """
    return CompletionFeedbackManager(state_accessor, state_mutator)


def main() -> None:
    """
    CLI entry point for testing the completion feedback logic.
    Simulates receiving feedback and updating a mock state.
    """
    # Mock state storage
    mock_state: Dict[str, ExecutionRun] = {}

    def mock_accessor(task_id: str) -> Optional[ExecutionRun]:
        return mock_state.get(task_id)

    def mock_mutator(run: ExecutionRun) -> None:
        # In a real scenario, this would save to disk or DB
        # Here we just update the local dict for the specific task
        for tid, task in run.tasks.items():
            mock_state[tid] = run
        logger.info(f"Mock state updated for run {run.run_id}")

    manager = create_feedback_manager(mock_accessor, mock_mutator)

    # Simulate a task
    from orchestrator.models import TaskChunk
    task = TaskChunk(task_id="task_001", chunk_data=b"test", status=TaskStatus.PENDING.value)
    run = ExecutionRun(run_id="run_001", tasks={"task_001": task})
    mock_state["task_001"] = run

    print("Testing Completion Feedback Loop...")

    # 1. Receive feedback
    try:
        feedback = manager.receive_task_status(
            node_id="node_192_168_1_10",
            task_id="task_001",
            status="completed",
            details={"ops_per_sec": 1500}
        )
        print(f"Feedback received: {feedback.to_dict()}")

        # 2. Update state
        manager.update_scheduler_state("task_001", TaskStatusEnum.COMPLETED)
        print("Scheduler state updated successfully.")

        # Verify
        updated_run = mock_accessor("task_001")
        if updated_run and updated_run.tasks["task_001"].status == "completed":
            print("Verification passed: Task status is 'completed'.")
        else:
            print("Verification failed: Task status not updated correctly.")

    except (InvalidStatusError, StateUpdateError) as e:
        print(f"Error during feedback loop: {e}")


if __name__ == "__main__":
    main()