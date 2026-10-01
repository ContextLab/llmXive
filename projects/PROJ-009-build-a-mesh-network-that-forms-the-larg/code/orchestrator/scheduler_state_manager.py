"""
Scheduler State Manager for the Mesh Network Supercomputer.

This module implements the global state management for the scheduler,
tracking task assignments, node availability, and task lifecycles.

Dependencies:
    - T008 (Models): Uses PhysicalNode, TaskChunk, TaskStatus, NodeStatus
    - T004 (Config): Uses Config, get_config
"""

from __future__ import annotations

import threading
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set

from orchestrator.models import PhysicalNode, TaskChunk, TaskStatus, NodeStatus
from orchestrator.config import get_config

logger = logging.getLogger(__name__)

@dataclass
class TaskAssignmentRecord:
    """Record of a specific task assignment to a node."""
    task_id: str
    node_id: str
    status: TaskStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    payload: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'node_id': self.node_id,
            'status': self.status.value if isinstance(self.status, TaskStatus) else self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'payload': self.payload
        }

class SchedulerStateManager:
    """
    Manages the global state of the scheduler.
    
    Maintains:
        - Dictionary of task_id -> TaskAssignmentRecord
        - Dictionary of node_id -> NodeStatus
        - Thread-safe access to state
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._tasks: Dict[str, TaskAssignmentRecord] = {}
        self._nodes: Dict[str, NodeStatus] = {}
        self._node_objects: Dict[str, PhysicalNode] = {}
        self._config = get_config()
        
    def register_node(self, node: PhysicalNode) -> None:
        """Register a node in the state manager."""
        with self._lock:
            self._nodes[node.node_id] = node.status
            self._node_objects[node.node_id] = node
            logger.debug(f"Registered node {node.node_id} with status {node.status}")
    
    def update_node_status(self, node_id: str, status: NodeStatus) -> None:
        """Update the status of a registered node."""
        with self._lock:
            if node_id not in self._nodes:
                logger.warning(f"Attempted to update status of unregistered node: {node_id}")
                return
            self._nodes[node_id] = status
            if node_id in self._node_objects:
                self._node_objects[node_id].status = status
            logger.debug(f"Updated node {node_id} status to {status}")
    
    def get_available_nodes(self) -> List[str]:
        """
        Get list of node IDs that are currently online and available.
        
        Returns:
            List of node IDs with status 'online'
        """
        with self._lock:
            return [
                node_id for node_id, status in self._nodes.items()
                if status == NodeStatus.ONLINE
            ]
    
    def get_all_nodes(self) -> List[str]:
        """Get list of all registered node IDs."""
        with self._lock:
            return list(self._nodes.keys())
    
    def assign_task(self, task_chunk: TaskChunk, node_id: str) -> str:
        """
        Assign a task chunk to a specific node.
        
        Args:
            task_chunk: The task chunk to assign
            node_id: The ID of the node to assign to
        
        Returns:
            The generated task_id
        
        Raises:
            ValueError: If node is not available
        """
        with self._lock:
            if node_id not in self._nodes:
                raise ValueError(f"Node {node_id} is not registered")
            
            if self._nodes[node_id] != NodeStatus.ONLINE:
                raise ValueError(f"Node {node_id} is not online (status: {self._nodes[node_id]})")
            
            task_id = f"{task_chunk.chunk_id}_{node_id}_{datetime.now(timezone.utc).timestamp()}"
            
            record = TaskAssignmentRecord(
                task_id=task_id,
                node_id=node_id,
                status=TaskStatus.ASSIGNED,
                start_time=None,
                end_time=None,
                payload={
                    'chunk_size': task_chunk.chunk_size,
                    'iterations': task_chunk.iterations,
                    'workload_type': task_chunk.workload_type
                }
            )
            
            self._tasks[task_id] = record
            logger.info(f"Assigned task {task_id} to node {node_id}")
            
            return task_id
    
    def get_task_status(self, task_id: str) -> Optional[TaskAssignmentRecord]:
        """
        Get the current status and record of a task.
        
        Args:
            task_id: The ID of the task
        
        Returns:
            TaskAssignmentRecord if found, None otherwise
        """
        with self._lock:
            return self._tasks.get(task_id)
    
    def update_task_status(self, task_id: str, new_status: TaskStatus) -> None:
        """
        Update the status of an existing task.
        
        Args:
            task_id: The ID of the task
            new_status: The new status to set
        
        Raises:
            ValueError: If task_id is not found
        """
        with self._lock:
            if task_id not in self._tasks:
                raise ValueError(f"Task {task_id} not found in state manager")
            
            record = self._tasks[task_id]
            old_status = record.status
            record.status = new_status
            
            if new_status == TaskStatus.RUNNING and record.start_time is None:
                record.start_time = datetime.now(timezone.utc)
            elif new_status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                record.end_time = datetime.now(timezone.utc)
            
            logger.info(f"Updated task {task_id} status from {old_status} to {new_status}")
    
    def complete_task(self, task_id: str, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark a task as completed with optional result data."""
        with self._lock:
            if task_id not in self._tasks:
                raise ValueError(f"Task {task_id} not found")
            
            self._tasks[task_id].status = TaskStatus.COMPLETED
            self._tasks[task_id].end_time = datetime.now(timezone.utc)
            if result:
                self._tasks[task_id].payload = result
            logger.info(f"Task {task_id} marked as completed")
    
    def fail_task(self, task_id: str, error: Optional[str] = None) -> None:
        """Mark a task as failed with optional error message."""
        with self._lock:
            if task_id not in self._tasks:
                raise ValueError(f"Task {task_id} not found")
            
            self._tasks[task_id].status = TaskStatus.FAILED
            self._tasks[task_id].end_time = datetime.now(timezone.utc)
            if error:
                if self._tasks[task_id].payload is None:
                    self._tasks[task_id].payload = {}
                self._tasks[task_id].payload['error'] = error
            logger.warning(f"Task {task_id} marked as failed: {error}")
    
    def get_task_by_node(self, node_id: str) -> List[str]:
        """Get all task IDs currently assigned to a specific node."""
        with self._lock:
            return [
                task_id for task_id, record in self._tasks.items()
                if record.node_id == node_id and record.status in (
                    TaskStatus.ASSIGNED, TaskStatus.RUNNING
                )
            ]
    
    def get_node_utilization(self, node_id: str) -> Dict[str, Any]:
        """
        Get utilization statistics for a specific node.
        
        Returns:
            Dict with total_tasks, completed, failed, running counts
        """
        with self._lock:
            node_tasks = [
                record for record in self._tasks.values()
                if record.node_id == node_id
            ]
            
            return {
                'total_tasks': len(node_tasks),
                'completed': sum(1 for r in node_tasks if r.status == TaskStatus.COMPLETED),
                'failed': sum(1 for r in node_tasks if r.status == TaskStatus.FAILED),
                'running': sum(1 for r in node_tasks if r.status == TaskStatus.RUNNING),
                'assigned': sum(1 for r in node_tasks if r.status == TaskStatus.ASSIGNED)
            }
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """
        Get a complete snapshot of the current scheduler state.
        
        Returns:
            Dict containing tasks and nodes state
        """
        with self._lock:
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'nodes': {
                    node_id: status.value for node_id, status in self._nodes.items()
                },
                'tasks': {
                    task_id: record.to_dict() for task_id, record in self._tasks.items()
                }
            }
    
    def reset_task(self, task_id: str) -> None:
        """Reset a task to ASSIGNED state (for re-assignment)."""
        with self._lock:
            if task_id not in self._tasks:
                raise ValueError(f"Task {task_id} not found")
            
            record = self._tasks[task_id]
            old_status = record.status
            record.status = TaskStatus.ASSIGNED
            record.start_time = None
            record.end_time = None
            logger.info(f"Task {task_id} reset from {old_status} to ASSIGNED")

# Singleton instance for global access
_scheduler_state_manager: Optional[SchedulerStateManager] = None

def get_scheduler_state_manager() -> SchedulerStateManager:
    """Get or create the singleton SchedulerStateManager instance."""
    global _scheduler_state_manager
    if _scheduler_state_manager is None:
        _scheduler_state_manager = SchedulerStateManager()
        logger.info("Initialized global SchedulerStateManager")
    return _scheduler_state_manager

def create_scheduler_state_manager() -> SchedulerStateManager:
    """Create a new SchedulerStateManager instance (for testing)."""
    return SchedulerStateManager()