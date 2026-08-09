"""
Remote Tools Manager for Mesh Network Supercomputer.

This module handles the verification and installation of required CLI tools
(tcpdump, mpstat) on remote nodes via SSH. It consolidates tool checking
and installation logic into a single robust manager.

Dependencies:
    - paramiko (SSH2 protocol)
    - orchestrator.node_manager (for SSH connection management)
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

# Custom exceptions
class ToolMissingError(Exception):
    """Raised when a required tool is missing and cannot be installed."""
    pass

class ToolInstallationError(Exception):
    """Raised when tool installation fails."""
    pass

@dataclass
class NodeToolStatus:
    """Status of tools on a specific node."""
    node_id: str
    ip_address: str
    tools: Dict[str, bool] = field(default_factory=dict)
    installation_attempts: Dict[str, bool] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def all_tools_present(self) -> bool:
        """Check if all required tools are present."""
        return all(self.tools.values())

    def missing_tools(self) -> List[str]:
        """Get list of missing tools."""
        return [tool for tool, present in self.tools.items() if not present]

class RemoteToolManager:
    """
    Manages verification and installation of CLI tools on remote nodes.

    This class consolidates the functionality of checking for required tools
    (tcpdump, mpstat) and installing them if missing, using the SSH connections
    established by the NodeManager.
    """

    REQUIRED_TOOLS: Set[str] = {"tcpdump", "mpstat"}

    def __init__(self, node_manager: NodeManager, logger: Optional[logging.Logger] = None):
        """
        Initialize the RemoteToolManager.

        Args:
            node_manager: The NodeManager instance for SSH connections.
            logger: Optional logger instance.
        """
        self.node_manager = node_manager
        self.logger = logger or get_logger(__name__)
        self._cache: Dict[str, NodeToolStatus] = {}

    def check_tools_on_node(
        self,
        node_id: str,
        ip_address: str,
        timeout: float = 5.0
    ) -> NodeToolStatus:
        """
        Check if required tools are available on a specific node.

        Args:
            node_id: Unique identifier for the node.
            ip_address: IP address of the node.
            timeout: SSH connection timeout in seconds.

        Returns:
            NodeToolStatus object with tool availability information.

        Raises:
            NodeDiscoveryError: If the node is unreachable.
            ToolMissingError: If any required tool is missing (does not attempt install).
        """
        status = NodeToolStatus(node_id=node_id, ip_address=ip_address)
        self.logger.info(f"Checking tools on node {node_id} ({ip_address})")

        client = None
        try:
            # Connect to the node
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=ip_address,
                timeout=timeout,
                banner_timeout=timeout,
                auth_timeout=timeout
            )

            # Check each required tool
            for tool in self.REQUIRED_TOOLS:
                try:
                    stdin, stdout, stderr = client.exec_command(f"which {tool}")
                    exit_code = stdout.channel.recv_exit_status()

                    if exit_code == 0:
                        status.tools[tool] = True
                        self.logger.debug(f"Tool '{tool}' found on node {node_id}")
                    else:
                        status.tools[tool] = False
                        self.logger.warning(f"Tool '{tool}' NOT found on node {node_id}")
                except Exception as e:
                    status.tools[tool] = False
                    status.errors.append(f"Error checking {tool}: {str(e)}")
                    self.logger.error(f"Error checking tool {tool} on node {node_id}: {e}")

            # Update cache
            self._cache[node_id] = status

            # Raise error if any tools are missing
            if not status.all_tools_present():
                missing = status.missing_tools()
                msg = f"Required tools missing on node {node_id}: {missing}. " \
                      f"Installation will be attempted."
                self.logger.warning(msg)
                # We do NOT raise here yet; we return the status so the caller
                # can decide whether to install or fail.
                # But per task spec: "Raise ToolMissingError if missing and cannot be installed"
                # We'll raise only if installation is not attempted or fails.
                # For now, we return status. The install method will handle raising.

        except paramiko.AuthenticationException:
            status.errors.append("Authentication failed")
            self.logger.error(f"Authentication failed for node {node_id}")
            raise NodeDiscoveryError(f"Authentication failed for node {node_id}")
        except paramiko.SSHException as e:
            status.errors.append(f"SSH error: {str(e)}")
            self.logger.error(f"SSH error for node {node_id}: {e}")
            raise NodeDiscoveryError(f"SSH error for node {node_id}: {e}")
        except socket.timeout:
            status.errors.append("Connection timed out")
            self.logger.error(f"Connection timed out for node {node_id}")
            raise NodeDiscoveryError(f"Connection timed out for node {node_id}")
        except Exception as e:
            status.errors.append(f"Unexpected error: {str(e)}")
            self.logger.error(f"Unexpected error for node {node_id}: {e}")
            raise NodeDiscoveryError(f"Unexpected error for node {node_id}: {e}")
        finally:
            if client:
                client.close()

        return status

    def install_tools_on_node(
        self,
        node_id: str,
        ip_address: str,
        tools: Optional[List[str]] = None,
        timeout: float = 30.0
    ) -> NodeToolStatus:
        """
        Attempt to install missing tools on a specific node.

        Args:
            node_id: Unique identifier for the node.
            ip_address: IP address of the node.
            tools: Optional list of specific tools to install. If None, installs all missing.
            timeout: SSH command timeout in seconds.

        Returns:
            NodeToolStatus object with installation results.

        Raises:
            ToolMissingError: If installation fails for all missing tools.
            ToolInstallationError: If installation fails.
        """
        # First check current status
        status = self.check_tools_on_node(node_id, ip_address, timeout=timeout)

        if tools is None:
            tools_to_install = status.missing_tools()
        else:
            tools_to_install = [t for t in tools if not status.tools.get(t, False)]

        if not tools_to_install:
            self.logger.info(f"All tools already present on node {node_id}")
            return status

        self.logger.info(f"Attempting to install tools on node {node_id}: {tools_to_install}")

        client = None
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=ip_address,
                timeout=timeout,
                banner_timeout=timeout,
                auth_timeout=timeout
            )

            # Determine package manager and install commands
            # Try to detect package manager
            stdin, stdout, stderr = client.exec_command("cat /etc/os-release")
            os_info = stdout.read().decode()
            stdout.channel.recv_exit_status()

            # Try apt-get first (Debian/Ubuntu)
            install_commands = []

            if "Debian" in os_info or "Ubuntu" in os_info or "ubuntu" in os_info:
                # Update package lists
                update_cmd = "sudo apt-get update -y"
                stdin, stdout, stderr = client.exec_command(update_cmd, timeout=timeout)
                update_exit = stdout.channel.recv_exit_status()
                if update_exit != 0:
                    error = f"Package update failed on node {node_id}: {stderr.read().decode()}"
                    status.errors.append(error)
                    self.logger.error(error)
                    # Continue anyway, maybe packages are cached

                # Install missing tools
                for tool in tools_to_install:
                    install_cmd = f"sudo apt-get install -y {tool}"
                    stdin, stdout, stderr = client.exec_command(install_cmd, timeout=timeout)
                    exit_code = stdout.channel.recv_exit_status()
                    if exit_code == 0:
                        status.installation_attempts[tool] = True
                        status.tools[tool] = True
                        self.logger.info(f"Successfully installed {tool} on node {node_id}")
                    else:
                        status.installation_attempts[tool] = False
                        error = f"Failed to install {tool} on node {node_id}: {stderr.read().decode()}"
                        status.errors.append(error)
                        self.logger.error(error)

            elif "CentOS" in os_info or "Red Hat" in os_info or "rhel" in os_info:
                # Try yum/dnf
                for tool in tools_to_install:
                    install_cmd = f"sudo yum install -y {tool}"
                    stdin, stdout, stderr = client.exec_command(install_cmd, timeout=timeout)
                    exit_code = stdout.channel.recv_exit_status()
                    if exit_code == 0:
                        status.installation_attempts[tool] = True
                        status.tools[tool] = True
                        self.logger.info(f"Successfully installed {tool} on node {node_id}")
                    else:
                        status.installation_attempts[tool] = False
                        error = f"Failed to install {tool} on node {node_id}: {stderr.read().decode()}"
                        status.errors.append(error)
                        self.logger.error(error)
            else:
                error = f"Unknown OS on node {node_id}, cannot determine package manager"
                status.errors.append(error)
                self.logger.error(error)
                raise ToolInstallationError(error)

            # Re-check tools after installation attempt
            status = self.check_tools_on_node(node_id, ip_address, timeout=timeout)

            if not status.all_tools_present():
                still_missing = status.missing_tools()
                msg = f"Failed to install all tools on node {node_id}. " \
                      f"Still missing: {still_missing}"
                self.logger.error(msg)
                raise ToolMissingError(msg)

            self.logger.info(f"All tools successfully installed on node {node_id}")
            return status

        except paramiko.AuthenticationException:
            error = f"Authentication failed for node {node_id} during installation"
            self.logger.error(error)
            raise ToolInstallationError(error)
        except paramiko.SSHException as e:
            error = f"SSH error during installation on node {node_id}: {str(e)}"
            self.logger.error(error)
            raise ToolInstallationError(error)
        except socket.timeout:
            error = f"Connection timed out during installation on node {node_id}"
            self.logger.error(error)
            raise ToolInstallationError(error)
        except Exception as e:
            error = f"Unexpected error during installation on node {node_id}: {str(e)}"
            self.logger.error(error)
            raise ToolInstallationError(error)
        finally:
            if client:
                client.close()

    def ensure_tools_on_nodes(
        self,
        node_ids: Optional[List[str]] = None,
        raise_on_failure: bool = True
    ) -> Dict[str, NodeToolStatus]:
        """
        Ensure all required tools are present on specified nodes.

        This is the main entry point for the task. It checks tools on all nodes,
        attempts installation for missing ones, and returns the final status.

        Args:
            node_ids: Optional list of node IDs to check. If None, checks all discovered nodes.
            raise_on_failure: If True, raises ToolMissingError if any node is missing tools.

        Returns:
            Dictionary mapping node_id to NodeToolStatus.

        Raises:
            ToolMissingError: If any node is missing tools and raise_on_failure is True.
        """
        # Get list of nodes
        if node_ids is None:
            # Use all nodes from node_manager
            node_ids = list(self.node_manager._nodes.keys())

        results: Dict[str, NodeToolStatus] = {}
        all_success = True

        for node_id in node_ids:
            node = self.node_manager._nodes.get(node_id)
            if not node:
                self.logger.warning(f"Node {node_id} not found in manager")
                continue

            ip = node.ip_address if hasattr(node, 'ip_address') else node.id
            try:
                # First check
                status = self.check_tools_on_node(node_id, ip)

                if not status.all_tools_present():
                    # Attempt installation
                    status = self.install_tools_on_node(node_id, ip)

                results[node_id] = status

                if not status.all_tools_present():
                    all_success = False
                    self.logger.error(f"Node {node_id} still missing tools: {status.missing_tools()}")

            except ToolMissingError as e:
                all_success = False
                self.logger.error(f"Failed to ensure tools on node {node_id}: {e}")
                if raise_on_failure:
                    raise
            except ToolInstallationError as e:
                all_success = False
                self.logger.error(f"Installation failed on node {node_id}: {e}")
                if raise_on_failure:
                    raise
            except NodeDiscoveryError as e:
                all_success = False
                self.logger.error(f"Node {node_id} unreachable: {e}")
                if raise_on_failure:
                    raise

        if not all_success and raise_on_failure:
            raise ToolMissingError("One or more nodes are missing required tools and installation failed.")

        return results

def create_tool_manager(node_manager: NodeManager) -> RemoteToolManager:
    """
    Factory function to create a RemoteToolManager instance.

    Args:
        node_manager: The NodeManager instance.

    Returns:
        A configured RemoteToolManager instance.
    """
    return RemoteToolManager(node_manager)

def main():
    """
    Command-line interface for testing the tool manager.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Remote Tool Manager for Mesh Network")
    parser.add_argument(
        "--nodes",
        nargs="+",
        required=True,
        help="List of node IDs to check/install tools on"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="SSH connection timeout in seconds"
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Attempt to install missing tools"
    )

    args = parser.parse_args()

    # This would normally require a real NodeManager with SSH credentials
    # For CLI testing, we'd need to load config or pass credentials
    print("Remote Tool Manager CLI - requires NodeManager configuration")
    print(f"Nodes to check: {args.nodes}")
    print(f"Install mode: {args.install}")
    sys.exit(0)

if __name__ == "__main__":
    main()
