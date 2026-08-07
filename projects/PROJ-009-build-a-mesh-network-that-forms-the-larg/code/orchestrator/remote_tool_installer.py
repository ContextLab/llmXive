"""
Remote Tool Installer for Mesh Network Orchestration.

This module handles the installation of missing system tools (tcpdump, mpstat)
on remote nodes via SSH. It attempts to use package managers (apt-get, yum)
and handles sudo prompts. If installation fails, the node is marked as unavailable.

Dependencies:
    - orchestrator.logger
    - orchestrator.models (PhysicalNode, NodeStatus)
    - paramiko (for SSH)
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from orchestrator.logger import get_logger
from orchestrator.models import PhysicalNode, NodeStatus
import paramiko

# Configure logger
logger = get_logger(__name__)


class ToolInstallationError(Exception):
    """Raised when tool installation fails on a remote node."""
    pass


@dataclass
class InstallationResult:
    """Result of a tool installation attempt."""
    node_ip: str
    tool_name: str
    success: bool
    message: str
    stdout: str
    stderr: str


class RemoteToolInstaller:
    """
    Manages the installation of required tools on remote nodes.

    This class attempts to install missing tools (tcpdump, mpstat) using
    the appropriate package manager for the node's OS.
    """

    def __init__(self, ssh_client: paramiko.SSHClient, timeout: int = 300):
        """
        Initialize the RemoteToolInstaller.

        Args:
            ssh_client: An active paramiko SSHClient instance connected to the node.
            timeout: Maximum time in seconds to wait for installation to complete.
        """
        self.ssh_client = ssh_client
        self.timeout = timeout
        self._supported_package_managers = {
            'apt-get': 'debian',
            'yum': 'redhat',
            'dnf': 'fedora',
            'apk': 'alpine'
        }

    def _detect_package_manager(self) -> Optional[str]:
        """
        Detect the available package manager on the remote node.

        Returns:
            The name of the package manager if found, None otherwise.
        """
        managers_to_check = list(self._supported_package_managers.keys())
        
        for manager in managers_to_check:
            try:
                stdin, stdout, stderr = self.ssh_client.exec_command(f"which {manager}")
                if stdout.channel.recv_exit_status() == 0:
                    logger.debug(f"Detected package manager: {manager}")
                    return manager
            except Exception as e:
                logger.debug(f"Package manager {manager} check failed: {e}")
                continue
        
        return None

    def _execute_command_with_sudo(self, command: str) -> Tuple[int, str, str]:
        """
        Execute a command with sudo privileges, handling password prompts if necessary.

        Args:
            command: The command to execute.

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        # Try running with sudo -n first (non-interactive)
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(f"sudo -n {command}", timeout=self.timeout)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8')
            err = stderr.read().decode('utf-8')
            
            if exit_code == 0:
                return exit_code, out, err
        except Exception:
            pass

        # If non-interactive sudo fails, try with password prompt handling
        # Note: This assumes the user has configured sudoers to allow passwordless sudo
        # or that the SSH key has appropriate permissions. For password-protected sudo,
        # we would need to use pexpect or similar, which is not standard in paramiko.
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(f"sudo {command}", timeout=self.timeout)
            # Read output until EOF
            out = stdout.read().decode('utf-8')
            err = stderr.read().decode('utf-8')
            exit_code = stdout.channel.recv_exit_status()
            return exit_code, out, err
        except Exception as e:
            logger.error(f"Failed to execute command with sudo: {e}")
            return -1, "", str(e)

    def install_tool(self, tool_name: str) -> InstallationResult:
        """
        Attempt to install a specific tool on the remote node.

        Args:
            tool_name: Name of the tool to install (e.g., 'tcpdump', 'sysstat').

        Returns:
            InstallationResult containing the outcome of the installation attempt.
        """
        package_name_map = {
            'tcpdump': 'tcpdump',
            'mpstat': 'sysstat'  # mpstat is part of sysstat package
        }

        if tool_name not in package_name_map:
            return InstallationResult(
                node_ip=self.ssh_client.get_transport().remote_ip if self.ssh_client.get_transport() else "unknown",
                tool_name=tool_name,
                success=False,
                message=f"Unknown tool: {tool_name}",
                stdout="",
                stderr=""
            )

        package_name = package_name_map[tool_name]
        package_manager = self._detect_package_manager()

        if not package_manager:
            return InstallationResult(
                node_ip=self.ssh_client.get_transport().remote_ip if self.ssh_client.get_transport() else "unknown",
                tool_name=tool_name,
                success=False,
                message="No supported package manager found",
                stdout="",
                stderr=""
            )

        # Construct installation command
        if package_manager == 'apt-get':
            install_cmd = f"apt-get update && apt-get install -y {package_name}"
        elif package_manager in ['yum', 'dnf']:
            install_cmd = f"{package_manager} install -y {package_name}"
        elif package_manager == 'apk':
            install_cmd = f"apk add {package_name}"
        else:
            return InstallationResult(
                node_ip=self.ssh_client.get_transport().remote_ip if self.ssh_client.get_transport() else "unknown",
                tool_name=tool_name,
                success=False,
                message=f"Unsupported package manager: {package_manager}",
                stdout="",
                stderr=""
            )

        logger.info(f"Attempting to install {tool_name} using {package_manager} on remote node")
        
        try:
            exit_code, stdout, stderr = self._execute_command_with_sudo(install_cmd)
            
            if exit_code == 0:
                logger.info(f"Successfully installed {tool_name}")
                return InstallationResult(
                    node_ip=self.ssh_client.get_transport().remote_ip if self.ssh_client.get_transport() else "unknown",
                    tool_name=tool_name,
                    success=True,
                    message=f"Successfully installed {tool_name} using {package_manager}",
                    stdout=stdout,
                    stderr=stderr
                )
            else:
                logger.error(f"Failed to install {tool_name}: {stderr}")
                return InstallationResult(
                    node_ip=self.ssh_client.get_transport().remote_ip if self.ssh_client.get_transport() else "unknown",
                    tool_name=tool_name,
                    success=False,
                    message=f"Installation failed with exit code {exit_code}",
                    stdout=stdout,
                    stderr=stderr
                )
        except Exception as e:
            logger.error(f"Exception during installation of {tool_name}: {e}")
            return InstallationResult(
                node_ip=self.ssh_client.get_transport().remote_ip if self.ssh_client.get_transport() else "unknown",
                tool_name=tool_name,
                success=False,
                message=f"Exception during installation: {str(e)}",
                stdout="",
                stderr=str(e)
            )

    def install_missing_tools(self, missing_tools: List[str]) -> List[InstallationResult]:
        """
        Install multiple missing tools on the remote node.

        Args:
            missing_tools: List of tool names to install.

        Returns:
            List of InstallationResult objects for each tool.
        """
        results = []
        for tool in missing_tools:
            result = self.install_tool(tool)
            results.append(result)
            # Small delay between installations to avoid overwhelming the package manager
            if not result.success:
                logger.warning(f"Skipping further tools due to failure in installing {tool}")
                break
        return results


def create_tool_installer(ssh_client: paramiko.SSHClient, timeout: int = 300) -> RemoteToolInstaller:
    """
    Factory function to create a RemoteToolInstaller instance.

    Args:
        ssh_client: An active paramiko SSHClient instance.
        timeout: Maximum time in seconds for installation operations.

    Returns:
        A configured RemoteToolInstaller instance.
    """
    return RemoteToolInstaller(ssh_client, timeout)


def main():
    """
    Main entry point for testing the RemoteToolInstaller.
    
    This function demonstrates how to use the installer with a mock SSH connection.
    In a real scenario, this would be integrated with the node_manager to handle
    actual remote nodes.
    """
    print("Remote Tool Installer - Test Mode")
    print("This module is designed to be used with actual SSH connections.")
    print("To test, integrate with node_manager.py and provide real node IPs.")
    
    # Example usage (would require real SSH connection):
    # ssh = paramiko.SSHClient()
    # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh.connect('node_ip', username='user', password='pass')
    # installer = create_tool_installer(ssh)
    # result = installer.install_tool('tcpdump')
    # print(f"Installation result: {result.success}")
    # ssh.close()


if __name__ == "__main__":
    main()