"""
Unit tests for RemoteToolInstaller module.

These tests verify the tool installation logic without requiring
actual remote nodes.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from orchestrator.remote_tool_installer import (
    RemoteToolInstaller,
    InstallationResult,
    ToolInstallationError,
    create_tool_installer,
    REQUIRED_TOOLS,
    PACKAGE_MANAGERS
)
from orchestrator.models import PhysicalNode, NodeStatus
from orchestrator.node_manager import NodeManager
from orchestrator.remote_tool_checker import RemoteToolChecker


class TestRemoteToolInstallerInit:
    """Tests for RemoteToolInstaller initialization."""

    def test_init_with_node_manager(self):
        """Test initialization with NodeManager."""
        mock_manager = Mock(spec=NodeManager)
        installer = RemoteToolInstaller(mock_manager)

        assert installer.node_manager == mock_manager
        assert installer.sudo_password is None

    def test_init_with_sudo_password(self):
        """Test initialization with sudo password."""
        mock_manager = Mock(spec=NodeManager)
        installer = RemoteToolInstaller(mock_manager, sudo_password="test_password")

        assert installer.node_manager == mock_manager
        assert installer.sudo_password == "test_password"


class TestDetectPackageManager:
    """Tests for package manager detection."""

    def test_detect_apt(self):
        """Test detection of apt package manager."""
        mock_ssh = Mock()
        mock_ssh.exec_command.return_value = Mock(
            channel=Mock(recv_exit_status=Mock(return_value=0))
        )

        installer = RemoteToolInstaller(Mock(spec=NodeManager))

        with patch.object(installer, '_detect_package_manager', return_value='apt'):
            result = installer._detect_package_manager(mock_ssh)
            assert result == 'apt'

    def test_detect_yum(self):
        """Test detection of yum package manager."""
        mock_ssh = Mock()
        # First two checks fail (apt, yum), third succeeds (dnf)
        mock_ssh.exec_command.side_effect = [
            Mock(channel=Mock(recv_exit_status=Mock(return_value=1))),  # apt
            Mock(channel=Mock(recv_exit_status=Mock(return_value=1))),  # yum
            Mock(channel=Mock(recv_exit_status=Mock(return_value=0)))   # dnf
        ]

        installer = RemoteToolInstaller(Mock(spec=NodeManager))

        with patch.object(installer, '_detect_package_manager', return_value='dnf'):
            result = installer._detect_package_manager(mock_ssh)
            assert result == 'dnf'

    def test_no_package_manager_found(self):
        """Test when no package manager is found."""
        mock_ssh = Mock()
        mock_ssh.exec_command.return_value = Mock(
            channel=Mock(recv_exit_status=Mock(return_value=1))
        )

        installer = RemoteToolInstaller(Mock(spec=NodeManager))

        with patch.object(installer, '_detect_package_manager', return_value=None):
            result = installer._detect_package_manager(mock_ssh)
            assert result is None


class TestInstallTool:
    """Tests for individual tool installation."""

    def test_install_success(self):
        """Test successful tool installation."""
        mock_ssh = Mock()
        mock_ssh.get_transport.return_value.getpeername.return_value = ("192.168.1.1", 22)
        mock_ssh.exec_command.return_value = Mock(
            channel=Mock(recv_exit_status=Mock(return_value=0))
        )

        installer = RemoteToolInstaller(Mock(spec=NodeManager))

        result = installer._install_tool(mock_ssh, "tcpdump", "apt")

        assert result.success is True
        assert result.tool_name == "tcpdump"
        assert result.node_ip == "192.168.1.1"
        assert "Successfully installed" in result.message

    def test_install_failure(self):
        """Test failed tool installation."""
        mock_ssh = Mock()
        mock_ssh.get_transport.return_value.getpeername.return_value = ("192.168.1.1", 22)
        mock_ssh.exec_command.return_value = Mock(
            channel=Mock(recv_exit_status=Mock(return_value=1))
        )

        installer = RemoteToolInstaller(Mock(spec=NodeManager))

        result = installer._install_tool(mock_ssh, "tcpdump", "apt")

        assert result.success is False
        assert result.exit_code == 1
        assert "failed" in result.message.lower() or "exit code" in result.message.lower()


class TestInstallMissingTools:
    """Tests for installing multiple missing tools."""

    def test_install_missing_tools_success(self):
        """Test successful installation of missing tools."""
        mock_node = PhysicalNode(ip_address="192.168.1.1", status=NodeStatus.DISCOVERED)
        mock_ssh = Mock()
        mock_ssh.get_transport.return_value.getpeername.return_value = ("192.168.1.1", 22)
        mock_ssh.exec_command.return_value = Mock(
            channel=Mock(recv_exit_status=Mock(return_value=0))
        )

        mock_manager = Mock(spec=NodeManager)
        mock_manager.connect_node.return_value = mock_ssh

        installer = RemoteToolInstaller(mock_manager)

        # Mock the checker to return missing tools
        with patch.object(installer, '_detect_package_manager', return_value='apt'):
            with patch.object(installer, '_install_tool', return_value=InstallationResult(
                node_ip="192.168.1.1",
                tool_name="tcpdump",
                success=True,
                message="Successfully installed tcpdump"
            )):
                results = installer.install_missing_tools(mock_node, tools=["tcpdump"])

                assert len(results) == 1
                assert all(r.success for r in results)
                mock_manager.connect_node.assert_called_once()

    def test_install_when_no_tools_missing(self):
        """Test when no tools are missing."""
        mock_node = PhysicalNode(ip_address="192.168.1.1", status=NodeStatus.DISCOVERED)
        mock_ssh = Mock()

        mock_manager = Mock(spec=NodeManager)
        mock_manager.connect_node.return_value = mock_ssh

        installer = RemoteToolInstaller(mock_manager)

        # Mock checker to return no missing tools
        with patch.object(RemoteToolChecker, 'check_node_tools', return_value=[]):
            results = installer.install_missing_tools(mock_node)

            assert len(results) == len(REQUIRED_TOOLS)
            assert all("already present" in r.message for r in results)
            mock_ssh.close.assert_called()

    def test_install_ssh_connection_failure(self):
        """Test installation when SSH connection fails."""
        mock_node = PhysicalNode(ip_address="192.168.1.1", status=NodeStatus.DISCOVERED)

        mock_manager = Mock(spec=NodeManager)
        mock_manager.connect_node.return_value = None

        installer = RemoteToolInstaller(mock_manager)

        results = installer.install_missing_tools(mock_node)

        assert len(results) == len(REQUIRED_TOOLS)
        assert all(not r.success for r in results)
        assert mock_node.status == NodeStatus.UNAVAILABLE


class TestInstallToolsForAllNodes:
    """Tests for batch installation across multiple nodes."""

    def test_install_for_multiple_nodes(self):
        """Test installation across multiple nodes."""
        nodes = [
            PhysicalNode(ip_address="192.168.1.1", status=NodeStatus.DISCOVERED),
            PhysicalNode(ip_address="192.168.1.2", status=NodeStatus.DISCOVERED)
        ]

        mock_manager = Mock(spec=NodeManager)
        installer = RemoteToolInstaller(mock_manager)

        # Mock the install_missing_tools method
        with patch.object(installer, 'install_missing_tools', return_value=[
            InstallationResult(node_ip="192.168.1.1", tool_name="tcpdump", success=True, message="OK")
        ]):
            results = installer.install_tools_for_all_nodes(nodes)

            assert len(results) == 2
            assert "192.168.1.1" in results
            assert "192.168.1.2" in results

    def test_skip_unavailable_nodes(self):
        """Test that unavailable nodes are skipped."""
        nodes = [
            PhysicalNode(ip_address="192.168.1.1", status=NodeStatus.UNAVAILABLE),
            PhysicalNode(ip_address="192.168.1.2", status=NodeStatus.DISCOVERED)
        ]

        mock_manager = Mock(spec=NodeManager)
        installer = RemoteToolInstaller(mock_manager)

        with patch.object(installer, 'install_missing_tools', return_value=[
            InstallationResult(node_ip="192.168.1.2", tool_name="tcpdump", success=True, message="OK")
        ]):
            results = installer.install_tools_for_all_nodes(nodes)

            assert len(results) == 2
            # Unavailable node should have failure results
            assert all(not r.success for r in results["192.168.1.1"])


class TestCreateToolInstaller:
    """Tests for factory function."""

    def test_create_installer(self):
        """Test factory function creates correct instance."""
        mock_manager = Mock(spec=NodeManager)
        installer = create_tool_installer(mock_manager, sudo_password="test")

        assert isinstance(installer, RemoteToolInstaller)
        assert installer.node_manager == mock_manager
        assert installer.sudo_password == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])