"""
Unit Tests for Scheduler Execution (T015b)

Tests for:
- assign_chunk(chunk, node)
- monitor_task(task_id)
- Adaptive chunking logic
- OOM detection
- Straggler handling
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

from orchestrator.models import TaskChunk, TaskStatus, PhysicalNode
from orchestrator.scheduler_execution import (
    Scheduler,
    TaskAssignment,
    AdaptiveChunkingError,
    OOMError,
    StragglerDetectedError,
    create_scheduler
)

@pytest.fixture
def mock_components():
    """Mock all external dependencies for the scheduler."""
    node_manager = Mock()
    node_manager.get_ssh_client = Mock(return_value=Mock())
    
    feedback_manager = Mock()
    feedback_manager.receive_task_status = Mock()
    feedback_manager.get_task_status = Mock(return_value="COMPLETED")
    
    heartbeat_monitor = Mock()
    heartbeat_monitor.get_events = Mock(return_value=[])
    
    tool_manager = Mock()
    instrumentor = Mock()
    timer = Mock()
    timer.start_timer = Mock()
    
    saturation_handler = Mock()
    
    config = {
        'base_chunk_size': 1024 * 1024,
        'straggler_multiplier': 3.0
    }
    
    return {
        'node_manager': node_manager,
        'feedback_manager': feedback_manager,
        'heartbeat_monitor': heartbeat_monitor,
        'tool_manager': tool_manager,
        'instrumentor': instrumentor,
        'timer': timer,
        'saturation_handler': saturation_handler,
        'config': config
    }

@pytest.fixture
def scheduler(mock_components):
    """Create a scheduler with mocked dependencies."""
    return create_scheduler(**mock_components)

@pytest.fixture
def sample_node():
    return PhysicalNode(
        ip="192.168.1.10",
        hostname="node-1",
        status="online"
    )

@pytest.fixture
def sample_chunk():
    return TaskChunk(
        id="test_task_001",
        start=0,
        end=1024 * 1024,
        size=1024 * 1024,
        iterations=10000
    )

class TestAdaptiveChunking:
    """Tests for adaptive chunk size calculation."""

    def test_chunk_fits_without_adjustment(self, scheduler, sample_node):
        """Test that a chunk fitting in RAM is not adjusted."""
        # Mock available RAM to be larger than chunk
        with patch.object(scheduler, '_check_available_ram', return_value=1024):
            result = scheduler._calculate_adaptive_chunk_size(sample_node, 1024 * 1024)
            assert result == 1024 * 1024

    def test_chunk_halved_when_exceeds_ram(self, scheduler, sample_node):
        """Test that chunk is halved when it exceeds available RAM."""
        # Mock available RAM to be smaller than chunk
        with patch.object(scheduler, '_check_available_ram', return_value=512):
            result = scheduler._calculate_adaptive_chunk_size(sample_node, 1024 * 1024)
            assert result == 512 * 1024

    def test_chunk_respects_minimum_size(self, scheduler, sample_node):
        """Test that chunk does not go below minimum size."""
        # Mock available RAM to be very small
        with patch.object(scheduler, '_check_available_ram', return_value=1):
            with pytest.raises(AdaptiveChunkingError):
                scheduler._calculate_adaptive_chunk_size(sample_node, 1024 * 1024)

    def test_chunk_halved_multiple_times(self, scheduler, sample_node):
        """Test that chunk is halved multiple times until it fits."""
        # Mock available RAM to require multiple halvings
        with patch.object(scheduler, '_check_available_ram', return_value=256):
            result = scheduler._calculate_adaptive_chunk_size(sample_node, 1024 * 1024)
            assert result == 256 * 1024

class TestAssignChunk:
    """Tests for the assign_chunk method."""

    @pytest.mark.asyncio
    async def test_assign_chunk_creates_assignment(self, scheduler, sample_node, sample_chunk):
        """Test that assign_chunk creates a TaskAssignment record."""
        with patch.object(scheduler, '_calculate_adaptive_chunk_size', return_value=sample_chunk.size):
            assignment = await scheduler.assign_chunk(sample_chunk, sample_node)
            
            assert assignment.task_id == sample_chunk.id
            assert assignment.node_id == sample_node.ip
            assert assignment.status == TaskStatus.RUNNING
            assert assignment.chunk == sample_chunk

    @pytest.mark.asyncio
    async def test_assign_chunk_handles_adaptive_failure(self, scheduler, sample_node, sample_chunk):
        """Test that assign_chunk handles adaptive chunking failures."""
        with patch.object(scheduler, '_calculate_adaptive_chunk_size', side_effect=AdaptiveChunkingError("Test")):
            assignment = await scheduler.assign_chunk(sample_chunk, sample_node)
            
            assert assignment.status == TaskStatus.FAILED
            assert "Test" in assignment.error

    @pytest.mark.asyncio
    async def test_assign_chunk_starts_timer(self, scheduler, sample_node, sample_chunk, mock_components):
        """Test that assign_chunk starts the remote timer."""
        with patch.object(scheduler, '_calculate_adaptive_chunk_size', return_value=sample_chunk.size):
            await scheduler.assign_chunk(sample_chunk, sample_node)
            
            mock_components['timer'].start_timer.assert_called_once_with(sample_node.ip, sample_chunk.id)

class TestMonitorTask:
    """Tests for the monitor_task method."""

    def test_monitor_task_detects_completion(self, scheduler, sample_chunk, sample_node):
        """Test that monitor_task detects task completion."""
        assignment = TaskAssignment(
            task_id=sample_chunk.id,
            node_id=sample_node.ip,
            chunk=sample_chunk,
            assigned_at=datetime.now(timezone.utc),
            status=TaskStatus.RUNNING
        )
        scheduler.task_assignments[sample_chunk.id] = assignment

        # Mock feedback to return COMPLETED immediately
        with patch.object(scheduler.feedback_manager, 'get_task_status', return_value="COMPLETED"):
            result = scheduler.monitor_task(sample_chunk.id)
            
            assert result.status == TaskStatus.COMPLETED

    def test_monitor_task_handles_oom(self, scheduler, sample_chunk, sample_node):
        """Test that monitor_task handles OOM detection."""
        assignment = TaskAssignment(
            task_id=sample_chunk.id,
            node_id=sample_node.ip,
            chunk=sample_chunk,
            assigned_at=datetime.now(timezone.utc),
            status=TaskStatus.RUNNING
        )
        scheduler.task_assignments[sample_chunk.id] = assignment

        with patch.object(scheduler, '_detect_oom', return_value=True):
            with pytest.raises(OOMError):
                scheduler.monitor_task(sample_chunk.id)

    def test_monitor_task_handles_straggler(self, scheduler, sample_chunk, sample_node):
        """Test that monitor_task handles straggler detection."""
        assignment = TaskAssignment(
            task_id=sample_chunk.id,
            node_id=sample_node.ip,
            chunk=sample_chunk,
            assigned_at=datetime.now(timezone.utc),
            status=TaskStatus.RUNNING,
            start_time=time.time() - 100  # Simulate long-running task
        )
        scheduler.task_assignments[sample_chunk.id] = assignment
        scheduler.median_task_time = 1.0  # Set low median to trigger straggler

        with patch.object(scheduler, '_detect_oom', return_value=False):
            with pytest.raises(StragglerDetectedError):
                scheduler.monitor_task(sample_chunk.id)

class TestSchedulerIntegration:
    """Integration tests for the Scheduler class."""

    def test_create_scheduler_initializes_all_components(self, mock_components):
        """Test that create_scheduler properly initializes all components."""
        scheduler = create_scheduler(**mock_components)
        
        assert scheduler.node_manager is mock_components['node_manager']
        assert scheduler.feedback_manager is mock_components['feedback_manager']
        assert scheduler.heartbeat_monitor is mock_components['heartbeat_monitor']
        assert scheduler.tool_manager is mock_components['tool_manager']
        assert scheduler.instrumentor is mock_components['instrumentor']
        assert scheduler.timer is mock_components['timer']
        assert scheduler.saturation_handler is mock_components['saturation_handler']
        assert scheduler.config == mock_components['config']

    def test_scheduler_handles_heartbeat_loss(self, scheduler, sample_node):
        """Test that scheduler handles heartbeat loss events."""
        # Create a running task
        assignment = TaskAssignment(
            task_id="test_task",
            node_id=sample_node.ip,
            chunk=TaskChunk(id="test_task", start=0, end=100, size=100, iterations=100),
            assigned_at=datetime.now(timezone.utc),
            status=TaskStatus.RUNNING
        )
        scheduler.task_assignments["test_task"] = assignment

        # Simulate heartbeat loss
        from orchestrator.heartbeat_monitoring import HeartbeatLostEvent
        event = HeartbeatLostEvent(node_id=sample_node.ip)
        
        with patch.object(scheduler.heartbeat_monitor, 'get_events', return_value=[event]):
            scheduler._monitor_heartbeats()  # This runs in a thread, so we test the logic
            # Note: In a real test, we would need to wait for the thread to process
            # For now, we verify the method exists and doesn't crash
            
        # Verify the task was marked as failed
        assert scheduler.task_assignments["test_task"].status == TaskStatus.FAILED