"""
Scheduler module for distributing TaskChunk units to PhysicalNodes.
Handles task assignment, monitoring, OOM detection, and straggler logic.
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from enum import Enum

from orchestrator.models import TaskChunk, PhysicalNode, TaskStatus, NodeStatus
from orchestrator.node_manager import NodeManager, NodeTimeoutError, NodeHeartbeatLost, NodeReassignError
from orchestrator.logger import get_logger
from orchestrator.benchmark import run_monte_carlo_integration

# Custom exceptions for scheduler-specific errors
class SchedulerError(Exception):
    """Base exception for scheduler errors."""
    pass

class OOMError(SchedulerError):
    """Raised when a node runs out of memory during task execution."""
    pass

class StragglerDetectedError(SchedulerError):
    """Raised when a task is identified as a straggler."""
    pass

@dataclass
class NodeState:
    """Tracks the current state and metrics of a node in the scheduler."""
    node: PhysicalNode
    assigned_chunks: List[TaskChunk] = field(default_factory=list)
    active_task_id: Optional[str] = None
    last_heartbeat: datetime = field(default_factory=datetime.now)
    status: NodeStatus = NodeStatus.IDLE
    total_compute_time: float = 0.0
    total_handshake_time: float = 0.0
    oom_events: int = 0
    straggler_events: int = 0
    last_error: Optional[str] = None

class Scheduler:
    """
    Orchestrates the distribution of TaskChunk units to PhysicalNodes.
    Implements assignment strategies, OOM handling, and straggler detection.
    """

    def __init__(self, node_manager: NodeManager, timeout_factor: float = 2.0):
        """
        Initialize the scheduler.

        Args:
            node_manager: The NodeManager instance for SSH/heartbeat operations.
            timeout_factor: Multiplier for median task time to detect stragglers.
        """
        self.node_manager = node_manager
        self.timeout_factor = timeout_factor
        self.nodes: Dict[str, NodeState] = {}
        self.pending_tasks: List[TaskChunk] = []
        self.completed_tasks: List[TaskChunk] = []
        self.logger = get_logger(__name__)
        self.task_start_times: Dict[str, datetime] = {}
        self.median_task_time: float = 0.0
        self.task_times: List[float] = []

    def _register_node(self, node: PhysicalNode) -> None:
        """Register a node with the scheduler if not already present."""
        if node.ip_address not in self.nodes:
            self.nodes[node.ip_address] = NodeState(node=node)
            self.logger.info(f"Registered node: {node.ip_address}")

    def assign_chunk(self, chunk: TaskChunk, node: PhysicalNode) -> bool:
        """
        Assign a TaskChunk to a specific node.

        Args:
            chunk: The task chunk to assign.
            node: The target physical node.

        Returns:
            True if assignment was successful, False otherwise.
        """
        self._register_node(node)
        node_state = self.nodes[node.ip_address]

        if node_state.status != NodeStatus.IDLE:
            self.logger.warning(f"Node {node.ip_address} is not idle (status: {node_state.status}). Cannot assign chunk.")
            return False

        try:
            # Update node state
            node_state.status = NodeStatus.BUSY
            node_state.assigned_chunks.append(chunk)
            node_state.active_task_id = chunk.task_id

            # Log assignment
            self.logger.info(f"Assigned chunk {chunk.task_id} to node {node.ip_address}")

            # Execute the task remotely (synchronous for this implementation)
            # In a real async system, this would return a Future/Promise
            result = self._execute_task_on_node(node, chunk)

            # Update task status
            chunk.status = TaskStatus.COMPLETED
            chunk.wall_clock_time = result.wall_clock_time
            chunk.ops_per_sec = result.ops_per_sec

            # Update node state
            node_state.status = NodeStatus.IDLE
            node_state.active_task_id = None
            node_state.last_heartbeat = datetime.now()
            node_state.total_compute_time += result.wall_clock_time

            # Track task time for straggler detection
            self.task_times.append(result.wall_clock_time)
            self._update_median_task_time()

            self.completed_tasks.append(chunk)
            return True

        except OOMError as e:
            self.logger.error(f"OOM detected on node {node.ip_address} for chunk {chunk.task_id}: {e}")
            node_state.oom_events += 1
            node_state.status = NodeStatus.IDLE  # Reset status
            node_state.last_error = str(e)
            return False

        except Exception as e:
            self.logger.error(f"Error assigning chunk {chunk.task_id} to node {node.ip_address}: {e}")
            node_state.status = NodeStatus.IDLE
            node_state.last_error = str(e)
            return False

    def _execute_task_on_node(self, node: PhysicalNode, chunk: TaskChunk) -> Any:
        """
        Execute a task chunk on a remote node via SSH.

        Args:
            node: The target node.
            chunk: The task chunk to execute.

        Returns:
            The result of the benchmark execution.

        Raises:
            OOMError: If the node runs out of memory.
            NodeTimeoutError: If the node does not respond.
        """
        try:
            # Simulate remote execution using the benchmark module
            # In a real scenario, this would be executed via SSH on the remote node
            # For now, we call the local benchmark function but treat it as remote
            self.logger.debug(f"Executing chunk {chunk.task_id} on node {node.ip_address}")

            # Check RAM availability before execution (simulated via SSH in real impl)
            # This is a placeholder for the actual RAM check logic (T047a/T047b)
            # In the full implementation, this would query `free -m` via SSH
            # For now, we assume the node has enough RAM or the chunk size is small enough

            start_time = datetime.now()
            result = run_monte_carlo_integration(chunk.iterations, chunk.chunk_size)
            end_time = datetime.now()

            return result

        except MemoryError:
            raise OOMError(f"Node {node.ip_address} ran out of memory while processing chunk {chunk.task_id}")
        except Exception as e:
            self.logger.error(f"Remote execution failed on {node.ip_address}: {e}")
            raise

    def monitor_task(self, task_id: str) -> bool:
        """
        Monitor a specific task for completion, OOM, or straggler status.

        Args:
            task_id: The ID of the task to monitor.

        Returns:
            True if the task completed successfully, False otherwise.
        """
        # Find the task in the pending or active list
        target_chunk: Optional[TaskChunk] = None
        target_node_ip: Optional[str] = None

        for chunk in self.pending_tasks:
            if chunk.task_id == task_id:
                target_chunk = chunk
                break

        if not target_chunk:
            # Check active tasks on nodes
            for ip, state in self.nodes.items():
                if state.active_task_id == task_id:
                    target_chunk = state.assigned_chunks[-1] if state.assigned_chunks else None
                    target_node_ip = ip
                    break

        if not target_chunk:
            self.logger.warning(f"Task {task_id} not found in active or pending queues.")
            return False

        node_ip = target_node_ip
        if not node_ip:
            # Find the node that was assigned this task
            for ip, state in self.nodes.items():
                if any(c.task_id == task_id for c in state.assigned_chunks):
                    node_ip = ip
                    break

        if not node_ip or node_ip not in self.nodes:
            self.logger.error(f"Cannot monitor task {task_id}: Node not found.")
            return False

        node_state = self.nodes[node_ip]

        try:
            # Check heartbeat
            if time.time() - node_state.last_heartbeat.timestamp() > 30:  # 30s threshold
                raise NodeHeartbeatLost(f"Node {node_ip} heartbeat lost while monitoring task {task_id}")

            # Check for straggler
            if task_id in self.task_start_times:
                elapsed = (datetime.now() - self.task_start_times[task_id]).total_seconds()
                if self.median_task_time > 0 and elapsed > self.timeout_factor * self.median_task_time:
                    self.logger.warning(f"Task {task_id} is a straggler (elapsed: {elapsed:.2f}s, median: {self.median_task_time:.2f}s)")
                    node_state.straggler_events += 1
                    # Re-assign logic would go here (T048)
                    # For now, we just log it
                    return False

            return True

        except NodeHeartbeatLost:
            self.logger.error(f"Task {task_id} lost connection. Re-assigning...")
            # Re-assign logic
            self._reassign_task(task_id)
            return False
        except Exception as e:
            self.logger.error(f"Error monitoring task {task_id}: {e}")
            return False

    def _reassign_task(self, task_id: str) -> None:
        """
        Re-assign a failed or lost task to a different node.

        Args:
            task_id: The ID of the task to re-assign.
        """
        # Find the chunk
        chunk = None
        for c in self.pending_tasks:
            if c.task_id == task_id:
                chunk = c
                break

        if not chunk:
            # Check completed nodes for the task
            for state in self.nodes.values():
                for c in state.assigned_chunks:
                    if c.task_id == task_id:
                        chunk = c
                        state.assigned_chunks.remove(c)
                        break
                if chunk:
                    break

        if chunk:
            self.pending_tasks.append(chunk)
            self.logger.info(f"Re-added task {task_id} to pending queue for re-assignment.")
            # Trigger re-assignment in the next scheduling cycle
        else:
            self.logger.warning(f"Could not find task {task_id} for re-assignment.")

    def _update_median_task_time(self) -> None:
        """Update the median task time for straggler detection."""
        if self.task_times:
            sorted_times = sorted(self.task_times)
            n = len(sorted_times)
            if n % 2 == 0:
                self.median_task_time = (sorted_times[n//2 - 1] + sorted_times[n//2]) / 2
            else:
                self.median_task_time = sorted_times[n//2]

    def distribute_tasks(self, chunks: List[TaskChunk], nodes: List[PhysicalNode]) -> List[TaskChunk]:
        """
        Distribute a list of task chunks across available nodes.

        Args:
            chunks: List of task chunks to distribute.
            nodes: List of available physical nodes.

        Returns:
            List of completed task chunks.
        """
        # Register all nodes
        for node in nodes:
            self._register_node(node)

        self.pending_tasks = list(chunks)
        self.completed_tasks = []

        # Simple round-robin or load-balanced assignment
        # For now, we iterate and assign to the first available node
        while self.pending_tasks:
            chunk = self.pending_tasks.pop(0)
            assigned = False

            # Find an idle node
            for ip, state in self.nodes.items():
                if state.status == NodeStatus.IDLE:
                    if self.assign_chunk(chunk, state.node):
                        assigned = True
                        break

            if not assigned:
                # No idle nodes, put back and wait (or handle as error)
                self.logger.warning(f"No idle nodes available for chunk {chunk.task_id}. Re-queueing.")
                self.pending_tasks.append(chunk)
                time.sleep(1)  # Simple back-off

        return self.completed_tasks

    def get_node_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all registered nodes.

        Returns:
            Dictionary of node IP to stats.
        """
        stats = {}
        for ip, state in self.nodes.items():
            stats[ip] = {
                "status": state.status.value,
                "assigned_chunks_count": len(state.assigned_chunks),
                "active_task_id": state.active_task_id,
                "total_compute_time": state.total_compute_time,
                "oom_events": state.oom_events,
                "straggler_events": state.straggler_events,
                "last_error": state.last_error
            }
        return stats

