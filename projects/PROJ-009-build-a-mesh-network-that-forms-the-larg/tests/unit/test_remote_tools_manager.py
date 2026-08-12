import pytest
from unittest.mock import patch, MagicMock
import paramiko

from orchestrator.remote_tools_manager import (
    RemoteToolManager,
    ToolMissingError,
    ToolInstallationError,
    create_tool_manager,
    NodeToolStatus
)


class TestRemoteToolManager:
    """Unit tests for RemoteToolManager."""

    @pytest.fixture
    def mock_ssh_client(self):
        """Mock paramiko SSHClient."""
        client = MagicMock(spec=paramiko.SSHClient)
        client.set_missing_host_key_policy = MagicMock()
        client.connect = MagicMock()
        client.exec_command = MagicMock()
        return client

    @pytest.fixture
    def manager(self):
        return RemoteToolManager(required_tools={"tcpdump", "mpstat"})

    def test_create_tool_manager(self):
        """Test factory function."""
        manager = create_tool_manager({"tcpdump"})
        assert manager.required_tools == {"tcpdump"}

    @patch('orchestrator.remote_tools_manager.paramiko.SSHClient')
    def test_check_tool_exists_found(self, mock_ssh_class, mock_ssh_client, manager):
        """Test that a present tool is detected correctly."""
        # Setup mock for exec_command
        mock_channel = MagicMock()
        mock_channel.recv_exit_status.return_value = 0
        
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"/usr/bin/tcpdump"
        mock_stdout.channel = mock_channel

        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""

        mock_ssh_client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)
        
        manager._get_ssh_client = MagicMock(return_value=mock_ssh_client)

        is_present, path = manager._check_tool_exists(mock_ssh_client, "tcpdump")
        
        assert is_present is True
        assert path == "/usr/bin/tcpdump"

    @patch('orchestrator.remote_tools_manager.paramiko.SSHClient')
    def test_check_tool_exists_not_found(self, mock_ssh_class, mock_ssh_client, manager):
        """Test that a missing tool is detected correctly."""
        mock_channel = MagicMock()
        mock_channel.recv_exit_status.return_value = 1 # Not found

        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b""
        mock_stdout.channel = mock_channel

        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b"/usr/bin/which: no tcpdump in ..."

        mock_ssh_client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

        is_present, error = manager._check_tool_exists(mock_ssh_client, "tcpdump")

        assert is_present is False
        assert "no tcpdump" in error

    @patch('orchestrator.remote_tools_manager.paramiko.SSHClient')
    def test_install_tool_success_apt(self, mock_ssh_class, mock_ssh_client, manager):
        """Test successful installation via apt-get."""
        # Mock for apt-get success
        mock_channel = MagicMock()
        mock_channel.recv_exit_status.return_value = 0

        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"Reading package lists... Done\nInstalling tcpdump..."
        mock_stdout.channel = mock_channel

        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""

        mock_ssh_client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

        success, msg = manager._install_tool(mock_ssh_client, "tcpdump")

        assert success is True
        # Verify apt command was called
        mock_ssh_client.exec_command.assert_called()
        call_args = mock_ssh_client.exec_command.call_args[0][0]
        assert "apt-get" in call_args

    @patch('orchestrator.remote_tools_manager.paramiko.SSHClient')
    def test_install_tool_fallback_to_yum(self, mock_ssh_class, mock_ssh_client, manager):
        """Test fallback to yum if apt fails."""
        # Mock apt failure
        mock_channel_fail = MagicMock()
        mock_channel_fail.recv_exit_status.return_value = 100
        mock_stdout_fail = MagicMock()
        mock_stdout_fail.read.return_value = b"apt error"
        mock_stdout_fail.channel = mock_channel_fail
        mock_stderr_fail = MagicMock()
        mock_stderr_fail.read.return_value = b"apt error"
        
        # Mock yum success
        mock_channel_success = MagicMock()
        mock_channel_success.recv_exit_status.return_value = 0
        mock_stdout_success = MagicMock()
        mock_stdout_success.read.return_value = b"yum success"
        mock_stdout_success.channel = mock_channel_success
        mock_stderr_success = MagicMock()
        mock_stderr_success.read.return_value = b""

        # First call fails (apt), second call succeeds (yum)
        mock_ssh_client.exec_command.side_effect = [
            (MagicMock(), mock_stdout_fail, mock_stderr_fail),
            (MagicMock(), mock_stdout_success, mock_stderr_success)
        ]

        success, msg = manager._install_tool(mock_ssh_client, "tcpdump")

        assert success is True
        assert mock_ssh_client.exec_command.call_count == 2

    @patch('orchestrator.remote_tools_manager.paramiko.SSHClient')
    def test_verify_and_install_tools_missing_and_installed(self, mock_ssh_class, mock_ssh_client, manager):
        """Test full flow: tool missing, then installed."""
        # 1. Check tcpdump -> Not found
        mock_channel_1 = MagicMock()
        mock_channel_1.recv_exit_status.return_value = 1
        mock_ssh_client.exec_command.return_value = (MagicMock(), MagicMock(read=lambda: b""), MagicMock(read=lambda: b"not found"))

        manager._get_ssh_client = MagicMock(return_value=mock_ssh_client)

        # We need to mock the flow inside verify_and_install_tools
        # It calls _check_tool_exists, then _install_tool, then _check_tool_exists again.
        
        # Side effects for the sequence:
        # 1. Check (fail)
        # 2. Install (success)
        # 3. Check (success)
        
        # Setup for Check 1 (fail)
        def exec_command_side_effect(cmd, timeout=None):
            if "which tcpdump" in cmd:
                # First check: not found
                mock_channel = MagicMock()
                mock_channel.recv_exit_status.return_value = 1
                mock_stdout = MagicMock()
                mock_stdout.read.return_value = b""
                mock_stdout.channel = mock_channel
                mock_stderr = MagicMock()
                mock_stderr.read.return_value = b"not found"
                return (MagicMock(), mock_stdout, mock_stderr)
            elif "apt-get" in cmd or "yum" in cmd:
                # Install command
                mock_channel = MagicMock()
                mock_channel.recv_exit_status.return_value = 0
                mock_stdout = MagicMock()
                mock_stdout.read.return_value = b"installed"
                mock_stdout.channel = mock_channel
                mock_stderr = MagicMock()
                mock_stderr.read.return_value = b""
                return (MagicMock(), mock_stdout, mock_stderr)
            else:
                # Second check (after install)
                mock_channel = MagicMock()
                mock_channel.recv_exit_status.return_value = 0
                mock_stdout = MagicMock()
                mock_stdout.read.return_value = b"/usr/bin/tcpdump"
                mock_stdout.channel = mock_channel
                mock_stderr = MagicMock()
                mock_stderr.read.return_value = b""
                return (MagicMock(), mock_stdout, mock_stderr)

        mock_ssh_client.exec_command.side_effect = exec_command_side_effect

        statuses = manager.verify_and_install_tools("192.168.1.10")

        assert len(statuses) == 1
        status = statuses[0]
        assert status.tool_name == "tcpdump"
        assert status.is_present is True
        assert status.installation_attempted is True
        assert status.installation_success is True
        assert status.error_message is None

    @patch('orchestrator.remote_tools_manager.paramiko.SSHClient')
    def test_verify_and_install_tools_installation_fails(self, mock_ssh_class, mock_ssh_client, manager):
        """Test that ToolMissingError is raised if installation fails."""
        # Check: not found
        # Install: fail
        # (Second check not reached)

        def exec_command_side_effect(cmd, timeout=None):
            if "which tcpdump" in cmd:
                mock_channel = MagicMock()
                mock_channel.recv_exit_status.return_value = 1
                mock_stdout = MagicMock()
                mock_stdout.read.return_value = b""
                mock_stdout.channel = mock_channel
                mock_stderr = MagicMock()
                mock_stderr.read.return_value = b"not found"
                return (MagicMock(), mock_stdout, mock_stderr)
            else:
                # Install command fails
                mock_channel = MagicMock()
                mock_channel.recv_exit_status.return_value = 100
                mock_stdout = MagicMock()
                mock_stdout.read.return_value = b"fail"
                mock_stdout.channel = mock_channel
                mock_stderr = MagicMock()
                mock_stderr.read.return_value = b"installation error"
                return (MagicMock(), mock_stdout, mock_stderr)

        mock_ssh_client.exec_command.side_effect = exec_command_side_effect

        with pytest.raises(ToolMissingError) as exc_info:
            manager.verify_and_install_tools("192.168.1.10")

        assert "installation failed" in str(exc_info.value).lower()

    def test_close_connections(self, manager):
        """Test closing connections."""
        mock_client = MagicMock()
        manager._ssh_client_cache["1.2.3.4"] = mock_client

        manager.close_connections()

        mock_client.close.assert_called_once()
        assert len(manager._ssh_client_cache) == 0