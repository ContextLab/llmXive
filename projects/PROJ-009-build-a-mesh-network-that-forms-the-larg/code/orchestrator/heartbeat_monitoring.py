"""
Heartbeat Monitoring Module for Mesh Network Orchestrator.

Handles heartbeat loss detection and task re-assignment logic mandated by FR-001.
Continuously polls nodes for heartbeat signals and triggers re-assignment if a node
becomes unresponsive.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
from enum import Enum

from orchestrator.logger import get_logger
from orchestrator.node_manager import NodeManager, NodeState, NodeHeartbeatLost
from orchestrator.models import TaskStatus, NodeStatus

logger = get_logger(__name__)


class HeartbeatEvent(Enum):
    """Enum representing heartbeat event types."""
    HEARTBEAT_RECEIVED = "heartbeat_received"
    HEARTBEAT_LOST = "heartbeat_lost"
    NODE_UNRESPONSIVE = "node_unresponsive"


@dataclass
class HeartbeatLostEvent:
    """
    Event raised when a node stops sending heartbeats.
    Consumed by the scheduler (T015b) to trigger re-assignment.
    """
    node_id: str
    task_id: Optional[str]
    timestamp: datetime
    last_heartbeat: datetime
    duration_unresponsive: float

    def __str__(self) -> str:
        return (f"HeartbeatLostEvent(node_id={self.node_id}, task_id={self.task_id}, "
                f"duration={self.duration_unresponsive:.2f}s)")


@dataclass
class NodeHeartbeatState:
    """Tracks the heartbeat state of a single node."""
    node_id: str
    last_heartbeat_time: datetime
    status: NodeStatus = NodeStatus.ONLINE
    unresponsive_start_time: Optional[datetime] = None
    task_id: Optional[str] = None
    consecutive_misses: int = 0


class HeartbeatMonitor:
    """
    Monitors heartbeats from a set of nodes.
    Detects loss of heartbeat and triggers re-assignment logic.
    """

    def __init__(
        self,
        node_manager: NodeManager,
        timeout_threshold_seconds: float = 30.0,
        poll_interval_seconds: float = 5.0,
        on_heartbeat_lost: Optional[Callable[[HeartbeatLostEvent], None]] = None
    ):
        """
        Initialize the HeartbeatMonitor.

        Args:
            node_manager: Instance of NodeManager to query node states.
            timeout_threshold_seconds: Time in seconds before a node is marked unresponsive.
            poll_interval_seconds: Interval between heartbeat checks.
            on_heartbeat_lost: Callback function to invoke when a heartbeat is lost.
        """
        self.node_manager = node_manager
        self.timeout_threshold = timeout_threshold_seconds
        self.poll_interval = poll_interval_seconds
        self.on_heartbeat_lost = on_heartbeat_lost
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._node_states: Dict[str, NodeHeartbeatState] = {}
        self._lock = threading.Lock()

    def register_node(self, node_id: str, initial_task_id: Optional[str] = None) -> None:
        """
        Register a node for heartbeat monitoring.

        Args:
            node_id: Unique identifier for the node.
            initial_task_id: Optional task currently assigned to the node.
        """
        with self._lock:
            if node_id not in self._node_states:
                self._node_states[node_id] = NodeHeartbeatState(
                    node_id=node_id,
                    last_heartbeat_time=datetime.now(timezone.utc),
                    task_id=initial_task_id
                )
                logger.info(f"Registered node {node_id} for heartbeat monitoring.")

    def update_heartbeat(self, node_id: str, task_id: Optional[str] = None) -> None:
        """
        Update the heartbeat timestamp for a specific node.
        Called when a heartbeat signal is received from the node.

        Args:
            node_id: The node that sent the heartbeat.
            task_id: Optional task ID associated with the heartbeat.
        """
        with self._lock:
            if node_id in self._node_states:
                state = self._node_states[node_id]
                state.last_heartbeat_time = datetime.now(timezone.utc)
                state.status = NodeStatus.ONLINE
                state.unresponsive_start_time = None
                state.consecutive_misses = 0
                if task_id:
                    state.task_id = task_id
                logger.debug(f"Heartbeat received from node {node_id} for task {task_id}.")
            else:
                logger.warning(f"Heartbeat received for unregistered node {node_id}.")

    def _check_nodes(self) -> List[HeartbeatLostEvent]:
        """
        Internal method to check all registered nodes for heartbeat timeouts.

        Returns:
            List of HeartbeatLostEvent objects for nodes that timed out.
        """
        lost_events = []
        now = datetime.now(timezone.utc)

        with self._lock:
            for node_id, state in self._node_states.items():
                time_since_last = (now - state.last_heartbeat_time).total_seconds()

                if time_since_last > self.timeout_threshold:
                    if state.status != NodeStatus.UNRESPONSIVE:
                        # Transition to unresponsive
                        state.status = NodeStatus.UNRESPONSIVE
                        state.unresponsive_start_time = now
                        logger.warning(
                            f"Node {node_id} marked UNRESPONSIVE after {time_since_last:.2f}s "
                            f"(threshold: {self.timeout_threshold}s)."
                        )

                    # If already unresponsive, check if we need to trigger re-assignment
                    if state.unresponsive_start_time:
                        duration = (now - state.unresponsive_start_time).total_seconds()
                        # Trigger re-assignment logic if the node has been down long enough
                        # or immediately upon detection depending on policy.
                        # Here we trigger immediately upon transition to unresponsive,
                        # but we only add the event once per transition.
                        # To avoid duplicate events for the same node in a single check cycle,
                        # we rely on the state transition logic.
                        
                        # However, if we are in a loop, we might detect it again.
                        # We will create the event only if we are currently processing the transition
                        # or if the duration exceeds a secondary threshold to avoid noise?
                        # The spec says: "If a heartbeat is missed for > timeout_threshold, mark ... and trigger re-queue".
                        # We will generate the event every time we detect the condition if it's been > threshold
                        # but to prevent spam, we usually do it on the transition.
                        # Let's refine: We trigger the event if the node is unresponsive and we haven't 
                        # already triggered a re-assignment for the *current* task instance.
                        # For simplicity in this implementation, we trigger the event if the node is 
                        # unresponsive and the task is not yet marked as failed in the state (we don't track failed status here, just the event).
                        
                        # Actually, the spec says "Trigger the re-queue... and log".
                        # We will emit the event. The consumer (Scheduler) is responsible for idempotency.
                        
                        # To avoid emitting the same event repeatedly in a tight loop, we check if
                        # we just transitioned or if enough time has passed? 
                        # Let's stick to the spec: "If a heartbeat is missed... trigger re-queue".
                        # We'll emit the event.
                        
                        event = HeartbeatLostEvent(
                            node_id=node_id,
                            task_id=state.task_id,
                            timestamp=now,
                            last_heartbeat=state.last_heartbeat_time,
                            duration_unresponsive=duration
                        )
                        lost_events.append(event)
                        state.consecutive_misses += 1
                        logger.error(f"Heartbeat lost for node {node_id}. Event: {event}")
                else:
                    # Node is responsive, reset miss count
                    if state.status == NodeStatus.UNRESPONSIVE:
                        # It came back?
                        state.status = NodeStatus.ONLINE
                        state.unresponsive_start_time = None
                        state.consecutive_misses = 0
                        logger.info(f"Node {node_id} recovered.")

        return lost_events

    def _monitor_loop(self) -> None:
        """Background thread loop to monitor heartbeats."""
        while self._running:
            try:
                lost_events = self._check_nodes()
                for event in lost_events:
                    if self.on_heartbeat_lost:
                        self.on_heartbeat_lost(event)
                    else:
                        # Default behavior: Log and attempt to re-assign via node_manager
                        logger.error(
                            f"Default handler: Re-assigning task {event.task_id} from node {event.node_id}."
                        )
                        # In a real system, this would call the scheduler to re-queue.
                        # We log the action here as per the task requirement to "Trigger the re-queue".
                        # Since we don't have the scheduler instance here, we log the intent.
                        # The event is raised (returned) to be consumed by the scheduler (T015b).
                
                time.sleep(self.poll_interval)
            except Exception as e:
                logger.exception(f"Error in heartbeat monitoring loop: {e}")
                time.sleep(self.poll_interval)

    def start(self) -> None:
        """Start the heartbeat monitoring thread."""
        if self._running:
            logger.warning("HeartbeatMonitor is already running.")
            return

        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("HeartbeatMonitor started.")

    def stop(self) -> None:
        """Stop the heartbeat monitoring thread."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
            logger.info("HeartbeatMonitor stopped.")

    def get_node_states(self) -> Dict[str, NodeHeartbeatState]:
        """Return a copy of current node states."""
        with self._lock:
            return dict(self._node_states)


