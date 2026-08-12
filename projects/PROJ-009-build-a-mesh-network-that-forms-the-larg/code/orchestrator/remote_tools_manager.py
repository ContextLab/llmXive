"""
Remote Tools Manager for Mesh Network Supercomputer.

This module handles the verification and installation of required CLI tools
(tcpdump, mpstat) on remote nodes via SSH.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path
import paramiko

from orchestrator.logger import get_logger

logger = get_logger(__name__)


class ToolMissingError(Exception):
    """Raised when a required tool is missing and cannot be installed."""
    pass


class ToolInstallationError(Exception):
    """Raised when tool installation fails."""
    pass


@dataclass
class ToolCheckResult:
    """Result of a tool check on a specific node."""
    tool_name: str
    node_ip: str
    is_present: bool
    version_output: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class NodeToolStatus:
    """Aggregated status of tools on a single node."""
    node_ip: str
    tcpdump_present: bool = False
    mpstat_present: bool = False
    tcpdump_version: Optional[str] = None
    mpstat_version: Optional[str] = None
    errors: List[str] = field(default_factory=list)


@dataclass
class RemoteToolManager:
    """
    Manages verification and installation of CLI tools on remote nodes.
    """
    required_tools: Set[str] = field(default_factory=lambda: {"tcpdump", "mpstat"})
    timeout: float = 30.0
    _ssh_client_cache: Dict[str, paramiko.SSHClient] = field(default_factory=dict)

    REQUIRED_TOOLS = {"tcpdump", "mpstat"}

    def __init__(self, ssh_timeout: float = 30.0, install_timeout: float = 300.0):
        """
        Initialize the RemoteToolManager.

        Args:
            ssh_timeout: Timeout for SSH connection and command execution.
            install_timeout: Timeout for package installation commands.
        """
        self.ssh_timeout = ssh_timeout
        self.install_timeout = install_timeout
        self.logger = get_logger(__name__)

    def _create_ssh_client(self, ip: str, username: str = "root", password: Optional[str] = None, key_filename: Optional[str] = None) -> paramiko.SSHClient:
        """
        Create and connect an SSH client to a remote node.

        Args:
            ip: IP address of the remote node.
            username: SSH username.
            password: SSH password (optional if using keys).
            key_filename: Path to private key file (optional).

        Returns:
            Connected paramiko.SSHClient instance.

        Raises:
            paramiko.SSHException: If connection fails.
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            if key_filename:
                client.connect(ip, username=username, key_filename=key_filename, timeout=self.ssh_timeout)
            elif password:
                client.connect(ip, username=username, password=password, timeout=self.ssh_timeout)
            else:
                # Try key-based auth or system defaults
                client.connect(ip, username=username, timeout=self.ssh_timeout)
            return client
        except Exception as e:
            self.logger.error(f"Failed to connect to {ip}: {e}")
            raise

    def check_tool(self, ssh_client: paramiko.SSHClient, tool_name: str) -> ToolCheckResult:
        """
        Check if a specific tool is present on the remote node.

        Args:
            ssh_client: Active SSH connection.
            tool_name: Name of the tool to check (e.g., 'tcpdump').

        Returns:
            ToolCheckResult with status details.
        """
        try:
            # Use 'which' to find the tool
            stdin, stdout, stderr = ssh_client.exec_command(f"which {tool_name}", timeout=self.ssh_timeout)
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()

            if exit_code == 0 and output:
                # Tool found, try to get version
                version_cmd = f"{output} --version 2>&1 || {output} -v 2>&1 || echo 'unknown'"
                stdin_v, stdout_v, stderr_v = ssh_client.exec_command(version_cmd, timeout=self.ssh_timeout)
                version_output = stdout_v.read().decode().strip()
                return ToolCheckResult(
                    tool_name=tool_name,
                    node_ip=ssh_client.get_transport().getpeername()[0] if ssh_client.get_transport() else "unknown",
                    is_present=True,
                    version_output=version_output
                )
            else:
                return ToolCheckResult(
                    tool_name=tool_name,
                    node_ip=ssh_client.get_transport().getpeername()[0] if ssh_client.get_transport() else "unknown",
                    is_present=False,
                    error_message=error if error else f"Tool '{tool_name}' not found"
                )
        except Exception as e:
            return ToolCheckResult(
                tool_name=tool_name,
                node_ip=ssh_client.get_transport().getpeername()[0] if ssh_client.get_transport() else "unknown",
                is_present=False,
                error_message=str(e)
            )

    def install_tool(self, ssh_client: paramiko.SSHClient, tool_name: str) -> Tuple[bool, str]:
        """
        Attempt to install a missing tool on the remote node.

        Args:
            ssh_client: Active SSH connection.
            tool_name: Name of the tool to install.

        Returns:
            Tuple of (success: bool, message: str).
        """
        # Determine package manager
        # Check for apt
        stdin, stdout, stderr = ssh_client.exec_command("which apt-get", timeout=self.ssh_timeout)
        exit_code_apt = stdout.channel.recv_exit_status()

        if exit_code_apt == 0:
            # Debian/Ubuntu
            cmd = f"sudo apt-get update && sudo apt-get install -y {tool_name}"
            package_manager = "apt"
        else:
            # Check for yum/dnf
            stdin, stdout, stderr = ssh_client.exec_command("which yum", timeout=self.ssh_timeout)
            exit_code_yum = stdout.channel.recv_exit_status()

            if exit_code_yum == 0:
                cmd = f"sudo yum install -y {tool_name}"
                package_manager = "yum"
            else:
                # Try dnf
                stdin, stdout, stderr = ssh_client.exec_command("which dnf", timeout=self.ssh_timeout)
                exit_code_dnf = stdout.channel.recv_exit_status()
                if exit_code_dnf == 0:
                    cmd = f"sudo dnf install -y {tool_name}"
                    package_manager = "dnf"
                else:
                    return False, "No supported package manager found (apt, yum, dnf)"

        self.logger.info(f"Attempting to install {tool_name} via {package_manager} on {ssh_client.get_transport().getpeername()[0] if ssh_client.get_transport() else 'unknown'}")

        try:
            stdin, stdout, stderr = ssh_client.exec_command(cmd, timeout=self.install_timeout)
            # Wait for completion
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode()
            error = stderr.read().decode()

            if exit_code == 0:
                self.logger.info(f"Successfully installed {tool_name}")
                return True, f"Installed via {package_manager}"
            else:
                self.logger.error(f"Failed to install {tool_name}: {error}")
                return False, f"Installation failed: {error}"
        except Exception as e:
            self.logger.error(f"Installation command failed: {e}")
            return False, str(e)

    def check_and_install_tools(self, ip: str, username: str = "root", password: Optional[str] = None, key_filename: Optional[str] = None, force_install: bool = False) -> NodeToolStatus:
        """
        Check for required tools on a remote node and install missing ones.

        Args:
            ip: IP address of the remote node.
            username: SSH username.
            password: SSH password.
            key_filename: Path to private key file.
            force_install: If True, attempt to install even if tools are present (for update).

        Returns:
            NodeToolStatus with the final state of tools on the node.

        Raises:
            ToolMissingError: If a required tool cannot be installed.
        """
        status = NodeToolStatus(node_ip=ip)
        client = None

        try:
            client = self._create_ssh_client(ip, username, password, key_filename)

            for tool in self.REQUIRED_TOOLS:
                check_result = self.check_tool(client, tool)

                if check_result.is_present:
                    if tool == "tcpdump":
                        status.tcpdump_present = True
                        status.tcpdump_version = check_result.version_output
                    elif tool == "mpstat":
                        status.mpstat_present = True
                        status.mpstat_version = check_result.version_output
                    self.logger.info(f"Tool '{tool}' is present on {ip}")
                else:
                    # Tool missing, attempt installation
                    self.logger.warning(f"Tool '{tool}' missing on {ip}. Attempting installation...")
                    success, msg = self.install_tool(client, tool)

                    if success:
                        # Re-check to confirm
                        recheck = self.check_tool(client, tool)
                        if recheck.is_present:
                            if tool == "tcpdump":
                                status.tcpdump_present = True
                                status.tcpdump_version = recheck.version_output
                            elif tool == "mpstat":
                                status.mpstat_present = True
                                status.mpstat_version = recheck.version_output
                            self.logger.info(f"Tool '{tool}' successfully installed on {ip}")
                        else:
                            status.errors.append(f"Installation of {tool} appeared to succeed but verification failed.")
                    else:
                        status.errors.append(f"Failed to install {tool}: {msg}")

            # Final validation
            missing_tools = []
            if not status.tcpdump_present:
                missing_tools.append("tcpdump")
            if not status.mpstat_present:
                missing_tools.append("mpstat")

            if missing_tools:
                raise ToolMissingError(f"Required tools missing on {ip} and could not be installed: {', '.join(missing_tools)}")

            return status

        except ToolMissingError:
            raise
        except Exception as e:
            self.logger.error(f"Error processing node {ip}: {e}")
            status.errors.append(str(e))
            raise ToolMissingError(f"Error checking/installing tools on {ip}: {e}")
        finally:
            if client:
                client.close()

    def check_all_nodes(self, node_ips: List[str], username: str = "root", password: Optional[str] = None, key_filename: Optional[str] = None) -> Dict[str, NodeToolStatus]:
        """
        Check and install tools on a list of nodes.

        Args:
            node_ips: List of IP addresses.
            username: SSH username.
            password: SSH password.
            key_filename: Path to private key file.

        Returns:
            Dictionary mapping IP to NodeToolStatus.

        Raises:
            ToolMissingError: If any node fails to have all required tools.
        """
        results = {}
        all_good = True

        for ip in node_ips:
            try:
                status = self.check_and_install_tools(ip, username, password, key_filename)
                results[ip] = status
            except ToolMissingError as e:
                self.logger.error(f"Node {ip} failed tool check: {e}")
                results[ip] = NodeToolStatus(node_ip=ip, errors=[str(e)])
                all_good = False
            except Exception as e:
                self.logger.error(f"Node {ip} encountered unexpected error: {e}")
                results[ip] = NodeToolStatus(node_ip=ip, errors=[str(e)])
                all_good = False

        if not all_good:
            # Collect all failures
            failures = [f"{ip}: {', '.join(r.errors)}" for ip, r in results.items() if r.errors]
            raise ToolMissingError(f"Tool check/installation failed on the following nodes: {'; '.join(failures)}")

        return results


