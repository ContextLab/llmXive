"""
Unit tests for node_manager.py.

These tests verify the discovery logic without requiring real hardware.
They mock the paramiko SSHClient to simulate connection success/failure.
"""
import pytest
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime, timezone

from orchestrator.node_manager import (
    NodeManager, 
    NodeDiscoveryError, 
    NodeState, 
    create_node_manager
)
from orchestrator.logger import configure_logging

# Configure logging for tests
configure_logging()

@pytest.fixture
def mock_config():
    return {
        'ssh_timeout': 2,
        'ssh_port': 22,
        'username': 'test_user'
    }

@pytest.fixture
def node_manager(mock_config):
    return create_node_manager(mock_config)

class TestNodeDiscovery:
    """Tests for the discover_nodes method."""

    def test_discover_single_online_node(self, node_manager):
        """Test discovery of a single online node."""
        ip_list = ['192.168.1.10']
        
        with patch('orchestrator.node_manager.SSHClient') as mock_ssh_class:
            mock_client = MagicMock()
            mock_ssh_class.return_value = mock_client
            
            # Simulate successful connection
            mock_client.connect.return_value = None
            mock_client.exec_command.return_value = (MagicMock(), MagicMock(read=lambda: b'node1'), MagicMock())
            mock_client.channel.recv_exit_status.return_value = 0
            
            results = node_manager.discover_nodes(ip_list)
            
            assert len(results) == 1
            assert results[0]['ip'] == '192.168.1.10'
            assert results[0]['status'] == 'online'
            assert results[0]['hostname'] == 'node1'
            
            mock_client.close.assert_called()

    def test_discover_single_offline_node(self, node_manager):
        """Test discovery of a single offline node."""
        ip_list = ['192.168.1.99']
        
        with patch('orchestrator.node_manager.SSHClient') as mock_ssh_class:
            mock_client = MagicMock()
            mock_ssh_class.return_value = mock_client
            
            # Simulate connection timeout
            mock_client.connect.side_effect = Exception("Connection timed out")
            
            results = node_manager.discover_nodes(ip_list)
            
            assert len(results) == 1
            assert results[0]['ip'] == '192.168.1.99'
            assert results[0]['status'] == 'offline'
            assert results[0]['hostname'] == '192.168.1.99' # Should fallback to IP

    def test_discover_mixed_nodes(self, node_manager):
        """Test discovery with a mix of online and offline nodes."""
        ip_list = ['192.168.1.10', '192.168.1.11', '192.168.1.99']
        
        with patch('orchestrator.node_manager.SSHClient') as mock_ssh_class:
            mock_client = MagicMock()
            mock_ssh_class.return_value = mock_client
            
            def connect_side_effect(*args, **kwargs):
                if '192.168.1.11' in args or kwargs.get('hostname') == '192.168.1.11':
                    raise Exception("Auth failed")
                return None
            
            mock_client.connect.side_effect = connect_side_effect
            mock_client.exec_command.return_value = (MagicMock(), MagicMock(read=lambda: b'mesh-node'), MagicMock())
            mock_client.channel.recv_exit_status.return_value = 0
            
            results = node_manager.discover_nodes(ip_list)
            
            assert len(results) == 3
            
            # Check online node
            online = [r for r in results if r['status'] == 'online']
            assert len(online) == 1
            assert online[0]['ip'] == '192.168.1.10'
            
            # Check offline nodes
            offline = [r for r in results if r['status'] == 'offline']
            assert len(offline) == 2

    def test_discover_all_offline_raises_error(self, node_manager):
        """Test that discovery raises NodeDiscoveryError if ALL nodes fail."""
        ip_list = ['192.168.1.99', '192.168.1.98']
        
        with patch('orchestrator.node_manager.SSHClient') as mock_ssh_class:
            mock_client = MagicMock()
            mock_ssh_class.return_value = mock_client
            mock_client.connect.side_effect = Exception("Connection refused")
            
            with pytest.raises(NodeDiscoveryError) as exc_info:
                node_manager.discover_nodes(ip_list)
            
            assert "Discovery failed for all" in str(exc_info.value.message)
            assert len(exc_info.value.failed_nodes) == 2

    def test_empty_ip_list(self, node_manager):
        """Test behavior with an empty IP list."""
        results = node_manager.discover_nodes([])
        assert results == []

    def test_hostname_retrieval_failure(self, node_manager):
        """Test that discovery continues if hostname retrieval fails."""
        ip_list = ['192.168.1.10']
        
        with patch('orchestrator.node_manager.SSHClient') as mock_ssh_class:
            mock_client = MagicMock()
            mock_ssh_class.return_value = mock_client
            
            mock_client.connect.return_value = None
            # Simulate successful connection but failed hostname command
            mock_client.exec_command.side_effect = Exception("Command failed")
            
            results = node_manager.discover_nodes(ip_list)
            
            assert len(results) == 1
            assert results[0]['status'] == 'online'
            # Should fallback to IP if hostname command fails
            assert results[0]['hostname'] == '192.168.1.10'

class TestNodeManagerFactory:
    """Tests for the create_node_manager factory."""

    def test_create_node_manager_default(self):
        """Test creating manager with default config."""
        manager = create_node_manager()
        assert isinstance(manager, NodeManager)
        assert manager.ssh_timeout == 5

    def test_create_node_manager_custom(self):
        """Test creating manager with custom config."""
        config = {'ssh_timeout': 10, 'ssh_port': 2222}
        manager = create_node_manager(config)
        assert manager.ssh_timeout == 10
        assert manager.ssh_port == 2222

if __name__ == '__main__':
    pytest.main([__file__, '-v'])