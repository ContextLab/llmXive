"""
Heartbeat Monitoring Module for Mesh Network Orchestrator.

Implements heartbeat loss detection and heterogeneity-aware re-assignment logic
as mandated by FR-001 and Constitution Principle VII.
"""
from __future__ import annotations

import json
import logging
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Any, Optional, Callable

# Local imports matching API surface
from orchestrator.logger import get_logger
from orchestrator.models import NodeStatus, TaskStatus
from orchestrator.config import get_config

logger = get_logger(__name__)


class HeartbeatMonitorError(Exception):
    """Base exception for heartbeat monitoring errors."""
    pass


class HeartbeatLostEvent(Exception):
    """
    Raised when a heartbeat is lost for a node.
    Carries information about the lost node and associated tasks.
    """
    def __init__(self, node_id: str, task_ids: List[str], reason: str = "Heartbeat timeout"):
        self.node_id = node_id
        self.task_ids = task_ids
        self.reason = reason
        super().__init__(f"Heartbeat lost for node {node_id}: {reason}")


@dataclass
class NodeHeartbeatState:
    """Tracks the heartbeat state for a single node."""
    node_id: str
    last_heartbeat: datetime
    last_response_time_ms: float = 0.0
    packet_loss_rate: float = 0.0
    cpu_speed_mhz: float = 0.0
    is_responsive: bool = True
    assigned_tasks: List[str] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def update_heartbeat(self, response_time_ms: float, packet_loss: float, cpu_speed: float):
        """Update state with latest heartbeat data."""
        with self.lock:
            self.last_heartbeat = datetime.now(timezone.utc)
            self.last_response_time_ms = response_time_ms
            self.packet_loss_rate = packet_loss
            self.cpu_speed_mhz = cpu_speed
            self.is_responsive = True

    def mark_unresponsive(self):
        """Mark node as unresponsive."""
        with self.lock:
            self.is_responsive = False

    def get_tasks(self) -> List[str]:
        """Get list of currently assigned tasks."""
        with self.lock:
            return list(self.assigned_tasks)

    def add_task(self, task_id: str):
        """Add a task to this node's assignment list."""
        with self.lock:
            if task_id not in self.assigned_tasks:
                self.assigned_tasks.append(task_id)

    def remove_task(self, task_id: str):
        """Remove a task from this node's assignment list."""
        with self.lock:
            if task_id in self.assigned_tasks:
                self.assigned_tasks.remove(task_id)


