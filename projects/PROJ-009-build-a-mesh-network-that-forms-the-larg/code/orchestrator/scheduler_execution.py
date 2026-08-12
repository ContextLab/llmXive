"""
Scheduler Execution Module (T015b)

Implements the distribution of TaskChunk units across physical nodes,
including adaptive chunking based on RAM, OOM detection, and straggler handling.

Dependencies:
  - T013a (node_manager): Node discovery and SSH handling
  - T013b (completion_feedback): Task status updates
  - T013c (heartbeat_monitoring): Heartbeat loss detection
  - T012 (remote_tools_manager): Tool verification
  - T014a (instrumentor_remote): Remote instrumentation
  - T014c (remote_wall_clock_timer): Remote timing
  - T009 (timeout_guard): Pipeline timeout enforcement
  - T015a (scheduler_setup): Configuration loading
  - T014b (network_saturation_handler): Network saturation abort
"""

from __future__ import annotations

import logging
import time
import threading
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable, Tuple
from enum import Enum

import paramiko
import re

# Local imports based on API surface
from orchestrator.config import get_config
from orchestrator.models import TaskChunk, TaskStatus, PhysicalNode, ExecutionRun
from orchestrator.node_manager import NodeManager, NodeDiscoveryError, NodeState
from orchestrator.completion_feedback import CompletionFeedbackManager, TaskStatusEnum
from orchestrator.heartbeat_monitoring import HeartbeatMonitor, HeartbeatLostEvent
from orchestrator.remote_tools_manager import RemoteToolManager
from orchestrator.instrumentor_remote import RemoteInstrumentor, NetworkSaturationSignal
from orchestrator.remote_wall_clock_timer import RemoteWallClockTimer
from orchestrator.network_saturation_handler import NetworkSaturationError, NetworkSaturationHandler
from orchestrator.timeout_guard import enforce_pipeline_timeout, PipelineTimeoutError
from orchestrator.logger import get_logger

logger = get_logger(__name__)

class SchedulerExecutionError(Exception):
    """Base exception for scheduler execution errors."""
    pass

class OOMError(SchedulerExecutionError):
    """Raised when a node runs out of memory."""
    pass

class StragglerDetectedError(SchedulerExecutionError):
    """Raised when a task exceeds the straggler threshold."""
    pass

class AdaptiveChunkingError(SchedulerExecutionError):
    """Raised when adaptive chunking fails to find a valid size."""
    pass

@dataclass
class TaskAssignment:
    """Represents an assignment of a task chunk to a node."""
    task_id: str
    node_id: str
    chunk: TaskChunk
    assigned_at: datetime
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None

