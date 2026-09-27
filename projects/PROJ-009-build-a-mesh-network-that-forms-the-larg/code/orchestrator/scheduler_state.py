"""
Scheduler State Machine and Feedback Handler Logic.

Defines the runtime `SchedulerState` machine and logic to process
task status updates and heartbeat loss events.
"""

from __future__ import annotations

import threading
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Callable

from orchestrator.logger import get_logger

logger = get_logger(__name__)


class SchedulerStateEnum(Enum):
    """
    Explicit enumeration of valid scheduler states.
    """
    IDLE = "IDLE"
    DISCOVERING = "DISCOVERING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    FAILED = "FAILED"


class TaskStatusEnum(Enum):
    """
    Explicit enumeration of task statuses for feedback handling.
    """
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


@dataclass
class TaskAssignmentRecord:
    """
    Tracks the state of a specific task assignment.
    """
    task_id: str
    node_id: str
    status: TaskStatusEnum = TaskStatusEnum.PENDING
    assigned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class SchedulerState:
    """
    Thread-safe state object representing the current runtime state of the scheduler.

    This object is accessible by T015b (scheduler_execution) and updated by
    T013b (completion_feedback) and T013c (heartbeat_monitoring).
    """
    current_state: SchedulerStateEnum = SchedulerStateEnum.IDLE
    active_tasks: Dict[str, TaskAssignmentRecord] = field(default_factory=dict)
    available_nodes: List[str] = field(default_factory=list)
    failed_nodes: List[str] = field(default_factory=list)
    last_state_transition: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    failure_reason: Optional[str] = None
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    def transition(self, new_state: SchedulerStateEnum, reason: Optional[str] = None) -> None:
        """
        Thread-safe state transition.
        """
        with self._lock:
            old_state = self.current_state
            self.current_state = new_state
            self.last_state_transition = datetime.now(timezone.utc)
            if reason:
                self.failure_reason = reason
                logger.info(f"State transitioned from {old_state.value} to {new_state.value}. Reason: {reason}")
            else:
                logger.info(f"State transitioned from {old_state.value} to {new_state.value}")

            # State validity checks
            if new_state == SchedulerStateEnum.FAILED:
                if not reason:
                    raise ValueError("Transition to FAILED state requires a reason.")

    def register_task(self, task_id: str, node_id: str) -> None:
        """
        Registers a new task assignment.
        """
        with self._lock:
            self.active_tasks[task_id] = TaskAssignmentRecord(
                task_id=task_id,
                node_id=node_id,
                status=TaskStatusEnum.ASSIGNED
            )
            logger.debug(f"Task {task_id} registered on node {node_id}")

    def update_task_status(self, task_id: str, status: TaskStatusEnum, error: Optional[str] = None) -> None:
        """
        Updates the status of an active task.
        """
        with self._lock:
            if task_id not in self.active_tasks:
                logger.warning(f"Attempted to update status for unknown task {task_id}")
                return

            task = self.active_tasks[task_id]
            old_status = task.status
            task.status = status
            if status in (TaskStatusEnum.COMPLETED, TaskStatusEnum.FAILED, TaskStatusEnum.TIMEOUT):
                task.completed_at = datetime.now(timezone.utc)
                if error:
                    task.error_message = error

            logger.debug(f"Task {task_id} status updated: {old_status.value} -> {status.value}")

    def mark_node_available(self, node_id: str) -> None:
        """
        Marks a node as available for scheduling.
        """
        with self._lock:
            if node_id not in self.available_nodes:
                self.available_nodes.append(node_id)
                if node_id in self.failed_nodes:
                    self.failed_nodes.remove(node_id)
            logger.debug(f"Node {node_id} marked as available")

    def mark_node_unavailable(self, node_id: str) -> None:
        """
        Marks a node as unavailable (failed or lost heartbeat).
        """
        with self._lock:
            if node_id in self.available_nodes:
                self.available_nodes.remove(node_id)
            if node_id not in self.failed_nodes:
                self.failed_nodes.append(node_id)
            logger.debug(f"Node {node_id} marked as unavailable")

    def get_available_nodes(self) -> List[str]:
        """
        Returns a copy of the list of currently available nodes.
        """
        with self._lock:
            return list(self.available_nodes)

    def get_task_status(self, task_id: str) -> Optional[TaskStatusEnum]:
        """
        Returns the status of a specific task.
        """
        with self._lock:
            if task_id in self.active_tasks:
                return self.active_tasks[task_id].status
            return None

    def is_running(self) -> bool:
        """
        Checks if the scheduler is currently in the RUNNING state.
        """
        with self._lock:
            return self.current_state == SchedulerStateEnum.RUNNING

    def is_failed(self) -> bool:
        """
        Checks if the scheduler has entered the FAILED state.
        """
        with self._lock:
            return self.current_state == SchedulerStateEnum.FAILED


