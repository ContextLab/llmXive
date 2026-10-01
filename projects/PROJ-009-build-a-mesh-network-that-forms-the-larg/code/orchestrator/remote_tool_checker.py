from __future__ import annotations

import logging
import socket
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import paramiko

from orchestrator.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ToolCheckResult:
    tool_name: str
    installed: bool
    path: Optional[str] = None
    error: Optional[str] = None


@dataclass
class NodeToolCheckResult:
    node_ip: str
    checks: List[ToolCheckResult] = field(default_factory=list)
    all_ready: bool = True


class RemoteToolChecker:
    """
    Checks for the existence of tools on remote nodes.
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
            raise RuntimeError("SSH client not configured")

        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            out_str = stdout.read().decode('utf-8', errors='ignore').strip()
            err_str = stderr.read().decode('utf-8', errors='ignore').strip()
            return exit_code, out_str, err_str
        except paramiko.SSHException as e:
            raise RuntimeError(f"SSH execution failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Remote execution error: {e}")

    def check_tool(self, tool_name: str) -> ToolCheckResult:
        """
        Checks if a tool is installed.
        """
        try:
            exit_code, stdout, stderr = self._execute_remote_command(f"which {tool_name}")
            if exit_code == 0:
                return ToolCheckResult(tool_name=tool_name, installed=True, path=stdout)
            else:
                return ToolCheckResult(tool_name=tool_name, installed=False, error="Not found")
        except Exception as e:
            return ToolCheckResult(tool_name=tool_name, installed=False, error=str(e))


def create_tool_checker(ssh_client: Optional[paramiko.SSHClient] = None) -> RemoteToolChecker:
    """Factory function to create a RemoteToolChecker."""
    return RemoteToolChecker(ssh_client=ssh_client)


def main():
    """
    Entry point for CLI testing.
    """
    logger.info("Remote Tool Checker module loaded.")
    pass


if __name__ == "__main__":
    main()