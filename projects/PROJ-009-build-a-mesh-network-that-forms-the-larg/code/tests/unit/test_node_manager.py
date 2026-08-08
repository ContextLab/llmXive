"""
Unit tests for Node Manager.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import sys
import socket

from orchestrator.node_manager import (
    NodeManager,
    NodeDiscoveryError,
    NodeHeartbeatLost,
    NodeTimeoutError,
    NodeReassignError,
    create_node_manager,
    NodeDiscoveryResult
)
from orchestrator.models import PhysicalNode, NodeStatus
from paramiko import SSHException, AuthenticationException, SocketTimeout


class TestNodeManagerInit:
    def test_create_node_manager(self):
        manager = create_node_manager(ssh_timeout=5.0, heartbeat_interval=10.0)
        assert isinstance(manager, NodeManager)
        assert manager.ssh_timeout == 5.0
        assert manager.heartbeat_interval == 10.0

    def test_default_values(self):
        manager = create_node_manager()
        assert manager.ssh_timeout == 2.0
        assert manager.heartbeat_interval == 5.0


class TestNodeDiscovery:
    @patch('orchestrator.node_manager.SSHClient')
    def test_discover_single_node_success(self, mock_ssh_class):
        mock_client = MagicMock()
        mock_client.exec_command.return_value = (MagicMock(), MagicMock(), MagicMock())
        mock_client.exec_command.return_value[1].channel.recv_exit_status.return_value = 0
        mock_ssh_class.return_value = mock_client

        manager = create_node_manager()
        result = manager.discover_nodes(["192.168.1.10"])

        assert len(result.discovered_nodes) == 1
        assert result.discovered_nodes[0].ip_address == "192.168.1.10"
        assert result.success_rate == 1.0
        assert len(result.failed_nodes) == 0

    @patch('orchestrator.node_manager.SSHClient')
    def test_discover_multiple_nodes_partial_failure(self, mock_ssh_class):
        mock_client_success = MagicMock()
        mock_client_success.exec_command.return_value = (MagicMock(), MagicMock(), MagicMock())
        mock_client_success.exec_command.return_value[1].channel.recv_exit_status.return_value = 0
        
        # First call succeeds, second fails with timeout
        mock_ssh_class.side_effect = [mock_client_success, SocketTimeout("Timeout")]

        manager = create_node_manager()
        result = manager.discover_nodes(["192.168.1.10", "192.168.1.11"])

        assert len(result.discovered_nodes) == 1
        assert len(result.failed_nodes) == 1
        assert result.success_rate == 0.5

    @patch('orchestrator.node_manager.SSHClient')
    def test_discover_all_nodes_fail_raises_error(self, mock_ssh_class):
        mock_ssh_class.side_effect = [
            SocketTimeout("Timeout"),
            AuthenticationException("Auth Failed")
        ]

        manager = create_node_manager()
        
        with pytest.raises(NodeDiscoveryError) as exc_info:
            manager.discover_nodes(["192.168.1.10", "192.168.1.11"])
        
        assert "all" in str(exc_info.value).lower() or "failed" in str(exc_info.value).lower()

    @patch('orchestrator.node_manager.SSHClient')
    def test_discover_empty_list(self, mock_ssh_class):
        manager = create_node_manager()
        result = manager.discover_nodes([])
        
        assert len(result.discovered_nodes) == 0
        assert result.success_rate == 0.0


class TestHeartbeat:
    @patch('orchestrator.node_manager.SSHClient')
    def test_heartbeat_success(self, mock_ssh_class):
        mock_client = MagicMock()
        mock_client.exec_command.return_value = (MagicMock(), MagicMock(), MagicMock())
        mock_client.exec_command.return_value[1].channel.recv_exit_status.return_value = 0
        mock_ssh_class.return_value = mock_client

        manager = create_node_manager()
        # Manually add a connection to simulate discovery
        manager._active_connections["192.168.1.10"] = mock_client
        manager._node_metadata["192.168.1.10"] = {"status": NodeStatus.ACTIVE}

        success = manager.send_heartbeat("192.168.1.10")
        assert success is True

    @patch('orchestrator.node_manager.SSHClient')
    def test_heartbeat_timeout(self, mock_ssh_class):
        mock_client = MagicMock()
        mock_client.exec_command.side_effect = SocketTimeout("Timeout")
        mock_ssh_class.return_value = mock_client

        manager = create_node_manager()
        manager._active_connections["192.168.1.10"] = mock_client

        success = manager.send_heartbeat("192.168.1.10")
        assert success is False


class TestCommandExecution:
    @patch('orchestrator.node_manager.SSHClient')
    def test_ping_node_success(self, mock_ssh_class):
        mock_client = MagicMock()
        mock_client.exec_command.return_value = (MagicMock(), MagicMock(), MagicMock())
        mock_client.exec_command.return_value[1].channel.recv_exit_status.return_value = 0
        mock_ssh_class.return_value = mock_client

        manager = create_node_manager()
        manager._active_connections["192.168.1.10"] = mock_client

        assert manager.ping_node("192.168.1.10") is True

    @patch('orchestrator.node_manager.SSHClient')
    def test_ping_node_no_connection(self, mock_ssh_class):
        manager = create_node_manager()
        # No connection added
        assert manager.ping_node("192.168.1.10") is False


class TestDropoutDetection:
    @patch('orchestrator.node_manager.SSHClient')
    def test_heartbeat_loss_detection(self, mock_ssh_class):
        mock_client = MagicMock()
        mock_client.exec_command.side_effect = SocketTimeout("Timeout")
        mock_ssh_class.return_value = mock_client

        manager = create_node_manager()
        manager._active_connections["192.168.1.10"] = mock_client
        manager._node_metadata["192.168.1.10"] = {"status": NodeStatus.ACTIVE}

        callback_called = False
        def on_loss(ip):
            nonlocal callback_called
            callback_called = True
            assert ip == "192.168.1.10"

        # Simulate monitor_heartbeats for one iteration
        # We call send_heartbeat directly to test the logic
        result = manager.send_heartbeat("192.168.1.10")
        assert result is False
        assert manager._node_metadata["192.168.1.10"]["status"] == NodeStatus.DROPPED


class TestConnectionManagement:
    @patch('orchestrator.node_manager.SSHClient')
    def test_close_all_connections(self, mock_ssh_class):
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client

        manager = create_node_manager()
        manager._active_connections["192.168.1.10"] = mock_client
        manager._active_connections["192.168.1.11"] = mock_client

        manager.close_all_connections()

        assert len(manager._active_connections) == 0
        assert mock_client.close.call_count == 2

    @patch('orchestrator.node_manager.SSHClient')
    def test_reassign_task_success(self, mock_ssh_class):
        mock_client = MagicMock()
        mock_client.exec_command.return_value = (MagicMock(), MagicMock(), MagicMock())
        mock_client.exec_command.return_value[1].channel.recv_exit_status.return_value = 0
        mock_ssh_class.return_value = mock_client

        manager = create_node_manager()
        manager._active_connections["192.168.1.20"] = mock_client

        success = manager.reassign_task("task-123", "192.168.1.20")
        assert success is True

    @patch('orchestrator.node_manager.SSHClient')
    def test_reassign_task_node_unreachable(self, mock_ssh_class):
        mock_ssh_class.side_effect = SocketTimeout("Timeout")

        manager = create_node_manager()
        # No connection exists for this IP

        with pytest.raises(NodeReassignError):
            manager.reassign_task("task-123", "192.168.1.99")