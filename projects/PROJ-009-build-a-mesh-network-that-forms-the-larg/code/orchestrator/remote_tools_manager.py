"""
Remote Tools Manager for Mesh Network Supercomputer.

This module handles the verification and installation of required CLI tools
on remote nodes via SSH. It consolidates tool checking and installation logic
to ensure remote nodes have `tcpdump`, `mpstat`, `iwlist`/`iw`, and `iperf3`.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path

import paramiko

from orchestrator.logger import get_logger
from orchestrator.config import get_config

logger = get_logger(__name__)


class ToolMissingError(Exception):
    """Raised when a required tool is missing and cannot be installed."""
    pass


class ToolInstallationError(Exception):
    """Raised when tool installation fails."""
    pass


class RemoteExecutionError(Exception):
    """Raised when remote command execution fails unexpectedly."""
    pass


@dataclass
class ToolCheckResult:
    """Result of checking a single tool on a node."""
    tool_name: str
    is_present: bool
    version_output: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class NodeToolStatus:
    """Status of all tools on a specific node."""
    node_id: str
    node_ip: str
    tool_statuses: Dict[str, ToolCheckResult] = field(default_factory=dict)
    all_tools_present: bool = True
    missing_tools: List[str] = field(default_factory=list)


class RemoteToolManager:
    """
    Manages verification and installation of CLI tools on remote nodes.

    This class consolidates the logic for checking tool availability and
    attempting installation via package managers (apt-get, yum, etc.).
    """

    # Required tools for the mesh network experiment
    REQUIRED_TOOLS = [
        "tcpdump",
        "mpstat",
        "iperf3",
        "iwlist",  # Primary Wi-Fi tool
        "iw",      # Fallback Wi-Fi tool
    ]

    # Mapping of tools to their package names for different package managers
    TOOL_PACKAGES = {
        "tcpdump": {"apt": "tcpdump", "yum": "tcpdump"},
        "mpstat": {"apt": "sysstat", "yum": "sysstat"},
        "iperf3": {"apt": "iperf3", "yum": "iperf3"},
        "iwlist": {"apt": "wireless-tools", "yum": "iw"},
        "iw": {"apt": "iw", "yum": "iw"},
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the RemoteToolManager.

        Args:
            config: Optional configuration dictionary. If None, loads from config.
        """
        self.config = config or get_config()
        self._ssh_timeout = self.config.get("ssh_timeout", 10)
        self._install_timeout = self.config.get("install_timeout", 120)

    def _create_ssh_connection(self, node_ip: str, username: str = "root", password: str = "") -> paramiko.SSHClient:
        """
        Create an SSH connection to a remote node.

        Args:
            node_ip: IP address of the remote node.
            username: SSH username (default: root).
            password: SSH password (default: empty).

        Returns:
            Connected SSH client.

        Raises:
            RemoteExecutionError: If connection fails.
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                hostname=node_ip,
                username=username,
                password=password,
                timeout=self._ssh_timeout,
                allow_agent=False,
                look_for_keys=False,
            )
            logger.debug(f"Successfully connected to {node_ip}")
            return client
        except Exception as e:
            raise RemoteExecutionError(f"Failed to connect to {node_ip}: {str(e)}")

    def _execute_command(self, client: paramiko.SSHClient, command: str, timeout: Optional[int] = None) -> Tuple[int, str, str]:
        """
        Execute a command on the remote node.

        Args:
            client: Active SSH client.
            command: Command to execute.
            timeout: Command timeout in seconds.

        Returns:
            Tuple of (exit_code, stdout, stderr).
        """
        try:
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout or self._ssh_timeout)
            exit_code = stdout.channel.recv_exit_status()
            stdout_text = stdout.read().decode("utf-8", errors="ignore")
            stderr_text = stderr.read().decode("utf-8", errors="ignore")
            return exit_code, stdout_text, stderr_text
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            return -1, "", str(e)

    def check_tool(self, client: paramiko.SSHClient, tool_name: str) -> ToolCheckResult:
        """
        Check if a specific tool is installed on the remote node.

        Args:
            client: Active SSH client.
            tool_name: Name of the tool to check.

        Returns:
            ToolCheckResult with status information.
        """
        # Try 'which' first to check if tool is in PATH
        exit_code, stdout, stderr = self._execute_command(client, f"which {tool_name}")

        if exit_code == 0:
            tool_path = stdout.strip()
            # Try to get version info
            version_exit, version_stdout, version_stderr = self._execute_command(
                client, f"{tool_name} --version 2>&1 || {tool_name} -v 2>&1 || echo 'version unknown'"
            )
            return ToolCheckResult(
                tool_name=tool_name,
                is_present=True,
                version_output=version_stdout.strip() if version_exit == 0 else None,
            )
        else:
            return ToolCheckResult(
                tool_name=tool_name,
                is_present=False,
                error_message=stderr.strip() or f"Tool '{tool_name}' not found in PATH",
            )

    def install_tool(self, client: paramiko.SSHClient, tool_name: str) -> bool:
        """
        Attempt to install a missing tool on the remote node.

        Args:
            client: Active SSH client.
            tool_name: Name of the tool to install.

        Returns:
            True if installation succeeded, False otherwise.
        """
        # Determine package manager
        # Check for apt first, then yum
        package = None

        # Try apt-get
        exit_code, _, _ = self._execute_command(client, "which apt-get")
        if exit_code == 0:
            package = self.TOOL_PACKAGES.get(tool_name, {}).get("apt")
            if package:
                logger.info(f"Installing {tool_name} via apt-get on remote node")
                # Update package list and install
                install_cmd = f"apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y {package}"
                exit_code, stdout, stderr = self._execute_command(
                    client, install_cmd, timeout=self._install_timeout
                )
                if exit_code == 0:
                    logger.info(f"Successfully installed {tool_name} via apt-get")
                    return True
                else:
                    logger.error(f"Failed to install {tool_name} via apt-get: {stderr}")

        # Try yum
        exit_code, _, _ = self._execute_command(client, "which yum")
        if exit_code == 0:
            package = self.TOOL_PACKAGES.get(tool_name, {}).get("yum")
            if package:
                logger.info(f"Installing {tool_name} via yum on remote node")
                install_cmd = f"yum install -y {package}"
                exit_code, stdout, stderr = self._execute_command(
                    client, install_cmd, timeout=self._install_timeout
                )
                if exit_code == 0:
                    logger.info(f"Successfully installed {tool_name} via yum")
                    return True
                else:
                    logger.error(f"Failed to install {tool_name} via yum: {stderr}")

        # Try dnf (newer Fedora/RHEL)
        exit_code, _, _ = self._execute_command(client, "which dnf")
        if exit_code == 0:
            package = self.TOOL_PACKAGES.get(tool_name, {}).get("yum")  # dnf uses same packages
            if package:
                logger.info(f"Installing {tool_name} via dnf on remote node")
                install_cmd = f"dnf install -y {package}"
                exit_code, stdout, stderr = self._execute_command(
                    client, install_cmd, timeout=self._install_timeout
                )
                if exit_code == 0:
                    logger.info(f"Successfully installed {tool_name} via dnf")
                    return True
                else:
                    logger.error(f"Failed to install {tool_name} via dnf: {stderr}")

        logger.warning(f"Could not determine package manager or install {tool_name}")
        return False

    def check_node_tools(self, node_ip: str, username: str = "root", password: str = "") -> NodeToolStatus:
        """
        Check all required tools on a specific node.

        Args:
            node_ip: IP address of the node.
            username: SSH username.
            password: SSH password.

        Returns:
            NodeToolStatus with results for all tools.
        """
        status = NodeToolStatus(node_id=f"node-{node_ip}", node_ip=node_ip)
        client = None

        try:
            client = self._create_ssh_connection(node_ip, username, password)

            for tool_name in self.REQUIRED_TOOLS:
                result = self.check_tool(client, tool_name)
                status.tool_statuses[tool_name] = result

                if not result.is_present:
                    status.all_tools_present = False
                    status.missing_tools.append(tool_name)

            return status

        except RemoteExecutionError as e:
            logger.error(f"SSH connection failed for {node_ip}: {str(e)}")
            # Mark all tools as missing due to connection failure
            for tool_name in self.REQUIRED_TOOLS:
                status.tool_statuses[tool_name] = ToolCheckResult(
                    tool_name=tool_name,
                    is_present=False,
                    error_message=f"SSH connection failed: {str(e)}",
                )
            status.missing_tools = self.REQUIRED_TOOLS.copy()
            return status

        finally:
            if client:
                client.close()

    def ensure_tools_installed(self, node_ip: str, username: str = "root", password: str = "") -> NodeToolStatus:
        """
        Check and install missing tools on a node.

        Args:
            node_ip: IP address of the node.
            username: SSH username.
            password: SSH password.

        Returns:
            NodeToolStatus with final status after installation attempts.
        """
        # First, check what's missing
        initial_status = self.check_node_tools(node_ip, username, password)

        if initial_status.all_tools_present:
            logger.info(f"All tools present on {node_ip}")
            return initial_status

        # Attempt to install missing tools
        client = None
        try:
            client = self._create_ssh_connection(node_ip, username, password)

            for tool_name in initial_status.missing_tools:
                logger.info(f"Attempting to install {tool_name} on {node_ip}")
                if self.install_tool(client, tool_name):
                    # Re-check the tool
                    result = self.check_tool(client, tool_name)
                    initial_status.tool_statuses[tool_name] = result
                    if result.is_present:
                        initial_status.missing_tools.remove(tool_name)

        except RemoteExecutionError as e:
            logger.error(f"Failed to connect for installation on {node_ip}: {str(e)}")

        finally:
            if client:
                client.close()

        # Update overall status
        initial_status.all_tools_present = len(initial_status.missing_tools) == 0

        return initial_status

    def validate_node_tools(self, node_ip: str, username: str = "root", password: str = "") -> None:
        """
        Validate that all required tools are present on a node.

        Args:
            node_ip: IP address of the node.
            username: SSH username.
            password: SSH password.

        Raises:
            ToolMissingError: If any required tool is missing and cannot be installed.
        """
        status = self.ensure_tools_installed(node_ip, username, password)

        if not status.all_tools_present:
            missing_str = ", ".join(status.missing_tools)
            raise ToolMissingError(
                f"Required tools missing on {node_ip} and could not be installed: {missing_str}. "
                f"Please install manually or check SSH connectivity and package manager access."
            )

        logger.info(f"All required tools validated on {node_ip}")


def create_tool_manager(config: Optional[Dict] = None) -> RemoteToolManager:
    """
    Factory function to create a RemoteToolManager instance.

    Args:
        config: Optional configuration dictionary.

    Returns:
        Configured RemoteToolManager instance.
    """
    return RemoteToolManager(config=config)


def main():
    """
    Main entry point for standalone execution.

    Usage:
        python -m orchestrator.remote_tools_manager --node-ip <ip> [--username <user>] [--password <pass>]
    """
    import argparse

    parser = argparse.ArgumentParser(description="Remote Tools Manager")
    parser.add_argument("--node-ip", required=True, help="IP address of the remote node")
    parser.add_argument("--username", default="root", help="SSH username")
    parser.add_argument("--password", default="", help="SSH password")
    parser.add_argument("--check-only", action="store_true", help="Only check tools, don't install")

    args = parser.parse_args()

    manager = create_tool_manager()

    if args.check_only:
        logger.info(f"Checking tools on {args.node_ip}...")
        status = manager.check_node_tools(args.node_ip, args.username, args.password)
    else:
        logger.info(f"Ensuring tools are installed on {args.node_ip}...")
        try:
            status = manager.ensure_tools_installed(args.node_ip, args.username, args.password)
        except ToolMissingError as e:
            logger.error(str(e))
            return 1

    # Print results
    print(f"\nNode: {status.node_id} ({status.node_ip})")
    print(f"All tools present: {status.all_tools_present}")
    if status.missing_tools:
        print(f"Missing tools: {', '.join(status.missing_tools)}")

    print("\nTool Status:")
    for tool_name, result in status.tool_statuses.items():
        status_str = "✓" if result.is_present else "✗"
        print(f"  {status_str} {tool_name}: {result.error_message or result.version_output or 'Present'}")

    return 0 if status.all_tools_present else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