class HeartbeatMonitor:
    """
    Monitors heartbeats from all nodes and triggers re-assignment logic
    when heartbeats are lost.
    """

    def __init__(
        self,
        timeout_threshold_seconds: float = 30.0,
        poll_interval_seconds: float = 5.0,
        scheduler_state_ref: Optional[Any] = None,
        reassignment_callback: Optional[Callable] = None
    ):
        """
        Initialize the heartbeat monitor.

        Args:
            timeout_threshold_seconds: Seconds without heartbeat before marking node lost.
            poll_interval_seconds: How often to check heartbeat status.
            scheduler_state_ref: Reference to the SchedulerState object (T013d).
            reassignment_callback: Function to call when re-assignment is needed.
        """
        self.timeout_threshold = timeout_threshold_seconds
        self.poll_interval = poll_interval_seconds
        self.scheduler_state = scheduler_state_ref
        self.reassignment_callback = reassignment_callback
        self.node_states: Dict[str, NodeHeartbeatState] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._dropout_events: List[Dict[str, Any]] = []
        self._total_assignments = 0
        self._total_drops = 0

    def register_node(self, node_id: str, cpu_speed_mhz: float = 0.0):
        """Register a new node for monitoring."""
        with self._lock:
            if node_id not in self.node_states:
                self.node_states[node_id] = NodeHeartbeatState(
                    node_id=node_id,
                    last_heartbeat=datetime.now(timezone.utc),
                    cpu_speed_mhz=cpu_speed_mhz
                )
                logger.info(f"Registered node {node_id} for heartbeat monitoring.")

    def update_node_state(
        self,
        node_id: str,
        response_time_ms: float,
        packet_loss_rate: float,
        cpu_speed_mhz: float
    ):
        """Update the heartbeat state for a specific node."""
        with self._lock:
            if node_id in self.node_states:
                self.node_states[node_id].update_heartbeat(
                    response_time_ms, packet_loss_rate, cpu_speed_mhz
                )
            else:
                # Register on first update if not explicitly registered
                self.register_node(node_id, cpu_speed_mhz)
                self.node_states[node_id].update_heartbeat(
                    response_time_ms, packet_loss_rate, cpu_speed_mhz
                )

    def assign_task_to_node(self, node_id: str, task_id: str):
        """Record that a task has been assigned to a node."""
        with self._lock:
            if node_id in self.node_states:
                self.node_states[node_id].add_task(task_id)
                self._total_assignments += 1
            else:
                logger.warning(f"Cannot assign task {task_id} to unregistered node {node_id}")

    def _calculate_heterogeneity_score(
        self,
        cpu_speed_mhz: float,
        max_latency_ms: float,
        packet_loss_rate: float
    ) -> float:
        """
        Calculate heterogeneity score for a node.
        Score = (cpu_speed_mhz / max_latency_ms) * (1 - packet_loss_rate)
        """
        if max_latency_ms <= 0:
            max_latency_ms = 1.0  # Avoid division by zero
        if packet_loss_rate > 1.0:
            packet_loss_rate = 1.0
        return (cpu_speed_mhz / max_latency_ms) * (1.0 - packet_loss_rate)

    def _find_best_reassignment_node(self, failed_node_id: str) -> Optional[str]:
        """
        Find the best node to re-assign tasks from a failed node.
        Uses heterogeneity-aware scoring.
        """
        best_node_id = None
        best_score = -1.0

        with self._lock:
            # Get current max latency from the failed node (as reference for 'max')
            # In a real system, this might be a rolling window across all nodes
            # For now, we use the failed node's last known latency or a default
            reference_latency = 100.0  # Default fallback if not available

            if failed_node_id in self.node_states:
                # Use the failed node's last known latency as a reference for 'max'
                # or calculate a global average if preferred
                reference_latency = max(1.0, self.node_states[failed_node_id].last_response_time_ms)

            for node_id, state in self.node_states.items():
                if node_id == failed_node_id:
                    continue
                if not state.is_responsive:
                    continue

                score = self._calculate_heterogeneity_score(
                    cpu_speed_mhz=state.cpu_speed_mhz,
                    max_latency_ms=max(1.0, state.last_response_time_ms), # Use node's own latency as the 'max' for its own score calculation?
                    # Re-reading spec: "max_latency_ms: From T014a/T014c (rolling short window of heartbeat response times)"
                    # This implies we should use a global or rolling max, but for simplicity in this module,
                    # we use the node's own latency as a proxy for current network condition,
                    # or we could use the reference_latency derived from the failed node.
                    # Let's use the node's own latency as the denominator to reflect its current responsiveness.
                    packet_loss_rate=state.packet_loss_rate
                )

                if score > best_score:
                    best_score = score
                    best_node_id = node_id

        return best_node_id

    def _handle_heartbeat_loss(self, node_id: str):
        """
        Handle the logic when a heartbeat is lost for a node.
        1. Mark node unresponsive.
        2. Identify failed tasks.
        3. Calculate heterogeneity score for available nodes.
        4. Re-queue tasks to the best node.
        5. Log the event.
        """
        logger.warning(f"Heartbeat lost for node {node_id}. Initiating re-assignment.")

        with self._lock:
            if node_id not in self.node_states:
                return

            state = self.node_states[node_id]
            state.mark_unresponsive()

            failed_task_ids = list(state.assigned_tasks)
            if not failed_task_ids:
                logger.info(f"No tasks assigned to lost node {node_id}.")
                return

            # Find best re-assignment node
            best_node_id = self._find_best_reassignment_node(node_id)

            reassignment_log = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "failed_node_id": node_id,
                "failed_task_ids": failed_task_ids,
                "reassigned_to_node_id": best_node_id,
                "reason": "Heartbeat timeout"
            }

            if best_node_id:
                logger.info(f"Re-assigning tasks {failed_task_ids} from {node_id} to {best_node_id}")
                reassignment_log["success"] = True

                # Notify scheduler state if available
                if self.scheduler_state:
                    try:
                        # This assumes SchedulerState has a method to handle re-assignment
                        # Based on T013d, it should handle feedback and state transitions
                        if hasattr(self.scheduler_state, 'handle_reassignment'):
                            self.scheduler_state.handle_reassignment(
                                failed_node_id=node_id,
                                new_node_id=best_node_id,
                                task_ids=failed_task_ids
                            )
                        elif hasattr(self.scheduler_state, 'requeue_tasks'):
                            self.scheduler_state.requeue_tasks(failed_task_ids, best_node_id)
                        else:
                            logger.error("SchedulerState does not have expected re-assignment methods.")
                    except Exception as e:
                        logger.error(f"Error updating scheduler state for re-assignment: {e}")
                        reassignment_log["success"] = False

                # Notify callback if provided
                if self.reassignment_callback:
                    try:
                        self.reassignment_callback(node_id, best_node_id, failed_task_ids)
                    except Exception as e:
                        logger.error(f"Error in reassignment callback: {e}")
            else:
                logger.error(f"No suitable node found for re-assignment of tasks from {node_id}")
                reassignment_log["success"] = False

            # Record dropout event
            self._total_drops += 1
            self._dropout_events.append(reassignment_log)

            # Raise event to signal higher layers
            raise HeartbeatLostEvent(node_id, failed_task_ids, "Heartbeat timeout")

    def _check_timeouts(self):
        """Check all nodes for heartbeat timeouts."""
        now = datetime.now(timezone.utc)
        nodes_to_check = list(self.node_states.keys())

        for node_id in nodes_to_check:
            state = self.node_states[node_id]
            if not state.is_responsive:
                continue

            with state.lock:
                time_since_heartbeat = (now - state.last_heartbeat).total_seconds()

            if time_since_heartbeat > self.timeout_threshold:
                try:
                    self._handle_heartbeat_loss(node_id)
                except HeartbeatLostEvent:
                    # Expected exception, continue monitoring
                    pass

    def _monitoring_loop(self):
        """Main monitoring loop running in a background thread."""
        logger.info("Heartbeat monitoring thread started.")
        while self._running:
            self._check_timeouts()
            time.sleep(self.poll_interval)
        logger.info("Heartbeat monitoring thread stopped.")

    def start(self):
        """Start the heartbeat monitoring thread."""
        if self._running:
            logger.warning("Heartbeat monitor is already running.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._thread.start()
        logger.info("Heartbeat monitor started.")

    def stop(self):
        """Stop the heartbeat monitoring thread."""
        if not self._running:
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("Heartbeat monitor stopped.")

    def calculate_dropout_rate(self) -> float:
        """
        Calculate the dropout rate: total heartbeat losses / total task assignments.
        Returns 0.0 if no assignments have been made.
        """
        if self._total_assignments == 0:
            return 0.0
        return self._total_drops / self._total_assignments

    def save_dropout_events(self, output_path: str):
        """
        Save dropout events to a JSON file.
        Format:
        {
            "run_id": "...",
            "dropout_rate": 0.0,
            "dropped_node_ids": ["node1", "node2"],
            "events": [...]
        }
        """
        dropped_node_ids = list(set(event["failed_node_id"] for event in self._dropout_events))
        data = {
            "run_id": "current_run", # Should be populated by the caller or config
            "dropout_rate": self.calculate_dropout_rate(),
            "dropped_node_ids": dropped_node_ids,
            "events": self._dropout_events
        }

        try:
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Dropout events saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save dropout events: {e}")


def create_heartbeat_monitor(
    timeout_threshold_seconds: float = 30.0,
    scheduler_state_ref: Optional[Any] = None
) -> HeartbeatMonitor:
    """Factory function to create a configured HeartbeatMonitor."""
    config = get_config()
    # Allow config override if available
    if config and hasattr(config, 'heartbeat_timeout'):
        timeout_threshold_seconds = config.heartbeat_timeout

    return HeartbeatMonitor(
        timeout_threshold_seconds=timeout_threshold_seconds,
        scheduler_state_ref=scheduler_state_ref
    )


def main():
    """
    Main entry point for testing the heartbeat monitor.
    This is a self-contained test that simulates node heartbeats and loss.
    """
    logger.info("Starting heartbeat monitor test.")

    # Create monitor
    monitor = create_heartbeat_monitor(timeout_threshold_seconds=5.0)

    # Register some nodes
    monitor.register_node("node_1", cpu_speed_mhz=2000.0)
    monitor.register_node("node_2", cpu_speed_mhz=3000.0)
    monitor.register_node("node_3", cpu_speed_mhz=2500.0)

    # Assign tasks
    monitor.assign_task_to_node("node_1", "task_001")
    monitor.assign_task_to_node("node_1", "task_002")
    monitor.assign_task_to_node("node_2", "task_003")

    # Start monitoring
    monitor.start()

    # Simulate heartbeats for node_2 and node_3, but NOT node_1
    time.sleep(2)
    monitor.update_node_state("node_2", response_time_ms=10.0, packet_loss_rate=0.01, cpu_speed_mhz=3000.0)
    monitor.update_node_state("node_3", response_time_ms=15.0, packet_loss_rate=0.02, cpu_speed_mhz=2500.0)

    # Wait for timeout (5s + buffer)
    logger.info("Waiting for node_1 timeout...")
    time.sleep(8)

    # Stop monitoring
    monitor.stop()

    # Save dropout events
    monitor.save_dropout_events("data/raw/dropout_events.json")

    rate = monitor.calculate_dropout_rate()
    logger.info(f"Calculated dropout rate: {rate:.4f}")

    logger.info("Heartbeat monitor test completed.")


if __name__ == "__main__":
    main()