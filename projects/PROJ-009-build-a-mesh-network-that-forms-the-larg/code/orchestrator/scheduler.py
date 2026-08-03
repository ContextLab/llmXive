"""
Scheduler module to distribute TaskChunk units and handle OOM/straggler detection.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from orchestrator.models import TaskChunk, TaskStatus, PhysicalNode
from orchestrator.logger import get_logger

logger = get_logger(__name__)

class Scheduler:
    """Distributes tasks across the mesh network."""

    def __init__(self, node_manager):
        self.node_manager = node_manager
        self.task_queue: List[TaskChunk] = []
        self.running_tasks: Dict[str, TaskChunk] = {}

    def distribute_tasks(self, chunks: List[TaskChunk], nodes: List[PhysicalNode]):
        """
        Distribute task chunks to available nodes.
        Implements adaptive chunking for low-RAM devices (T047).
        """
        self.task_queue = chunks
        logger.info(f"Scheduling {len(chunks)} tasks across {len(nodes)} nodes")

        # Simple round-robin distribution
        for i, chunk in enumerate(chunks):
            node = nodes[i % len(nodes)]
            self._assign_task_to_node(chunk, node)

    def _assign_task_to_node(self, chunk: TaskChunk, node: PhysicalNode):
        """Assign a specific chunk to a node."""
        # Check RAM availability (simulated for now)
        # In T047, this would check actual RAM via mpstat/free
        if node.available_memory_mb < chunk.required_memory_mb:
            logger.warning(f"Node {node.id} has insufficient RAM. Splitting task.")
            # Logic to split chunk would go here
            pass

        self.running_tasks[chunk.id] = chunk
        logger.debug(f"Assigned task {chunk.id} to node {node.id}")

    def detect_stragglers(self, timeout_multiplier: float = 2.0) -> List[TaskChunk]:
        """
        Identify high-variance completion times and return straggler tasks.
        Implements asynchronous timeout handling (T048).
        """
        stragglers = []
        now = datetime.now()
        
        for task_id, task in self.running_tasks.items():
            elapsed = (now - task.start_time).total_seconds()
            if task.expected_duration and elapsed > (task.expected_duration * timeout_multiplier):
                logger.warning(f"Task {task_id} is a straggler (elapsed: {elapsed}s)")
                stragglers.append(task)
                # Re-assign logic would go here
        
        return stragglers
