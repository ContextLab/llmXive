"""
Unit tests for NodeManager module.

These tests verify SSH connection handling, heartbeat logic, and device discovery.
They use the MockNodeManager from tests.unit.mock_nodes to avoid requiring
real SSH connections during unit testing.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestrator.models import PhysicalNode, NodeStatus
from orchestrator.node_manager import NodeManager, NodeDiscoveryResult
from orchestrator.config import Config


class TestNodeManagerInit:
    """Tests for NodeManager initialization."""

    def test_init_with_config(self):
        """Test initialization with explicit config."""
        config = {
            "nodes": [
                {"id": "node1", "host": "192.168.1.1", "port": 22, "user": "root", "key_path": "/keys/node1"}
            ],
            "heartbeat_interval_seconds": 10
        }
        manager = NodeManager(config=config)
        assert len(manager._node_defs) == 1
        assert manager._heartbeat_interval == 10

    def test_init_without_nodes_raises(self):
        """Test that initialization without nodes raises ValueError."""
        config = {"nodes": []}
        with pytest.raises(ValueError, match="No nodes defined"):
            NodeManager(config=config)

    def test_init_loads_from_global_config(self):
        """Test that initialization loads nodes from global config if not provided."""
        # This would normally test get_config(), but we mock it to avoid side effects
        with patch("orchestrator.node_manager.get_config") as mock_get_config:
            mock_get_config.return_value = {
                "nodes": [
                    {"id": "test_node", "host": "10.0.0.1", "port": 22, "user": "admin", "key_path": "/keys/test"}
                ]
            }
            manager = NodeManager()
            assert len(manager._node_defs) == 1


class TestNodeDiscovery:
    """Tests for node discovery functionality."""

    def test_discover_nodes_success(self):
        """Test successful discovery of nodes."""
        config = {
            "nodes": [
                {"id": "node1", "host": "192.168.1.1", "port": 22, "user": "root", "key_path": "/keys/node1"}
            ]
        }
        manager = NodeManager(config=config)

        # Mock the connection creation to simulate success
        with patch.object(manager, '_create_connection') as mock_conn:
            mock_conn.return_value = MagicMock()
            result = manager.discover_nodes()

            assert len(result.discovered_nodes) == 1
            assert len(result.failed_hosts) == 0
            assert result.discovered_nodes[0].id == "node1"
            assert result.discovered_nodes[0].status == NodeStatus.ONLINE

    def test_discover_nodes_partial_failure(self):
        """Test discovery when some nodes fail."""
        config = {
            "nodes": [
                {"id": "node1", "host": "192.168.1.1", "port": 22, "user": "root", "key_path": "/keys/node1"},
                {"id": "node2", "host": "192.168.1.2", "port": 22, "user": "root", "key_path": "/keys/node2"}
            ]
        }
        manager = NodeManager(config=config)

        # Mock first success, second failure
        call_count = [0]
        def mock_connect_side_effect(node):
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock()
            raise ConnectionError("Connection refused")

        with patch.object(manager, '_create_connection', side_effect=mock_connect_side_effect):
            result = manager.discover_nodes()

            assert len(result.discovered_nodes) == 1
            assert len(result.failed_hosts) == 1
            assert result.failed_hosts[0] == "192.168.1.2"

    def test_discover_nodes_all_fail(self):
        """Test discovery when all nodes fail."""
        config = {
            "nodes": [
                {"id": "node1", "host": "192.168.1.1", "port": 22, "user": "root", "key_path": "/keys/node1"}
            ]
        }
        manager = NodeManager(config=config)

        with patch.object(manager, '_create_connection') as mock_conn:
            mock_conn.side_effect = ConnectionError("All hosts unreachable")
            result = manager.discover_nodes()

            assert len(result.discovered_nodes) == 0
            assert len(result.failed_hosts) == 1


class TestHeartbeat:
    """Tests for heartbeat functionality."""

    def test_ping_node_success(self):
        """Test successful ping to a node."""
        config = {
            "nodes": [
                {"id": "node1", "host": "192.168.1.1", "port": 22, "user": "root", "key_path": "/keys/node1"}
            ]
        }
        manager = NodeManager(config=config)

        with patch.object(manager, 'get_connection') as mock_get_conn:
            mock_client = MagicMock()
            mock_get_conn.return_value = mock_client
            mock_client.exec_command.return_value = (MagicMock(), MagicMock(), MagicMock())
            mock_client.exec_command.return_value[0].channel.recv_exit_status.return_value = 0

            result = manager.ping_node("node1")
            assert result is True

    def test_ping_node_failure(self):
        """Test ping failure when node is unreachable."""
        config = {
            "nodes": [
                {"id": "node1", "host": "192.168.1.1", "port": 22, "user": "root", "key_path": "/keys/node1"}
            ]
        }
        manager = NodeManager(config=config)

        with patch.object(manager, 'get_connection') as mock_get_conn:
            mock_get_conn.side_effect = ConnectionError("Connection failed")

            result = manager.ping_node("node1")
            assert result is False

    def test_start_heartbeat_monitor(self):
        """Test starting the heartbeat monitor thread."""
        config = {
            "nodes": [
                {"id": "node1", "host": "192.168.1.1", "port": 22, "user": "root", "key_path": "/keys/node1"}
            ],
            "heartbeat_interval_seconds": 1
        }
        manager = NodeManager(config=config)

        callback_mock = Mock()
        manager.start_heartbeat_monitor(callback=callback_mock)

        # Give thread time to start
        import time
        time.sleep(0.5)

        assert manager._heartbeat_thread is not None
        assert manager._heartbeat_thread.is_alive()

        manager.stop_heartbeat_monitor()
        assert not manager._heartbeat_thread.is_alive()


class TestCommandExecution:
    """Tests for remote command execution."""

    def test_execute_command_success(self):
        """Test successful command execution."""
        config = {
            "nodes": [
                {"id": "node1", "host": "192.168.1.1", "port": 22, "user": "root", "key_path": "/keys/node1"}
            ]
        }
        manager = NodeManager(config=config)

        with patch.object(manager, 'get_connection') as mock_get_conn:
            mock_client = MagicMock()
            mock_get_conn.return_value = mock_client

            mock_stdout = MagicMock()
            mock_stderr = MagicMock()
            mock_stdout.read.return_value = b"output"
            mock_stderr.read.return_value = b""
            mock_client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)
            mock_stdout.channel.recv_exit_status.return_value = 0

            result = manager.execute_command("node1", "echo hello")

            assert result["stdout"] == "output"
            assert result["stderr"] == ""
            assert result["exit_code"] == 0

    def test_execute_command_timeout(self):
        """Test command execution timeout."""
        config = {
            "nodes": [
                {"id": "node1", "host": "192.168.1.1", "port": 22, "user": "root", "key_path": "/keys/node1"}
            ]
        }
        manager = NodeManager(config=config)

        with patch.object(manager, 'get_connection') as mock_get_conn:
            mock_get_conn.side_effect = TimeoutError("Command timed out")

            with pytest.raises(TimeoutError, match="timed out"):
                manager.execute_command("node1", "sleep 10", timeout=1)


class TestDropoutDetection:
    """Tests for dropout event detection."""

    def test_detect_dropout_events(self):
        """Test detection of dropout events."""
        config = {
            "nodes": [
                {"id": "node1", "host": "192.168.1.1", "port": 22, "user": "root", "key_path": "/keys/node1"},
                {"id": "node2", "host": "192.168.1.2", "port": 22, "user": "root", "key_path": "/keys/node2"}
            ]
        }
        manager = NodeManager(config=config)

        # Mock ping to fail for node2 only
        call_count = [0]
        def mock_ping(node_id):
            call_count[0] += 1
            return node_id == "node1"  # node1 OK, node2 fails

        with patch.object(manager, 'ping_node', side_effect=mock_ping):
            events = manager.detect_dropout_events()

            assert len(events) == 1
            assert events[0]["node_id"] == "node2"
            assert events[0]["event_type"] == "dropout"


class TestConnectionManagement:
    """Tests for connection lifecycle management."""

    def test_close_all_connections(self):
        """Test closing all connections."""
        config = {
            "nodes": [
                {"id": "node1", "host": "192.168.1.1", "port": 22, "user": "root", "key_path": "/keys/node1"}
            ]
        }
        manager = NodeManager(config=config)

        # Create a mock connection
        mock_client = MagicMock()
        manager._connections["node1"] = mock_client

        manager.close_all()

        mock_client.close.assert_called_once()
        assert len(manager._connections) == 0

    def test_context_manager(self):
        """Test using NodeManager as context manager."""
        config = {
            "nodes": [
                {"id": "node1", "host": "192.168.1.1", "port": 22, "user": "root", "key_path": "/keys/node1"}
            ]
        }

        with patch("orchestrator.node_manager.NodeManager.close_all") as mock_close:
            with NodeManager(config=config) as manager:
                assert manager is not None

            mock_close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])