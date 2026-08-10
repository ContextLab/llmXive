"""
Unit tests for the Node Manager module (T013a).

These tests verify the discovery logic, error handling, and state management
without requiring actual network hardware (using mocking).
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timezone
import socket
import time

from orchestrator.node_manager import (
    NodeManager,
    NodeDiscoveryError,
    NodeHeartbeatLost,
    NodeState,
    create_node_manager
)

class TestNodeDiscovery:
    """Tests for the discovery functionality."""

    def test_empty_ip_list_returns_empty(self):
        """Test that an empty IP list returns an empty result."""
        manager = create_node_manager()
        result = manager.discover_nodes([])
        assert result == []

    @patch('socket.socket')
    def test_all_nodes_unreachable_raises_error(self, mock_socket_class):
        """Test that if all nodes are unreachable, NodeDiscoveryError is raised."""
        # Configure socket to always fail
        mock_socket_instance = MagicMock()
        mock_socket_instance.connect.side_effect = socket.timeout("Connection timed out")
        mock_socket_class.return_value = mock_socket_instance

        manager = create_node_manager()
        ip_list = ['192.168.1.10', '192.168.1.11']

        with pytest.raises(NodeDiscoveryError) as exc_info:
            manager.discover_nodes(ip_list)

        assert "All" in str(exc_info.value)
        assert "unreachable" in str(exc_info.value)

    @patch('socket.socket')
    @patch('paramiko.SSHClient')
    def test_single_node_online(self, mock_ssh_client_class, mock_socket_class):
        """Test successful discovery of a single online node."""
        # Mock socket connection success
        mock_socket_instance = MagicMock()
        mock_socket_instance.connect.return_value = None
        mock_socket_class.return_value = mock_socket_instance

        # Mock SSH client
        mock_ssh_client = MagicMock()
        mock_ssh_client_class.return_value = mock_ssh_client
        
        # Mock exec_command for hostname
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'test-node-01'
        mock_ssh_client.exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())

        manager = create_node_manager()
        result = manager.discover_nodes(['192.168.1.10'])

        assert len(result) == 1
        assert result[0]['ip'] == '192.168.1.10'
        assert result[0]['status'] == 'online'
        assert result[0]['hostname'] == 'test-node-01'
        
        # Verify state was stored
        assert '192.168.1.10' in manager.nodes
        assert manager.nodes['192.168.1.10'].status == 'online'

    @patch('socket.socket')
    @patch('paramiko.SSHClient')
    def test_mixed_online_offline_nodes(self, mock_ssh_client_class, mock_socket_class):
        """Test discovery with a mix of online and offline nodes."""
        # First call (online) succeeds, second call (offline) times out
        mock_socket_instance_1 = MagicMock()
        mock_socket_instance_1.connect.return_value = None
        
        mock_socket_instance_2 = MagicMock()
        mock_socket_instance_2.connect.side_effect = socket.timeout("Timeout")

        # Mock SSH for the first node
        mock_ssh_client = MagicMock()
        mock_ssh_client_class.return_value = mock_ssh_client
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'node-01'
        mock_ssh_client.exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())

        # Configure socket to return different instances for different calls
        # We need to simulate that the first IP works and the second doesn't
        # Since socket.connect is called with args, we can't easily distinguish by IP in this mock
        # Instead, we'll mock the logic to return different behaviors based on a counter or side_effect list
        
        # Reset mocks to use side_effect list
        mock_socket_class.return_value = MagicMock()
        mock_socket_class.return_value.connect.side_effect = [None, socket.timeout("Timeout")]

        manager = create_node_manager()
        ip_list = ['192.168.1.10', '192.168.1.11']
        
        # We need to mock SSH for the first one only
        # The second one won't reach SSH because socket fails
        
        result = manager.discover_nodes(ip_list)

        assert len(result) == 2
        
        # First node should be online
        assert result[0]['ip'] == '192.168.1.10'
        assert result[0]['status'] == 'online'
        
        # Second node should be offline
        assert result[1]['ip'] == '192.168.1.11'
        assert result[1]['status'] == 'offline'

        # Only the online node should be in the manager's state
        assert '192.168.1.10' in manager.nodes
        assert '192.168.1.11' not in manager.nodes

class TestHeartbeat:
    """Tests for heartbeat functionality."""

    def test_heartbeat_on_unknown_node_raises(self):
        """Test that checking heartbeat on an unknown node raises NodeHeartbeatLost."""
        manager = create_node_manager()
        
        with pytest.raises(NodeHeartbeatLost):
            manager.check_heartbeat('192.168.1.99')

    @patch('paramiko.SSHClient')
    def test_heartbeat_success(self, mock_ssh_client_class):
        """Test successful heartbeat check."""
        manager = create_node_manager()
        # Pre-populate node state
        manager.nodes['192.168.1.10'] = NodeState(
            ip='192.168.1.10',
            hostname='test-node',
            status='online'
        )

        mock_ssh_client = MagicMock()
        mock_ssh_client_class.return_value = mock_ssh_client
        
        # Mock exec_command
        mock_stdout = MagicMock()
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_ssh_client.exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())

        result = manager.check_heartbeat('192.168.1.10')
        
        assert result is True
        assert manager.nodes['192.168.1.10'].last_heartbeat is not None

    @patch('paramiko.SSHClient')
    def test_heartbeat_failure(self, mock_ssh_client_class):
        """Test failed heartbeat check."""
        manager = create_node_manager()
        manager.nodes['192.168.1.10'] = NodeState(
            ip='192.168.1.10',
            hostname='test-node',
            status='online'
        )

        mock_ssh_client = MagicMock()
        mock_ssh_client_class.return_value = mock_ssh_client
        mock_ssh_client.connect.side_effect = Exception("Connection refused")

        with pytest.raises(NodeHeartbeatLost):
            manager.check_heartbeat('192.168.1.10')

        assert manager.nodes['192.168.1.10'].status == 'offline'

class TestFactory:
    """Tests for factory functions."""

    def test_create_node_manager(self):
        """Test that the factory function returns a NodeManager instance."""
        manager = create_node_manager()
        assert isinstance(manager, NodeManager)

    def test_create_node_manager_with_config(self):
        """Test factory function with custom config."""
        config = {'discovery_timeout': 10.0, 'ssh_port': 2222}
        manager = create_node_manager(config)
        assert manager.discovery_timeout == 10.0
        assert manager.ssh_port == 2222