def create_tool_manager(ssh_timeout: float = 30.0, install_timeout: float = 300.0) -> RemoteToolManager:
    """
    Factory function to create a RemoteToolManager instance.

    Args:
        ssh_timeout: Timeout for SSH operations.
        install_timeout: Timeout for installation operations.

    Returns:
        Configured RemoteToolManager instance.
    """
    return RemoteToolManager(ssh_timeout=ssh_timeout, install_timeout=install_timeout)


def main():
    """
    CLI entry point for testing the RemoteToolManager.
    Expects environment variables or arguments for node IPs and credentials.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Check and install tools on remote nodes")
    parser.add_argument("--ips", nargs="+", required=True, help="List of node IP addresses")
    parser.add_argument("--user", default="root", help="SSH username")
    parser.add_argument("--password", default=None, help="SSH password")
    parser.add_argument("--key", default=None, help="Path to SSH private key")

    args = parser.parse_args()
    
    manager = RemoteToolManager(required_tools=set(args.tools))
    
    try:
        statuses = manager.verify_and_install_tools(args.ip, username=args.user)
        for status in statuses:
            print(f"Node: {status.node_ip}, Tool: {status.tool_name}, Present: {status.is_present}")
            if status.installation_attempted:
                print(f"  -> Installation attempted: {status.installation_success}")
                if status.error_message:
                    print(f"  -> Error: {status.error_message}")
    except ToolMissingError as e:
        print(f"CRITICAL: {e}")
        exit(1)
    except ToolInstallationError as e:
        print(f"INSTALLATION ERROR: {e}")
        exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        exit(1)
    finally:
        manager.close_connections()

    manager = create_tool_manager()

    try:
        results = manager.check_all_nodes(args.ips, username=args.user, password=args.password, key_filename=args.key)
        print("Tool Check Results:")
        for ip, status in results.items():
            print(f"  {ip}: tcpdump={'OK' if status.tcpdump_present else 'MISSING'}, mpstat={'OK' if status.mpstat_present else 'MISSING'}")
            if status.errors:
                for err in status.errors:
                    print(f"    Error: {err}")
        print("All nodes have required tools.")
    except ToolMissingError as e:
        print(f"CRITICAL: {e}")
        exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        exit(1)


if __name__ == "__main__":
    main()
