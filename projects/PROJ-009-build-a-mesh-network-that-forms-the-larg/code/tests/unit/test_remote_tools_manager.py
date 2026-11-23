"""
Unit tests for RemoteToolManager.

These tests verify the tool checking and installation logic without
requiring actual remote nodes.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from orchestrator.remote_tools_manager import (
    RemoteToolManager,
    ToolMissingError,
    ToolInstallationError,
    RemoteExecutionError,
    ToolCheckResult,
    NodeToolStatus,
    create_tool_manager,
)


@pytest.fixture
def mock_config():
    return {
        "ssh_timeout": 5,
        "install_timeout": 60,
    }


@pytest.fixture
def tool_manager(mock_config):
    return RemoteToolManager(config=mock_config)


class TestToolCheckResult:
    """Tests for ToolCheckResult dataclass."""

    def test_present_tool(self):
        result = ToolCheckResult(
            tool_name="tcpdump",
            is_present=True,
            version_output="tcpdump version 4.9.3",
        )
        assert result.tool_name == "tcpdump"
        assert result.is_present is True
        assert result.version_output == "tcpdump version 4.9.3"
        assert result.error_message is None

    def test_missing_tool(self):
        result = ToolCheckResult(
            tool_name="tcpdump",
            is_present=False,
            error_message="which: no tcpdump in (/usr/bin:/bin)",
        )
        assert result.tool_name == "tcpdump"
        assert result.is_present is False
        assert result.error_message is not None


class TestNodeToolStatus:
    """Tests for NodeToolStatus dataclass."""

    def test_all_tools_present(self):
        status = NodeToolStatus(
            node_id="node-192.168.1.10",
            node_ip="192.168.1.10",
            all_tools_present=True,
            missing_tools=[],
        )
        assert status.all_tools_present is True
        assert len(status.missing_tools) == 0

    def test_missing_tools(self):
        status = NodeToolStatus(
            node_id="node-192.168.1.10",
            node_ip="192.168.1.10",
            all_tools_present=False,
            missing_tools=["tcpdump", "iperf3"],
        )
        assert status.all_tools_present is False
        assert len(status.missing_tools) == 2
        assert "tcpdump" in status.missing_tools
        assert "iperf3" in status.missing_tools


class TestRemoteToolManager:
    """Tests for RemoteToolManager class."""

    def test_init_with_config(self, tool_manager, mock_config):
        assert tool_manager._ssh_timeout == 5
        assert tool_manager._install_timeout == 60

    def test_init_without_config(self):
        with patch("orchestrator.remote_tools_manager.get_config") as mock_get_config:
            mock_get_config.return_value = {"ssh_timeout": 10}
            manager = RemoteToolManager()
            assert manager._ssh_timeout == 10

    @patch("paramiko.SSHClient")
    def test_create_ssh_connection_success(self, mock_ssh_client, tool_manager):
        mock_client_instance = MagicMock()
        mock_ssh_client.return_value = mock_client_instance

        client = tool_manager._create_ssh_connection("192.168.1.10")

        mock_ssh_client.assert_called_once()
        mock_client_instance.connect.assert_called_once()
        assert client is mock_client_instance

    @patch("paramiko.SSHClient")
    def test_create_ssh_connection_failure(self, mock_ssh_client, tool_manager):
        mock_ssh_client.return_value.connect.side_effect = Exception("Connection refused")

        with pytest.raises(RemoteExecutionError, match="Failed to connect"):
            tool_manager._create_ssh_connection("192.168.1.10")

    @patch.object(RemoteToolManager, "_create_ssh_connection")
    @patch.object(RemoteToolManager, "_execute_command")
    def test_check_tool_present(self, mock_execute, mock_connect, tool_manager):
        mock_client = MagicMock()
        mock_connect.return_value = mock_client
        mock_execute.return_value = (0, "/usr/bin/tcpdump\n", "")

        result = tool_manager.check_tool(mock_client, "tcpdump")

        assert result.is_present is True
        assert result.tool_name == "tcpdump"

    @patch.object(RemoteToolManager, "_create_ssh_connection")
    @patch.object(RemoteToolManager, "_execute_command")
    def test_check_tool_missing(self, mock_execute, mock_connect, tool_manager):
        mock_client = MagicMock()
        mock_connect.return_value = mock_client
        mock_execute.return_value = (1, "", "which: no tcpdump in ...")

        result = tool_manager.check_tool(mock_client, "tcpdump")

        assert result.is_present is False
        assert result.error_message is not None

    @patch.object(RemoteToolManager, "_create_ssh_connection")
    @patch.object(RemoteToolManager, "_execute_command")
    def test_install_tool_apt_success(self, mock_execute, mock_connect, tool_manager):
        mock_client = MagicMock()
        mock_connect.return_value = mock_client

        # First call: check apt-get exists
        # Second call: apt-get update && install
        mock_execute.side_effect = [
            (0, "/usr/bin/apt-get\n", ""),  # which apt-get
            (0, "Installing...\n", ""),     # install command
        ]

        result = tool_manager.install_tool(mock_client, "tcpdump")

        assert result is True

    @patch.object(RemoteToolManager, "_create_ssh_connection")
    @patch.object(RemoteToolManager, "_execute_command")
    def test_install_tool_apt_failure(self, mock_execute, mock_connect, tool_manager):
        mock_client = MagicMock()
        mock_connect.return_value = mock_client

        # First call: check apt-get exists
        # Second call: apt-get update && install (fails)
        mock_execute.side_effect = [
            (0, "/usr/bin/apt-get\n", ""),  # which apt-get
            (1, "", "Package not found\n"),  # install command fails
        ]

        result = tool_manager.install_tool(mock_client, "tcpdump")

        assert result is False

    @patch.object(RemoteToolManager, "_create_ssh_connection")
    @patch.object(RemoteToolManager, "_execute_command")
    def test_install_tool_no_package_manager(self, mock_execute, mock_connect, tool_manager):
        mock_client = MagicMock()
        mock_connect.return_value = mock_client

        # All package manager checks fail
        mock_execute.return_value = (1, "", "not found")

        result = tool_manager.install_tool(mock_client, "tcpdump")

        assert result is False

    @patch.object(RemoteToolManager, "check_tool")
    @patch.object(RemoteToolManager, "_create_ssh_connection")
    def test_check_node_tools_all_present(self, mock_connect, mock_check, tool_manager):
        mock_client = MagicMock()
        mock_connect.return_value = mock_client

        # All tools present
        mock_check.return_value = ToolCheckResult(
            tool_name="tcpdump",
            is_present=True,
        )

        status = tool_manager.check_node_tools("192.168.1.10")

        assert status.all_tools_present is True
        assert len(status.missing_tools) == 0

    @patch.object(RemoteToolManager, "check_tool")
    @patch.object(RemoteToolManager, "_create_ssh_connection")
    def test_check_node_tools_some_missing(self, mock_connect, mock_check, tool_manager):
        mock_client = MagicMock()
        mock_connect.return_value = mock_client

        # Simulate some tools missing
        def mock_check_side_effect(client, tool_name):
            if tool_name == "tcpdump":
                return ToolCheckResult(tool_name=tool_name, is_present=True)
            else:
                return ToolCheckResult(
                    tool_name=tool_name,
                    is_present=False,
                    error_message="not found",
                )

        mock_check.side_effect = mock_check_side_effect

        status = tool_manager.check_node_tools("192.168.1.10")

        assert status.all_tools_present is False
        assert len(status.missing_tools) > 0

    @patch.object(RemoteToolManager, "check_node_tools")
    @patch.object(RemoteToolManager, "install_tool")
    @patch.object(RemoteToolManager, "check_tool")
    @patch.object(RemoteToolManager, "_create_ssh_connection")
    def test_ensure_tools_installed_success(
        self, mock_connect, mock_check, mock_install, mock_check_node, tool_manager
    ):
        mock_client = MagicMock()
        mock_connect.return_value = mock_client

        # Initial check shows missing tools
        initial_status = NodeToolStatus(
            node_id="node-192.168.1.10",
            node_ip="192.168.1.10",
            all_tools_present=False,
            missing_tools=["tcpdump"],
        )
        mock_check_node.return_value = initial_status

        # Installation succeeds
        mock_install.return_value = True

        # Re-check shows tool present
        mock_check.return_value = ToolCheckResult(tool_name="tcpdump", is_present=True)

        status = tool_manager.ensure_tools_installed("192.168.1.10")

        assert status.all_tools_present is True
        assert len(status.missing_tools) == 0

    @patch.object(RemoteToolManager, "check_node_tools")
    @patch.object(RemoteToolManager, "install_tool")
    @patch.object(RemoteToolManager, "_create_ssh_connection")
    def test_ensure_tools_installed_failure(
        self, mock_connect, mock_install, mock_check_node, tool_manager
    ):
        mock_client = MagicMock()
        mock_connect.return_value = mock_client

        # Initial check shows missing tools
        initial_status = NodeToolStatus(
            node_id="node-192.168.1.10",
            node_ip="192.168.1.10",
            all_tools_present=False,
            missing_tools=["tcpdump"],
        )
        mock_check_node.return_value = initial_status

        # Installation fails
        mock_install.return_value = False

        status = tool_manager.ensure_tools_installed("192.168.1.10")

        assert status.all_tools_present is False
        assert "tcpdump" in status.missing_tools

    @patch.object(RemoteToolManager, "ensure_tools_installed")
    def test_validate_node_tools_success(self, mock_ensure, tool_manager):
        mock_ensure.return_value = NodeToolStatus(
            node_id="node-192.168.1.10",
            node_ip="192.168.1.10",
            all_tools_present=True,
            missing_tools=[],
        )

        # Should not raise
        tool_manager.validate_node_tools("192.168.1.10")

    @patch.object(RemoteToolManager, "ensure_tools_installed")
    def test_validate_node_tools_failure(self, mock_ensure, tool_manager):
        mock_ensure.return_value = NodeToolStatus(
            node_id="node-192.168.1.10",
            node_ip="192.168.1.10",
            all_tools_present=False,
            missing_tools=["tcpdump"],
        )

        with pytest.raises(ToolMissingError, match="Required tools missing"):
            tool_manager.validate_node_tools("192.168.1.10")


class TestFactoryFunction:
    """Tests for factory functions."""

    def test_create_tool_manager(self):
        manager = create_tool_manager()
        assert isinstance(manager, RemoteToolManager)

    def test_create_tool_manager_with_config(self):
        config = {"ssh_timeout": 15}
        manager = create_tool_manager(config=config)
        assert manager._ssh_timeout == 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])