"""
Scheduler module for distributing TaskChunk units across PhysicalNodes.
Handles load balancing, OOM detection, and straggler management.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set

from orchestrator.models import TaskChunk, TaskStatus, PhysicalNode, NodeStatus
from orchestrator.logger import get_logger
from orchestrator.config import get_config
from orchestrator.runner import run_with_hard_timeout, ExecutionTimeoutError

logger = get_logger(__name__)


@dataclass
class NodeState:
    """Tracks the runtime state of a node for the scheduler."""
    node: PhysicalNode
    assigned_tasks: List[TaskChunk] = field(default_factory=list)
    available_ram_mb: float = 0.0
    is_straggler: bool = False
    last_heartbeat: datetime = field(default_factory=datetime.now)
    status: NodeStatus = NodeStatus.IDLE
    current_task: Optional[TaskChunk] = None

class Scheduler:
    """
    Distributes TaskChunk units to PhysicalNodes.
    Implements OOM avoidance via RAM checks and straggler detection.
    """

    def __init__(self, nodes: List[PhysicalNode], config: Optional[Dict[str, Any]] = None):
        self.nodes = {node.node_id: node for node in nodes}
        self.node_states: Dict[str, NodeState] = {}
        self.task_queue: List[TaskChunk] = []
        self.completed_tasks: List[TaskChunk] = []
        self.failed_tasks: List[TaskChunk] = []
        self.config = config or get_config()
        
        # Initialize node states
        for node_id, node in self.nodes.items():
            self.node_states[node_id] = NodeState(
                node=node,
                available_ram_mb=node.total_memory_mb, # Assume full initially
                status=NodeStatus.IDLE
            )

    def _estimate_task_memory(self, task: TaskChunk) -> float:
        """
        Estimates memory required for a task based on its size/parameters.
        This is a heuristic; real OOM detection comes from node feedback.
        """
        # Base overhead + estimate based on data size or complexity
        base_overhead_mb = 50.0
        size_factor = task.size_mb if task.size_mb else 10.0
        return base_overhead_mb + (size_factor * 1.5)

    def _check_oom_risk(self, node_state: NodeState, task: TaskChunk) -> bool:
        """
        Checks if assigning the task would likely cause an OOM on the node.
        Returns True if risk is detected.
        """
        estimated_needed = self._estimate_task_memory(task)
        available = node_state.available_ram_mb
        
        # Safety margin of 10%
        if available < (estimated_needed * 1.1):
            logger.warning(
                f"OOM risk detected for task {task.task_id} on node {node_state.node.node_id}. "
                f"Need {estimated_needed:.1f}MB, have {available:.1f}MB."
            )
            return True
        return False

    def _find_best_node(self, task: TaskChunk) -> Optional[str]:
        """
        Finds the best available node for a task based on:
        1. Not a straggler (unless all are)
        2. Sufficient RAM (OOM check)
        3. Lowest current load (number of assigned tasks)
        """
        candidates = []

        for node_id, state in self.node_states.items():
            if state.status == NodeStatus.OFFLINE:
                continue
            
            # Check OOM risk
            if self._check_oom_risk(state, task):
                continue

            # Prefer non-stragglers
            penalty = 100 if state.is_straggler else 0
            load_penalty = len(state.assigned_tasks) * 10
            
            score = penalty + load_penalty
            candidates.append((score, node_id))

        if not candidates:
            logger.error("No suitable nodes found for task. All offline or OOM risk.")
            return None

        # Sort by score (lowest is best)
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    def assign_tasks(self, tasks: List[TaskChunk]) -> Dict[str, List[TaskChunk]]:
        """
        Assigns a list of tasks to available nodes.
        Returns a dict mapping node_id to list of assigned task_ids.
        """
        self.task_queue = list(tasks)
        assignments: Dict[str, List[TaskChunk]] = defaultdict(list)

        # Simple round-robin / best-fit assignment
        while self.task_queue:
            task = self.task_queue.pop(0)
            target_node_id = self._find_best_node(task)

            if target_node_id:
                state = self.node_states[target_node_id]
                state.assigned_tasks.append(task)
                state.status = NodeStatus.BUSY
                assignments[target_node_id].append(task)
                logger.debug(f"Assigned task {task.task_id} to node {target_node_id}")
            else:
                # No node available, push back to queue or mark as failed
                logger.warning(f"Could not assign task {task.task_id} to any node. Re-queueing.")
                self.task_queue.append(task)
                # Prevent infinite loop if all nodes are dead
                if len(self.task_queue) > len(tasks) * 2:
                    logger.critical("Task queue stalled. Breaking loop.")
                    break

        return dict(assignments)

    def handle_task_complete(self, node_id: str, task_id: str, result_data: Optional[Dict] = None):
        """
        Called when a task finishes successfully on a node.
        Updates node state and RAM availability if reported.
        """
        state = self.node_states.get(node_id)
        if not state:
            logger.error(f"Task completion reported for unknown node {node_id}")
            return

        # Remove from assigned list
        state.assigned_tasks = [t for t in state.assigned_tasks if t.task_id != task_id]
        state.current_task = None
        state.status = NodeStatus.IDLE

        # Update RAM if reported in result
        if result_data and 'available_memory_mb' in result_data:
            state.available_ram_mb = result_data['available_memory_mb']

        # Find task object
        task = next((t for t in self.completed_tasks + self.failed_tasks if t.task_id == task_id), None)
        if task:
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.now()

    def handle_oom_event(self, node_id: str, task_id: str):
        """
        Handles an OOM event. Reduces available RAM estimate for the node
        and re-queues the task for a different node.
        """
        logger.error(f"OOM detected on node {node_id} for task {task_id}")
        state = self.node_states.get(node_id)
        if state:
            # Penalize node RAM estimate to avoid future assignments
            state.available_ram_mb *= 0.8 
            state.is_straggler = True # Temporary straggler status
        
        # Re-queue task
        task = next((t for t in self.completed_tasks + self.failed_tasks if t.task_id == task_id), None)
        if task:
            task.status = TaskStatus.PENDING
            self.task_queue.append(task)

    def detect_stragglers(self, timeout_seconds: float = 300.0):
        """
        Marks nodes as stragglers if they haven't reported progress within timeout.
        """
        now = datetime.now()
        for node_id, state in self.node_states.items():
            if state.status == NodeStatus.BUSY and state.current_task:
                elapsed = (now - state.last_heartbeat).total_seconds()
                if elapsed > timeout_seconds:
                    logger.warning(
                        f"Straggler detected: Node {node_id} has not updated in {elapsed:.1f}s. "
                        f"Task {state.current_task.task_id} may be stuck."
                    )
                    state.is_straggler = True
                    # Optional: Trigger re-assignment logic here if needed

    def reassign_straggler_tasks(self):
        """
        Re-assigns tasks from nodes marked as stragglers.
        """
        tasks_to_reassign = []
        for node_id, state in self.node_states.items():
            if state.is_straggler and state.current_task:
                tasks_to_reassign.append(state.current_task)
                state.current_task = None
                state.status = NodeStatus.IDLE
                state.is_straggler = False # Reset for retry

        for task in tasks_to_reassign:
            task.status = TaskStatus.PENDING
            self.task_queue.append(task)
            logger.info(f"Re-assigning straggler task {task.task_id}")

    def get_summary(self) -> Dict[str, Any]:
        """Returns a summary of the scheduler's current state."""
        return {
            "total_nodes": len(self.nodes),
            "active_nodes": sum(1 for s in self.node_states.values() if s.status != NodeStatus.OFFLINE),
            "stragglers": sum(1 for s in self.node_states.values() if s.is_straggler),
            "pending_tasks": len(self.task_queue),
            "completed_tasks": len([t for t in self.completed_tasks if t.status == TaskStatus.COMPLETED]),
            "failed_tasks": len([t for t in self.failed_tasks if t.status == TaskStatus.FAILED])
        }

