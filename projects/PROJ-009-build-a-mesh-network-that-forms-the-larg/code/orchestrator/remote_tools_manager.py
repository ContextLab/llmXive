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
class NodeToolStatus:
    """Status of a tool on a specific node."""
    node_ip: str
    tool_name: str
    is_present: bool
    installation_attempted: bool = False
    installation_success: bool = False
    error_message: Optional[str] = None


@dataclass
class RemoteToolManager:
    """
    Manages verification and installation of CLI tools on remote nodes.
    Consolidates checking (T012a) and installation (T012b) logic.
    """
    required_tools: Set[str] = field(default_factory=lambda: {"tcpdump", "mpstat"})
    timeout: float = 30.0
    _ssh_client_cache: Dict[str, paramiko.SSHClient] = field(default_factory=dict)

    def _get_ssh_client(self, ip: str, username: str = "root", password: str = "") -> paramiko.SSHClient:
        """
        Establishes or retrieves a cached SSH connection to a node.
        In a real deployment, this would use key-based auth or a secrets manager.
        """
        if ip in self._ssh_client_cache:
            return self._ssh_client_cache[ip]

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                hostname=ip,
                username=username,
                password=password,
                timeout=self.timeout,
                allow_agent=False,
                look_for_keys=False
            )
            self._ssh_client_cache[ip] = client
            logger.info(f"SSH connection established to {ip}")
        except Exception as e:
            logger.error(f"Failed to establish SSH connection to {ip}: {e}")
            raise

        return client

    def _check_tool_exists(self, ssh_client: paramiko.SSHClient, tool_name: str) -> Tuple[bool, str]:
        """
        Checks if a tool exists on the remote node using 'which'.
        Returns (is_present, stdout/stderr).
        """
        command = f"which {tool_name}"
        try:
            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=self.timeout)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if exit_status == 0 and output:
                logger.debug(f"Tool '{tool_name}' found at {output} on remote node.")
                return True, output
            else:
                logger.debug(f"Tool '{tool_name}' NOT found on remote node.")
                return False, error
        except Exception as e:
            logger.error(f"Error checking tool '{tool_name}' on remote node: {e}")
            return False, str(e)

    def _install_tool(self, ssh_client: paramiko.SSHClient, tool_name: str) -> Tuple[bool, str]:
        """
        Attempts to install a tool using apt-get or yum.
        Returns (success, message).
        """
        # Try apt-get first (Debian/Ubuntu)
        apt_command = f"apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y {tool_name}"
        # Fallback to yum (RHEL/CentOS)
        yum_command = f"yum install -y {tool_name}"

        commands_to_try = [apt_command, yum_command]

        for cmd in commands_to_try:
            try:
                logger.info(f"Attempting to install '{tool_name}' via: {cmd}")
                stdin, stdout, stderr = ssh_client.exec_command(cmd, timeout=120) # Longer timeout for install
                exit_status = stdout.channel.recv_exit_status()
                output = stdout.read().decode()
                error = stderr.read().decode()

                if exit_status == 0:
                    logger.info(f"Successfully installed '{tool_name}' on remote node.")
                    return True, output
                else:
                    logger.warning(f"Installation attempt failed for '{tool_name}' (exit {exit_status}): {error}")
                    # Continue to next package manager
            except Exception as e:
                logger.warning(f"Installation command failed for '{tool_name}': {e}")
                continue

        return False, "All installation attempts failed."

    def verify_and_install_tools(self, node_ip: str, username: str = "root", password: str = "") -> List[NodeToolStatus]:
        """
        Verifies and installs required tools on a specific remote node.
        
        Args:
            node_ip: IP address of the target node.
            username: SSH username.
            password: SSH password (or use key-based auth in production).
        
        Returns:
            List of NodeToolStatus objects for each required tool.
        
        Raises:
            ToolMissingError: If a tool is missing and cannot be installed.
        """
        results = []
        ssh_client = None

        try:
            ssh_client = self._get_ssh_client(node_ip, username, password)

            for tool in self.required_tools:
                is_present, _ = self._check_tool_exists(ssh_client, tool)
                status = NodeToolStatus(
                    node_ip=node_ip,
                    tool_name=tool,
                    is_present=is_present
                )

                if not is_present:
                    logger.warning(f"Tool '{tool}' missing on {node_ip}. Attempting installation...")
                    status.installation_attempted = True
                    success, msg = self._install_tool(ssh_client, tool)
                    status.installation_success = success
                    status.error_message = msg if not success else None

                    if not success:
                        logger.error(f"Failed to install '{tool}' on {node_ip}.")
                        raise ToolMissingError(
                            f"Required tool '{tool}' is missing on node {node_ip} and installation failed."
                        )
                    else:
                        # Verify installation succeeded
                        is_now_present, _ = self._check_tool_exists(ssh_client, tool)
                        if not is_now_present:
                            raise ToolMissingError(
                                f"Tool '{tool}' installation reported success but 'which' still fails on {node_ip}."
                            )
                        status.is_present = True
                        logger.info(f"Tool '{tool}' successfully installed on {node_ip}.")

                results.append(status)

        except ToolMissingError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during tool verification/installation on {node_ip}: {e}")
            raise ToolInstallationError(f"Error managing tools on {node_ip}: {e}")
        finally:
            if ssh_client:
                # We keep the connection open for subsequent tasks if needed, 
                # but in a simple manager, we might close it. 
                # For this task, we assume the caller manages the lifecycle or 
                # we close it here if it's a one-off check. 
                # Given the architecture, we'll leave it open if cached, 
                # but ensure we don't leak if an exception happened early.
                pass 
                # Optional: ssh_client.close() 

        return results

    def close_connections(self):
        """Closes all cached SSH connections."""
        for ip, client in self._ssh_client_cache.items():
            try:
                client.close()
                logger.debug(f"Closed SSH connection to {ip}")
            except Exception as e:
                logger.warning(f"Error closing connection to {ip}: {e}")
        self._ssh_client_cache.clear()


def create_tool_manager(required_tools: Optional[Set[str]] = None) -> RemoteToolManager:
    """Factory function to create a RemoteToolManager."""
    if required_tools:
        return RemoteToolManager(required_tools=required_tools)
    return RemoteToolManager()


def main():
    """
    CLI entry point for testing the RemoteToolManager.
    Usage: python -m orchestrator.remote_tools_manager --ip 192.168.1.10 --user root
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify and install tools on remote nodes.")
    parser.add_argument("--ip", required=True, help="IP address of the target node.")
    parser.add_argument("--user", default="root", help="SSH username.")
    parser.add_argument("--tools", nargs="+", default=["tcpdump", "mpstat"], help="Tools to verify/install.")
    
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


if __name__ == "__main__":
    main()
