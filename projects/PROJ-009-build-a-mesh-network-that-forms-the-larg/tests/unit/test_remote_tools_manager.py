import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add code to path
sys.path.insert(0, os.path.join(os.dirname(__file__), '..', '..', 'code'))

from orchestrator.remote_tools_manager import (
    RemoteToolManager,
    ToolCheckResult,
    NodeToolStatus,
    ToolMissingError,
    RemoteExecutionError,
    create_tool_manager
)


@pytest.fixture
def mock_ssh_client():
    """Create a mock SSH client."""
    return MagicMock()


@pytest.fixture
def tool_manager(mock_ssh_client):
    """Create a RemoteToolManager instance."""
    return RemoteToolManager(ssh_client=mock_ssh_client)


def test_check_tool_installed(tool_manager):
    """Test checking for an installed tool."""
    # Mock successful 'which' command
    tool_manager._execute_remote_command = Mock(return_value=(0, "/usr/bin/tcpdump", ""))

    result = tool_manager.check_tool("tcpdump")

    assert result.installed is True
    assert result.path == "/usr/bin/tcpdump"
    assert result.install_command is None


def test_check_tool_missing_no_package_manager(tool_manager):
    """Test checking for a missing tool when no package manager is found."""
    # Mock failed 'which'
    tool_manager._execute_remote_command = Mock(side_effect=[
        (1, "", ""), # which failed
        (1, "", ""), # apt failed
        (1, "", "")  # yum failed
    ])

    result = tool_manager.check_tool("tcpdump")

    assert result.installed is False
    assert result.install_command is None
    assert "package manager" in result.error_message


def test_check_tool_missing_with_apt(tool_manager):
    """Test checking for a missing tool when apt is available."""
    # Mock failed 'which', successful apt
    tool_manager._execute_remote_command = Mock(side_effect=[
        (1, "", ""), # which failed
        (0, "apt-get", "") # apt available
    ])

    result = tool_manager.check_tool("tcpdump")

    assert result.installed is False
    assert "apt-get" in result.install_command


def test_install_tool_success(tool_manager):
    """Test successful tool installation."""
    tool_manager._execute_remote_command = Mock(return_value=(0, "Installing...", ""))

    result = tool_manager.install_tool("tcpdump", "sudo apt-get install -y tcpdump")

    assert result.install_success is True
    assert result.installed is True


def test_install_tool_failure(tool_manager):
    """Test failed tool installation."""
    tool_manager._execute_remote_command = Mock(return_value=(1, "", "Error: Package not found"))

    result = tool_manager.install_tool("tcpdump", "sudo apt-get install -y tcpdump")

    assert result.install_success is False
    assert result.installed is False
    assert "Error: Package not found" in result.error_message


def test_verify_and_install_tools_all_success(tool_manager, mock_ssh_client):
    """Test verifying and installing tools where all succeed."""
    # Mock check_tool to return installed=True for all
    with patch.object(tool_manager, 'check_tool') as mock_check:
        mock_check.return_value = ToolCheckResult(tool_name="tcpdump", installed=True, path="/usr/bin/tcpdump")
        
        # Mock SSH client connection check
        with patch.object(tool_manager, '_execute_remote_command') as mock_exec:
            mock_exec.return_value = (0, "apt-get", "") # Just for package manager detection logic inside check_tool if needed, but we mock check_tool directly here
            
            # We need to mock the internal flow because verify_and_install_tools calls check_tool
            # Let's mock the internal flow more accurately
            pass

    # Simpler test: mock the entire verify_and_install_tools flow
    with patch.object(tool_manager, 'check_tool') as mock_check:
        mock_check.return_value = ToolCheckResult(tool_name="tcpdump", installed=True, path="/usr/bin/tcpdump")
        with patch.object(tool_manager, '_execute_remote_command') as mock_exec:
            # We need to ensure the internal logic doesn't fail
            # For simplicity, we assume check_tool returns installed=True
            pass

    # Actual test logic
    mock_ips = ["192.168.1.10"]
    # Mock the internal check_tool and install_tool calls
    with patch.object(tool_manager, 'check_tool') as mock_check:
        mock_check.return_value = ToolCheckResult(tool_name="tcpdump", installed=True, path="/usr/bin/tcpdump")
        with patch.object(tool_manager, 'install_tool') as mock_install:
            mock_install.return_value = ToolCheckResult(tool_name="tcpdump", installed=True, install_success=True)
            
            status = tool_manager.verify_and_install_tools(mock_ips[0])
            
            assert status.all_tools_ready is True
            assert len(status.results) > 0


def test_verify_all_tools_raises_missing(tool_manager):
    """Test that verify_all_tools raises ToolMissingError if tools are missing."""
    mock_ips = ["192.168.1.10"]
    
    # Mock check_tool to return missing and install_tool to fail
    with patch.object(tool_manager, 'check_tool') as mock_check:
        mock_check.return_value = ToolCheckResult(tool_name="tcpdump", installed=False, error_message="Not found")
        with patch.object(tool_manager, 'install_tool') as mock_install:
            mock_install.return_value = ToolCheckResult(tool_name="tcpdump", installed=False, install_success=False)
            
            with pytest.raises(ToolMissingError):
                tool_manager.verify_all_tools(mock_ips)


def test_remote_execution_error(tool_manager):
    """Test that RemoteExecutionError is raised on SSH failure."""
    tool_manager.ssh_client = None
    with pytest.raises(RemoteExecutionError):
        tool_manager._execute_remote_command("ls")