def main():
    """
    Entry point for standalone testing or CLI usage of the scheduler.
    Simulates a simple assignment scenario.
    """
    logger.info("Scheduler module initialized.")
    
    # Create mock nodes for demonstration
    nodes = [
        PhysicalNode(
            node_id="node-001", 
            hostname="192.168.1.10", 
            status=NodeStatus.IDLE,
            total_memory_mb=8192,
            cpu_cores=4
        ),
        PhysicalNode(
            node_id="node-002", 
            hostname="192.168.1.11", 
            status=NodeStatus.IDLE,
            total_memory_mb=4096,
            cpu_cores=2
        )
    ]

    # Create mock tasks
    tasks = [
        TaskChunk(task_id="task-001", size_mb=100, complexity=1.0),
        TaskChunk(task_id="task-002", size_mb=500, complexity=2.5),
        TaskChunk(task_id="task-003", size_mb=200, complexity=1.2),
    ]

    scheduler = Scheduler(nodes)
    assignments = scheduler.assign_tasks(tasks)

    logger.info(f"Assignments: {assignments}")
    logger.info(f"Summary: {scheduler.get_summary()}")

    # Simulate completion
    if "node-001" in assignments:
        scheduler.handle_task_complete("node-001", "task-001", {"available_memory_mb": 7000})
        logger.info("Simulated task completion.")

    logger.info(f"Final Summary: {scheduler.get_summary()}")

if __name__ == "__main__":
    main()
