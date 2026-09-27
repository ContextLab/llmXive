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


class RemoteExecutionError(Exception):
    """Raised when a remote SSH execution fails."""
    pass


class ToolMissingError(Exception):
    """Raised when a required tool is missing and cannot be installed."""
    pass


class ToolInstallationError(Exception):
    """Raised when tool installation fails."""
    pass


@dataclass
class ToolCheckResult:
    """Result of checking a single tool on a remote node."""
    tool_name: str
    found: bool
    version: Optional[str] = None
    error: Optional[str] = None


@dataclass
class NodeToolStatus:
    """Status of all tools on a specific node."""
    node_id: str
    ip: str
    checks: Dict[str, ToolCheckResult] = field(default_factory=dict)
    missing_tools: Set[str] = field(default_factory=set)
    installed_tools: Set[str] = field(default_factory=set)
    installation_attempts: Dict[str, bool] = field(default_factory=dict)


class RemoteToolManager:
    """
    Manages verification and installation of required CLI tools on remote nodes.
    Consolidates checking (which) and installation (apt/yum) logic.
    """

    REQUIRED_TOOLS = {
        'tcpdump': 'tcpdump',
        'mpstat': 'sysstat',
        'iperf3': 'iperf3',
        'iwlist': 'iw',
        'iw': 'iw'
    }

    def __init__(self, node_manager):
        """
        Initialize with a NodeManager instance to handle SSH connections.
        """
        self.node_manager = node_manager
        self.logger = get_logger(__name__)

    def _execute_remote_command(self, node_id: str, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """
        Execute a command on a remote node via SSH.
        Returns (exit_code, stdout, stderr).
        """
        try:
            client = self.node_manager.get_ssh_client(node_id)
            if not client:
                raise RemoteExecutionError(f"Could not get SSH client for {node_id}")

            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            return exit_code, stdout.read().decode('utf-8', errors='ignore'), stderr.read().decode('utf-8', errors='ignore')
        except paramiko.SSHException as e:
            raise RemoteExecutionError(f"SSH error executing '{command}' on {node_id}: {e}")
        except Exception as e:
            raise RemoteExecutionError(f"Unexpected error on {node_id}: {e}")

    def check_tool(self, node_id: str, tool_name: str) -> ToolCheckResult:
        """
        Check if a specific tool exists on the remote node using 'which'.
        """
        try:
            exit_code, stdout, stderr = self._execute_remote_command(node_id, f"which {tool_name}")
            if exit_code == 0 and stdout.strip():
                return ToolCheckResult(tool_name=tool_name, found=True, version=stdout.strip())
            else:
                return ToolCheckResult(tool_name=tool_name, found=False, error=f"Not found: {stderr.strip()}")
        except Exception as e:
            self.logger.error(f"Error checking tool {tool_name} on {node_id}: {e}")
            return ToolCheckResult(tool_name=tool_name, found=False, error=str(e))

    def install_tool(self, node_id: str, tool_name: str, package_name: str) -> bool:
        """
        Attempt to install a tool using apt-get or yum.
        Returns True if successful, False otherwise.
        """
        # Detect package manager
        check_pm_exit, pm_stdout, _ = self._execute_remote_command(node_id, "which apt-get")
        if check_pm_exit == 0:
            pkg_manager = "apt-get"
            install_cmd = f"DEBIAN_FRONTEND=noninteractive apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y {package_name}"
        else:
            check_yum_exit, _, _ = self._execute_remote_command(node_id, "which yum")
            if check_yum_exit == 0:
                pkg_manager = "yum"
                install_cmd = f"yum install -y {package_name}"
            else:
                self.logger.error(f"No package manager (apt-get or yum) found on {node_id} for {tool_name}")
                return False

        self.logger.info(f"Installing {tool_name} ({package_name}) via {pkg_manager} on {node_id}...")
        try:
            exit_code, stdout, stderr = self._execute_remote_command(node_id, install_cmd, timeout=120)
            if exit_code == 0:
                self.logger.info(f"Successfully installed {tool_name} on {node_id}")
                return True
            else:
                self.logger.error(f"Failed to install {tool_name} on {node_id}: {stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Installation error for {tool_name} on {node_id}: {e}")
            return False

    def check_and_install_tools(self, node_ids: List[str]) -> Dict[str, NodeToolStatus]:
        """
        Check for required tools on all specified nodes and attempt installation for missing ones.
        Returns a dictionary mapping node_id to NodeToolStatus.
        """
        results = {}
        for node_id in node_ids:
            self.logger.info(f"Checking tools on node {node_id}...")
            status = NodeToolStatus(node_id=node_id, ip=self.node_manager.get_node_ip(node_id))

            for tool_name, package_name in self.REQUIRED_TOOLS.items():
                check_result = self.check_tool(node_id, tool_name)
                status.checks[tool_name] = check_result

                if check_result.found:
                    status.installed_tools.add(tool_name)
                else:
                    status.missing_tools.add(tool_name)
                    # Attempt installation
                    install_success = self.install_tool(node_id, tool_name, package_name)
                    status.installation_attempts[tool_name] = install_success

                    if install_success:
                        # Re-check to confirm
                        recheck = self.check_tool(node_id, tool_name)
                        if recheck.found:
                            status.installed_tools.add(tool_name)
                            status.missing_tools.discard(tool_name)
                        else:
                            self.logger.error(f"Re-check failed for {tool_name} on {node_id} after install attempt")
                    else:
                        self.logger.error(f"Installation failed for {tool_name} on {node_id}")

            results[node_id] = status

        return results

    def validate_all_tools_present(self, node_ids: List[str]) -> Tuple[bool, List[str]]:
        """
        Checks if all required tools are present on all nodes.
        If any tool is missing and could not be installed, raises ToolMissingError.
        Returns (True, []) if all good, or (False, [list of errors]) if issues found.
        """
        all_status = self.check_and_install_tools(node_ids)
        errors = []

        for node_id, status in all_status.items():
            if status.missing_tools:
                error_msg = f"Node {node_id} missing tools: {list(status.missing_tools)}"
                errors.append(error_msg)
                self.logger.error(error_msg)

        if errors:
            raise ToolMissingError(f"Critical tools missing after installation attempts: {'; '.join(errors)}")

        return True, []


def create_tool_manager(node_manager) -> RemoteToolManager:
    """Factory function to create a RemoteToolManager."""
    return RemoteToolManager(node_manager)


def main():
    """CLI entry point for testing tool management."""
    import argparse
    from orchestrator.node_manager import create_node_manager, get_config

    parser = argparse.ArgumentParser(description="Check and install tools on remote nodes")
    parser.add_argument('--config', type=str, default='config/orchestrator.yaml', help='Path to config file')
    args = parser.parse_args()

    config = get_config(args.config)
    node_manager = create_node_manager(config)
    tool_manager = create_tool_manager(node_manager)

    node_ids = list(config.get('nodes', {}).keys())
    if not node_ids:
        print("No nodes found in config.")
        return

    try:
        success, errors = tool_manager.validate_all_tools_present(node_ids)
        if success:
            print("All tools verified or installed successfully.")
        else:
            print("Errors found:")
            for err in errors:
                print(f"  - {err}")
    except ToolMissingError as e:
        print(f"CRITICAL: {e}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exit(1)


if __name__ == '__main__':
    main()
