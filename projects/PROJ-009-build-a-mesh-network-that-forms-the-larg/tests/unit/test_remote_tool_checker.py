"""
Unit tests for RemoteToolChecker.
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
from dataclasses import dataclass

import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from orchestrator.remote_tool_checker import (
    RemoteToolChecker,
    ToolMissingError,
    ToolCheckResult,
    NodeToolCheckResult,
    create_tool_checker
)
from orchestrator.node_manager import NodeDiscoveryError


class TestRemoteToolCheckerInit:
    def test_default_timeout(self):
        checker = RemoteToolChecker()
        assert checker.timeout == 2.0

    def test_custom_timeout(self):
        checker = RemoteToolChecker(timeout=5.0)
        assert checker.timeout == 5.0


class TestRemoteToolCheckerMockSSH:
    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        # Mock the exec_command context
        mock_stdout = MagicMock()
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stdout.read.return_value = b"/usr/bin/tcpdump"
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""
        client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)
        return client

    @patch('orchestrator.remote_tool_checker.paramiko.SSHClient')
    def test_tool_present(self, mock_ssh_class, mock_client):
        mock_ssh_instance = mock_ssh_class.return_value
        mock_ssh_instance.connect.return_value = None
        mock_ssh_instance.exec_command.return_value = (
            MagicMock(),
            MagicMock(read=lambda: b"/usr/bin/tcpdump", channel=MagicMock(recv_exit_status=lambda: 0)),
            MagicMock(read=lambda: b"")
        )

        checker = RemoteToolChecker()
        result = checker.check_tool(mock_ssh_instance, "tcpdump")

        assert result.is_present is True
        assert result.path == "/usr/bin/tcpdump"

    @patch('orchestrator.remote_tool_checker.paramiko.SSHClient')
    def test_tool_missing(self, mock_ssh_class, mock_client):
        # Mock exit status 1 (not found)
        mock_stdout = MagicMock()
        mock_stdout.channel.recv_exit_status.return_value = 1
        mock_stdout.read.return_value = b""
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b"which: no tcpdump in (/usr/bin)"

        mock_ssh_instance = mock_ssh_class.return_value
        mock_ssh_instance.connect.return_value = None
        mock_ssh_instance.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

        checker = RemoteToolChecker()
        result = checker.check_tool(mock_ssh_instance, "tcpdump")

        assert result.is_present is False
        assert result.path is None
        assert "which: no tcpdump" in result.error

    @patch('orchestrator.remote_tool_checker.paramiko.SSHClient')
    def test_check_node_all_present(self, mock_ssh_class):
        mock_ssh_instance = mock_ssh_class.return_value
        mock_ssh_instance.connect.return_value = None
        
        # Mock tcpdump found
        mock_stdout1 = MagicMock()
        mock_stdout1.channel.recv_exit_status.return_value = 0
        mock_stdout1.read.return_value = b"/usr/bin/tcpdump"
        mock_stderr1 = MagicMock()
        mock_stderr1.read.return_value = b""
        
        # Mock mpstat found
        mock_stdout2 = MagicMock()
        mock_stdout2.channel.recv_exit_status.return_value = 0
        mock_stdout2.read.return_value = b"/usr/bin/mpstat"
        mock_stderr2 = MagicMock()
        mock_stderr2.read.return_value = b""

        # Sequence of calls
        mock_ssh_instance.exec_command.side_effect = [
            (MagicMock(), mock_stdout1, mock_stderr1),
            (MagicMock(), mock_stdout2, mock_stderr2)
        ]

        checker = RemoteToolChecker()
        result = checker.check_node("node-1", "192.168.1.1")

        assert result.node_id == "node-1"
        assert result.all_tools_present is True
        assert len(result.tool_results) == 2

    @patch('orchestrator.remote_tool_checker.paramiko.SSHClient')
    def test_check_node_one_missing(self, mock_ssh_class):
        mock_ssh_instance = mock_ssh_class.return_value
        mock_ssh_instance.connect.return_value = None

        # tcpdump found
        mock_stdout1 = MagicMock()
        mock_stdout1.channel.recv_exit_status.return_value = 0
        mock_stdout1.read.return_value = b"/usr/bin/tcpdump"
        mock_stderr1 = MagicMock()
        mock_stderr1.read.return_value = b""

        # mpstat missing
        mock_stdout2 = MagicMock()
        mock_stdout2.channel.recv_exit_status.return_value = 1
        mock_stdout2.read.return_value = b""
        mock_stderr2 = MagicMock()
        mock_stderr2.read.return_value = b"not found"

        mock_ssh_instance.exec_command.side_effect = [
            (MagicMock(), mock_stdout1, mock_stderr1),
            (MagicMock(), mock_stdout2, mock_stderr2)
        ]

        checker = RemoteToolChecker()
        result = checker.check_node("node-2", "192.168.1.2")

        assert result.all_tools_present is False
        assert any(not t.is_present for t in result.tool_results)

    @patch('orchestrator.remote_tool_checker.paramiko.SSHClient')
    def test_check_all_nodes_success(self, mock_ssh_class):
        mock_ssh_instance = mock_ssh_class.return_value
        mock_ssh_instance.connect.return_value = None
        mock_ssh_instance.close.return_value = None

        # Mock successful execution for all calls
        def mock_exec(cmd, *args, **kwargs):
            stdout = MagicMock()
            stdout.channel.recv_exit_status.return_value = 0
            if "tcpdump" in cmd:
                stdout.read.return_value = b"/usr/bin/tcpdump"
            else:
                stdout.read.return_value = b"/usr/bin/mpstat"
            return (MagicMock(), stdout, MagicMock(read=lambda: b""))

        mock_ssh_instance.exec_command.side_effect = mock_exec

        checker = RemoteToolChecker()
        nodes = [
            {"id": "n1", "ip": "10.0.0.1"},
            {"id": "n2", "ip": "10.0.0.2"}
        ]

        results = checker.check_all_nodes(nodes)

        assert len(results) == 2
        assert all(r.all_tools_present for r in results)

    @patch('orchestrator.remote_tool_checker.paramiko.SSHClient')
    def test_check_all_nodes_raises_tool_missing(self, mock_ssh_class):
        mock_ssh_instance = mock_ssh_class.return_value
        mock_ssh_instance.connect.return_value = None
        mock_ssh_instance.close.return_value = None

        # Mock tcpdump found, mpstat missing
        def mock_exec(cmd, *args, **kwargs):
            stdout = MagicMock()
            if "tcpdump" in cmd:
                stdout.channel.recv_exit_status.return_value = 0
                stdout.read.return_value = b"/usr/bin/tcpdump"
            else:
                stdout.channel.recv_exit_status.return_value = 1
                stdout.read.return_value = b""
            return (MagicMock(), stdout, MagicMock(read=lambda: b"not found"))

        mock_ssh_instance.exec_command.side_effect = mock_exec

        checker = RemoteToolChecker()
        nodes = [{"id": "n1", "ip": "10.0.0.1"}]

        with pytest.raises(ToolMissingError) as exc_info:
            checker.check_all_nodes(nodes)

        assert "mpstat" in str(exc_info.value)
        assert "missing" in str(exc_info.value).lower()

    @patch('orchestrator.remote_tool_checker.paramiko.SSHClient')
    def test_check_all_nodes_raises_connection_error(self, mock_ssh_class):
        mock_ssh_instance = mock_ssh_class.return_value
        mock_ssh_instance.connect.side_effect = NodeDiscoveryError("Connection failed")

        checker = RemoteToolChecker()
        nodes = [{"id": "n1", "ip": "10.0.0.1"}]

        # Should return a result with error, not raise immediately for single node
        # unless all nodes fail. Here we test the result structure.
        result = checker.check_node("n1", "10.0.0.1")
        assert result.error is not None
        assert "Connection failed" in result.error


class TestFactoryFunction:
    def test_create_tool_checker(self):
        checker = create_tool_checker(timeout=3.0)
        assert isinstance(checker, RemoteToolChecker)
        assert checker.timeout == 3.0