"""
Unit tests for NodeManager.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestrator.node_manager import (
    NodeManager,
    NodeDiscoveryError,
    NodeHeartbeatLost,
    NodeTimeoutError,
    NodeReassignError,
    create_node_manager
)
from orchestrator.models import PhysicalNode, NodeStatus
from paramiko import AuthenticationException, SocketTimeout, SSHException

@pytest.fixture
def mock_ssh_client():
    """Mock paramiko SSHClient."""
    with patch('orchestrator.node_manager.SSHClient') as mock_client:
        instance = MagicMock()
        instance.set_missing_host_key_policy = MagicMock()
        instance.connect = MagicMock()
        instance.exec_command = MagicMock()
        # Mock stdin/stdout/stderr
        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_stdout.read.return_value = b"pong"
        instance.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        instance.close = MagicMock()
        mock_client.return_value = instance
        yield instance

class TestNodeManagerInit:
    def test_create_node_manager(self):
        manager = create_node_manager()
        assert isinstance(manager, NodeManager)
        assert manager.timeout == 2.0

    def test_create_node_manager_with_config(self):
        manager = create_node_manager({"ssh_timeout": 5.0})
        assert manager.timeout == 5.0

class TestNodeDiscovery:
    @patch('orchestrator.node_manager.SSHClient')
    def test_discover_nodes_success(self, mock_ssh_class):
        # Setup mock
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance
        mock_instance.connect.return_value = None
        mock_instance.exec_command.return_value = (MagicMock(), MagicMock(read=MagicMock(return_value=b"pong")), MagicMock())
        
        manager = create_node_manager()
        result = manager.discover_nodes(["192.168.1.10"], username="test")
        
        assert len(result.discovered_nodes) == 1
        assert result.discovered_nodes[0].ip_address == "192.168.1.10"
        assert result.failed_ips == []
        assert result.success_rate == 1.0

    @patch('orchestrator.node_manager.SSHClient')
    def test_discover_nodes_failure(self, mock_ssh_class):
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance
        # Simulate connection failure
        mock_instance.connect.side_effect = AuthenticationException("Auth failed")
        
        manager = create_node_manager()
        with pytest.raises(NodeDiscoveryError):
            manager.discover_nodes(["192.168.1.10"], username="test")

    @patch('orchestrator.node_manager.SSHClient')
    def test_discover_nodes_partial_failure(self, mock_ssh_class):
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance
        
        # First node fails, second succeeds
        call_count = 0
        def connect_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise AuthenticationException("Auth failed")
            return None

        mock_instance.connect.side_effect = connect_side_effect
        mock_instance.exec_command.return_value = (MagicMock(), MagicMock(read=MagicMock(return_value=b"pong")), MagicMock())
        
        manager = create_node_manager()
        result = manager.discover_nodes(["192.168.1.10", "192.168.1.11"], username="test")
        
        assert len(result.discovered_nodes) == 1
        assert len(result.failed_ips) == 1
        assert result.discovered_nodes[0].ip_address == "192.168.1.11"

class TestHeartbeat:
    @patch('orchestrator.node_manager.SSHClient')
    def test_heartbeat_success(self, mock_ssh_class):
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance
        mock_instance.connect.return_value = None
        mock_instance.exec_command.return_value = (MagicMock(), MagicMock(read=MagicMock(return_value=b"pong")), MagicMock())
        
        manager = create_node_manager()
        # First connect to establish state
        manager.ping_node("192.168.1.10")
        
        # Now test heartbeat
        result = manager.heartbeat("192.168.1.10")
        assert result is True

    @patch('orchestrator.node_manager.SSHClient')
    def test_heartbeat_failure(self, mock_ssh_class):
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance
        mock_instance.connect.side_effect = SocketTimeout("Timeout")
        
        manager = create_node_manager()
        with pytest.raises(NodeHeartbeatLost):
            manager.heartbeat("192.168.1.10")

class TestCommandExecution:
    @patch('orchestrator.node_manager.SSHClient')
    def test_ping_node_success(self, mock_ssh_class):
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance
        mock_instance.connect.return_value = None
        mock_instance.exec_command.return_value = (MagicMock(), MagicMock(read=MagicMock(return_value=b"pong")), MagicMock())
        
        manager = create_node_manager()
        result = manager.ping_node("192.168.1.10")
        assert result is True

    @patch('orchestrator.node_manager.SSHClient')
    def test_ping_node_timeout(self, mock_ssh_class):
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance
        mock_instance.connect.side_effect = SocketTimeout("Connection timed out")
        
        manager = create_node_manager()
        with pytest.raises(SocketTimeout):
            manager.ping_node("192.168.1.10")

class TestDropoutDetection:
    @patch('orchestrator.node_manager.SSHClient')
    def test_detect_dropout_success(self, mock_ssh_class):
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance
        mock_instance.connect.return_value = None
        mock_instance.exec_command.return_value = (MagicMock(), MagicMock(read=MagicMock(return_value=b"pong")), MagicMock())
        
        manager = create_node_manager()
        dropouts = manager.detect_dropout_events(["192.168.1.10"], consecutive_threshold=3)
        assert dropouts == []

    @patch('orchestrator.node_manager.SSHClient')
    def test_detect_dropout_failure(self, mock_ssh_class):
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance
        mock_instance.connect.side_effect = SocketTimeout("Timeout")
        
        manager = create_node_manager()
        dropouts = manager.detect_dropout_events(["192.168.1.10"], consecutive_threshold=1)
        assert "192.168.1.10" in dropouts

class TestConnectionManagement:
    @patch('orchestrator.node_manager.SSHClient')
    def test_reassign_task_success(self, mock_ssh_class):
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance
        mock_instance.connect.return_value = None
        mock_instance.exec_command.return_value = (MagicMock(), MagicMock(read=MagicMock(return_value=b"pong")), MagicMock())
        
        manager = create_node_manager()
        # Setup state
        manager.node_status["192.168.1.10"] = NodeStatus.BUSY
        
        result = manager.reassign_task("task-1", "192.168.1.10", "192.168.1.11")
        
        assert result is True
        assert manager.node_status["192.168.1.10"] == NodeStatus.IDLE
        assert manager.node_status["192.168.1.11"] == NodeStatus.BUSY

    @patch('orchestrator.node_manager.SSHClient')
    def test_reassign_task_failure_new_node_unreachable(self, mock_ssh_class):
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance
        # First call (ping new node) fails
        mock_instance.connect.side_effect = AuthenticationException("Auth failed")
        
        manager = create_node_manager()
        with pytest.raises(NodeReassignError):
            manager.reassign_task("task-1", "192.168.1.10", "192.168.1.11")