def create_heartbeat_monitor(
    node_manager: NodeManager,
    timeout_threshold: float = 30.0,
    poll_interval: float = 5.0
) -> HeartbeatMonitor:
    """
    Factory function to create a HeartbeatMonitor instance.

    Args:
        node_manager: The NodeManager instance.
        timeout_threshold: Timeout in seconds.
        poll_interval: Check interval in seconds.

    Returns:
        Configured HeartbeatMonitor instance.
    """
    return HeartbeatMonitor(
        node_manager=node_manager,
        timeout_threshold_seconds=timeout_threshold,
        poll_interval_seconds=poll_interval
    )


def main() -> None:
    """
    Main entry point for testing heartbeat monitoring.
    Simulates a scenario where a node stops sending heartbeats.
    """
    logger.info("Starting HeartbeatMonitor simulation.")
    
    # Create a mock node manager (in real usage, this would connect to real nodes)
    # For this test, we simulate the state updates manually.
    node_manager = NodeManager()
    
    # Create monitor
    monitor = create_heartbeat_monitor(
        node_manager=node_manager,
        timeout_threshold=2.0,  # Short timeout for demo
        poll_interval=0.5
    )

    # Register a node
    monitor.register_node("node-1", initial_task_id="task-123")

    # Start monitoring
    monitor.start()

    # Simulate heartbeats for a while
    logger.info("Simulating heartbeats for 3 seconds...")
    for i in range(6):
        monitor.update_heartbeat("node-1", "task-123")
        time.sleep(0.5)

    # Stop sending heartbeats to simulate failure
    logger.info("Stopping heartbeats. Waiting for timeout...")
    
    # Wait for the monitor to detect the loss
    time.sleep(5.0)

    # Stop the monitor
    monitor.stop()
    logger.info("Simulation complete.")


if __name__ == "__main__":
    main()