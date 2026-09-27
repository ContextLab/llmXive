import pytest
from unittest.mock import Mock, patch, MagicMock
from orchestrator.remote_tools_manager import (
    RemoteToolManager,
    ToolMissingError,
    RemoteExecutionError,
    ToolCheckResult,
    NodeToolStatus,
    create_tool_manager
)


class TestRemoteToolManager:
    @pytest.fixture
    def mock_node_manager(self):
        mock = Mock()
        mock.get_ssh_client = Mock(return_value=Mock())
        mock.get_node_ip = Mock(return_value="192.168.1.10")
        return mock

    @pytest.fixture
    def tool_manager(self, mock_node_manager):
        return RemoteToolManager(mock_node_manager)

    def test_init(self, mock_node_manager):
        manager = RemoteToolManager(mock_node_manager)
        assert manager.node_manager == mock_node_manager

    @patch.object(RemoteToolManager, '_execute_remote_command')
    def test_check_tool_found(self, mock_exec, tool_manager):
        mock_exec.return_value = (0, "/usr/bin/tcpdump", "")
        result = tool_manager.check_tool("node1", "tcpdump")
        assert result.found is True
        assert result.tool_name == "tcpdump"
        assert result.version == "/usr/bin/tcpdump"

    @patch.object(RemoteToolManager, '_execute_remote_command')
    def test_check_tool_not_found(self, mock_exec, tool_manager):
        mock_exec.return_value = (1, "", "which: no tcpdump in (/usr/bin)")
        result = tool_manager.check_tool("node1", "tcpdump")
        assert result.found is False
        assert "Not found" in result.error

    @patch.object(RemoteToolManager, '_execute_remote_command')
    def test_check_tool_ssh_error(self, mock_exec, tool_manager):
        mock_exec.side_effect = RemoteExecutionError("SSH failed")
        result = tool_manager.check_tool("node1", "tcpdump")
        assert result.found is False
        assert "SSH failed" in result.error

    @patch.object(RemoteToolManager, '_execute_remote_command')
    def test_install_tool_apt_success(self, mock_exec, tool_manager):
        # First call: check apt-get exists
        mock_exec.side_effect = [
            (0, "/usr/bin/apt-get", ""), # which apt-get
            (0, "Installing...", "") # install command
        ]
        success = tool_manager.install_tool("node1", "tcpdump", "tcpdump")
        assert success is True
        # Verify calls
        assert mock_exec.call_count == 2

    @patch.object(RemoteToolManager, '_execute_remote_command')
    def test_install_tool_yum_fallback(self, mock_exec, tool_manager):
        # First call: apt-get missing
        mock_exec.side_effect = [
            (1, "", "not found"), # which apt-get
            (0, "/usr/bin/yum", ""), # which yum
            (0, "Installing...", "") # install command
        ]
        success = tool_manager.install_tool("node1", "tcpdump", "tcpdump")
        assert success is True
        assert mock_exec.call_count == 3

    @patch.object(RemoteToolManager, '_execute_remote_command')
    def test_install_tool_no_package_manager(self, mock_exec, tool_manager):
        # Both apt and yum missing
        mock_exec.side_effect = [
            (1, "", ""), # apt
            (1, "", ""), # yum
        ]
        success = tool_manager.install_tool("node1", "tcpdump", "tcpdump")
        assert success is False

    @patch.object(RemoteToolManager, 'check_tool')
    @patch.object(RemoteToolManager, 'install_tool')
    def test_check_and_install_tools(self, mock_install, mock_check, tool_manager):
        # Setup mocks
        mock_check.return_value = ToolCheckResult("tcpdump", False)
        mock_install.return_value = True

        result = tool_manager.check_and_install_tools(["node1"])

        assert "node1" in result
        assert result["node1"].checks["tcpdump"].found is False
        assert result["node1"].installation_attempts["tcpdump"] is True
        assert "tcpdump" in result["node1"].installed_tools

    @patch.object(RemoteToolManager, 'check_and_install_tools')
    def test_validate_all_tools_present_success(self, mock_check_install, tool_manager):
        mock_status = NodeToolStatus(node_id="node1", ip="1.2.3.4")
        mock_status.installed_tools = {"tcpdump", "mpstat"}
        mock_check_install.return_value = {"node1": mock_status}

        success, errors = tool_manager.validate_all_tools_present(["node1"])
        assert success is True
        assert len(errors) == 0

    @patch.object(RemoteToolManager, 'check_and_install_tools')
    def test_validate_all_tools_present_failure(self, mock_check_install, tool_manager):
        mock_status = NodeToolStatus(node_id="node1", ip="1.2.3.4")
        mock_status.missing_tools = {"tcpdump"}
        mock_check_install.return_value = {"node1": mock_status}

        with pytest.raises(ToolMissingError) as exc_info:
            tool_manager.validate_all_tools_present(["node1"])
        assert "Critical tools missing" in str(exc_info.value)

    def test_create_tool_manager(self, mock_node_manager):
        manager = create_tool_manager(mock_node_manager)
        assert isinstance(manager, RemoteToolManager)
        assert manager.node_manager == mock_node_manager