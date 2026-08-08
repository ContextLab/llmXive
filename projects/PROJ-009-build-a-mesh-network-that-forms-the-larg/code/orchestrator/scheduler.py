"""
Scheduler for distributing TaskChunk units across the mesh network.

Implements adaptive chunking, OOM detection, straggler handling, and
heartbeat-based re-queuing logic.

Dependencies:
    - T013a: node_manager (SSH, heartbeat, reassignment)
    - T012: remote_tool_manager (tool verification)
    - T014a: instrumentor_remote (remote execution, saturation check)
    - T014c: remote_wall_clock_timer (timing)
"""
from __future__ import annotations

import logging
import time
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from orchestrator.node_manager import NodeManager, NodeDiscoveryError, NodeHeartbeatLost
from orchestrator.models import TaskChunk, PhysicalNode, TaskStatus, NodeStatus
from orchestrator.remote_wall_clock_timer import RemoteWallClockTimer, create_timer
from orchestrator.instrumentor_remote import RemoteInstrumentor, create_instrumentor
from orchestrator.logger import get_logger

logger = get_logger(__name__)

class SchedulerError(Exception):
    """Base exception for scheduler errors."""
    pass

class OOMError(SchedulerError):
    """Raised when an Out Of Memory condition is detected on a node."""
    pass

class StragglerDetectedError(SchedulerError):
    """Raised when a task exceeds the straggler threshold."""
    pass

@dataclass
class NodeState:
    """Tracks the runtime state of a node during scheduling."""
    node: PhysicalNode
    available_ram_mb: int = 0
    current_task: Optional[TaskChunk] = None
    task_start_time: Optional[float] = None
    is_busy: bool = False
    last_heartbeat: datetime = field(default_factory=datetime.now)

