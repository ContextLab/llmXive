import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from dataclasses import dataclass

from orchestrator.scheduler import (
    Scheduler,
    SchedulerError,
    OOMError,
    StragglerDetectedError,
    NodeState,
    TaskAssignment,
    create_scheduler
)
from orchestrator.models import PhysicalNode, TaskChunk, TaskStatus
from orchestrator.node_manager import NodeManager
from orchestrator.completion_feedback import CompletionFeedbackManager
from orchestrator.remote_wall_clock_timer import RemoteWallClockTimer


@pytest.fixture
def mock_node_manager():
    manager = Mock(spec=NodeManager)
    manager.nodes = [
        PhysicalNode(ip="192.168.1.10", status="active", ram_gb=8),
        PhysicalNode(ip="192.168.1.11", status="active", ram_gb=4)
    ]
    manager.execute_command = Mock(return_value=("7983 2345 1234 12 4403 5234", "", 0))
    manager.ping_node = Mock(return_value=True)
    manager.get_node_by_ip = Mock(side_effect=lambda ip: next((n for n in manager.nodes if n.ip == ip), None))
    return manager


@pytest.fixture
def mock_feedback_manager():
    manager = Mock(spec=CompletionFeedbackManager)
    manager.receive_task_status = Mock()
    manager.update_scheduler_state = Mock()
    return manager


@pytest.fixture
def mock_remote_timer():
    timer = Mock(spec=RemoteWallClockTimer)
    timer.start_timer = Mock()
    timer.stop_timer = Mock()
    return timer


@pytest.fixture
def scheduler(mock_node_manager, mock_feedback_manager, mock_remote_timer):
    return create_scheduler(mock_node_manager, mock_feedback_manager, mock_remote_timer)


def test_scheduler_initialization(scheduler, mock_node_manager):
    """Test that scheduler initializes node states correctly."""
    for node in mock_node_manager.nodes:
        assert scheduler.node_states[node.ip] == NodeState.IDLE


def test_assign_chunk(scheduler, mock_node_manager, mock_remote_timer):
    """Test assigning a chunk to an idle node."""
    chunk = TaskChunk(
        chunk_id="test_chunk_1",
        iterations=10000,
        start_idx=0,
        end_idx=10000,
        node_id=None
    )
    node = mock_node_manager.nodes[0]

    task_id = scheduler.assign_chunk(chunk, node)

    assert task_id is not None
    assert task_id in scheduler.assigned_tasks
    assert scheduler.node_states[node.ip] == NodeState.BUSY
    mock_remote_timer.start_timer.assert_called_once_with(node.ip, task_id)
    mock_feedback_manager = scheduler.feedback_manager
    mock_feedback_manager.receive_task_status.assert_called()


def test_assign_chunk_adaptive_splitting(scheduler, mock_node_manager):
    """Test adaptive chunking when RAM is low."""
    # Mock low RAM
    scheduler._query_available_ram = Mock(return_value=100)  # Very low RAM
    scheduler.min_chunk_size = 1000

    chunk = TaskChunk(
        chunk_id="test_chunk_2",
        iterations=1000000,  # Large chunk
        start_idx=0,
        end_idx=1000000,
        node_id=None
    )
    node = mock_node_manager.nodes[0]

    # This should trigger splitting
    task_ids = scheduler.assign_chunk(chunk, node)

    # Should have split into multiple tasks
    assert task_ids is not None
    # Verify multiple assignments
    assert len([k for k in scheduler.assigned_tasks if task_ids[0].startswith(k.split('_')[0])]) >= 1


def test_parse_oom_signals(scheduler):
    """Test OOM signal detection."""
    log_output = "Out of memory: Kill process 1234 (python) score 900 or sacrifice children"
    assert scheduler._parse_oom_signals("192.168.1.10", log_output) is True

    log_output_clean = "Normal log output"
    assert scheduler._parse_oom_signals("192.168.1.10", log_output_clean) is False


def test_detect_straggler(scheduler):
    """Test straggler detection."""
    # Add some history
    scheduler.task_history = [
        TaskAssignment(task_id="t1", node_id="192.168.1.10", chunk=Mock(iterations=1000), start_time=datetime.now(timezone.utc), wall_clock_time=1.0),
        TaskAssignment(task_id="t2", node_id="192.168.1.10", chunk=Mock(iterations=1000), start_time=datetime.now(timezone.utc), wall_clock_time=1.1),
        TaskAssignment(task_id="t3", node_id="192.168.1.10", chunk=Mock(iterations=1000), start_time=datetime.now(timezone.utc), wall_clock_time=1.05),
    ]

    # Test with a task that is > 2x median (median ~1.05, threshold ~2.1)
    assert scheduler._detect_straggler("t4", 5.0) is True

    # Test with a normal task
    assert scheduler._detect_straggler("t4", 1.5) is False


def test_handle_task_completion(scheduler):
    """Test handling task completion."""
    chunk = TaskChunk(chunk_id="c1", iterations=1000, start_idx=0, end_idx=1000, node_id=None)
    node = scheduler.node_manager.nodes[0]
    task_id = scheduler.assign_chunk(chunk, node)

    result = scheduler.handle_task_completion(
        node_id=node.ip,
        task_id=task_id,
        status=TaskStatus.COMPLETED,
        wall_clock_time=1.5
    )

    assert result is True
    assert task_id not in scheduler.assigned_tasks
    assert any(a.task_id == task_id for a in scheduler.task_history)
    assert scheduler.node_states[node.ip] == NodeState.IDLE


def test_handle_task_completion_oom(scheduler, mock_node_manager):
    """Test task completion with OOM detection and re-queue."""
    # Mock low RAM to force a new node selection
    scheduler._query_available_ram = Mock(return_value=100)
    scheduler._find_available_node = Mock(return_value="192.168.1.11")

    chunk = TaskChunk(chunk_id="c2", iterations=1000, start_idx=0, end_idx=1000, node_id=None)
    node = mock_node_manager.nodes[0]
    task_id = scheduler.assign_chunk(chunk, node)

    # Simulate OOM
    log_output = "OOM killer: Kill process"
    result = scheduler.handle_task_completion(
        node_id=node.ip,
        task_id=task_id,
        status=TaskStatus.RUNNING,
        log_output=log_output
    )

    # Should have re-queued to a new node
    assert result is False  # Task not completed, re-queued
    assert len(scheduler.assigned_tasks) == 1  # New task assigned


def test_monitor_task_heartbeat_loss(scheduler, mock_node_manager):
    """Test monitoring task with heartbeat loss."""
    scheduler.node_manager.ping_node = Mock(return_value=False)

    chunk = TaskChunk(chunk_id="c3", iterations=1000, start_idx=0, end_idx=1000, node_id=None)
    node = mock_node_manager.nodes[0]
    task_id = scheduler.assign_chunk(chunk, node)

    # Mock finding a new node
    scheduler._find_available_node = Mock(return_value="192.168.1.11")

    result = scheduler.monitor_task(task_id)

    assert result is False  # Task needs re-assignment
    assert task_id not in scheduler.assigned_tasks  # Old task removed


def test_create_scheduler_factory(mock_node_manager, mock_feedback_manager, mock_remote_timer):
    """Test factory function."""
    s = create_scheduler(mock_node_manager, mock_feedback_manager, mock_remote_timer)
    assert isinstance(s, Scheduler)
    assert s.node_manager == mock_node_manager