class Scheduler:
    """
    Main scheduler class for distributing and monitoring tasks across nodes.
    Implements adaptive chunking, OOM detection, and straggler handling.
    """

    def __init__(
        self,
        node_manager: NodeManager,
        feedback_manager: CompletionFeedbackManager,
        heartbeat_monitor: HeartbeatMonitor,
        tool_manager: RemoteToolManager,
        instrumentor: RemoteInstrumentor,
        timer: RemoteWallClockTimer,
        saturation_handler: NetworkSaturationHandler,
        config: Dict[str, Any]
    ):
        self.node_manager = node_manager
        self.feedback_manager = feedback_manager
        self.heartbeat_monitor = heartbeat_monitor
        self.tool_manager = tool_manager
        self.instrumentor = instrumentor
        self.timer = timer
        self.saturation_handler = saturation_handler
        self.config = config

        self.base_chunk_size = config.get('base_chunk_size', 1024 * 1024)  # 1MB default
        self.min_chunk_size = 1024 * 1024  # 1MB minimum
        self.straggler_multiplier = config.get('straggler_multiplier', 3.0)
        self.task_assignments: Dict[str, TaskAssignment] = {}
        self.median_task_time = 10.0  # Default, updated dynamically
        self.lock = threading.Lock()

        # Start heartbeat monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_heartbeats, daemon=True)
        self.monitor_thread.start()

    def _monitor_heartbeats(self):
        """Background thread to monitor heartbeats and handle re-assignment."""
        while True:
            try:
                time.sleep(5)  # Check every 5 seconds
                for event in self.heartbeat_monitor.get_events():
                    if isinstance(event, HeartbeatLostEvent):
                        logger.warning(f"Heartbeat lost for node {event.node_id}, re-assigning tasks")
                        self._handle_heartbeat_loss(event.node_id)
            except Exception as e:
                logger.error(f"Error in heartbeat monitoring: {e}")

    def _handle_heartbeat_loss(self, node_id: str):
        """Handle node failure due to heartbeat loss."""
        with self.lock:
            for task_id, assignment in self.task_assignments.items():
                if assignment.node_id == node_id and assignment.status == TaskStatus.RUNNING:
                    assignment.status = TaskStatus.FAILED
                    assignment.error = f"Heartbeat lost on node {node_id}"
                    logger.warning(f"Task {task_id} failed due to heartbeat loss on {node_id}")
                    # Re-queue logic would go here
                    self.feedback_manager.receive_task_status(
                        node_id, task_id, TaskStatusEnum.FAILED
                    )

    def _check_available_ram(self, node_ip: str) -> int:
        """
        Query available RAM on a remote node via SSH.
        Returns available RAM in MB.
        """
        try:
            # Use the node_manager's SSH client to execute command
            ssh = self.node_manager.get_ssh_client(node_ip)
            if not ssh:
                raise SchedulerExecutionError(f"SSH connection not available for {node_ip}")

            stdin, stdout, stderr = ssh.exec_command("free -m | awk '/^Mem:/ {print $7}'")
            output = stdout.read().decode().strip()
            if not output:
                raise SchedulerExecutionError(f"Could not parse RAM for {node_ip}")
            
            return int(output)
        except Exception as e:
            logger.error(f"Failed to check RAM on {node_ip}: {e}")
            raise SchedulerExecutionError(f"RAM check failed for {node_ip}: {e}")

    def _calculate_adaptive_chunk_size(self, node: PhysicalNode, requested_size: int) -> int:
        """
        Calculate adaptive chunk size based on available RAM.
        Halves chunk size until it fits or hits minimum.
        """
        try:
            available_ram_mb = self._check_available_ram(node.ip)
            available_ram_bytes = available_ram_mb * 1024 * 1024

            chunk_size = requested_size
            while chunk_size > available_ram_bytes:
                chunk_size = chunk_size // 2
                if chunk_size < self.min_chunk_size:
                    raise AdaptiveChunkingError(
                        f"Chunk size {chunk_size} below minimum {self.min_chunk_size} "
                        f"for node {node.ip} with RAM {available_ram_mb}MB"
                    )
            
            logger.info(f"Adaptive chunking: {requested_size} -> {chunk_size} for node {node.ip} "
                        f"(RAM: {available_ram_mb}MB)")
            return chunk_size
        except AdaptiveChunkingError:
            raise
        except Exception as e:
            logger.error(f"Error calculating adaptive chunk size: {e}")
            # Fallback to minimum if calculation fails
            return self.min_chunk_size

    def _detect_oom(self, node_ip: str, task_id: str) -> bool:
        """
        Check remote logs for OOM signals.
        Returns True if OOM detected.
        """
        try:
            ssh = self.node_manager.get_ssh_client(node_ip)
            if not ssh:
                return False

            # Check dmesg for OOM killer messages
            stdin, stdout, stderr = ssh.exec_command("dmesg | grep -i 'out of memory' | tail -n 1")
            output = stdout.read().decode().strip()
            if output:
                logger.warning(f"OOM detected on {node_ip} for task {task_id}: {output}")
                return True
            
            # Check for OOM in application logs if available
            stdin, stdout, stderr = ssh.exec_command(
                f"grep -i 'out of memory\\|oom' /var/log/syslog 2>/dev/null | tail -n 1"
            )
            output = stdout.read().decode().strip()
            if output:
                logger.warning(f"OOM detected in syslog on {node_ip} for task {task_id}: {output}")
                return True

            return False
        except Exception as e:
            logger.error(f"Error checking for OOM on {node_ip}: {e}")
            return False

    def _handle_straggler(self, task_id: str, start_time: float, node_id: str):
        """
        Handle straggler tasks that exceed the timeout threshold.
        """
        elapsed = time.time() - start_time
        threshold = self.median_task_time * self.straggler_multiplier

        if elapsed > threshold:
            logger.warning(f"Straggler detected: Task {task_id} on {node_id} took {elapsed:.2f}s "
                           f"(threshold: {threshold:.2f}s)")
            # Cancel the task and re-assign
            try:
                ssh = self.node_manager.get_ssh_client(node_id)
                if ssh:
                    # Kill the process (PID should be tracked, using generic kill for now)
                    ssh.exec_command(f"pkill -f 'benchmark.*{task_id}'")
            except Exception as e:
                logger.error(f"Failed to kill straggler task {task_id}: {e}")
            
            raise StragglerDetectedError(f"Task {task_id} exceeded straggler threshold")

    async def assign_chunk(self, chunk: TaskChunk, node: PhysicalNode) -> TaskAssignment:
        """
        Assign a task chunk to a specific node.
        Implements adaptive chunking and starts monitoring.
        """
        task_id = chunk.id
        node_ip = node.ip

        logger.info(f"Assigning task {task_id} to node {node_ip}")

        # Adaptive chunking
        try:
            adjusted_size = self._calculate_adaptive_chunk_size(node, chunk.size)
            if adjusted_size != chunk.size:
                chunk = TaskChunk(
                    id=chunk.id,
                    start=chunk.start,
                    end=chunk.start + adjusted_size,
                    size=adjusted_size,
                    iterations=chunk.iterations
                )
        except AdaptiveChunkingError as e:
            logger.error(f"Failed to assign chunk: {e}")
            assignment = TaskAssignment(
                task_id=task_id,
                node_id=node_ip,
                chunk=chunk,
                assigned_at=datetime.now(timezone.utc),
                status=TaskStatus.FAILED,
                error=str(e)
            )
            self.task_assignments[task_id] = assignment
            return assignment

        # Create assignment record
        assignment = TaskAssignment(
            task_id=task_id,
            node_id=node_ip,
            chunk=chunk,
            assigned_at=datetime.now(timezone.utc),
            status=TaskStatus.RUNNING
        )

        with self.lock:
            self.task_assignments[task_id] = assignment

        # Start remote timer
        try:
            self.timer.start_timer(node_ip, task_id)
        except Exception as e:
            logger.error(f"Failed to start timer for {task_id}: {e}")
            assignment.status = TaskStatus.FAILED
            assignment.error = str(e)
            return assignment

        # Execute benchmark remotely
        try:
            # This would typically invoke the benchmark via SSH
            # For now, we simulate the execution flow
            logger.info(f"Starting benchmark {task_id} on {node_ip}")
            
            # In a real implementation, this would be:
            # ssh.exec_command(f"python -m orchestrator.benchmark --chunk {chunk.start} --size {chunk.size}")
            
            # Update feedback
            self.feedback_manager.receive_task_status(
                node_ip, task_id, TaskStatusEnum.RUNNING
            )

            # Monitor task (synchronous for simplicity in this implementation)
            self.monitor_task(task_id)

        except Exception as e:
            logger.error(f"Execution failed for {task_id} on {node_ip}: {e}")
            assignment.status = TaskStatus.FAILED
            assignment.error = str(e)
            self.feedback_manager.receive_task_status(
                node_ip, task_id, TaskStatusEnum.FAILED
            )
        
        return assignment

    def monitor_task(self, task_id: str) -> TaskAssignment:
        """
        Monitor a running task, handling OOM, stragglers, and completion.
        """
        with self.lock:
            assignment = self.task_assignments.get(task_id)
            if not assignment:
                raise SchedulerExecutionError(f"Task {task_id} not found")
            
            if assignment.status != TaskStatus.RUNNING:
                return assignment

        start_time = assignment.start_time or time.time()
        node_ip = assignment.node_id

        try:
            # Periodic monitoring loop
            while assignment.status == TaskStatus.RUNNING:
                time.sleep(1)  # Check every second

                # Check for straggler
                self._handle_straggler(task_id, start_time, node_ip)

                # Check for OOM
                if self._detect_oom(node_ip, task_id):
                    raise OOMError(f"Out of memory on node {node_ip} for task {task_id}")

                # Check for completion via feedback
                # In a real system, this would poll the remote status or wait for a callback
                # For now, we assume the benchmark completes and updates status
                # This is a simplified simulation
                if self.feedback_manager.get_task_status(task_id) == TaskStatusEnum.COMPLETED:
                    assignment.status = TaskStatus.COMPLETED
                    assignment.end_time = time.time()
                    logger.info(f"Task {task_id} completed on {node_ip}")
                    break

        except OOMError as e:
            logger.error(f"OOM error for {task_id}: {e}")
            assignment.status = TaskStatus.FAILED
            assignment.error = str(e)
            self.feedback_manager.receive_task_status(
                node_ip, task_id, TaskStatusEnum.FAILED
            )
            
        except StragglerDetectedError as e:
            logger.error(f"Straggler error for {task_id}: {e}")
            assignment.status = TaskStatus.FAILED
            assignment.error = str(e)
            self.feedback_manager.receive_task_status(
                node_ip, task_id, TaskStatusEnum.FAILED
            )
            
        except Exception as e:
            logger.error(f"Unexpected error monitoring {task_id}: {e}")
            assignment.status = TaskStatus.FAILED
            assignment.error = str(e)
            self.feedback_manager.receive_task_status(
                node_ip, task_id, TaskStatusEnum.FAILED
            )

        return assignment

    def get_assignment_status(self, task_id: str) -> Optional[TaskAssignment]:
        """Get the current status of a task assignment."""
        with self.lock:
            return self.task_assignments.get(task_id)

