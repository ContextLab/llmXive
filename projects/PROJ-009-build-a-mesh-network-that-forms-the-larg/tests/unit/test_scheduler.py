"""
Unit tests for the Scheduler module.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from orchestrator.models import TaskChunk, PhysicalNode, NodeStatus, TaskStatus
from orchestrator.scheduler import Scheduler, NodeState


class TestSchedulerInitialization:
    def test_scheduler_initializes_with_nodes(self):
        """Test that scheduler correctly initializes internal state from nodes."""
        nodes = [
            PhysicalNode(node_id="n1", hostname="1.1.1.1", status=NodeStatus.IDLE, total_memory_mb=4096, cpu_cores=2)
        ]
        scheduler = Scheduler(nodes)
        
        assert len(scheduler.nodes) == 1
        assert "n1" in scheduler.node_states
        assert scheduler.node_states["n1"].available_ram_mb == 4096
        assert scheduler.node_states["n1"].status == NodeStatus.IDLE


class TestTaskAssignment:
    def test_assigns_tasks_to_available_nodes(self):
        """Test basic task assignment to an available node."""
        nodes = [
            PhysicalNode(node_id="n1", hostname="1.1.1.1", status=NodeStatus.IDLE, total_memory_mb=8192, cpu_cores=4)
        ]
        tasks = [TaskChunk(task_id="t1", size_mb=100, complexity=1.0)]
        
        scheduler = Scheduler(nodes)
        assignments = scheduler.assign_tasks(tasks)
        
        assert "n1" in assignments
        assert len(assignments["n1"]) == 1
        assert assignments["n1"][0].task_id == "t1"

    def test_avoids_nodes_with_oom_risk(self):
        """Test that scheduler avoids assigning tasks that exceed node RAM."""
        # Create a node with very low memory
        nodes = [
            PhysicalNode(node_id="n1", hostname="1.1.1.1", status=NodeStatus.IDLE, total_memory_mb=100, cpu_cores=1)
        ]
        # Create a task that is too big
        tasks = [TaskChunk(task_id="t1", size_mb=500, complexity=1.0)]
        
        scheduler = Scheduler(nodes)
        assignments = scheduler.assign_tasks(tasks)
        
        # Should not assign because of OOM risk
        assert "n1" not in assignments or len(assignments.get("n1", [])) == 0
        # Task should remain in queue
        assert len(scheduler.task_queue) == 1

    def test_load_balancing_across_nodes(self):
        """Test that tasks are distributed when multiple nodes are available."""
        nodes = [
            PhysicalNode(node_id="n1", hostname="1.1.1.1", status=NodeStatus.IDLE, total_memory_mb=8192, cpu_cores=4),
            PhysicalNode(node_id="n2", hostname="1.1.1.2", status=NodeStatus.IDLE, total_memory_mb=8192, cpu_cores=4)
        ]
        tasks = [
            TaskChunk(task_id="t1", size_mb=100, complexity=1.0),
            TaskChunk(task_id="t2", size_mb=100, complexity=1.0)
        ]
        
        scheduler = Scheduler(nodes)
        assignments = scheduler.assign_tasks(tasks)
        
        # Both nodes should get a task
        assert len(assignments.get("n1", [])) >= 1
        assert len(assignments.get("n2", [])) >= 1


class TestOOMHandling:
    def test_handle_oom_event_reduces_ram_estimate(self):
        """Test that OOM event handler reduces available RAM estimate."""
        nodes = [
            PhysicalNode(node_id="n1", hostname="1.1.1.1", status=NodeStatus.IDLE, total_memory_mb=1000, cpu_cores=2)
        ]
        scheduler = Scheduler(nodes)
        
        initial_ram = scheduler.node_states["n1"].available_ram_mb
        assert initial_ram == 1000
        
        # Simulate OOM
        scheduler.handle_oom_event("n1", "t1")
        
        # RAM should be reduced (80% of original)
        new_ram = scheduler.node_states["n1"].available_ram_mb
        assert new_ram < initial_ram
        assert scheduler.node_states["n1"].is_straggler is True

    def test_oom_task_requeued(self):
        """Test that a task causing OOM is re-queued."""
        nodes = [
            PhysicalNode(node_id="n1", hostname="1.1.1.1", status=NodeStatus.IDLE, total_memory_mb=1000, cpu_cores=2)
        ]
        # First assign a task
        tasks = [TaskChunk(task_id="t1", size_mb=100, complexity=1.0)]
        scheduler = Scheduler(nodes)
        scheduler.assign_tasks(tasks)
        
        # Manually mark task as current to simulate execution
        scheduler.node_states["n1"].current_task = tasks[0]
        scheduler.node_states["n1"].assigned_tasks = [tasks[0]]
        
        # Trigger OOM
        scheduler.handle_oom_event("n1", "t1")
        
        # Task should be back in queue
        assert any(t.task_id == "t1" for t in scheduler.task_queue)


class TestStragglerDetection:
    def test_detects_stragglers_after_timeout(self):
        """Test that nodes are marked as stragglers after timeout."""
        nodes = [
            PhysicalNode(node_id="n1", hostname="1.1.1.1", status=NodeStatus.IDLE, total_memory_mb=8192, cpu_cores=4)
        ]
        scheduler = Scheduler(nodes)
        
        # Set up a busy state with old heartbeat
        state = scheduler.node_states["n1"]
        state.status = NodeStatus.BUSY
        state.last_heartbeat = datetime.now() - timedelta(seconds=400) # > 300s timeout
        state.current_task = TaskChunk(task_id="t1", size_mb=100, complexity=1.0)
        
        scheduler.detect_stragglers(timeout_seconds=300.0)
        
        assert scheduler.node_states["n1"].is_straggler is True

    def test_reassigns_straggler_tasks(self):
        """Test that straggler tasks are moved back to queue."""
        nodes = [
            PhysicalNode(node_id="n1", hostname="1.1.1.1", status=NodeStatus.IDLE, total_memory_mb=8192, cpu_cores=4)
        ]
        tasks = [TaskChunk(task_id="t1", size_mb=100, complexity=1.0)]
        scheduler = Scheduler(nodes)
        
        # Setup straggler state
        state = scheduler.node_states["n1"]
        state.status = NodeStatus.BUSY
        state.last_heartbeat = datetime.now() - timedelta(seconds=400)
        state.current_task = tasks[0]
        state.assigned_tasks = [tasks[0]]
        state.is_straggler = True # Pre-marked for simplicity in this test logic flow
        
        scheduler.reassign_straggler_tasks()
        
        assert any(t.task_id == "t1" for t in scheduler.task_queue)
        assert scheduler.node_states["n1"].current_task is None
        assert scheduler.node_states["n1"].status == NodeStatus.IDLE
        assert scheduler.node_states["n1"].is_straggler is False # Reset


class TestNodeStatusUpdates:
    def test_task_completion_updates_state(self):
        """Test that completing a task updates node state and RAM."""
        nodes = [
            PhysicalNode(node_id="n1", hostname="1.1.1.1", status=NodeStatus.IDLE, total_memory_mb=8192, cpu_cores=4)
        ]
        tasks = [TaskChunk(task_id="t1", size_mb=100, complexity=1.0)]
        scheduler = Scheduler(nodes)
        scheduler.assign_tasks(tasks)
        
        # Simulate completion
        scheduler.handle_task_complete("n1", "t1", {"available_memory_mb": 7500})
        
        assert scheduler.node_states["n1"].status == NodeStatus.IDLE
        assert len(scheduler.node_states["n1"].assigned_tasks) == 0
        assert scheduler.node_states["n1"].available_ram_mb == 7500
        assert tasks[0].status == TaskStatus.COMPLETED