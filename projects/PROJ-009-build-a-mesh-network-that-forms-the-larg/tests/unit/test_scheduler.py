import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add code to path if not already
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from orchestrator.scheduler import Scheduler, OOMError, StragglerDetectedError, SchedulerError
from orchestrator.models import TaskChunk, PhysicalNode, NodeStatus
from orchestrator.node_manager import NodeManager, NodeDiscoveryError

@pytest.fixture
def mock_node_manager():
    manager = Mock(spec=NodeManager)
    manager.execute_command = Mock(return_value=MagicMock(returncode=0, stdout="1024", stderr=""))
    manager.ping_node = Mock(return_value=True)
    return manager

@pytest.fixture
def mock_node():
    node = PhysicalNode(
        node_id="node-1",
        ip_address="192.168.1.10",
        status=NodeStatus.AVAILABLE,
        hostname="test-node-1"
    )
    return node

@pytest.fixture
def mock_chunk():
    return TaskChunk(
        task_id="task-1",
        iterations=1000,
        node_id="node-1",
        start_idx=0,
        seed=42
    )

class TestSchedulerRAMCheck:
    def test_adaptive_chunking_splits_large_chunk(self, mock_node_manager, mock_node, mock_chunk):
        """Test that a chunk larger than available RAM is split."""
        # Mock RAM to be very low (100 MB)
        mock_node_manager.execute_command.return_value = MagicMock(returncode=0, stdout="100", stderr="")
        
        scheduler = Scheduler(mock_node_manager)
        # Manually set state to simulate RAM check
        from orchestrator.scheduler import NodeState
        scheduler.node_states["192.168.1.10"] = NodeState(node=mock_node, available_ram_mb=100)
        
        # Assume chunk size is estimated as iterations (1000 MB)
        # 1000 > 100, so it should split
        adapted = scheduler._adapt_chunk_size(mock_chunk, 100)
        
        assert len(adapted) > 1, "Chunk should be split if size > RAM"
        total_iterations = sum(c.iterations for c in adapted)
        assert total_iterations == mock_chunk.iterations, "Total iterations must be preserved"

    def test_adaptive_chunking_preserves_chunk_if_small(self, mock_node_manager, mock_node, mock_chunk):
        """Test that a chunk smaller than RAM is not split."""
        mock_node_manager.execute_command.return_value = MagicMock(returncode=0, stdout="2000", stderr="")
        
        scheduler = Scheduler(mock_node_manager)
        scheduler.node_states["192.168.1.10"] = NodeState(node=mock_node, available_ram_mb=2000)
        
        adapted = scheduler._adapt_chunk_size(mock_chunk, 2000)
        assert len(adapted) == 1
        assert adapted[0].task_id == mock_chunk.task_id

class TestSchedulerOOM:
    def test_parse_oom_signals_detects_oom(self, mock_node_manager):
        scheduler = Scheduler(mock_node_manager)
        log = "Out of memory: Kill process 1234 (python)"
        assert scheduler._parse_oom_signals(log) is True

    def test_parse_oom_signals_false_positive(self, mock_node_manager):
        scheduler = Scheduler(mock_node_manager)
        log = "Memory usage is high but no OOM"
        assert scheduler._parse_oom_signals(log) is False

class TestSchedulerStraggler:
    def test_straggler_detection(self, mock_node_manager, mock_node, mock_chunk):
        """Test that a task taking > 2 * median time is flagged."""
        scheduler = Scheduler(mock_node_manager)
        
        # Setup completed tasks with median time 10s
        scheduler.completed_tasks = [
            (mock_chunk, 10.0, "192.168.1.10"),
            (mock_chunk, 10.0, "192.168.1.10"),
            (mock_chunk, 10.0, "192.168.1.10")
        ]
        
        # Setup state with a task running for 25s ( > 2 * 10)
        from orchestrator.scheduler import NodeState
        state = NodeState(node=mock_node, current_task=mock_chunk)
        state.task_start_time = datetime.now() - timedelta(seconds=25)
        state.last_heartbeat = datetime.now()
        scheduler.node_states["192.168.1.10"] = state
        
        with pytest.raises(StragglerDetectedError):
            scheduler.monitor_task("task-1")

    def test_no_straggler_if_fast(self, mock_node_manager, mock_node, mock_chunk):
        scheduler = Scheduler(mock_node_manager)
        scheduler.completed_tasks = [
            (mock_chunk, 10.0, "192.168.1.10")
        ]
        
        from orchestrator.scheduler import NodeState
        state = NodeState(node=mock_node, current_task=mock_chunk)
        state.task_start_time = datetime.now() - timedelta(seconds=5) # 5s < 2*10
        state.last_heartbeat = datetime.now()
        scheduler.node_states["192.168.1.10"] = state
        
        # Should not raise
        duration = scheduler.monitor_task("task-1")
        assert duration == 5.0

class TestSchedulerHeartbeat:
    def test_heartbeat_loss_detection(self, mock_node_manager, mock_node, mock_chunk):
        scheduler = Scheduler(mock_node_manager)
        
        from orchestrator.scheduler import NodeState
        state = NodeState(node=mock_node, current_task=mock_chunk)
        state.task_start_time = datetime.now()
        state.last_heartbeat = datetime.now() - timedelta(seconds=60) # Lost 60s ago
        scheduler.node_states["192.168.1.10"] = state
        
        with pytest.raises(Exception): # NodeHeartbeatLost or generic
            scheduler.monitor_task("task-1")