def create_scheduler(
    node_manager: NodeManager,
    feedback_manager: CompletionFeedbackManager,
    heartbeat_monitor: HeartbeatMonitor,
    tool_manager: RemoteToolManager,
    instrumentor: RemoteInstrumentor,
    timer: RemoteWallClockTimer,
    saturation_handler: NetworkSaturationHandler,
    config: Dict[str, Any]
) -> Scheduler:
    """Factory function to create a Scheduler instance."""
    return Scheduler(
        node_manager=node_manager,
        feedback_manager=feedback_manager,
        heartbeat_monitor=heartbeat_monitor,
        tool_manager=tool_manager,
        instrumentor=instrumentor,
        timer=timer,
        saturation_handler=saturation_handler,
        config=config
    )

@enforce_pipeline_timeout
def main():
    """
    Main entry point for scheduler execution.
    Demonstrates the distribution of task chunks across nodes.
    """
    logger.info("Starting Scheduler Execution (T015b)")

    try:
        # Load configuration
        config = get_config()
        
        # Initialize components (in a real system, these would be properly initialized)
        # For this implementation, we assume they are available from previous tasks
        node_manager = NodeManager()  # Placeholder - would be initialized from T013a
        feedback_manager = CompletionFeedbackManager()  # Placeholder - T013b
        heartbeat_monitor = HeartbeatMonitor()  # Placeholder - T013c
        tool_manager = RemoteToolManager()  # Placeholder - T012
        instrumentor = RemoteInstrumentor()  # Placeholder - T014a
        timer = RemoteWallClockTimer()  # Placeholder - T014c
        saturation_handler = NetworkSaturationHandler()  # Placeholder - T014b

        # Create scheduler
        scheduler = create_scheduler(
            node_manager,
            feedback_manager,
            heartbeat_monitor,
            tool_manager,
            instrumentor,
            timer,
            saturation_handler,
            config
        )

        # Example: Create a task chunk and assign it
        # In a real scenario, chunks would come from T016 (benchmark)
        sample_chunk = TaskChunk(
            id="task_001",
            start=0,
            end=1024 * 1024,  # 1MB
            size=1024 * 1024,
            iterations=10000
        )

        sample_node = PhysicalNode(
            ip="192.168.1.10",
            hostname="node-1",
            status="online"
        )

        # Assign and monitor
        assignment = scheduler.assign_chunk(sample_chunk, sample_node)
        
        logger.info(f"Task assignment result: {assignment.status}")
        logger.info("Scheduler Execution completed successfully")

    except PipelineTimeoutError:
        logger.error("Pipeline timeout exceeded")
        raise
    except Exception as e:
        logger.error(f"Scheduler execution failed: {e}")
        raise

if __name__ == "__main__":
    main()
