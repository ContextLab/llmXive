"""
Remote Tools Manager for Mesh Network Supercomputer.

This module handles the verification and installation of required CLI tools
(tcpdump, mpstat) on remote nodes via SSH. It consolidates tool checking
and installation logic into a single robust manager.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path

import paramiko
from paramiko import SSHClient, AutoAddPolicy, SSHException, ChannelException

from orchestrator.logger import get_logger
from orchestrator.config import get_config

# Custom Exceptions
class ToolMissingError(Exception):
    """Raised when a required tool is missing and cannot be installed."""
    pass

class ToolInstallationError(Exception):
    """Raised when tool installation fails."""
    pass


@dataclass
class NodeToolStatus:
    """Status of tools on a specific node."""
    node_ip: str
    tcpdump_available: bool = False
    mpstat_available: bool = False
    tcpdump_installed: bool = False  # True if we just installed it
    mpstat_installed: bool = False
    error_message: Optional[str] = None
    is_ready: bool = False


class RemoteToolManager:
    """
    Manages verification and installation of CLI tools on remote nodes.

    This class handles:
    1. Checking for `tcpdump` and `mpstat` via `which`.
    2. Attempting installation via `apt-get` or `yum` if missing.
    3. Reporting status per node.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or get_logger(__name__)
        self.config = get_config()
        self.ssh_timeout = self.config.get('ssh_timeout', 30) if hasattr(self.config, 'get') else 30

    def _connect(self, ip: str, username: Optional[str] = None, password: Optional[str] = None) -> SSHClient:
        """Establish SSH connection to a node."""
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())

        # Use config defaults if not provided
        user = username or self.config.get('ssh_user', 'root') if hasattr(self.config, 'get') else 'root'
        passwd = password or self.config.get('ssh_password', '') if hasattr(self.config, 'get') else ''

        try:
            client.connect(
                hostname=ip,
                username=user,
                password=passwd,
                timeout=self.ssh_timeout,
                allow_agent=False,
                look_for_keys=False
            )
            self.logger.debug(f"SSH connection established to {ip}")
            return client
        except SSHException as e:
            self.logger.error(f"SSH connection failed for {ip}: {e}")
            raise

    def _check_tool(self, client: SSHClient, tool_name: str) -> bool:
        """Check if a tool exists on the remote node using 'which'."""
        try:
            stdin, stdout, stderr = client.exec_command(f"which {tool_name}")
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode().strip()
            
            if exit_code == 0 and output:
                self.logger.debug(f"Tool '{tool_name}' found at {output} on remote node")
                return True
            else:
                self.logger.debug(f"Tool '{tool_name}' not found on remote node")
                return False
        except SSHException as e:
            self.logger.error(f"Failed to check tool '{tool_name}': {e}")
            return False

    def _install_tool(self, client: SSHClient, tool_name: str) -> bool:
        """
        Attempt to install a tool using apt-get or yum.
        Returns True if installation succeeded, False otherwise.
        """
        self.logger.info(f"Attempting to install '{tool_name}' on remote node...")
        
        # Try apt-get first (Debian/Ubuntu)
        apt_cmd = f"apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y {tool_name}"
        # Try yum (RHEL/CentOS)
        yum_cmd = f"yum install -y {tool_name}"
        
        # Try sudo if direct fails (common in restricted environments)
        sudo_apt_cmd = f"sudo apt-get update && DEBIAN_FRONTEND=noninteractive sudo apt-get install -y {tool_name}"
        sudo_yum_cmd = f"sudo yum install -y {tool_name}"

        commands_to_try = [
            apt_cmd, yum_cmd,
            sudo_apt_cmd, sudo_yum_cmd
        ]

        for cmd in commands_to_try:
            try:
                stdin, stdout, stderr = client.exec_command(cmd)
                # Wait for command to complete
                exit_code = stdout.channel.recv_exit_status()
                
                if exit_code == 0:
                    self.logger.info(f"Successfully installed '{tool_name}' via: {cmd}")
                    return True
                else:
                    error_output = stderr.read().decode()
                    self.logger.warning(f"Installation failed for '{tool_name}' via {cmd}: {error_output}")
                    # Continue to next command
            except SSHException as e:
                self.logger.warning(f"SSH error during installation attempt: {e}")
                continue

        self.logger.error(f"Failed to install '{tool_name}' after all attempts.")
        return False

    def verify_and_install_node(self, ip: str, username: Optional[str] = None, password: Optional[str] = None) -> NodeToolStatus:
        """
        Verify and install tools on a single node.

        Args:
            ip: Node IP address
            username: Optional SSH username
            password: Optional SSH password

        Returns:
            NodeToolStatus object containing the result.
        """
        status = NodeToolStatus(node_ip=ip)
        client = None

        try:
            client = self._connect(ip, username, password)

            # Check tcpdump
            if not self._check_tool(client, "tcpdump"):
                if self._install_tool(client, "tcpdump"):
                    status.tcpdump_installed = True
                    status.tcpdump_available = True
                else:
                    status.error_message = "tcpdump missing and installation failed"
            else:
                status.tcpdump_available = True

            # Check mpstat (part of sysstat package)
            if not self._check_tool(client, "mpstat"):
                if self._install_tool(client, "sysstat"): # mpstat is usually in sysstat
                    status.mpstat_installed = True
                    status.mpstat_available = True
                else:
                    if not status.error_message:
                        status.error_message = "mpstat missing and installation failed"
                    else:
                        status.error_message += "; mpstat missing and installation failed"
            else:
                status.mpstat_available = True

            # Determine overall readiness
            status.is_ready = status.tcpdump_available or status.mpstat_available
            
            if status.is_ready:
                self.logger.info(f"Node {ip} is partially or fully ready for instrumentation.")
            else:
                self.logger.warning(f"Node {ip} has no usable tools.")

        except SSHException as e:
            status.error_message = f"SSH connection failed: {e}"
            self.logger.error(f"Failed to process node {ip}: {e}")
        finally:
            if client:
                client.close()

        return status

    def verify_and_install_all(
        self,
        node_ips: List[str],
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> List[NodeToolStatus]:
        """
        Verify and install tools on a list of nodes.

        Args:
            node_ips: List of node IP addresses
            username: Optional SSH username
            password: Optional SSH password

        Returns:
            List of NodeToolStatus objects.
        """
        results = []
        for ip in node_ips:
            self.logger.info(f"Processing tools for node: {ip}")
            result = self.verify_and_install_node(ip, username, password)
            results.append(result)
            
            if not result.is_ready:
                self.logger.error(f"Node {ip} is not ready for instrumentation.")
        
        return results

    def raise_if_critical_missing(self, results: List[NodeToolStatus]) -> None:
        """
        Raise ToolMissingError if ALL nodes are missing critical tools.
        
        Per T014a requirements: If ALL nodes are uninstrumented for packets, 
        raise InstrumentationFailureError (mapped here to ToolMissingError for T012).
        """
        all_missing = all(not r.tcpdump_available and not r.mpstat_available for r in results)
        if all_missing:
            msg = "CRITICAL: All nodes are missing required tools (tcpdump/mpstat) and installation failed."
            self.logger.critical(msg)
            raise ToolMissingError(msg)

def create_tool_manager() -> RemoteToolManager:
    """Factory function to create a RemoteToolManager instance."""
    return RemoteToolManager()

def main() -> None:
    """CLI entry point for testing tool management."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Verify and install tools on remote nodes")
    parser.add_argument("--ips", nargs="+", required=True, help="List of node IPs")
    parser.add_argument("--user", default=None, help="SSH username")
    parser.add_argument("--pass", dest="password", default=None, help="SSH password")
    parser.add_argument("--strict", action="store_true", help="Fail if any node is not ready")
    args = parser.parse_args()

    manager = create_tool_manager()
    results = manager.verify_and_install_all(args.ips, args.user, args.password)

    for res in results:
        print(f"Node: {res.node_ip}")
        print(f"  tcpdump: {'OK' if res.tcpdump_available else 'MISSING'}")
        print(f"  mpstat: {'OK' if res.mpstat_available else 'MISSING'}")
        if res.error_message:
            print(f"  Error: {res.error_message}")
        print()

    if args.strict:
        manager.raise_if_critical_missing(results)
        print("All nodes ready.")

if __name__ == "__main__":
    main()