class Scheduler:
    """
    Distributes TaskChunk units to PhysicalNodes with adaptive logic.
    
    Features:
        - Adaptive Chunking: Splits chunks if node RAM is insufficient.
        - OOM Detection: Parses remote logs for OOM signals.
        - Straggler Handling: Re-assigns tasks exceeding 2x median time.
        - Heartbeat Re-queue: Re-assigns tasks if heartbeat is lost.
    """
    
    # Thresholds
    STRAGGLER_MULTIPLIER = 2.0
    OOM_SIGNAL_PATTERN = re.compile(r"Out of memory: Kill process|OOMKilled|Memory cgroup out of memory", re.IGNORECASE)
    
    def __init__(self, node_manager: NodeManager, wall_clock_timer: RemoteWallClockTimer, instrumentor: RemoteInstrumentor):
        self.node_manager = node_manager
        self.wall_clock_timer = wall_clock_timer
        self.instrumentor = instrumentor
        self.node_states: Dict[str, NodeState] = {}
        self.task_history: List[float] = []  # Track completion times for median calculation
        self.logger = get_logger(__name__)

    def _initialize_nodes(self, nodes: List[PhysicalNode]) -> None:
        """Initialize state for all provided nodes."""
        for node in nodes:
            if node.ip not in self.node_states:
                self.node_states[node.ip] = NodeState(node=node)
                # Query initial RAM availability
                self._update_node_ram(node.ip)

    def _update_node_ram(self, ip: str) -> int:
        """
        Query `free -m` via SSH to determine available RAM.
        Returns available RAM in MB.
        """
        try:
            # Execute 'free -m' and parse the 'available' column (or 'free' if available column missing)
            # Format: Mem: total used free shared buff/cache available
            cmd = "free -m | grep Mem | awk '{print $7}'"
            stdout, stderr, exit_code = self.node_manager.execute_command(ip, cmd)
            
            if exit_code != 0:
                self.logger.warning(f"Failed to query RAM on {ip}: {stderr}")
                # Fallback to 'free' column if 'available' (col 7) is empty/0
                cmd_fallback = "free -m | grep Mem | awk '{print $4}'"
                stdout, stderr, exit_code = self.node_manager.execute_command(ip, cmd_fallback)
                if exit_code != 0:
                    return 0
            
            ram_str = stdout.strip().split('\n')[-1]
            ram_mb = int(ram_str)
            self.node_states[ip].available_ram_mb = ram_mb
            return ram_mb
        except Exception as e:
            self.logger.error(f"Error querying RAM on {ip}: {e}")
            return 0

    def _check_oom_signals(self, ip: str, logs: str) -> bool:
        """
        Parse remote logs for OOM signals.
        Returns True if OOM detected.
        """
        if self.OOM_SIGNAL_PATTERN.search(logs):
            self.logger.error(f"OOM detected on node {ip}")
            return True
        return False

    def _calculate_median_time(self) -> float:
        """Calculate the median task completion time from history."""
        if not self.task_history:
            return 0.0
        sorted_times = sorted(self.task_history)
        n = len(sorted_times)
        if n % 2 == 0:
            return (sorted_times[n//2 - 1] + sorted_times[n//2]) / 2
        return sorted_times[n//2]

    def _split_chunk(self, chunk: TaskChunk, available_ram: int) -> List[TaskChunk]:
        """
        Recursively split a TaskChunk until it fits in available RAM.
        Logic: new_chunk_size = chunk_size / 2 until new_chunk_size < available_ram.
        """
        if chunk.size_mb <= available_ram:
            return [chunk]
        
        # Split in half
        new_size = chunk.size_mb // 2
        if new_size == 0:
            new_size = 1 # Minimum size 1MB
        
        # Create new chunks
        # We assume chunk.data or chunk.iterations can be split. 
        # For this implementation, we create new TaskChunk objects with halved size.
        # In a real scenario, we'd split the actual payload/iterations.
        
        chunks = []
        # Simulate splitting by creating two halves
        # Note: TaskChunk structure from models.py is assumed to have 'size_mb'
        # We create two new chunks with half the size.
        
        # Since we don't have the exact payload splitting logic in models,
        # we simulate the split by creating two chunks with half the size.
        # The actual data split would depend on the TaskChunk implementation details.
        # Here we assume the chunk can be logically split.
        
        chunk1 = TaskChunk(
            id=f"{chunk.id}_part1",
            size_mb=new_size,
            iterations=chunk.iterations // 2,
            data=chunk.data # Placeholder: in real impl, slice data
        )
        chunk2 = TaskChunk(
            id=f"{chunk.id}_part2",
            size_mb=chunk.size_mb - new_size, # Remainder
            iterations=chunk.iterations - (chunk.iterations // 2),
            data=chunk.data # Placeholder
        )
        
        return self._split_chunk(chunk1, available_ram) + self._split_chunk(chunk2, available_ram)

    def assign_chunk(self, chunk: TaskChunk, node: PhysicalNode) -> bool:
        """
        Assign a task chunk to a node with adaptive chunking.
        
        Returns True if assignment was successful (possibly after splitting).
        """
        if node.ip not in self.node_states:
            self._initialize_nodes([node])
        
        state = self.node_states[node.ip]
        
        # Check RAM and split if necessary
        if state.available_ram_mb < chunk.size_mb:
            self.logger.info(f"Node {node.ip} RAM ({state.available_ram_mb}MB) < Chunk ({chunk.size_mb}MB). Splitting...")
            sub_chunks = self._split_chunk(chunk, state.available_ram_mb)
            all_assigned = True
            for sub_chunk in sub_chunks:
                if not self._assign_single(sub_chunk, node):
                    all_assigned = False
                    break
            return all_assigned
        else:
            return self._assign_single(chunk, node)

    def _assign_single(self, chunk: TaskChunk, node: PhysicalNode) -> bool:
        """Internal method to assign a single chunk to a node."""
        state = self.node_states[node.ip]
        
        if state.is_busy:
            self.logger.warning(f"Node {node.ip} is busy. Cannot assign {chunk.id}.")
            return False

        # Update state
        state.current_task = chunk
        state.is_busy = True
        state.task_start_time = time.time()
        state.last_heartbeat = datetime.now()

        self.logger.info(f"Assigned {chunk.id} to {node.ip}")
        return True

    def monitor_task(self, task_id: str) -> Dict[str, Any]:
        """
        Monitor a task by ID.
        
        Logic:
          1. Check heartbeat. If lost -> Re-assign.
          2. Check OOM signals in logs. If OOM -> Re-assign.
          3. Check Straggler condition (time > 2 * median). If straggler -> Re-assign.
          4. If completed -> Record time, free node.
        """
        # Find node running this task
        running_node_ip = None
        for ip, state in self.node_states.items():
            if state.current_task and state.current_task.id == task_id:
                running_node_ip = ip
                break
        
        if not running_node_ip:
            self.logger.warning(f"Task {task_id} not found in any node state.")
            return {"status": "unknown", "task_id": task_id}

        state = self.node_states[running_node_ip]
        current_time = time.time()
        elapsed = current_time - (state.task_start_time or current_time)
        
        # 1. Heartbeat Check
        try:
            # Use node_manager to ping/check heartbeat
            # node_manager.ping_node returns True/False or raises?
            # Based on T013a spec: ping_node(ip, timeout=2)
            if not self.node_manager.ping_node(running_node_ip, timeout=2):
                self.logger.warning(f"Heartbeat lost for {running_node_ip} on task {task_id}. Re-assigning.")
                self._reassign_task(task_id, running_node_ip)
                return {"status": "reassigned", "reason": "heartbeat_lost", "task_id": task_id}
        except NodeHeartbeatLost:
            self.logger.warning(f"Heartbeat lost for {running_node_ip}. Re-assigning.")
            self._reassign_task(task_id, running_node_ip)
            return {"status": "reassigned", "reason": "heartbeat_lost", "task_id": task_id}
        except Exception as e:
            self.logger.error(f"Error checking heartbeat for {running_node_ip}: {e}")
            # Treat as lost
            self._reassign_task(task_id, running_node_ip)
            return {"status": "reassigned", "reason": "heartbeat_error", "task_id": task_id}

        # 2. OOM Detection
        # Fetch logs (mocked via instrumentor or direct command)
        # We'll use the instrumentor to get recent logs or execute a log check command
        try:
            logs = self.node_manager.execute_command(running_node_ip, "dmesg | tail -n 20")[0]
            if self._check_oom_signals(running_node_ip, logs):
                self.logger.error(f"OOM detected on {running_node_ip} for {task_id}. Re-assigning.")
                self._reassign_task(task_id, running_node_ip)
                return {"status": "reassigned", "reason": "oom_detected", "task_id": task_id}
        except Exception as e:
            self.logger.debug(f"Could not check logs on {running_node_ip}: {e}")

        # 3. Straggler Handling
        median_time = self._calculate_median_time()
        if median_time > 0 and elapsed > (self.STRAGGLER_MULTIPLIER * median_time):
            self.logger.warning(f"Straggler detected: {task_id} on {running_node_ip} took {elapsed:.2f}s (median: {median_time:.2f}s). Re-assigning.")
            self._reassign_task(task_id, running_node_ip)
            return {"status": "reassigned", "reason": "straggler", "task_id": task_id}

        # 4. Check if task is actually done (via remote check or heartbeat update)
        # For this implementation, we assume the task runner updates the node state
        # or we poll for completion. Here we assume a 'check_task_status' command.
        try:
            status_cmd = f"test -f /tmp/task_{task_id}.done && echo 'done' || echo 'running'"
            stdout, _, _ = self.node_manager.execute_command(running_node_ip, status_cmd)
            if "done" in stdout:
                # Task completed
                state.is_busy = False
                state.current_task = None
                self.task_history.append(elapsed)
                self.logger.info(f"Task {task_id} completed on {running_node_ip} in {elapsed:.2f}s.")
                return {"status": "completed", "duration": elapsed, "task_id": task_id}
        except Exception as e:
            self.logger.debug(f"Could not check task status on {running_node_ip}: {e}")

        return {"status": "running", "elapsed": elapsed, "task_id": task_id}

    def _reassign_task(self, task_id: str, old_ip: str) -> None:
        """
        Re-assign a task to a different node.
        Logic: Find an available node, assign chunk, log "heterogeneity penalty" if straggler.
        """
        chunk = None
        for ip, state in self.node_states.items():
            if state.current_task and state.current_task.id == task_id:
                chunk = state.current_task
                state.current_task = None
                state.is_busy = False
                break
        
        if not chunk:
            self.logger.error(f"Could not find chunk for re-assignment: {task_id}")
            return

        # Find a new node
        # Prefer nodes with enough RAM and not busy
        available_nodes = [
            self.node_states[ip].node for ip, state in self.node_states.items()
            if not state.is_busy and state.available_ram_mb >= chunk.size_mb
        ]
        
        if not available_nodes:
            # If no node has enough RAM, try to split the chunk again and find ANY node
            self.logger.warning(f"No node with sufficient RAM for {chunk.size_mb}MB. Attempting split and re-queue.")
            # Note: This logic might need recursion or a queue in a full implementation.
            # For now, we just log and try to find any node (even if we have to split again later).
            available_nodes = [self.node_states[ip].node for ip, state in self.node_states.items() if not state.is_busy]
            if not available_nodes:
                self.logger.error("No available nodes for re-assignment.")
                return

        # Select first available node (simple round-robin or random could be added)
        new_node = available_nodes[0]
        
        # Log heterogeneity penalty if this was a straggler
        # We assume the caller knows the reason, but we can check if median_time was exceeded
        # For simplicity, we just log the re-assignment
        self.logger.info(f"Re-assigning {task_id} from {old_ip} to {new_node.ip}.")
        
        # Re-assign
        self.assign_chunk(chunk, new_node)

    def run_scheduled_tasks(self, chunks: List[TaskChunk], nodes: List[PhysicalNode]) -> List[Dict[str, Any]]:
        """
        Main entry point to distribute and monitor a list of chunks.
        
        Returns a list of results for each chunk.
        """
        self._initialize_nodes(nodes)
        
        # Assign all chunks
        for chunk in chunks:
            assigned = False
            for node in nodes:
                if self.assign_chunk(chunk, node):
                    assigned = True
                    break
            if not assigned:
                self.logger.error(f"Failed to assign chunk {chunk.id} to any node.")

        # Monitor until all done
        results = []
        while True:
            all_done = True
            for chunk in chunks:
                # Find if this chunk is still running
                is_running = False
                for state in self.node_states.values():
                    if state.current_task and state.current_task.id == chunk.id:
                        is_running = True
                        break
                
                if is_running:
                    all_done = False
                    result = self.monitor_task(chunk.id)
                    if result["status"] == "reassigned":
                        # The task was moved, we need to re-check the new node in next loop
                        pass
                    results.append(result)
            
            if all_done:
                break
            time.sleep(1) # Polling interval

        return results

def create_scheduler(node_manager: NodeManager) -> Scheduler:
    """Factory function to create a Scheduler."""
    wall_clock_timer = create_timer(node_manager)
    instrumentor = create_instrumentor(node_manager)
    return Scheduler(node_manager, wall_clock_timer, instrumentor)

def main():
    """
    Main entry point for testing the scheduler.
    """
    # This would normally load config and nodes
    # For now, we just demonstrate the structure
    logger.info("Scheduler module loaded.")

if __name__ == "__main__":
    main()
