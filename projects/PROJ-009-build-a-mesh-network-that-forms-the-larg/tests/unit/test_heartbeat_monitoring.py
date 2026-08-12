"""
Unit tests for heartbeat_monitoring.py (T013c).
"""
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from orchestrator.heartbeat_monitoring import (
    HeartbeatMonitor,
    HeartbeatLostEvent,
    create_heartbeat_monitor,
    NodeHeartbeatState
)
from orchestrator.models import NodeStatus


class MockNodeManager:
    """Mock NodeManager for testing."""
    pass


@pytest.fixture
def mock_node_manager():
    return MockNodeManager()


@pytest.fixture
def monitor(mock_node_manager):
    """Create a monitor with a very short timeout for testing."""
    return create_heartbeat_monitor(
        node_manager=mock_node_manager,
        timeout_threshold=0.5,
        poll_interval=0.1
    )


def test_register_node(monitor):
    """Test that a node can be registered."""
    monitor.register_node("node_1", "task_1")
    assert "node_1" in monitor._node_states
    assert monitor._node_states["node_1"].current_task_id == "task_1"
    assert monitor._node_states["node_1"].status == NodeStatus.ONLINE


def test_unregister_node(monitor):
    """Test that a node can be unregistered."""
    monitor.register_node("node_1", "task_1")
    monitor.unregister_node("node_1")
    assert "node_1" not in monitor._node_states


def test_record_heartbeat(monitor):
    """Test that recording a heartbeat updates the state."""
    monitor.register_node("node_1", "task_1")
    before = datetime.now()
    monitor.record_heartbeat("node_1", "task_1")
    after = datetime.now()

    state = monitor._node_states["node_1"]
    assert before <= state.last_heartbeat <= after
    assert state.status == NodeStatus.ONLINE
    assert state.missed_count == 0


def test_heartbeat_loss_detection(monitor):
    """Test that a missed heartbeat triggers a loss event."""
    events_received = []

    def callback(event):
        events_received.append(event)

    # Re-create monitor with callback
    monitor.callback_on_loss = callback
    monitor.register_node("node_1", "task_1")

    # Record initial heartbeat
    monitor.record_heartbeat("node_1", "task_1")

    # Start the monitor
    monitor.start()

    # Wait for timeout (0.5s) + poll interval + buffer
    time.sleep(1.0)

    monitor.stop()

    assert len(events_received) > 0
    event = events_received[0]
    assert event.node_id == "node_1"
    assert event.task_id == "task_1"
    assert isinstance(event, HeartbeatLostEvent)


def test_get_node_status(monitor):
    """Test retrieving node status."""
    monitor.register_node("node_1", "task_1")
    assert monitor.get_node_status("node_1") == NodeStatus.ONLINE
    assert monitor.get_node_status("non_existent") is None


def test_get_failed_tasks(monitor):
    """Test retrieving list of failed tasks."""
    monitor.register_node("node_1", "task_1")
    monitor.register_node("node_2", "task_2")

    # Simulate state manually for speed (bypassing thread wait)
    with monitor._lock:
        monitor._node_states["node_1"].status = NodeStatus.UNRESPONSIVE
        monitor._node_states["node_2"].status = NodeStatus.ONLINE

    failed = monitor.get_failed_tasks()
    assert "task_1" in failed
    assert "task_2" not in failed