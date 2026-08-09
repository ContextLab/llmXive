"""
Unit tests for the Node Manager.
Tests discovery, heartbeat, and reassignment logic using mock SSH.
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime
import socket

from orchestrator.node_manager import (
    NodeManager, 
    NodeDiscoveryError, 
    NodeReassignError, 
    NodeDiscoveryResult,
    create_node_manager
)
from orchestrator.models import PhysicalNode, NodeStatus

class TestNodeManager:
    
    def test_init(self):
        manager = create_node_manager()
        assert manager is not None
        assert manager.nodes == {}
        assert manager.ssh_clients == {}

    @patch('paramiko.SSHClient')
    def test_discover_nodes_success(self, mock_ssh_class):
        """Test successful discovery of a node."""
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client
        
        manager = create_node_manager()
        # Mock config to avoid dependency on real config file for this unit test
        manager.config = MagicMock()
        manager.config.ssh_username = "test_user"
        manager.config.ssh_password = "test_pass"
        manager.config.node_timeout = 2.0

        result = manager.discover_nodes(["192.168.1.10"])
        
        assert "192.168.1.10" in result.discovered_nodes
        assert len(result.failed_nodes) == 0
        assert "192.168.1.10" in manager.nodes
        assert manager.nodes["192.168.1.10"].status == "active"

    @patch('paramiko.SSHClient')
    def test_discover_nodes_timeout(self, mock_ssh_class):
        """Test discovery failure due to timeout."""
        mock_client = MagicMock()
        mock_client.connect.side_effect = socket.timeout("Connection timed out")
        mock_ssh_class.return_value = mock_client

        manager = create_node_manager()
        manager.config = MagicMock()
        manager.config.ssh_username = "test_user"
        manager.config.ssh_password = "test_pass"
        manager.config.node_timeout = 2.0

        result = manager.discover_nodes(["192.168.1.99"])
        
        assert "192.168.1.99" in result.failed_nodes
        assert "192.168.1.99" not in result.discovered_nodes

    @patch('paramiko.SSHClient')
    def test_discover_nodes_all_fail_raises_error(self, mock_ssh_class):
        """Test that NodeDiscoveryError is raised if ALL nodes fail."""
        mock_client = MagicMock()
        mock_client.connect.side_effect = socket.timeout("Timeout")
        mock_ssh_class.return_value = mock_client

        manager = create_node_manager()
        manager.config = MagicMock()
        manager.config.ssh_username = "test_user"
        manager.config.ssh_password = "test_pass"
        manager.config.node_timeout = 2.0

        with pytest.raises(NodeDiscoveryError) as excinfo:
            manager.discover_nodes(["192.168.1.99", "192.168.1.98"])
        
        assert "All" in str(excinfo.value)

    @patch('paramiko.SSHClient')
    def test_ping_node_success(self, mock_ssh_class):
        """Test successful ping."""
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client
        
        # Setup node state
        manager = create_node_manager()
        manager.nodes["192.168.1.10"] = MagicMock()
        manager.nodes["192.168.1.10"].status = "active"
        
        # Mock exec_command
        stdin, stdout, stderr = MagicMock(), MagicMock(), MagicMock()
        stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (stdin, stdout, stderr)

        result = manager.ping_node("192.168.1.10")
        
        assert result is True
        assert manager.nodes["192.168.1.10"].status == "active"

    @patch('paramiko.SSHClient')
    def test_ping_node_failure(self, mock_ssh_class):
        """Test ping failure updates status."""
        mock_client = MagicMock()
        mock_client.exec_command.side_effect = socket.timeout("Timeout")
        mock_ssh_class.return_value = mock_client

        manager = create_node_manager()
        manager.nodes["192.168.1.10"] = MagicMock()
        manager.nodes["192.168.1.10"].status = "active"

        result = manager.ping_node("192.168.1.10")
        
        assert result is False
        assert manager.nodes["192.168.1.10"].status == "heartbeat_lost"

    def test_reassign_task_success(self):
        """Test successful task reassignment."""
        manager = create_node_manager()
        # Pre-populate a node
        manager.nodes["192.168.1.20"] = MagicMock()
        manager.nodes["192.168.1.20"].status = "active"
        manager.nodes["192.168.1.20"].task_queue = []

        result = manager.reassign_task("task_123", "192.168.1.20")
        
        assert result is True
        assert "task_123" in manager.nodes["192.168.1.20"].task_queue

    def test_reassign_task_target_not_active(self):
        """Test reassignment fails if target is not active."""
        manager = create_node_manager()
        manager.nodes["192.168.1.20"] = MagicMock()
        manager.nodes["192.168.1.20"].status = "heartbeat_lost"
        manager.nodes["192.168.1.20"].task_queue = []

        with pytest.raises(NodeReassignError) as excinfo:
            manager.reassign_task("task_123", "192.168.1.20")
        
        assert "not active" in str(excinfo.value)

    def test_reassign_task_unknown_target(self):
        """Test reassignment fails if target IP is unknown."""
        manager = create_node_manager()

        with pytest.raises(NodeReassignError) as excinfo:
            manager.reassign_task("task_123", "192.168.1.99")
        
        assert "not in the active node list" in str(excinfo.value)
