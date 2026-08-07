"""
Unit tests for the scheduler module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import sys

from orchestrator.scheduler import Scheduler, NodeState, OOMError, StragglerDetectedError
from orchestrator.models import PhysicalNode, TaskChunk, NodeStatus, TaskStatus
from orchestrator.node_manager import NodeManager

@pytest.fixture
def mock_node_manager():
    """Create a mock NodeManager."""
    manager = Mock(spec=NodeManager)
    manager.ping_node.return_value = True
    manager.execute_command.return_value = {"stdout": "OK", "stderr": ""}
    return manager

@pytest.fixture
def mock_nodes():
    """Create a list of mock PhysicalNodes."""
    return [
        PhysicalNode(ip_address="192.168.1.10", hostname="node1", status=NodeStatus.IDLE),
        PhysicalNode(ip_address="192.168.1.11", hostname="node2", status=NodeStatus.IDLE),
    ]

@pytest.fixture
def mock_chunks():
    """Create a list of mock TaskChunks."""
    return [
        TaskChunk(task_id="chunk_1", iterations=100, chunk_size=10, status=TaskStatus.PENDING),
        TaskChunk(task_id="chunk_2", iterations=100, chunk_size=10, status=TaskStatus.PENDING),
    ]

def test_scheduler_initialization(mock_node_manager):
    """Test that the scheduler initializes correctly."""
    scheduler = Scheduler(mock_node_manager)
    assert scheduler.node_manager == mock_node_manager
    assert scheduler.timeout_factor == 2.0
    assert len(scheduler.nodes) == 0
    assert len(scheduler.pending_tasks) == 0
    assert len(scheduler.completed_tasks) == 0

def test_assign_chunk_success(mock_node_manager, mock_nodes, mock_chunks):
    """Test successful chunk assignment."""
    scheduler = Scheduler(mock_node_manager)
    node = mock_nodes[0]
    chunk = mock_chunks[0]

    # Mock the _execute_task_on_node method to return a successful result
    mock_result = Mock()
    mock_result.wall_clock_time = 1.0
    mock_result.ops_per_sec = 100.0
    with patch.object(scheduler, '_execute_task_on_node', return_value=mock_result):
        result = scheduler.assign_chunk(chunk, node)

    assert result is True
    assert chunk.status == TaskStatus.COMPLETED
    assert scheduler.nodes[node.ip_address].status == NodeStatus.IDLE
    assert chunk in scheduler.completed_tasks

def test_assign_chunk_node_not_idle(mock_node_manager, mock_nodes, mock_chunks):
    """Test chunk assignment fails when node is not idle."""
    scheduler = Scheduler(mock_node_manager)
    node = mock_nodes[0]
    chunk = mock_chunks[0]

    # Set node status to BUSY
    scheduler._register_node(node)
    scheduler.nodes[node.ip_address].status = NodeStatus.BUSY

    result = scheduler.assign_chunk(chunk, node)

    assert result is False
    assert chunk.status == TaskStatus.PENDING

def test_assign_chunk_oom(mock_node_manager, mock_nodes, mock_chunks):
    """Test OOM handling during chunk assignment."""
    scheduler = Scheduler(mock_node_manager)
    node = mock_nodes[0]
    chunk = mock_chunks[0]

    # Mock OOMError
    with patch.object(scheduler, '_execute_task_on_node', side_effect=OOMError("Out of memory")):
        result = scheduler.assign_chunk(chunk, node)

    assert result is False
    assert scheduler.nodes[node.ip_address].oom_events == 1
    assert chunk.status == TaskStatus.PENDING  # Should not be marked completed

def test_monitor_task_success(mock_node_manager, mock_nodes, mock_chunks):
    """Test successful task monitoring."""
    scheduler = Scheduler(mock_node_manager)
    node = mock_nodes[0]
    chunk = mock_chunks[0]

    # Register node and set active task
    scheduler._register_node(node)
    scheduler.nodes[node.ip_address].active_task_id = chunk.task_id
    scheduler.nodes[node.ip_address].status = NodeStatus.BUSY
    scheduler.task_start_times[chunk.task_id] = datetime.now()

    # Mock task times to avoid straggler detection
    scheduler.task_times = [1.0, 1.1, 0.9]
    scheduler._update_median_task_time()

    result = scheduler.monitor_task(chunk.task_id)

    assert result is True

def test_monitor_task_heartbeat_lost(mock_node_manager, mock_nodes, mock_chunks):
    """Test monitoring fails when heartbeat is lost."""
    scheduler = Scheduler(mock_node_manager)
    node = mock_nodes[0]
    chunk = mock_chunks[0]

    # Register node and set active task with old heartbeat
    scheduler._register_node(node)
    scheduler.nodes[node.ip_address].active_task_id = chunk.task_id
    scheduler.nodes[node.ip_address].status = NodeStatus.BUSY
    scheduler.nodes[node.ip_address].last_heartbeat = datetime.now() - __import__('datetime').timedelta(seconds=60)

    result = scheduler.monitor_task(chunk.task_id)

    assert result is False
    assert chunk.task_id not in scheduler.pending_tasks
    # Task should be re-added to pending for re-assignment

def test_distribute_tasks(mock_node_manager, mock_nodes, mock_chunks):
    """Test full task distribution workflow."""
    scheduler = Scheduler(mock_node_manager)

    # Mock execution to return success
    mock_result = Mock()
    mock_result.wall_clock_time = 1.0
    mock_result.ops_per_sec = 100.0

    with patch.object(scheduler, '_execute_task_on_node', return_value=mock_result):
        results = scheduler.distribute_tasks(mock_chunks, mock_nodes)

    assert len(results) == len(mock_chunks)
    for r in results:
        assert r.status == TaskStatus.COMPLETED
    assert len(scheduler.pending_tasks) == 0

def test_get_node_stats(mock_node_manager, mock_nodes, mock_chunks):
    """Test retrieving node statistics."""
    scheduler = Scheduler(mock_node_manager)
    node = mock_nodes[0]
    chunk = mock_chunks[0]

    # Register node
    scheduler._register_node(node)
    scheduler.nodes[node.ip_address].oom_events = 1
    scheduler.nodes[node.ip_address].straggler_events = 2
    scheduler.nodes[node.ip_address].last_error = "Test error"

    stats = scheduler.get_node_stats()

    assert node.ip_address in stats
    assert stats[node.ip_address]["oom_events"] == 1
    assert stats[node.ip_address]["straggler_events"] == 2
    assert stats[node.ip_address]["last_error"] == "Test error"
    assert stats[node.ip_address]["status"] == NodeStatus.IDLE.value

def test_reassign_task(mock_node_manager, mock_nodes, mock_chunks):
    """Test task re-assignment logic."""
    scheduler = Scheduler(mock_node_manager)
    chunk = mock_chunks[0]

    # Add chunk to pending
    scheduler.pending_tasks.append(chunk)

    # Simulate re-assignment (which should move it back to pending if not found in active)
    # In this test, we just check that the method exists and doesn't crash
    scheduler._reassign_task(chunk.task_id)

    # The task should still be in pending (or re-added)
    assert len(scheduler.pending_tasks) >= 1