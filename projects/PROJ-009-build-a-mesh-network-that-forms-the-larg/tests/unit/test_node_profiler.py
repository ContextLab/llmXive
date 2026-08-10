import pytest
import paramiko
from unittest.mock import MagicMock, patch
from orchestrator.node_profiler import NodeProfiler, CPUProfile, CPUFrequencyError, ProfilerError


class TestNodeProfiler:
    @pytest.fixture
    def mock_ssh_client(self):
        client = MagicMock(spec=paramiko.SSHClient)
        return client

    def test_profile_linux_success(self, mock_ssh_client):
        """Test successful Linux CPU profiling."""
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_stdout.read.return_value = b"CPU MHz:                2400.000\n"
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0

        mock_channel = MagicMock()
        mock_channel.recv_exit_status.return_value = 0

        mock_ssh_client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

        profiler = NodeProfiler(mock_ssh_client, "node-1")
        profile = profiler.profile_linux()

        assert profile.node_id == "node-1"
        assert profile.cpu_speed_mhz == 2400.0
        assert "lscpu" in profile.command_used
        assert profile.raw_output == "CPU MHz:                2400.000\n"

    def test_profile_linux_parse_error(self, mock_ssh_client):
        """Test failure when lscpu output is malformed."""
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_stdout.read.return_value = b"Some random output\n"
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0

        mock_ssh_client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

        profiler = NodeProfiler(mock_ssh_client, "node-1")

        with pytest.raises(CPUFrequencyError, match="Could not parse CPU MHz"):
            profiler.profile_linux()

    def test_profile_macos_success(self, mock_ssh_client):
        """Test successful macOS CPU profiling."""
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        # sysctl returns Hz, e.g., 2400000000 Hz = 2400 MHz
        mock_stdout.read.return_value = b"2400000000\n"
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0

        mock_ssh_client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

        profiler = NodeProfiler(mock_ssh_client, "node-1")
        profile = profiler.profile_macos()

        assert profile.node_id == "node-1"
        assert profile.cpu_speed_mhz == 2400.0
        assert "sysctl" in profile.command_used

    def test_profile_macos_parse_error(self, mock_ssh_client):
        """Test failure when sysctl output is malformed."""
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_stdout.read.return_value = b"not a number\n"
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0

        mock_ssh_client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

        profiler = NodeProfiler(mock_ssh_client, "node-1")

        with pytest.raises(CPUFrequencyError, match="Could not parse CPU frequency"):
            profiler.profile_macos()

    def test_detect_and_profile_linux_fallback(self, mock_ssh_client):
        """Test fallback to macOS when Linux fails."""
        # Setup Linux failure
        mock_stdout_linux = MagicMock()
        mock_stdout_linux.read.return_value = b"Invalid output\n"
        mock_stdout_linux.channel.recv_exit_status.return_value = 0
        
        # Setup macOS success
        mock_stdout_macos = MagicMock()
        mock_stdout_macos.read.return_value = b"2400000000\n"
        mock_stdout_macos.channel.recv_exit_status.return_value = 0

        def exec_command_side_effect(cmd):
            if "lscpu" in cmd:
                return (MagicMock(), mock_stdout_linux, MagicMock())
            elif "sysctl" in cmd:
                return (MagicMock(), mock_stdout_macos, MagicMock())
            return (MagicMock(), MagicMock(), MagicMock())

        mock_ssh_client.exec_command.side_effect = exec_command_side_effect

        profiler = NodeProfiler(mock_ssh_client, "node-1")
        profile = profiler.detect_and_profile()

        assert profile.cpu_speed_mhz == 2400.0
        assert "sysctl" in profile.command_used

    def test_detect_and_profile_all_fail(self, mock_ssh_client):
        """Test failure when both Linux and macOS profiling fail."""
        mock_stdout_linux = MagicMock()
        mock_stdout_linux.read.return_value = b"Invalid\n"
        mock_stdout_linux.channel.recv_exit_status.return_value = 0

        mock_stdout_macos = MagicMock()
        mock_stdout_macos.read.return_value = b"Invalid\n"
        mock_stdout_macos.channel.recv_exit_status.return_value = 0

        def exec_command_side_effect(cmd):
            if "lscpu" in cmd:
                return (MagicMock(), mock_stdout_linux, MagicMock())
            elif "sysctl" in cmd:
                return (MagicMock(), mock_stdout_macos, MagicMock())
            return (MagicMock(), MagicMock(), MagicMock())

        mock_ssh_client.exec_command.side_effect = exec_command_side_effect

        profiler = NodeProfiler(mock_ssh_client, "node-1")

        with pytest.raises(CPUFrequencyError, match="Could not profile CPU"):
            profiler.detect_and_profile()

    def test_execution_error(self, mock_ssh_client):
        """Test handling of SSH execution exceptions."""
        mock_ssh_client.exec_command.side_effect = Exception("SSH Connection Lost")

        profiler = NodeProfiler(mock_ssh_client, "node-1")

        with pytest.raises(ProfilerError, match="Failed to execute command"):
            profiler.profile_linux()