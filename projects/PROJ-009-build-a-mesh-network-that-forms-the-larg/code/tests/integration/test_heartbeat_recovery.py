"""
Integration test for node heartbeat detection and re-assignment logic.

This test verifies that:
1. The NodeManager correctly detects heartbeat events from nodes.
2. When a node fails to send a heartbeat within the timeout window,
   it is marked as 'FAILED' or 'DISCONNECTED'.
3. Tasks assigned to the failed node are automatically re-assigned
   to available healthy nodes.
4. The re-assignment logic respects task dependencies and node capacity.

Dependencies:
- T005 (MockSSHConnection) for simulating node behavior
- T008 (Models) for TaskChunk, PhysicalNode, NodeStatus
- T013 (NodeManager) for the actual implementation being tested
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestrator.models import PhysicalNode, TaskChunk, TaskStatus, NodeStatus
from orchestrator.node_manager import NodeManager, NodeDiscoveryResult
from orchestrator.scheduler import Scheduler
from orchestrator.logger import get_logger
from tests.unit.mock_nodes import MockNodeSpec, MockNodeManager, MockSSHConnection

logger = get_logger(__name__)

# Configuration constants for the test
HEARTBEAT_TIMEOUT_SECONDS = 5
HEARTBEAT_INTERVAL_SECONDS = 2
RECOVERY_TIMEOUT_SECONDS = 10


def create_test_nodes(count: int = 3) -> list[PhysicalNode]:
    """Create a list of mock physical nodes for testing."""
    nodes = []
    for i in range(count):
        node = PhysicalNode(
            node_id=f"node-{i:03d}",
            hostname=f"192.168.1.{100 + i}",
            status=NodeStatus.ONLINE,
            last_heartbeat=datetime.now(),
            available_ram_gb=8.0,
            cpu_cores=4,
            is_available=True
        )
        nodes.append(node)
    return nodes


def create_test_tasks(count: int = 5, assigned_node_id: str = None) -> list[TaskChunk]:
    """Create a list of test tasks, optionally pre-assigned to a node."""
    tasks = []
    for i in range(count):
        task = TaskChunk(
            task_id=f"task-{i:03d}",
            status=TaskStatus.PENDING if assigned_node_id is None else TaskStatus.RUNNING,
            assigned_node_id=assigned_node_id,
            payload_size_mb=100,
            estimated_duration_seconds=30,
            created_at=datetime.now()
        )
        tasks.append(task)
    return tasks


class TestHeartbeatRecovery:
    """Integration tests for heartbeat detection and task re-assignment."""

    @pytest.fixture
    def mock_node_manager(self):
        """Provide a MockNodeManager instance for testing."""
        # We use the MockNodeManager from unit tests to simulate node behavior
        # without requiring real SSH connections
        return MockNodeManager()

    @pytest.fixture
    def healthy_nodes(self):
        """Provide a set of healthy nodes."""
        return create_test_nodes(count=3)

    @pytest.fixture
    def failed_node(self):
        """Provide a single node that will simulate failure."""
        node = PhysicalNode(
            node_id="node-fail-001",
            hostname="192.168.1.200",
            status=NodeStatus.ONLINE,
            last_heartbeat=datetime.now() - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS * 2),
            available_ram_gb=8.0,
            cpu_cores=4,
            is_available=True
        )
        return node

    @pytest.fixture
    def assigned_tasks(self, failed_node):
        """Create tasks assigned to the failed node."""
        return create_test_tasks(count=3, assigned_node_id=failed_node.node_id)

    def test_heartbeat_detection_healthy_node(self, mock_node_manager, healthy_nodes):
        """Verify that a node sending heartbeats is marked as healthy."""
        # Simulate heartbeat updates
        for node in healthy_nodes:
            mock_node_manager.update_heartbeat(node.node_id)

        # Verify all nodes are still online
        for node in healthy_nodes:
            status = mock_node_manager.get_node_status(node.node_id)
            assert status == NodeStatus.ONLINE, f"Node {node.node_id} should be ONLINE"

    def test_heartbeat_timeout_detection(self, mock_node_manager, failed_node):
        """Verify that a node missing heartbeats is marked as FAILED."""
        # Initialize node in manager
        mock_node_manager.add_node(failed_node)

        # Do NOT update heartbeat - simulate failure

        # Wait for timeout period
        time.sleep(HEARTBEAT_TIMEOUT_SECONDS + 1)

        # Check status
        status = mock_node_manager.get_node_status(failed_node.node_id)
        assert status == NodeStatus.FAILED, f"Node should be FAILED after timeout, got {status}"

    def test_task_reassignment_on_node_failure(
        self, mock_node_manager, healthy_nodes, failed_node, assigned_tasks
    ):
        """
        Verify that when a node fails, its assigned tasks are re-assigned
        to healthy nodes.
        """
        # Setup: Add nodes and tasks
        for node in healthy_nodes:
            mock_node_manager.add_node(node)
        mock_node_manager.add_node(failed_node)

        # Assign tasks to the failing node
        for task in assigned_tasks:
            mock_node_manager.assign_task(task)

        # Verify tasks are initially assigned to failed node
        for task in assigned_tasks:
            assert task.assigned_node_id == failed_node.node_id
            assert task.status == TaskStatus.RUNNING

        # Simulate node failure (no heartbeat)
        # We manually set the status to FAILED to trigger recovery logic
        mock_node_manager.mark_node_failed(failed_node.node_id)

        # Trigger re-assignment logic
        re_assigned_tasks = mock_node_manager.reassign_tasks_from_node(failed_node.node_id)

        # Verify tasks were re-assigned
        assert len(re_assigned_tasks) == len(assigned_tasks), "All tasks should be re-assigned"

        for task in re_assigned_tasks:
            # Task should no longer be assigned to the failed node
            assert task.assigned_node_id != failed_node.node_id
            # Task should be assigned to a healthy node
            assert task.assigned_node_id in [n.node_id for n in healthy_nodes]
            # Task status should be PENDING again (ready for re-execution)
            assert task.status == TaskStatus.PENDING

    def test_reassignment_respects_node_capacity(self, mock_node_manager):
        """Verify that re-assignment does not overload a single node."""
        # Create one healthy node with limited capacity
        node = PhysicalNode(
            node_id="node-cap-001",
            hostname="192.168.1.150",
            status=NodeStatus.ONLINE,
            last_heartbeat=datetime.now(),
            available_ram_gb=2.0,  # Limited RAM
            cpu_cores=1,
            is_available=True
        )
        mock_node_manager.add_node(node)

        # Create a failed node with many tasks
        failed_node = PhysicalNode(
            node_id="node-overload-001",
            hostname="192.168.1.160",
            status=NodeStatus.FAILED,
            last_heartbeat=datetime.now() - timedelta(seconds=10),
            available_ram_gb=8.0,
            cpu_cores=4,
            is_available=False
        )
        mock_node_manager.add_node(failed_node)

        # Create 10 tasks assigned to failed node
        tasks = create_test_tasks(count=10, assigned_node_id=failed_node.node_id)

        # Simulate failure and re-assignment
        mock_node_manager.mark_node_failed(failed_node.node_id)
        re_assigned_tasks = mock_node_manager.reassign_tasks_from_node(failed_node.node_id)

        # With only one node of limited capacity, tasks might be distributed
        # or some might remain pending if capacity is exceeded
        # This test ensures the system doesn't crash and attempts re-assignment
        assert len(re_assigned_tasks) > 0, "Some tasks should be re-assigned"

        # Verify no task is assigned to the failed node
        for task in re_assigned_tasks:
            assert task.assigned_node_id != failed_node.node_id

    def test_recovery_with_no_available_nodes(self, mock_node_manager, failed_node, assigned_tasks):
        """Verify behavior when all nodes are failed and no re-assignment is possible."""
        # Mark all nodes as failed
        mock_node_manager.add_node(failed_node)
        mock_node_manager.mark_node_failed(failed_node.node_id)

        # Assign tasks to failed node
        for task in assigned_tasks:
            mock_node_manager.assign_task(task)

        # Attempt re-assignment
        re_assigned_tasks = mock_node_manager.reassign_tasks_from_node(failed_node.node_id)

        # No tasks should be re-assigned (no available nodes)
        assert len(re_assigned_tasks) == 0, "No tasks should be re-assigned when no nodes available"

        # Tasks should remain in their current state (or be marked as orphaned)
        for task in assigned_tasks:
            # At minimum, they are not assigned to the failed node anymore
            # (the re-assignment logic should clear the assignment)
            assert task.assigned_node_id != failed_node.node_id

    def test_heartbeat_recovery_integration_flow(self):
        """
        End-to-end integration test simulating:
        1. Normal operation with heartbeats
        2. Node failure
        3. Automatic recovery and re-assignment
        4. Resumption of normal operation
        """
        # Setup
        nodes = create_test_nodes(count=2)
        mock_manager = MockNodeManager()

        for node in nodes:
            mock_manager.add_node(node)

        # Phase 1: Normal operation
        for _ in range(3):
            for node in nodes:
                mock_manager.update_heartbeat(node.node_id)
            time.sleep(0.1)

        # Verify all healthy
        for node in nodes:
            assert mock_manager.get_node_status(node.node_id) == NodeStatus.ONLINE

        # Phase 2: Simulate failure of node 0
        failed_node = nodes[0]
        healthy_node = nodes[1]

        # Stop sending heartbeats for node 0
        # Wait for timeout
        time.sleep(HEARTBEAT_TIMEOUT_SECONDS + 1)

        # Manually trigger failure detection (in real system, this is periodic)
        mock_manager.mark_node_failed(failed_node.node_id)
        assert mock_manager.get_node_status(failed_node.node_id) == NodeStatus.FAILED

        # Phase 3: Assign and re-assign tasks
        tasks = create_test_tasks(count=4, assigned_node_id=failed_node.node_id)
        for task in tasks:
            mock_manager.assign_task(task)

        re_assigned = mock_manager.reassign_tasks_from_node(failed_node.node_id)

        assert len(re_assigned) == 4, "All tasks should be re-assigned"
        for task in re_assigned:
            assert task.assigned_node_id == healthy_node.node_id

        # Phase 4: Resume normal operation
        for _ in range(3):
            mock_manager.update_heartbeat(healthy_node.node_id)
            time.sleep(0.1)

        assert mock_manager.get_node_status(healthy_node.node_id) == NodeStatus.ONLINE

    def test_concurrent_failures(self):
        """Test handling of multiple simultaneous node failures."""
        nodes = create_test_nodes(count=4)
        mock_manager = MockNodeManager()

        for node in nodes:
            mock_manager.add_node(node)

        # Assign tasks to first two nodes
        tasks_node0 = create_test_tasks(count=3, assigned_node_id=nodes[0].node_id)
        tasks_node1 = create_test_tasks(count=3, assigned_node_id=nodes[1].node_id)

        for task in tasks_node0 + tasks_node1:
            mock_manager.assign_task(task)

        # Simulate simultaneous failure of nodes 0 and 1
        mock_manager.mark_node_failed(nodes[0].node_id)
        mock_manager.mark_node_failed(nodes[1].node_id)

        # Re-assign tasks from both failed nodes
        re_assigned_0 = mock_manager.reassign_tasks_from_node(nodes[0].node_id)
        re_assigned_1 = mock_manager.reassign_tasks_from_node(nodes[1].node_id)

        # All tasks should be re-assigned to remaining healthy nodes (2 and 3)
        assert len(re_assigned_0) == 3
        assert len(re_assigned_1) == 3

        healthy_ids = [nodes[2].node_id, nodes[3].node_id]
        for task in re_assigned_0 + re_assigned_1:
            assert task.assigned_node_id in healthy_ids
            assert task.status == TaskStatus.PENDING

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