def main():
    """
    Main entry point for testing the scheduler.
    """
    logging.basicConfig(level=logging.INFO)
    logger = get_logger(__name__)

    # Create mock nodes and chunks for testing
    # In a real scenario, these would come from node_manager and task generation
    from orchestrator.models import PhysicalNode, TaskChunk, NodeStatus, TaskStatus
    from orchestrator.node_manager import NodeManager, create_node_manager

    # Mock node manager
    node_manager = create_node_manager()

    # Create scheduler
    scheduler = Scheduler(node_manager)

    # Create mock nodes
    nodes = [
        PhysicalNode(ip_address="192.168.1.10", hostname="node1", status=NodeStatus.IDLE),
        PhysicalNode(ip_address="192.168.1.11", hostname="node2", status=NodeStatus.IDLE),
        PhysicalNode(ip_address="192.168.1.12", hostname="node3", status=NodeStatus.IDLE),
    ]

    # Create mock chunks
    chunks = [
        TaskChunk(task_id="chunk_1", iterations=1000, chunk_size=100, status=TaskStatus.PENDING),
        TaskChunk(task_id="chunk_2", iterations=1000, chunk_size=100, status=TaskStatus.PENDING),
        TaskChunk(task_id="chunk_3", iterations=1000, chunk_size=100, status=TaskStatus.PENDING),
    ]

    logger.info("Starting task distribution...")
    results = scheduler.distribute_tasks(chunks, nodes)

    logger.info(f"Completed {len(results)} tasks.")
    for r in results:
        logger.info(f"Task {r.task_id}: {r.wall_clock_time:.4f}s, {r.ops_per_sec:.2f} ops/sec")

    logger.info("Node stats:")
    for ip, stat in scheduler.get_node_stats().items():
        logger.info(f"  {ip}: {stat}")

if __name__ == "__main__":
    main()
