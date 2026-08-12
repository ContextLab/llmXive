"""
Unit tests for node_manager.py
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
import socket
import paramiko

from orchestrator.node_manager import (
    NodeManager,
    NodeDiscoveryError,
    NodeState,
    create_node_manager
)


class TestNodeManager:
    """Tests for NodeManager class."""

    @pytest.fixture
    def manager(self):
        """Create a NodeManager instance for testing."""
        return NodeManager({
            'ssh_timeout': 2,
            'discovery_timeout': 5,
            'ssh_port': 22,
            'ssh_username': 'testuser'
        })

    def test_init_with_config(self, manager):
        """Test that manager initializes with correct config values."""
        assert manager.discovery_timeout == 5
        assert manager.ssh_timeout == 2
        assert manager.ssh_port == 22
        assert manager.ssh_username == 'testuser'

    @patch('socket.gethostbyaddr')
    @patch('paramiko.SSHClient')
    def test_discover_nodes_success(self, mock_ssh_client, mock_gethostbyaddr, manager):
        """Test successful node discovery."""
        mock_gethostbyaddr.return_value = ('node1.local', [], ['192.168.1.10'])
        
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client
        
        # Mock connect to succeed
        mock_client.connect = MagicMock()
        
        ip_list = ['192.168.1.10']
        results = manager.discover_nodes(ip_list)
        
        assert len(results) == 1
        assert results[0]['ip'] == '192.168.1.10'
        assert results[0]['status'] == 'online'
        assert results[0]['hostname'] == 'node1.local'
        assert '192.168.1.10' in manager.known_nodes
        assert manager.known_nodes['192.168.1.10'].status == 'online'

    @patch('socket.gethostbyaddr')
    @patch('paramiko.SSHClient')
    def test_discover_nodes_partial_failure(self, mock_ssh_client, mock_gethostbyaddr, manager):
        """Test discovery with some nodes failing."""
        mock_gethostbyaddr.return_value = ('node1.local', [], ['192.168.1.10'])
        
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client
        
        # First node succeeds
        def connect_side_effect(*args, **kwargs):
            if args[0] == '192.168.1.10':
                return
            raise socket.timeout("Connection timed out")
        
        mock_client.connect = MagicMock(side_effect=connect_side_effect)
        
        ip_list = ['192.168.1.10', '192.168.1.11']
        results = manager.discover_nodes(ip_list)
        
        assert len(results) == 2
        assert results[0]['status'] == 'online'
        assert results[1]['status'] == 'offline'

    @patch('paramiko.SSHClient')
    def test_discover_nodes_all_fail_raises_error(self, mock_ssh_client, manager):
        """Test that discovery raises error if ALL nodes fail."""
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client
        
        # All connections fail
        mock_client.connect = MagicMock(side_effect=socket.timeout("All failed"))
        
        ip_list = ['192.168.1.10', '192.168.1.11']
        
        with pytest.raises(NodeDiscoveryError) as exc_info:
            manager.discover_nodes(ip_list)
        
        assert "All" in str(exc_info.value)

    @patch('paramiko.SSHClient')
    def test_ping_node_success(self, mock_ssh_client, manager):
        """Test successful heartbeat ping."""
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client
        mock_client.connect = MagicMock()
        
        # Setup known node
        manager.known_nodes['192.168.1.10'] = NodeState(
            ip='192.168.1.10',
            hostname='test',
            status='online',
            ssh_client=mock_client
        )
        
        # Mock exec_command to succeed
        mock_transport = MagicMock()
        mock_transport.is_active.return_value = True
        mock_client.get_transport.return_value = mock_transport
        
        mock_channel = MagicMock()
        mock_channel.recv_exit_status = MagicMock()
        mock_client.exec_command.return_value = (MagicMock(), MagicMock(channel=mock_channel), MagicMock())
        
        result = manager.ping_node('192.168.1.10')
        
        assert result is True
        assert manager.known_nodes['192.168.1.10'].status == 'online'

    @patch('paramiko.SSHClient')
    def test_ping_node_failure(self, mock_ssh_client, manager):
        """Test heartbeat ping failure."""
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client
        
        # Setup known node as unresponsive
        manager.known_nodes['192.168.1.10'] = NodeState(
            ip='192.168.1.10',
            hostname='test',
            status='unresponsive',
            ssh_client=mock_client
        )
        
        result = manager.ping_node('192.168.1.10')
        
        assert result is False

    def test_ping_node_unknown(self, manager):
        """Test pinging an unknown node."""
        result = manager.ping_node('192.168.1.99')
        assert result is False

    def test_close_connections(self, manager):
        """Test closing all connections."""
        mock_client = MagicMock()
        mock_client.close = MagicMock()
        
        manager.known_nodes['192.168.1.10'] = NodeState(
            ip='192.168.1.10',
            hostname='test',
            status='online',
            ssh_client=mock_client
        )
        
        manager.close_connections()
        
        mock_client.close.assert_called_once()
        assert len(manager.known_nodes) == 0

def test_create_node_manager_factory():
    """Test factory function."""
    config = {'ssh_timeout': 10}
    manager = create_node_manager(config)
    assert isinstance(manager, NodeManager)
    assert manager.ssh_timeout == 10