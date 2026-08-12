"""
Unit tests for RemoteToolManager.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from paramiko import SSHClient, Transport

from orchestrator.remote_tools_manager import (
    RemoteToolManager,
    ToolMissingError,
    ToolInstallationError,
    ToolCheckResult,
    NodeToolStatus,
    create_tool_manager
)


@pytest.fixture
def mock_ssh_client():
    """Create a mock SSH client."""
    client = MagicMock(spec=SSHClient)
    transport = MagicMock(spec=Transport)
    transport.getpeername.return_value = ("192.168.1.10", 22)
    client.get_transport.return_value = transport
    return client

    def test_create_tool_manager(self):
        """Test factory function."""
        manager = create_tool_manager({"tcpdump"})
        assert manager.required_tools == {"tcpdump"}

@pytest.fixture
def tool_manager():
    """Create a RemoteToolManager instance."""
    return create_tool_manager()


def test_tool_check_result_creation():
    """Test ToolCheckResult dataclass initialization."""
    result = ToolCheckResult(
        tool_name="tcpdump",
        node_ip="192.168.1.10",
        is_present=True,
        version_output="tcpdump 4.9.3"
    )
    assert result.tool_name == "tcpdump"
    assert result.is_present is True
    assert result.version_output == "tcpdump 4.9.3"

        mock_ssh_client.exec_command.side_effect = exec_command_side_effect

def test_node_tool_status_creation():
    """Test NodeToolStatus dataclass initialization."""
    status = NodeToolStatus(node_ip="192.168.1.10")
    assert status.node_ip == "192.168.1.10"
    assert status.tcpdump_present is False
    assert status.mpstat_present is False
    assert len(status.errors) == 0


@patch('paramiko.SSHClient')
def test_check_tool_present(mock_ssh_class, tool_manager, mock_ssh_client):
    """Test checking for a tool that is present."""
    mock_ssh_class.return_value = mock_ssh_client
    
    # Mock exec_command for 'which'
    mock_which_stdout = MagicMock()
    mock_which_stdout.channel.recv_exit_status.return_value = 0
    mock_which_stdout.read.return_value = b"/usr/bin/tcpdump"
    
    # Mock exec_command for version
    mock_version_stdout = MagicMock()
    mock_version_stdout.read.return_value = b"tcpdump 4.9.3"
    
    mock_ssh_client.exec_command.side_effect = [
        (None, mock_which_stdout, None), # which tcpdump
        (None, mock_version_stdout, None) # version
    ]

    result = tool_manager.check_tool(mock_ssh_client, "tcpdump")

    assert result.is_present is True
    assert result.tool_name == "tcpdump"
    assert "tcpdump 4.9.3" in result.version_output


@patch('paramiko.SSHClient')
def test_check_tool_missing(mock_ssh_class, tool_manager, mock_ssh_client):
    """Test checking for a tool that is missing."""
    mock_ssh_class.return_value = mock_ssh_client
    
    # Mock exec_command for 'which' returning failure
    mock_which_stdout = MagicMock()
    mock_which_stdout.channel.recv_exit_status.return_value = 1
    mock_which_stderr = MagicMock()
    mock_which_stderr.read.return_value = b"which: no tcpdump in (/usr/bin)"
    
    mock_ssh_client.exec_command.return_value = (None, mock_which_stdout, mock_which_stderr)

    result = tool_manager.check_tool(mock_ssh_client, "tcpdump")

    assert result.is_present is False
    assert "not found" in result.error_message


@patch('paramiko.SSHClient')
def test_install_tool_success(mock_ssh_class, tool_manager, mock_ssh_client):
    """Test successful tool installation."""
    mock_ssh_class.return_value = mock_ssh_client
    
    # Mock apt-get check
    mock_apt_stdout = MagicMock()
    mock_apt_stdout.channel.recv_exit_status.return_value = 0
    
    # Mock install command
    mock_install_stdout = MagicMock()
    mock_install_stdout.channel.recv_exit_status.return_value = 0
    mock_install_stdout.read.return_value = b"Setting up tcpdump..."
    
    mock_ssh_client.exec_command.side_effect = [
        (None, mock_apt_stdout, None), # which apt-get
        (None, mock_install_stdout, None) # install
    ]

    success, msg = tool_manager.install_tool(mock_ssh_client, "tcpdump")

    assert success is True
    assert "apt" in msg


@patch('paramiko.SSHClient')
def test_install_tool_failure(mock_ssh_class, tool_manager, mock_ssh_client):
    """Test failed tool installation."""
    mock_ssh_class.return_value = mock_ssh_client
    
    # Mock apt-get check
    mock_apt_stdout = MagicMock()
    mock_apt_stdout.channel.recv_exit_status.return_value = 0
    
    # Mock install command failure
    mock_install_stderr = MagicMock()
    mock_install_stderr.read.return_value = b"E: Unable to locate package"
    mock_install_stdout = MagicMock()
    mock_install_stdout.channel.recv_exit_status.return_value = 1
    
    mock_ssh_client.exec_command.side_effect = [
        (None, mock_apt_stdout, None), # which apt-get
        (None, mock_install_stdout, mock_install_stderr) # install
    ]

    success, msg = tool_manager.install_tool(mock_ssh_client, "tcpdump")

    assert success is False
    assert "failed" in msg.lower()


@patch('paramiko.SSHClient')
def test_check_and_install_tools_all_present(mock_ssh_class, tool_manager, mock_ssh_client):
    """Test checking and installing when all tools are already present."""
    mock_ssh_class.return_value = mock_ssh_client
    
    # Mock 'which' for tcpdump (success)
    mock_tcpdump_which = MagicMock()
    mock_tcpdump_which.channel.recv_exit_status.return_value = 0
    mock_tcpdump_which.read.return_value = b"/usr/bin/tcpdump"
    
    mock_tcpdump_version = MagicMock()
    mock_tcpdump_version.read.return_value = b"tcpdump 4.9.3"
    
    # Mock 'which' for mpstat (success)
    mock_mpstat_which = MagicMock()
    mock_mpstat_which.channel.recv_exit_status.return_value = 0
    mock_mpstat_which.read.return_value = b"/usr/bin/mpstat"
    
    mock_mpstat_version = MagicMock()
    mock_mpstat_version.read.return_value = b"sysstat 12.0.3"
    
    # Mock apt-get check
    mock_apt_stdout = MagicMock()
    mock_apt_stdout.channel.recv_exit_status.return_value = 0

    call_sequence = [
        (None, mock_tcpdump_which, None), # which tcpdump
        (None, mock_tcpdump_version, None), # tcpdump version
        (None, mock_mpstat_which, None), # which mpstat
        (None, mock_mpstat_version, None), # mpstat version
        (None, mock_apt_stdout, None), # which apt-get (for mpstat check path, though not used)
    ]
    
    mock_ssh_client.exec_command.side_effect = call_sequence

    status = tool_manager.check_and_install_tools("192.168.1.10")

    assert status.tcpdump_present is True
    assert status.mpstat_present is True
    assert len(status.errors) == 0


@patch('paramiko.SSHClient')
def test_check_and_install_tools_install_missing(mock_ssh_class, tool_manager, mock_ssh_client):
    """Test checking and installing when one tool is missing."""
    mock_ssh_class.return_value = mock_ssh_client
    
    # Mock 'which' for tcpdump (success)
    mock_tcpdump_which = MagicMock()
    mock_tcpdump_which.channel.recv_exit_status.return_value = 0
    mock_tcpdump_which.read.return_value = b"/usr/bin/tcpdump"
    
    mock_tcpdump_version = MagicMock()
    mock_tcpdump_version.read.return_value = b"tcpdump 4.9.3"
    
    # Mock 'which' for mpstat (failure)
    mock_mpstat_which = MagicMock()
    mock_mpstat_which.channel.recv_exit_status.return_value = 1
    mock_mpstat_which_stderr = MagicMock()
    mock_mpstat_which_stderr.read.return_value = b"not found"
    
    # Mock apt-get check
    mock_apt_stdout = MagicMock()
    mock_apt_stdout.channel.recv_exit_status.return_value = 0
    
    # Mock install success
    mock_install_stdout = MagicMock()
    mock_install_stdout.channel.recv_exit_status.return_value = 0
    mock_install_stdout.read.return_value = b"Installed"
    
    # Mock re-check mpstat
    mock_mpstat_recheck = MagicMock()
    mock_mpstat_recheck.channel.recv_exit_status.return_value = 0
    mock_mpstat_recheck.read.return_value = b"/usr/bin/mpstat"
    
    mock_mpstat_recheck_version = MagicMock()
    mock_mpstat_recheck_version.read.return_value = b"sysstat 12.0.3"

    call_sequence = [
        (None, mock_tcpdump_which, None), # which tcpdump
        (None, mock_tcpdump_version, None), # tcpdump version
        (None, mock_mpstat_which, mock_mpstat_which_stderr), # which mpstat
        (None, mock_apt_stdout, None), # which apt-get
        (None, mock_install_stdout, None), # install mpstat
        (None, mock_mpstat_recheck, None), # re-check mpstat
        (None, mock_mpstat_recheck_version, None), # mpstat version
    ]
    
    mock_ssh_client.exec_command.side_effect = call_sequence

    status = tool_manager.check_and_install_tools("192.168.1.10")

    assert status.tcpdump_present is True
    assert status.mpstat_present is True
    assert len(status.errors) == 0


@patch('paramiko.SSHClient')
def test_check_and_install_tools_install_fails(mock_ssh_class, tool_manager, mock_ssh_client):
    """Test checking and installing when installation fails."""
    mock_ssh_class.return_value = mock_ssh_client
    
    # Mock 'which' for tcpdump (success)
    mock_tcpdump_which = MagicMock()
    mock_tcpdump_which.channel.recv_exit_status.return_value = 0
    mock_tcpdump_which.read.return_value = b"/usr/bin/tcpdump"
    
    mock_tcpdump_version = MagicMock()
    mock_tcpdump_version.read.return_value = b"tcpdump 4.9.3"
    
    # Mock 'which' for mpstat (failure)
    mock_mpstat_which = MagicMock()
    mock_mpstat_which.channel.recv_exit_status.return_value = 1
    mock_mpstat_which_stderr = MagicMock()
    mock_mpstat_which_stderr.read.return_value = b"not found"
    
    # Mock apt-get check
    mock_apt_stdout = MagicMock()
    mock_apt_stdout.channel.recv_exit_status.return_value = 0
    
    # Mock install failure
    mock_install_stderr = MagicMock()
    mock_install_stderr.read.return_value = b"Error: Package not found"
    mock_install_stdout = MagicMock()
    mock_install_stdout.channel.recv_exit_status.return_value = 1

    call_sequence = [
        (None, mock_tcpdump_which, None), # which tcpdump
        (None, mock_tcpdump_version, None), # tcpdump version
        (None, mock_mpstat_which, mock_mpstat_which_stderr), # which mpstat
        (None, mock_apt_stdout, None), # which apt-get
        (None, mock_install_stdout, mock_install_stderr), # install mpstat (fail)
    ]
    
    mock_ssh_client.exec_command.side_effect = call_sequence

    with pytest.raises(ToolMissingError) as exc_info:
        tool_manager.check_and_install_tools("192.168.1.10")

    assert "mpstat" in str(exc_info.value)
    assert "could not be installed" in str(exc_info.value)


def test_create_tool_manager():
    """Test factory function."""
    manager = create_tool_manager()
    assert isinstance(manager, RemoteToolManager)
    assert manager.ssh_timeout == 30.0
    assert manager.install_timeout == 300.0
    
    manager_custom = create_tool_manager(ssh_timeout=10.0, install_timeout=600.0)
    assert manager_custom.ssh_timeout == 10.0
    assert manager_custom.install_timeout == 600.0
