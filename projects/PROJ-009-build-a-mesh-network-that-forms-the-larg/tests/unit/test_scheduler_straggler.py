import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import threading
import time

from orchestrator.scheduler import Scheduler, TaskAssignment, SchedulerState
from orchestrator.models import PhysicalNode, TaskChunk, ExecutionRun, NodeStatus, TaskStatus, ExecutionStatus
from orchestrator.config import OrchestratorConfig
from orchestrator.node_manager import NodeManager, SSHConnection


class MockNodeManager(NodeManager):
    """Mock NodeManager for testing straggler/dropout logic."""
    def __init__(self):
        self.connections = {}
    
    def get_connection(self, node_id: str) -> Optional[SSHConnection]:
        return self.connections.get(node_id)
    
    def execute_command(self, node_id: str, command: str) -> str:
        return "OK"
    
    def set_connection_alive(self, node_id: str, alive: bool):
        if node_id not in self.connections:
            self.connections[node_id] = Mock(spec=SSHConnection)
        self.connections[node_id].is_alive = lambda: alive


class MockConnection:
    def __init__(self, alive=True):
        self._alive = alive
    
    def is_alive(self):
        return self._alive
    
    def close(self):
        pass


@pytest.fixture
def sample_execution_run():
    nodes = [
        PhysicalNode(id="node-1", host="10.0.0.1", port=22, username="user", hardware_spec={}),
        PhysicalNode(id="node-2", host="10.0.0.2", port=22, username="user", hardware_spec={}),
    ]
    tasks = [
        TaskChunk(id=f"task-{i}", iterations=100, payload="test")
        for i in range(3)
    ]
    return ExecutionRun(
        id="run-test",
        nodes=nodes,
        task_chunks=tasks,
        status=ExecutionStatus.RUNNING
    )


@pytest.fixture
def sample_config():
    return OrchestratorConfig(
        heartbeat_timeout_seconds=1,
        straggler_threshold_multiplier=2.0,
        max_task_retries=2
    )


@pytest.fixture
def scheduler(sample_execution_run, sample_config):
    node_manager = MockNodeManager()
    # Initialize connections as alive
    for node in sample_execution_run.nodes:
        node_manager.connections[node.id] = MockConnection(alive=True)
    
    return Scheduler(sample_execution_run, node_manager, sample_config)


def test_straggler_detection_and_reassignment(scheduler, sample_config):
    """
    T017 Test: Verify that a task with a stale heartbeat is detected as a straggler
    and re-assigned.
    """
    # Manually set up an assignment with an old heartbeat
    task_id = "task-0"
    old_time = datetime.now() - timedelta(seconds=sample_config.heartbeat_timeout_seconds + 1)
    
    assignment = TaskAssignment(
        task_id=task_id,
        node_id="node-1",
        assigned_at=datetime.now(),
        last_heartbeat=old_time,
        status=TaskStatus.RUNNING,
        retries=0
    )
    
    with scheduler.state.lock:
        scheduler.state.active_assignments[task_id] = assignment
        scheduler.state.node_health["node-1"] = NodeStatus.BUSY
        # Ensure task is not in pending
        if any(t.id == task_id for t in scheduler.state.pending_tasks):
            scheduler.state.pending_tasks.remove(next(t for t in scheduler.state.pending_tasks if t.id == task_id))
    
    # Trigger heartbeat check
    scheduler._check_heartbeats()
    
    # Verify straggler event logged
    assert len(scheduler.state.straggler_events) == 1
    event = scheduler.state.straggler_events[0]
    assert event["task_id"] == task_id
    assert event["reason"] == "straggler_timeout"
    assert event["attempt"] == 1
    
    # Verify task was moved back to pending (or re-assigned logic triggered)
    # In this mock, _handle_straggler puts it in pending_tasks if no node is free immediately,
    # or re-assigns if a node is free.
    # We check that the active assignment is gone
    assert task_id not in scheduler.state.active_assignments


def test_node_dropout_detection(scheduler, sample_config):
    """
    T017 Test: Verify that a node with a dead connection is marked as DROPPED
    and its tasks are re-assigned.
    """
    task_id = "task-1"
    current_time = datetime.now()
    
    # Setup assignment
    assignment = TaskAssignment(
        task_id=task_id,
        node_id="node-2",
        assigned_at=current_time,
        last_heartbeat=current_time,
        status=TaskStatus.RUNNING
    )
    
    with scheduler.state.lock:
        scheduler.state.active_assignments[task_id] = assignment
        scheduler.state.node_health["node-2"] = NodeStatus.BUSY
    
    # Simulate node death
    scheduler.node_manager.set_connection_alive("node-2", False)
    
    # Trigger check
    scheduler._check_heartbeats()
    
    # Verify dropout event
    assert len(scheduler.state.dropout_events) == 1
    event = scheduler.state.dropout_events[0]
    assert event["node_id"] == "node-2"
    assert event["task_id"] == task_id
    assert event["reason"] == "heartbeat_loss"
    
    # Verify node status changed
    assert scheduler.state.node_health["node-2"] == NodeStatus.OFFLINE


def test_max_retries_exceeded(scheduler, sample_config):
    """
    T017 Test: Verify that a task exceeding max retries is marked as FAILED.
    """
    task_id = "task-2"
    current_time = datetime.now()
    
    # Setup assignment with max retries already reached
    assignment = TaskAssignment(
        task_id=task_id,
        node_id="node-1",
        assigned_at=current_time,
        last_heartbeat=current_time - timedelta(seconds=sample_config.heartbeat_timeout_seconds + 1),
        status=TaskStatus.RUNNING,
        retries=sample_config.max_task_retries
    )
    
    with scheduler.state.lock:
        scheduler.state.active_assignments[task_id] = assignment
        scheduler.state.node_health["node-1"] = NodeStatus.BUSY
    
    # Trigger check
    scheduler._check_heartbeats()
    
    # Verify task failed and not re-assigned
    assert task_id in scheduler.state.failed_tasks
    assert task_id not in scheduler.state.active_assignments
    # Verify no new straggler event (since we gave up)
    # The logic in _handle_straggler checks retries before adding event
    # But we need to ensure the event wasn't added for the "give up" case
    # The current logic adds event before checking retries? No, it checks first.
    # Let's verify the count didn't increase for this specific task if it was already at max
    # Actually, the logic: if retries >= max -> fail. So no event added for the "give up" moment.
    # But the previous attempts would have added events.
    # This test verifies the final state is FAILED.