class SchedulerStateError(Exception):
    """Base exception for scheduler state errors."""
    pass


class StateTransitionError(SchedulerStateError):
    """Raised when an invalid state transition is attempted."""
    pass


class HeartbeatLostEvent:
    """
    Event object raised/consumed when a heartbeat is lost.
    Carries the node_id and timestamp.
    """
    def __init__(self, node_id: str, timestamp: datetime):
        self.node_id = node_id
        self.timestamp = timestamp

    def __repr__(self):
        return f"HeartbeatLostEvent(node_id={self.node_id}, timestamp={self.timestamp})"


class TaskStatusEvent:
    """
    Event object for task status updates.
    """
    def __init__(self, task_id: str, node_id: str, status: TaskStatusEnum, error: Optional[str] = None):
        self.task_id = task_id
        self.node_id = node_id
        self.status = status
        self.error = error

    def __repr__(self):
        return f"TaskStatusEvent(task_id={self.task_id}, status={self.status.value})"


def create_scheduler_state() -> SchedulerState:
    """
    Factory function to create a new SchedulerState instance.
    """
    return SchedulerState()


# --- Feedback Handler Logic ---
# This logic is intended to be consumed by T013b and T013c

def handle_task_status_update(
    state: SchedulerState,
    task_id: str,
    node_id: str,
    status: TaskStatusEnum,
    error: Optional[str] = None
) -> Optional[TaskStatusEvent]:
    """
    Processes a task status update and updates the SchedulerState.
    Returns a TaskStatusEvent if the state changes significantly.
    """
    # Validate transition
    current_task_status = state.get_task_status(task_id)
    
    if current_task_status is None:
        # Task not found, might be a re-assignment or late arrival
        logger.warning(f"Received status update for unknown task {task_id}. Ignoring.")
        return None

    state.update_task_status(task_id, status, error)

    # Check for terminal states that might trigger global state changes
    if status in (TaskStatusEnum.COMPLETED, TaskStatusEnum.FAILED, TaskStatusEnum.TIMEOUT):
        # Check if all tasks are done
        with state._lock:
            all_done = all(t.status in (TaskStatusEnum.COMPLETED, TaskStatusEnum.FAILED, TaskStatusEnum.TIMEOUT) 
                           for t in state.active_tasks.values())
            if all_done and state.current_state == SchedulerStateEnum.RUNNING:
                state.transition(SchedulerStateEnum.IDLE)
    
    return TaskStatusEvent(task_id, node_id, status, error)


def handle_heartbeat_loss(
    state: SchedulerState,
    node_id: str
) -> HeartbeatLostEvent:
    """
    Processes a heartbeat loss event.
    Updates state to mark node unavailable and potentially transitions global state.
    """
    logger.warning(f"Heartbeat lost for node {node_id}")
    
    state.mark_node_unavailable(node_id)

    # If we are running and lose a node, we might need to pause or fail
    # depending on policy. For now, we just mark it unavailable.
    if state.current_state == SchedulerStateEnum.RUNNING:
        if len(state.get_available_nodes()) == 0:
            state.transition(
                SchedulerStateEnum.FAILED, 
                reason=f"No available nodes after heartbeat loss on {node_id}"
            )

    return HeartbeatLostEvent(node_id, datetime.now(timezone.utc))