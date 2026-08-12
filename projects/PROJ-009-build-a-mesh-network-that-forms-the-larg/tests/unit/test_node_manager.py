"""
Unit tests for the Node Manager module.
"""
import pytest
from unittest.mock import patch, MagicMock
import socket
import paramiko

from orchestrator.node_manager import (
    NodeManager,
    NodeDiscoveryError,
    NodeState,
    create_node_manager
)


@pytest.fixture
def mock_config():
    return {
        'ssh_user': 'testuser',
        'ssh_password': 'testpass',
        'discovery_timeout': 2.0,
        'heartbeat_interval': 5.0,
        'heartbeat_timeout': 15.0
    }


@pytest.fixture
def node_manager(mock_config):
    return create_node_manager(mock_config)


class TestNodeDiscovery:
    def test_empty_ip_list_raises_error(self, node_manager):
        with pytest.raises(NodeDiscoveryError) as exc_info:
            node_manager.discover_nodes([])
        assert "No IP addresses provided" in str(exc_info.value)

    @patch('orchestrator.node_manager.paramiko.SSHClient')
    def test_discover_single_online_node(self, mock_ssh_class, node_manager):
        mock_ssh = MagicMock()
        mock_ssh_class.return_value = mock_ssh
        mock_ssh.connect.return_value = None
        mock_channel = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'node-01-hostname\n'
        mock_ssh.exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())
        mock_channel.recv_exit_status.return_value = 0
        mock_ssh.exec_command.return_value[1].channel = mock_channel

        results = node_manager.discover_nodes(['192.168.1.10'])

        assert len(results) == 1
        assert results[0]['ip'] == '192.168.1.10'
        assert results[0]['hostname'] == 'node-01-hostname'
        assert results[0]['status'] == 'online'
        assert '192.168.1.10' in node_manager.nodes
        assert node_manager.nodes['192.168.1.10'].status == 'online'

    @patch('orchestrator.node_manager.paramiko.SSHClient')
    def test_discover_mixed_nodes(self, mock_ssh_class, node_manager):
        mock_ssh = MagicMock()
        mock_ssh_class.return_value = mock_ssh

        # First call succeeds
        mock_ssh.connect.side_effect = [None, socket.timeout(), None]
        mock_channel = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'node-01-hostname\n'
        mock_ssh.exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())
        mock_channel.recv_exit_status.return_value = 0
        mock_ssh.exec_command.return_value[1].channel = mock_channel

        # Second call times out (handled by side_effect logic implicitly via exception)
        # Third call succeeds
        mock_ssh.connect.reset_mock()
        mock_ssh.connect.side_effect = [None, socket.timeout(), None]
        
        # Mock exec_command to return different results based on call count
        def exec_command_side_effect(cmd):
            if 'hostname' in cmd:
                mock_out = MagicMock()
                mock_out.read.return_value = b'node-03-hostname\n'
                mock_ch = MagicMock()
                mock_ch.recv_exit_status.return_value = 0
                return (MagicMock(), mock_out, MagicMock())
            return (MagicMock(), MagicMock(), MagicMock())
        
        mock_ssh.exec_command.side_effect = exec_command_side_effect

        results = node_manager.discover_nodes(['192.168.1.10', '192.168.1.11', '192.168.1.12'])

        assert len(results) == 3
        # First node online
        assert results[0]['status'] == 'online'
        # Second node offline (timeout)
        assert results[1]['status'] == 'offline'
        # Third node online
        assert results[2]['status'] == 'online'

        # Verify at least one node is online (otherwise error would be raised)
        assert node_manager.nodes['192.168.1.10'].status == 'online'
        assert node_manager.nodes['192.168.1.12'].status == 'online'
        assert '192.168.1.11' not in node_manager.nodes

    @patch('orchestrator.node_manager.paramiko.SSHClient')
    def test_all_nodes_unreachable_raises_error(self, mock_ssh_class, node_manager):
        mock_ssh = MagicMock()
        mock_ssh_class.return_value = mock_ssh
        mock_ssh.connect.side_effect = socket.timeout()

    @patch('paramiko.SSHClient')
    def test_discover_nodes_all_fail_raises_error(self, mock_ssh_client, manager):
        """Test that discovery raises error if ALL nodes fail."""
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client
        
        # All connections fail
        mock_client.connect = MagicMock(side_effect=socket.timeout("All failed"))
        
        ip_list = ['192.168.1.10', '192.168.1.11']
        
        with pytest.raises(NodeDiscoveryError) as exc_info:
            node_manager.discover_nodes(['192.168.1.10', '192.168.1.11'])
        
        assert "All 2 nodes are unreachable" in str(exc_info.value)

    @patch('orchestrator.node_manager.paramiko.SSHClient')
    def test_authentication_failure_marks_offline(self, mock_ssh_class, node_manager):
        mock_ssh = MagicMock()
        mock_ssh_class.return_value = mock_ssh
        mock_ssh.connect.side_effect = paramiko.AuthenticationException("Auth failed")

        results = node_manager.discover_nodes(['192.168.1.10'])

        assert results[0]['status'] == 'offline'
        assert '192.168.1.10' not in node_manager.nodes


class TestHeartbeat:
    @patch('orchestrator.node_manager.paramiko.SSHClient')
    def test_send_heartbeat_success(self, mock_ssh_class, node_manager):
        # Setup discovered node
        mock_ssh = MagicMock()
        mock_ssh_class.return_value = mock_ssh
        mock_ssh.connect.return_value = None
        mock_channel = MagicMock()
        mock_stdout = MagicMock()
        mock_ssh.exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())
        mock_channel.recv_exit_status.return_value = 0
        mock_ssh.exec_command.return_value[1].channel = mock_channel

        node_manager.discover_nodes(['192.168.1.10'])
        
        # Reset mock for heartbeat call
        mock_ssh.reset_mock()
        mock_ssh.exec_command.return_value[1].channel.recv_exit_status.return_value = 0

        result = node_manager.send_heartbeat('192.168.1.10')

        assert result is True
        assert node_manager.nodes['192.168.1.10'].status == 'online'
        assert node_manager.nodes['192.168.1.10'].last_heartbeat is not None

    def test_send_heartbeat_unknown_node(self, node_manager):
        result = node_manager.send_heartbeat('192.168.1.99')
        assert result is False

    @patch('orchestrator.node_manager.paramiko.SSHClient')
    def test_send_heartbeat_failure(self, mock_ssh_class, node_manager):
        # Setup discovered node
        mock_ssh = MagicMock()
        mock_ssh_class.return_value = mock_ssh
        mock_ssh.connect.return_value = None
        mock_channel = MagicMock()
        mock_ssh.exec_command.return_value = (MagicMock(), MagicMock(), MagicMock())
        mock_channel.recv_exit_status.return_value = 1
        mock_ssh.exec_command.return_value[1].channel = mock_channel

        node_manager.discover_nodes(['192.168.1.10'])
        
        mock_ssh.reset_mock()
        mock_ssh.exec_command.return_value[1].channel.recv_exit_status.return_value = 1

        result = node_manager.send_heartbeat('192.168.1.10')

        assert result is False
        assert node_manager.nodes['192.168.1.10'].status == 'online' # Status doesn't change on heartbeat failure unless connection lost, but here we just return False


class TestNodeManagerFactory:
    def test_create_node_manager(self):
        manager = create_node_manager({'test': 'config'})
        assert isinstance(manager, NodeManager)
        assert manager.config['test'] == 'config'