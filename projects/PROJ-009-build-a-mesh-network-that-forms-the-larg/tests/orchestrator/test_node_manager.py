import pytest
from unittest.mock import patch, MagicMock
import socket
import sys
import os

# Add code to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from orchestrator.node_manager import (
    NodeManager, 
    NodeDiscoveryError, 
    create_node_manager,
    NodeState
)


class TestNodeDiscovery:
    """Tests for the initial node discovery logic."""

    def test_discover_single_online_node(self):
        """Test discovering a single reachable node."""
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_instance.connect_ex.return_value = 0  # Success
            mock_socket.return_value = mock_instance
            
            manager = create_node_manager()
            results = manager.discover_nodes(['192.168.1.10'])
            
            assert len(results) == 1
            assert results[0]['ip'] == '192.168.1.10'
            assert results[0]['status'] == 'online'
            
            mock_socket.assert_called_once()
            mock_instance.connect_ex.assert_called_once_with(('192.168.1.10', 22))

    def test_discover_offline_node(self):
        """Test discovering an unreachable node."""
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_instance.connect_ex.return_value = 1  # Failure
            mock_socket.return_value = mock_instance
            
            manager = create_node_manager()
            results = manager.discover_nodes(['192.168.1.99'])
            
            assert len(results) == 1
            assert results[0]['status'] == 'offline'

    def test_discover_mixed_nodes(self):
        """Test discovering a mix of online and offline nodes."""
        def connect_side_effect(addr):
            if addr[0] == '192.168.1.10':
                return 0  # Online
            return 1  # Offline

        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_instance.connect_ex.side_effect = connect_side_effect
            mock_socket.return_value = mock_instance
            
            manager = create_node_manager()
            results = manager.discover_nodes(['192.168.1.10', '192.168.1.99'])
            
            assert len(results) == 2
            assert results[0]['status'] == 'online'
            assert results[1]['status'] == 'offline'

    def test_discover_all_offline_raises_error(self):
        """Test that discovering all offline nodes raises NodeDiscoveryError."""
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_instance.connect_ex.return_value = 1  # All fail
            mock_socket.return_value = mock_instance
            
            manager = create_node_manager()
            
            with pytest.raises(NodeDiscoveryError) as exc_info:
                manager.discover_nodes(['192.168.1.99', '192.168.1.98'])
            
            assert "All" in str(exc_info.value)

    def test_discover_empty_list_raises_error(self):
        """Test that an empty IP list raises NodeDiscoveryError."""
        manager = create_node_manager()
        
        with pytest.raises(NodeDiscoveryError) as exc_info:
            manager.discover_nodes([])
        
        assert "empty" in str(exc_info.value).lower()

    def test_hostname_resolution(self):
        """Test that hostname resolution works or falls back to IP."""
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_instance.connect_ex.return_value = 0
            mock_socket.return_value = mock_instance
            
            with patch('socket.gethostbyaddr', return_value=('node1.local', [], [])):
                manager = create_node_manager()
                results = manager.discover_nodes(['192.168.1.10'])
                
                assert results[0]['hostname'] == 'node1.local'

    def test_hostname_resolution_fallback(self):
        """Test fallback to IP if DNS fails."""
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_instance.connect_ex.return_value = 0
            mock_socket.return_value = mock_instance
            
            with patch('socket.gethostbyaddr', side_effect=socket.herror("No address associated with hostname")):
                manager = create_node_manager()
                results = manager.discover_nodes(['192.168.1.10'])
                
                # Should fall back to the IP itself
                assert results[0]['hostname'] == '192.168.1.10'


class TestNodeStateManagement:
    """Tests for node state registration and updates."""

    def test_register_node(self):
        """Test registering a new node."""
        manager = create_node_manager()
        node = manager.register_node('192.168.1.10', 'node1', 'online')
        
        assert node.ip == '192.168.1.10'
        assert node.status == 'online'
        assert manager.get_node('192.168.1.10') is node

    def test_update_node_status(self):
        """Test updating a node's status."""
        manager = create_node_manager()
        manager.register_node('192.168.1.10', 'node1', 'online')
        
        manager.update_node_status('192.168.1.10', 'unresponsive')
        
        node = manager.get_node('192.168.1.10')
        assert node.status == 'unresponsive'
        assert node.last_heartbeat is not None

    def test_update_unknown_node(self):
        """Test updating an unknown node logs a warning (handled gracefully)."""
        manager = create_node_manager()
        # Should not raise, just log warning
        manager.update_node_status('192.168.1.99', 'online')
        
        assert manager.get_node('192.168.1.99') is None

    def test_ping_node_online(self):
        """Test pinging an online node."""
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_instance.connect_ex.return_value = 0
            mock_socket.return_value = mock_instance
            
            manager = create_node_manager()
            assert manager.ping_node('192.168.1.10') is True

    def test_ping_node_offline(self):
        """Test pinging an offline node."""
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_instance.connect_ex.return_value = 1
            mock_socket.return_value = mock_instance
            
            manager = create_node_manager()
            assert manager.ping_node('192.168.1.99') is False
