from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import paramiko

from orchestrator.logger import get_logger

logger = get_logger(__name__)


class ToolInstallationError(Exception):
    """Raised when tool installation fails."""
    pass


@dataclass
class InstallationResult:
    tool_name: str
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


class RemoteToolInstaller:
    """
    Handles the installation of tools on remote nodes.
    """

    def __init__(self, ssh_client: Optional[paramiko.SSHClient] = None):
        self.ssh_client = ssh_client
        self.logger = logger

    def set_ssh_client(self, client: paramiko.SSHClient) -> None:
        self.ssh_client = client

    def _execute_remote_command(self, command: str, timeout: int = 120) -> Tuple[int, str, str]:
        """
        Executes a command on the remote node via SSH.
        Returns (exit_code, stdout, stderr).
        """
        if not self.ssh_client:
            raise ToolInstallationError("SSH client not configured")

        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            out_str = stdout.read().decode('utf-8', errors='ignore').strip()
            err_str = stderr.read().decode('utf-8', errors='ignore').strip()
            return exit_code, out_str, err_str
        except paramiko.SSHException as e:
            raise ToolInstallationError(f"SSH execution failed: {e}")
        except Exception as e:
            raise ToolInstallationError(f"Remote execution error: {e}")

    def install_package(self, package_name: str, install_command: str) -> InstallationResult:
        """
        Installs a package using the provided command.
        """
        self.logger.info(f"Installing {package_name} using: {install_command}")
        try:
            exit_code, stdout, stderr = self._execute_remote_command(install_command)
            if exit_code != 0:
                return InstallationResult(
                    tool_name=package_name,
                    success=False,
                    error=stderr
                )
            return InstallationResult(
                tool_name=package_name,
                success=True,
                message=stdout
            )
        except ToolInstallationError as e:
            return InstallationResult(
                tool_name=package_name,
                success=False,
                error=str(e)
            )


def create_tool_installer(ssh_client: Optional[paramiko.SSHClient] = None) -> RemoteToolInstaller:
    """Factory function to create a RemoteToolInstaller."""
    return RemoteToolInstaller(ssh_client=ssh_client)


def main():
    """
    Entry point for CLI testing.
    """
    logger.info("Remote Tool Installer module loaded.")
    # This module is primarily used by RemoteToolManager
    pass


if __name__ == "__main__":
    main()
