"""
Scheduler module for distributing TaskChunk units across the mesh network.
Handles adaptive chunking, OOM detection, straggler handling, and re-queuing.
"""
from __future__ import annotations

import logging
import time
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from orchestrator.node_manager import NodeManager, NodeDiscoveryError
from orchestrator.models import PhysicalNode, TaskChunk, TaskStatus, NodeStatus
from orchestrator.logger import get_logger
from orchestrator.completion_feedback import CompletionFeedbackManager, TaskFeedback
from orchestrator.remote_wall_clock_timer import RemoteWallClockTimer, WallClockTimerError

logger = get_logger(__name__)


class SchedulerError(Exception):
    """Base exception for scheduler errors."""
    pass


class OOMError(SchedulerError):
    """Raised when an Out-Of-Memory event is detected on a remote node."""
    pass


class StragglerDetectedError(SchedulerError):
    """Raised when a task exceeds the straggler threshold (2x median time)."""
    pass


class NodeState(Enum):
    """Current state of a node in the scheduler."""
    IDLE = "idle"
    BUSY = "busy"
    UNAVAILABLE = "unavailable"
    RECOVERING = "recovering"


@dataclass
class TaskAssignment:
    """Tracks the state of an assigned task."""
    task_id: str
    node_id: str
    chunk: TaskChunk
    start_time: datetime
    status: TaskStatus = TaskStatus.RUNNING
    end_time: Optional[datetime] = None
    wall_clock_time: Optional[float] = None
    requeue_count: int = 0


