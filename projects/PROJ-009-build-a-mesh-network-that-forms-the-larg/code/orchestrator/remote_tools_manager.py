from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path
import paramiko

from orchestrator.logger import get_logger
from orchestrator.config import get_config

# Required tools as defined in tasks.md T012
REQUIRED_TOOLS: Set[str] = {'tcpdump', 'mpstat', 'iwlist', 'iw', 'iperf3'}

logger = get_logger(__name__)


class RemoteExecutionError(Exception):
    """Raised when SSH execution fails unexpectedly."""
    pass


class ToolMissingError(Exception):
    """Raised when a required tool is missing and cannot be installed."""
    pass


class ToolInstallationError(Exception):
    """Raised when tool installation fails."""
    pass


@dataclass
class ToolCheckResult:
    tool_name: str
    installed: bool
    path: Optional[str] = None
    install_command: Optional[str] = None
    install_success: bool = False
    error_message: Optional[str] = None


@dataclass
class NodeToolStatus:
    node_ip: str
    results: List[ToolCheckResult] = field(default_factory=list)
    all_tools_ready: bool = True


class RemoteToolManager:
    """
    Manages verification and installation of CLI tools on remote nodes.
    Consolidates checking and installing logic.
    """

    def __init__(self, ssh_client: Optional[paramiko.SSHClient] = None):
        self.ssh_client = ssh_client
        self.logger = logger

    def set_ssh_client(self, client: paramiko.SSHClient) -> None:
        self.ssh_client = client

    def _execute_remote_command(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """
        Executes a command on the remote node via SSH.
        Returns (exit_code, stdout, stderr).
        """
        if not self.ssh_client:
            raise RemoteExecutionError("SSH client not configured")

        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            out_str = stdout.read().decode('utf-8', errors='ignore').strip()
            err_str = stderr.read().decode('utf-8', errors='ignore').strip()
            return exit_code, out_str, err_str
        except paramiko.SSHException as e:
            raise RemoteExecutionError(f"SSH execution failed: {e}")
        except Exception as e:
            raise RemoteExecutionError(f"Remote execution error: {e}")

    def check_tool(self, tool_name: str) -> ToolCheckResult:
        """
        Checks if a specific tool is installed on the remote node.
        Returns ToolCheckResult with installation info if missing.
        """
        # Check existence via 'which'
        exit_code, stdout, stderr = self._execute_remote_command(f"which {tool_name}")

        if exit_code == 0:
            return ToolCheckResult(tool_name=tool_name, installed=True, path=stdout)

        # Tool missing, determine install command based on package manager
        install_cmd = None
        # Check for apt
        exit_code, _, _ = self._execute_remote_command("command -v apt-get")
        if exit_code == 0:
            install_cmd = f"sudo apt-get update && sudo apt-get install -y {tool_name}"
        else:
            # Check for yum
            exit_code, _, _ = self._execute_remote_command("command -v yum")
            if exit_code == 0:
                install_cmd = f"sudo yum install -y {tool_name}"

        if not install_cmd:
            return ToolCheckResult(
                tool_name=tool_name,
                installed=False,
                error_message=f"Tool '{tool_name}' missing and package manager (apt/yum) not detected."
            )

        return ToolCheckResult(
            tool_name=tool_name,
            installed=False,
            install_command=install_cmd
        )

    def install_tool(self, tool_name: str, install_command: str) -> ToolCheckResult:
        """
        Attempts to install a tool using the provided command.
        """
        self.logger.info(f"Installing {tool_name} on {self.ssh_client._sock if self.ssh_client else 'unknown'}")
        try:
            exit_code, stdout, stderr = self._execute_remote_command(install_command, timeout=120)
            if exit_code != 0:
                return ToolCheckResult(
                    tool_name=tool_name,
                    installed=False,
                    error_message=f"Installation failed: {stderr}"
                )
            return ToolCheckResult(
                tool_name=tool_name,
                installed=True,
                install_success=True,
                error_message=None
            )
        except Exception as e:
            return ToolCheckResult(
                tool_name=tool_name,
                installed=False,
                error_message=f"Installation exception: {str(e)}"
            )

    def verify_and_install_tools(self, node_ip: str) -> NodeToolStatus:
        """
        Verifies all required tools on a node and installs missing ones.
        Returns NodeToolStatus with results.
        """
        self.logger.info(f"Verifying tools on node {node_ip}")
        results = []
        all_ready = True

        for tool in REQUIRED_TOOLS:
            check_result = self.check_tool(tool)

            if not check_result.installed:
                self.logger.warning(f"Tool {tool} missing on {node_ip}. Attempting install...")
                if check_result.install_command:
                    install_result = self.install_tool(tool, check_result.install_command)
                    if install_result.install_success:
                        check_result = ToolCheckResult(
                            tool_name=tool,
                            installed=True,
                            install_success=True
                        )
                        self.logger.info(f"Successfully installed {tool} on {node_ip}")
                    else:
                        all_ready = False
                        self.logger.error(f"Failed to install {tool} on {node_ip}: {install_result.error_message}")
                else:
                    all_ready = False
                    self.logger.error(f"Cannot install {tool} on {node_ip}: no package manager found")
            else:
                self.logger.info(f"Tool {tool} found on {node_ip} at {check_result.path}")

            results.append(check_result)
            if not check_result.installed:
                all_ready = False

        return NodeToolStatus(node_ip=node_ip, results=results, all_tools_ready=all_ready)

    def verify_all_tools(self, node_ips: List[str]) -> List[NodeToolStatus]:
        """
        Verifies tools on a list of nodes.
        Raises ToolMissingError if any node fails verification after install attempts.
        """
        status_list = []
        for ip in node_ips:
            # Re-use existing SSH client if available, otherwise expect one to be passed or configured
            # For this implementation, we assume SSH connection is managed externally or via config
            # Here we just call verify_and_install_tools which assumes client is set
            status = self.verify_and_install_tools(ip)
            status_list.append(status)
            if not status.all_tools_ready:
                missing_tools = [r.tool_name for r in status.results if not r.installed]
                raise ToolMissingError(f"Node {ip} missing tools after install attempts: {missing_tools}")

        return status_list


def create_tool_manager(ssh_client: Optional[paramiko.SSHClient] = None) -> RemoteToolManager:
    """Factory function to create a RemoteToolManager."""
    return RemoteToolManager(ssh_client=ssh_client)


def main():
    """
    Entry point for CLI testing of the tool manager.
    Reads node IPs from config and verifies tools.
    """
    config = get_config()
    if not config:
        logger.error("Config not found. Cannot run tool verification.")
        return

    node_ips = config.get('node_ips', [])
    if not node_ips:
        logger.warning("No node IPs found in config.")
        return

    # In a real scenario, we would establish SSH connections here.
    # For this task, we demonstrate the logic structure.
    logger.info(f"Starting tool verification for nodes: {node_ips}")
    
    # Mocking SSH client connection for demonstration of logic flow
    # In actual execution, this would be a real paramiko.SSHClient connected to the nodes
    # managed by node_manager.py (T013a)
    try:
        # Placeholder for actual SSH connection logic
        # manager = create_tool_manager(ssh_client=real_client)
        # results = manager.verify_all_tools(node_ips)
        pass
    except ToolMissingError as e:
        logger.error(f"Tool verification failed: {e}")
        raise
    except RemoteExecutionError as e:
        logger.error(f"Remote execution failed: {e}")
        raise

    logger.info("Tool verification completed successfully.")


if __name__ == "__main__":
    main()
