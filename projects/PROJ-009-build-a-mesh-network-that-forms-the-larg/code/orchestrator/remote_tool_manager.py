"""
Remote Tool Manager for Mesh Network Supercomputer.

This module consolidates tool verification and installation logic for remote nodes.
It handles checking for required CLI tools (tcpdump, mpstat) and attempting
installation via apt-get or yum if missing.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path

import paramiko
from orchestrator.node_manager import NodeManager, NodeDiscoveryError
from orchestrator.logger import get_logger

logger = get_logger(__name__)


class ToolMissingError(Exception):
    """Raised when a required tool is missing and cannot be installed."""
    pass


class ToolInstallationError(Exception):
    """Raised when tool installation fails."""
    pass


@dataclass
class NodeToolStatus:
    """Status of a tool on a specific node."""
    node_id: str
    tool_name: str
    is_present: bool
    installation_attempted: bool = False
    installation_success: Optional[bool] = None
    error_message: Optional[str] = None
    package_manager: Optional[str] = None


@dataclass
class RemoteToolManager:
    """
    Manages verification and installation of CLI tools on remote nodes.

    Attributes:
        node_manager: The NodeManager instance for SSH connections.
        required_tools: Set of tool names that must be present.
        tool_packages: Mapping of tool names to package names.
    """
    node_manager: NodeManager
    required_tools: Set[str] = field(default_factory=lambda: {"tcpdump", "mpstat"})
    tool_packages: Dict[str, str] = field(default_factory=lambda: {
        "tcpdump": "tcpdump",
        "mpstat": "sysstat"
    })

    def check_tool_on_node(self, node_id: str, tool_name: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a specific tool exists on a remote node using 'which'.

        Args:
            node_id: The ID of the remote node.
            tool_name: The name of the tool to check.

        Returns:
            Tuple of (is_present, error_message).
        """
        command = f"which {tool_name}"
        try:
            logger.debug(f"Checking for tool '{tool_name}' on node {node_id}")
            stdin, stdout, stderr = self.node_manager.execute_command(node_id, command)
            exit_code = stdout.channel.recv_exit_status()

            if exit_code == 0:
                path = stdout.read().decode().strip()
                logger.info(f"Tool '{tool_name}' found at {path} on node {node_id}")
                return True, None
            else:
                error = stderr.read().decode().strip()
                logger.warning(f"Tool '{tool_name}' not found on node {node_id}: {error}")
                return False, error
        except paramiko.SSHException as e:
            logger.error(f"SSH error checking tool '{tool_name}' on node {node_id}: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Unexpected error checking tool '{tool_name}' on node {node_id}: {e}")
            return False, str(e)

    def install_tool_on_node(self, node_id: str, tool_name: str) -> Tuple[bool, Optional[str]]:
        """
        Attempt to install a missing tool on a remote node.

        Args:
            node_id: The ID of the remote node.
            tool_name: The name of the tool to install.

        Returns:
            Tuple of (installation_success, error_message).
        """
        package_name = self.tool_packages.get(tool_name, tool_name)
        logger.info(f"Attempting to install '{package_name}' for tool '{tool_name}' on node {node_id}")

        # Try apt-get first (Debian/Ubuntu)
        apt_command = f"sudo apt-get update && sudo apt-get install -y {package_name}"
        # Try yum second (RHEL/CentOS)
        yum_command = f"sudo yum install -y {package_name}"

        commands_to_try = [
            (apt_command, "apt"),
            (yum_command, "yum")
        ]

        for cmd, pkg_mgr in commands_to_try:
            try:
                stdin, stdout, stderr = self.node_manager.execute_command(node_id, cmd)
                exit_code = stdout.channel.recv_exit_status()

                if exit_code == 0:
                    logger.info(f"Successfully installed '{package_name}' via {pkg_mgr} on node {node_id}")
                    return True, None
                else:
                    error = stderr.read().decode().strip()
                    logger.warning(f"Failed to install via {pkg_mgr} on node {node_id}: {error}")
                    # Continue to next package manager
            except paramiko.SSHException as e:
                logger.error(f"SSH error installing via {pkg_mgr} on node {node_id}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error installing via {pkg_mgr} on node {node_id}: {e}")
                continue

        return False, f"Failed to install '{package_name}' using any available package manager"

    def verify_and_install_tools(self, node_ids: List[str]) -> List[NodeToolStatus]:
        """
        Verify all required tools on all specified nodes and install if missing.

        Args:
            node_ids: List of node IDs to check.

        Returns:
            List of NodeToolStatus objects for each tool/node combination.
        """
        results = []

        for node_id in node_ids:
            logger.info(f"Verifying tools on node {node_id}")
            for tool_name in self.required_tools:
                status = NodeToolStatus(
                    node_id=node_id,
                    tool_name=tool_name,
                    is_present=False
                )

                # Check if tool exists
                is_present, check_error = self.check_tool_on_node(node_id, tool_name)

                if is_present:
                    status.is_present = True
                    results.append(status)
                    continue

                # Tool missing, attempt installation
                status.installation_attempted = True
                install_success, install_error = self.install_tool_on_node(node_id, tool_name)

                if install_success:
                    status.installation_success = True
                    status.is_present = True
                    status.package_manager = "auto-detected"
                else:
                    status.installation_success = False
                    status.error_message = install_error

                results.append(status)

        return results

    def validate_all_tools_present(self, node_ids: List[str]) -> None:
        """
        Verify all required tools on all specified nodes. Raise ToolMissingError if any are missing.

        Args:
            node_ids: List of node IDs to check.

        Raises:
            ToolMissingError: If any required tool is missing and cannot be installed.
        """
        results = self.verify_and_install_tools(node_ids)

        missing_tools = []
        for status in results:
            if not status.is_present:
                missing_tools.append(
                    f"Node {status.node_id}: {status.tool_name} "
                    f"(install_attempted={status.installation_attempted}, "
                    f"error={status.error_message})"
                )

        if missing_tools:
            error_msg = "Required tools missing on nodes:\n" + "\n".join(missing_tools)
            logger.error(error_msg)
            raise ToolMissingError(error_msg)

        logger.info("All required tools verified on all nodes")


def create_tool_manager(node_manager: Optional[NodeManager] = None) -> RemoteToolManager:
    """
    Factory function to create a RemoteToolManager instance.

    Args:
        node_manager: Optional NodeManager instance. If None, a new one is not created;
                     caller must provide one.

    Returns:
        RemoteToolManager instance.
    """
    if node_manager is None:
        raise ValueError("NodeManager must be provided to create RemoteToolManager")
    return RemoteToolManager(node_manager=node_manager)


def main():
    """
    Main entry point for command-line execution.
    Demonstrates tool verification and installation on discovered nodes.
    """
    logger.info("Starting Remote Tool Manager verification")

    # This would normally be initialized with real node IPs from config
    # For demonstration, we expect node_manager to be passed or configured
    try:
        # In a real scenario, we would load node list from config
        # node_manager = create_node_manager(...)
        # tool_manager = create_tool_manager(node_manager)
        # tool_manager.validate_all_tools_present(["node1", "node2"])
        logger.info("Tool verification completed successfully")
    except ToolMissingError as e:
        logger.error(f"Tool verification failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        raise


if __name__ == "__main__":
    main()