class Scheduler:
    """
    Distributes TaskChunk units to PhysicalNodes.
    Implements adaptive chunking, OOM detection, straggler handling, and re-queuing.
    """

    def __init__(
        self,
        node_manager: NodeManager,
        feedback_manager: CompletionFeedbackManager,
        remote_timer: RemoteWallClockTimer,
        straggler_multiplier: float = 2.0,
        min_chunk_size: int = 1000
    ):
        """
        Initialize the scheduler.

        Args:
            node_manager: Instance to handle SSH connections and node discovery.
            feedback_manager: Instance to handle task completion feedback.
            remote_timer: Instance to capture wall-clock times remotely.
            straggler_multiplier: Multiplier for median time to detect stragglers (default 2.0).
            min_chunk_size: Minimum chunk size to prevent infinite splitting.
        """
        self.node_manager = node_manager
        self.feedback_manager = feedback_manager
        self.remote_timer = remote_timer
        self.straggler_multiplier = straggler_multiplier
        self.min_chunk_size = min_chunk_size

        self.node_states: Dict[str, NodeState] = {}
        self.assigned_tasks: Dict[str, TaskAssignment] = {}
        self.pending_chunks: List[TaskChunk] = []
        self.task_history: List[TaskAssignment] = []

        # Initialize node states
        for node in self.node_manager.nodes:
            self.node_states[node.ip] = NodeState.IDLE

    def _query_available_ram(self, node_ip: str) -> int:
        """
        Query available RAM on a remote node via SSH.
        Returns available RAM in MB.
        """
        try:
            # Execute 'free -m' and parse the output
            # Expected format:
            #              total        used        free      shared  buff/cache   available
            # Mem:           7983        2345        1234          12        4403        5234
            # Swap:             0           0           0
            command = "free -m | awk '/^Mem:/ {print $7}'"
            stdout, stderr, exit_code = self.node_manager.execute_command(
                node_ip, command, timeout=5
            )

            if exit_code != 0:
                logger.warning(f"Failed to query RAM on {node_ip}: {stderr}")
                return 0

            output = stdout.strip()
            if not output:
                return 0

            return int(output)
        except Exception as e:
            logger.error(f"Error querying RAM on {node_ip}: {e}")
            return 0

    def _split_chunk_adaptively(
        self, chunk: TaskChunk, node_ip: str
    ) -> List[TaskChunk]:
        """
        Dynamically split a TaskChunk if available RAM is insufficient.
        Recursive splitting: new_chunk_size = chunk_size / 2 until new_chunk_size < available_ram.
        """
        available_ram = self._query_available_ram(node_ip)
        logger.debug(f"Node {node_ip} has {available_ram}MB available RAM.")

        if available_ram == 0:
            # If we can't determine RAM, assume it's safe to proceed with original chunk
            # or fail loudly. Here we proceed with original to avoid blocking.
            return [chunk]

        current_chunk = chunk
        chunks_to_return = []

        # If the chunk size (in iterations) is too large for available RAM
        # We estimate RAM usage: roughly 1MB per 100k iterations (heuristic)
        # This is a simplified model; real usage depends on implementation
        estimated_ram_needed = (current_chunk.iterations // 100000) + 1

        while estimated_ram_needed > available_ram:
            if current_chunk.iterations <= self.min_chunk_size:
                logger.warning(
                    f"Chunk size {current_chunk.iterations} is below minimum "
                    f"{self.min_chunk_size}. Cannot split further."
                )
                break

            # Split in half
            new_size = current_chunk.iterations // 2
            if new_size < self.min_chunk_size:
                new_size = self.min_chunk_size

            # Create new chunk
            new_chunk = TaskChunk(
                chunk_id=f"{current_chunk.chunk_id}_split_{len(chunks_to_return)}",
                iterations=new_size,
                start_idx=current_chunk.start_idx,
                end_idx=current_chunk.start_idx + new_size,
                node_id=current_chunk.node_id
            )
            chunks_to_return.append(new_chunk)

            # Update current chunk for next iteration
            current_chunk = TaskChunk(
                chunk_id=f"{current_chunk.chunk_id}_remainder",
                iterations=current_chunk.iterations - new_size,
                start_idx=current_chunk.start_idx + new_size,
                end_idx=current_chunk.end_idx,
                node_id=current_chunk.node_id
            )
            estimated_ram_needed = (current_chunk.iterations // 100000) + 1

        if current_chunk.iterations > 0:
            chunks_to_return.append(current_chunk)

        return chunks_to_return

    def _parse_oom_signals(self, node_ip: str, log_output: str) -> bool:
        """
        Detect OOM signals from remote logs.
        Returns True if OOM is detected.
        """
        oom_indicators = [
            r"Out of memory:",
            r"OOM killer:",
            r"Kill process.*\(.*\) score.*or.*",
            r"Memory allocation failed",
            r"SIGKILL.*memory"
        ]
        for pattern in oom_indicators:
            if re.search(pattern, log_output, re.IGNORECASE):
                logger.warning(f"OOM detected on node {node_ip}")
                return True
        return False

    def _detect_straggler(self, task_id: str, task_time: float) -> bool:
        """
        Check if a task is a straggler (time > 2x median of completed tasks).
        """
        # Collect times of completed tasks
        completed_times = [
            a.wall_clock_time
            for a in self.task_history
            if a.wall_clock_time is not None and a.task_id != task_id
        ]

        if not completed_times:
            return False

        median_time = sorted(completed_times)[len(completed_times) // 2]
        threshold = median_time * self.straggler_multiplier

        if task_time > threshold:
            logger.warning(
                f"Straggler detected: task {task_id} took {task_time:.2f}s "
                f"(threshold: {threshold:.2f}s, median: {median_time:.2f}s). "
                f"Logging 'heterogeneity penalty'."
            )
            return True
        return False

    def _reassign_task(self, task_id: str, new_node_ip: str) -> bool:
        """
        Reassign a task to a new node.
        """
        if task_id not in self.assigned_tasks:
            logger.error(f"Task {task_id} not found for reassignment.")
            return False

        assignment = self.assigned_tasks[task_id]
        old_node = assignment.node_id

        logger.info(f"Reassigning task {task_id} from {old_node} to {new_node_ip}")

        # Update state
        self.node_states[old_node] = NodeState.IDLE
        self.node_states[new_node_ip] = NodeState.BUSY

        # Update assignment
        assignment.node_id = new_node_ip
        assignment.requeue_count += 1
        assignment.start_time = datetime.now(timezone.utc)

        # Add back to pending if not already handled by feedback loop
        # For simplicity, we assume the feedback loop handles re-queuing
        # This method is called when we detect a problem and need to move it
        return True

    def assign_chunk(self, chunk: TaskChunk, node: PhysicalNode) -> Optional[str]:
        """
        Assign a TaskChunk to a node, handling adaptive chunking.

        Args:
            chunk: The task chunk to assign.
            node: The target physical node.

        Returns:
            The assigned task ID, or None if assignment failed.
        """
        if node.ip not in self.node_states:
            self.node_states[node.ip] = NodeState.IDLE

        if self.node_states[node.ip] != NodeState.IDLE:
            logger.warning(f"Node {node.ip} is not idle. Skipping assignment.")
            return None

        # Adaptive chunking
        chunks = self._split_chunk_adaptively(chunk, node.ip)

        task_ids = []
        for c in chunks:
            task_id = f"task_{c.chunk_id}_{node.ip}_{int(time.time())}"
            c.node_id = node.ip

            # Start remote timer
            try:
                self.remote_timer.start_timer(node.ip, task_id)
            except WallClockTimerError as e:
                logger.error(f"Failed to start timer on {node.ip}: {e}")
                continue

            assignment = TaskAssignment(
                task_id=task_id,
                node_id=node.ip,
                chunk=c,
                start_time=datetime.now(timezone.utc)
            )
            self.assigned_tasks[task_id] = assignment
            self.node_states[node.ip] = NodeState.BUSY

            # Notify completion feedback manager
            self.feedback_manager.receive_task_status(
                node_id=node.ip,
                task_id=task_id,
                status=TaskStatus.RUNNING
            )

            task_ids.append(task_id)
            logger.info(f"Assigned chunk {c.chunk_id} to node {node.ip} as {task_id}")

        return task_ids[0] if task_ids else None

    def monitor_task(self, task_id: str) -> bool:
        """
        Monitor a running task for OOM, straggler, or heartbeat loss.
        Returns True if task is still healthy, False if action needed.

        This method is typically called periodically in a main loop.
        For this implementation, we simulate the check.
        """
        if task_id not in self.assigned_tasks:
            logger.warning(f"Task {task_id} not found in assigned tasks.")
            return True

        assignment = self.assigned_tasks[task_id]
        node_ip = assignment.node_id

        # Check heartbeat (via node_manager)
        try:
            is_healthy = self.node_manager.ping_node(node_ip, timeout=2)
            if not is_healthy:
                logger.warning(f"Heartbeat lost for node {node_ip}. Re-queuing task {task_id}.")
                # Find a new node
                new_node_ip = self._find_available_node()
                if new_node_ip:
                    self._reassign_task(task_id, new_node_ip)
                return False
        except Exception as e:
            logger.error(f"Error checking heartbeat for {node_ip}: {e}")
            # Assume lost, try to reassign
            new_node_ip = self._find_available_node()
            if new_node_ip:
                self._reassign_task(task_id, new_node_ip)
            return False

        # Check for OOM (would typically read logs, here we simulate or check a flag)
        # In a real system, we'd poll logs or check dmesg
        # For this implementation, we assume the feedback loop handles OOM signals
        # and we just check the task state.

        # Check for straggler
        current_time = datetime.now(timezone.utc)
        elapsed = (current_time - assignment.start_time).total_seconds()

        if assignment.wall_clock_time is not None:
            # Task completed, check if it was a straggler
            if self._detect_straggler(task_id, assignment.wall_clock_time):
                # Log penalty, but task is done
                pass

        return True

    def _find_available_node(self) -> Optional[str]:
        """Find an idle node for reassignment."""
        for ip, state in self.node_states.items():
            if state == NodeState.IDLE:
                return ip
        return None

    def handle_task_completion(
        self,
        node_id: str,
        task_id: str,
        status: TaskStatus,
        wall_clock_time: Optional[float] = None,
        log_output: Optional[str] = None
    ) -> bool:
        """
        Handle task completion feedback.
        Checks for OOM, records metrics, and manages state.
        """
        if task_id not in self.assigned_tasks:
            logger.warning(f"Task {task_id} not found in assigned tasks.")
            return False

        assignment = self.assigned_tasks[task_id]

        # Stop remote timer
        try:
            self.remote_timer.stop_timer(node_id, task_id)
        except WallClockTimerError as e:
            logger.error(f"Failed to stop timer for {task_id}: {e}")

        # Check for OOM
        if log_output and self._parse_oom_signals(node_id, log_output):
            logger.error(f"OOM detected for task {task_id} on {node_id}. Re-queuing.")
            # Find new node
            new_node_ip = self._find_available_node()
            if new_node_ip:
                # Create new chunk from the failed one
                new_chunk = TaskChunk(
                    chunk_id=f"{assignment.chunk.chunk_id}_retry",
                    iterations=assignment.chunk.iterations,
                    start_idx=assignment.chunk.start_idx,
                    end_idx=assignment.chunk.end_idx,
                    node_id=new_node_ip
                )
                # Re-assign
                self.assign_chunk(new_chunk, self.node_manager.get_node_by_ip(new_node_ip))
                # Remove old assignment
                del self.assigned_tasks[task_id]
                return False
            else:
                logger.error("No available nodes for OOM re-queue.")
                return False

        # Record completion
        assignment.status = status
        assignment.end_time = datetime.now(timezone.utc)
        assignment.wall_clock_time = wall_clock_time

        # Update node state
        self.node_states[node_id] = NodeState.IDLE

        # Move to history
        self.task_history.append(assignment)
        del self.assigned_tasks[task_id]

        logger.info(f"Task {task_id} completed on {node_id} in {wall_clock_time}s")

        return True

    def get_pending_chunks(self) -> List[TaskChunk]:
        """Return list of pending chunks."""
        return self.pending_chunks

    def add_pending_chunk(self, chunk: TaskChunk) -> None:
        """Add a chunk to the pending queue."""
        self.pending_chunks.append(chunk)

    def run_scheduling_loop(
        self,
        chunks: List[TaskChunk],
        timeout: Optional[float] = None
    ) -> List[TaskAssignment]:
        """
        Main scheduling loop: assign chunks, monitor, and collect results.

        Args:
            chunks: List of task chunks to process.
            timeout: Optional timeout for the entire loop.

        Returns:
            List of completed task assignments.
        """
        self.pending_chunks = list(chunks)
        start_time = time.time()

        while self.pending_chunks or self.assigned_tasks:
            if timeout and (time.time() - start_time) > timeout:
                logger.error("Scheduling loop timeout exceeded.")
                break

            # Assign pending chunks to idle nodes
            for chunk in list(self.pending_chunks):
                if not self.pending_chunks:
                    break
                for node in self.node_manager.nodes:
                    if self.node_states.get(node.ip) == NodeState.IDLE:
                        assigned_id = self.assign_chunk(chunk, node)
                        if assigned_id:
                            self.pending_chunks.remove(chunk)
                            break

            # Monitor running tasks
            for task_id in list(self.assigned_tasks.keys()):
                self.monitor_task(task_id)

            # Small sleep to prevent busy-waiting
            time.sleep(0.5)

        return list(self.task_history)

    def main(self) -> None:
        """Main entry point for the scheduler."""
        logger.info("Scheduler main entry point.")
        # This would typically be called by an orchestrator
        pass


def create_scheduler(
    node_manager: NodeManager,
    feedback_manager: CompletionFeedbackManager,
    remote_timer: RemoteWallClockTimer
) -> Scheduler:
    """Factory function to create a Scheduler instance."""
    return Scheduler(node_manager, feedback_manager, remote_timer)


def main() -> None:
    """Main function for standalone execution."""
    logger.info("Scheduler module main function.")
    # Example usage would require real node_manager, feedback_manager, etc.
    pass
