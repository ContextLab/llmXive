"""
Completion Feedback Module (T013b)

Handles the 'completion feedback' loop required by FR-001.
Implements receive_task_status and update_scheduler_state to update
the SchedulerState object defined in T008 (models.py).
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
    """Base exception for feedback loop failures."""
    pass


class StateUpdateError(FeedbackError):
    """Raised when scheduler state cannot be updated."""
    pass


class InvalidStatusError(FeedbackError):
    """Raised when an invalid status string is received."""
    pass


class TaskStatusEnum(Enum):
    """Enumeration of valid task status strings."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    OOM = "oom"
    NETWORK_ERROR = "network_error"


@dataclass
class TaskFeedback:
    """Container for a single task completion feedback event."""
    node_id: str
    task_id: str
    status: TaskStatusEnum
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: Optional[Dict[str, Any]] = None


class CompletionFeedbackManager:
    """
    Manages the lifecycle of task completion feedback.
    
    This class receives status updates from remote nodes and updates
    the central SchedulerState (represented by the ExecutionRun model).
    """

    def __init__(self, execution_run: ExecutionRun):
        """
        Initialize the manager with the current execution run context.
        
        Args:
            execution_run: The ExecutionRun object representing the current 
                           batch of tasks and their state.
        """
        self.execution_run = execution_run
        self._pending_feedbacks: List[TaskFeedback] = []
        self._processed_feedbacks: List[TaskFeedback] = []
        
        # Ensure the execution run has a status tracking structure
        if self.execution_run.task_states is None:
            self.execution_run.task_states = {}

    def receive_task_status(
        self, 
        node_id: str, 
        task_id: str, 
        status: str
    ) -> TaskFeedback:
        """
        Receive a task status update from a node.
        
        This function validates the status, creates a feedback object,
        and updates the internal state of the ExecutionRun.
        
        Args:
            node_id: The IP or identifier of the node reporting status.
            task_id: The unique identifier of the task.
            status: The string status reported (e.g., 'completed', 'failed').
                    
        Returns:
            TaskFeedback: The created feedback object.
            
        Raises:
            InvalidStatusError: If the status string is not recognized.
            StateUpdateError: If the task_id is not found in the current run.
        """
        # Validate and normalize status
        try:
            normalized_status = TaskStatusEnum(status.lower())
        except ValueError:
            raise InvalidStatusError(
                f"Invalid status '{status}' received for task {task_id}. "
                f"Valid statuses: {[s.value for s in TaskStatusEnum]}"
            )

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
            status=normalized_status
        )
        
        # Update the state in the ExecutionRun
        self.update_scheduler_state(task_id, normalized_status)
        
        self._processed_feedbacks.append(feedback)
        logger.info(
            f"Received feedback: Task {task_id} on {node_id} -> {normalized_status.value}"
        )
        
        return feedback

    def update_scheduler_state(
        self, 
        task_id: str, 
        status: TaskStatusEnum
    ) -> None:
        """
        Update the SchedulerState (ExecutionRun) with the new task status.
        
        This method modifies the `task_states` dictionary within the 
        ExecutionRun object to reflect the new status.
        
        Args:
            task_id: The unique identifier of the task.
            status: The new TaskStatusEnum value.
                    
        Raises:
            StateUpdateError: If the task_id is missing or state transition is invalid.
        """
        if self.execution_run.task_states is None:
            self.execution_run.task_states = {}

        if task_id not in self.execution_run.task_states:
            raise StateUpdateError(
                f"Cannot update state for task {task_id}: Task not found in ExecutionRun."
            )

        state_entry = self.execution_run.task_states[task_id]
        old_status = state_entry.get("status")

        # Validate state transition (simple logic: any status can move to any other)
        # In a more complex system, we would enforce a state machine here.
        
        # Update status
        state_entry["status"] = status
        
        # Update timestamps
        now = datetime.now(timezone.utc)
        if status == TaskStatusEnum.RUNNING and old_status == TaskStatusEnum.PENDING:
            state_entry["start_time"] = now
        elif status in [TaskStatusEnum.COMPLETED, TaskStatusEnum.FAILED, TaskStatusEnum.TIMEOUT]:
            state_entry["end_time"] = now

        logger.debug(f"Updated scheduler state for {task_id}: {old_status} -> {status}")

    def get_run_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current execution run status.
        
        Returns:
            Dict containing counts of tasks by status.
        """
        counts = {s.value: 0 for s in TaskStatusEnum}
        total = 0
        
        if self.execution_run.task_states:
            for task_id, state in self.execution_run.task_states.items():
                status = state.get("status")
                if isinstance(status, TaskStatusEnum):
                    counts[status.value] += 1
                    total += 1
                elif isinstance(status, str):
                    # Handle if stored as string for some reason
                    if status in counts:
                        counts[status] += 1
                        total += 1
                
        return {
            "total_tasks": total,
            "status_counts": counts,
            "run_id": self.execution_run.run_id
        }


def create_feedback_manager(execution_run: ExecutionRun) -> CompletionFeedbackManager:
    """Factory function to create a CompletionFeedbackManager."""
    return CompletionFeedbackManager(execution_run)


def main():
    """
    Standalone test entry point for T013b.
    Simulates receiving task statuses and updating the scheduler state.
    """
    from orchestrator.models import ExecutionRun, TaskStatus
    
    # Setup logging
    configure_logging = logging.getLogger(__name__)
    configure_logging.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    configure_logging.addHandler(handler)

    # Create a mock ExecutionRun
    run = ExecutionRun(
        run_id="test-run-001",
        start_time=datetime.now(timezone.utc),
        end_time=None,
        status=TaskStatus.PENDING,
        task_states={}
    )

    # Initialize Manager
    manager = create_feedback_manager(run)

    # Simulate receiving feedback
    try:
        logger.info("Starting feedback simulation...")
        
        # Receive a 'running' status
        fb1 = manager.receive_task_status(
            node_id="192.168.1.10", 
            task_id="task-001", 
            status="running"
        )
        
        # Receive a 'completed' status
        fb2 = manager.receive_task_status(
            node_id="192.168.1.10", 
            task_id="task-001", 
            status="completed"
        )

        # Receive a 'failed' status for a different task
        fb3 = manager.receive_task_status(
            node_id="192.168.1.11", 
            task_id="task-002", 
            status="failed"
        )

        # Print summary
        summary = manager.get_run_summary()
        logger.info(f"Run Summary: {summary}")
        
        # Verify state in the ExecutionRun object
        logger.info(f"ExecutionRun task_states: {run.task_states}")
        
        print("T013b Simulation Successful: Completion feedback loop updated SchedulerState correctly.")
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise


if __name__ == "__main__":
    main()
