"""
Remote Tool Installer for Mesh Network Supercomputer.

This module handles the installation of required CLI tools (tcpdump, mpstat)
on remote nodes via SSH. It relies on T012a (remote_tool_checker) to determine
if installation is necessary.

Dependencies:
    - paramiko (SSH)
    - logging
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

import paramiko

from orchestrator.node_manager import NodeManager, NodeDiscoveryError
from orchestrator.remote_tool_checker import ToolMissingError, RemoteToolChecker, ToolCheckResult

logger = logging.getLogger(__name__)

class ToolInstallationError(Exception):
    """Raised when tool installation fails on a remote node."""
    pass

@dataclass
class InstallationResult:
    """Result of a tool installation attempt on a single node."""
    node_ip: str
    success: bool
    installed_tools: List[str]
    failed_tools: List[str]
    error_message: Optional[str] = None
    duration_seconds: float = 0.0

class RemoteToolInstaller:
    """
    Handles installation of required CLI tools on remote nodes.

    This class attempts to install 'tcpdump' and 'mpstat' (sysstat package)
    using apt-get (Debian/Ubuntu) or yum/dnf (RHEL/CentOS) via SSH.
    """

    def __init__(self, node_manager: NodeManager, timeout: int = 300):
        """
        Initialize the installer.

        Args:
            node_manager: Instance of NodeManager to handle SSH connections.
            timeout: Timeout in seconds for installation commands.
        """
        self.node_manager = node_manager
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def _detect_package_manager(self, ssh_client: paramiko.SSHClient) -> Optional[str]:
        """
        Detect the package manager available on the remote node.

        Returns:
            'apt', 'yum', 'dnf', or None if none found.
        """
        # Check for apt
        stdin, stdout, stderr = ssh_client.exec_command("command -v apt-get", timeout=5)
        if stdout.channel.recv_exit_status() == 0:
            self.logger.debug("Detected apt-get on remote node")
            return "apt"

        # Check for dnf (newer RHEL/Fedora)
        stdin, stdout, stderr = ssh_client.exec_command("command -v dnf", timeout=5)
        if stdout.channel.recv_exit_status() == 0:
            self.logger.debug("Detected dnf on remote node")
            return "dnf"

        # Check for yum (older RHEL/CentOS)
        stdin, stdout, stderr = ssh_client.exec_command("command -v yum", timeout=5)
        if stdout.channel.recv_exit_status() == 0:
            self.logger.debug("Detected yum on remote node")
            return "yum"

        self.logger.warning("No supported package manager (apt, dnf, yum) found on remote node")
        return None

    def _install_tools_with_pm(
        self,
        ssh_client: paramiko.SSHClient,
        package_manager: str,
        tools_to_install: List[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Execute installation commands based on the detected package manager.

        Args:
            ssh_client: Active SSH connection.
            package_manager: One of 'apt', 'yum', 'dnf'.
            tools_to_install: List of tool names to install.

        Returns:
            Tuple of (successfully_installed, failed_installations).
        """
        installed = []
        failed = []

        # Map tools to packages
        # tcpdump -> tcpdump
        # mpstat -> sysstat
        package_map = {
            "tcpdump": "tcpdump",
            "mpstat": "sysstat"
        }

        packages = []
        tool_to_pkg = {}
        for tool in tools_to_install:
            if tool in package_map:
                pkg = package_map[tool]
                packages.append(pkg)
                tool_to_pkg[tool] = pkg

        if not packages:
            return installed, failed

        unique_packages = list(set(packages))

        # Construct install command
        if package_manager == "apt":
            # apt-get install -y <packages>
            cmd = f"apt-get update && apt-get install -y {' '.join(unique_packages)}"
            sudo_prefix = "sudo "
        elif package_manager in ["yum", "dnf"]:
            # yum/dnf install -y <packages>
            cmd = f"{package_manager} install -y {' '.join(unique_packages)}"
            sudo_prefix = "sudo " # Assuming sudo is required for package mgmt
        else:
            raise ToolInstallationError(f"Unsupported package manager: {package_manager}")

        # Execute command
        # We need to handle sudo potentially. The node_manager should ideally
        # handle SSH key auth that allows passwordless sudo, or we assume
        # the user has configured the environment correctly.
        # If sudo requires a password, this will hang or fail without TTY.
        # We assume non-interactive sudo for this research pipeline.

        full_cmd = f"echo '' | {cmd}" # Attempt to pipe empty to sudo if it asks for password (fails safely)

        try:
            self.logger.info(f"Executing installation command: {cmd}")
            stdin, stdout, stderr = ssh_client.exec_command(cmd, timeout=self.timeout)

            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8', errors='ignore')
            error_output = stderr.read().decode('utf-8', errors='ignore')

            if exit_status != 0:
                self.logger.error(f"Installation failed with exit code {exit_status}: {error_output}")
                # If specific packages failed, we might try to parse, but for now we treat as general failure
                failed.extend(tools_to_install)
            else:
                self.logger.info(f"Installation succeeded: {output}")
                installed.extend(tools_to_install)

        except Exception as e:
            self.logger.error(f"Exception during installation: {str(e)}")
            failed.extend(tools_to_install)
            raise ToolInstallationError(f"Failed to execute installation command: {str(e)}")

        return installed, failed

    def install_tools(
        self,
        node_ip: str,
        tools: Optional[List[str]] = None,
        check_first: bool = True
    ) -> InstallationResult:
        """
        Attempt to install specified tools on a remote node.

        Args:
            node_ip: IP address of the target node.
            tools: List of tools to install. Defaults to ['tcpdump', 'mpstat'].
            check_first: If True, verify tools are missing before installing (uses T012a logic).

        Returns:
            InstallationResult object.
        """
        start_time = time.time()
        if tools is None:
            tools = ["tcpdump", "mpstat"]

        self.logger.info(f"Starting tool installation for node {node_ip}: {tools}")

        # If check_first is True, we rely on the checker to tell us what's missing
        # However, to keep this module self-contained for the installation phase,
        # we can re-use the checker logic or just attempt install.
        # The task says: "Attempt ... if check_tool_status() fails".
        # We will assume the caller (or a higher level orchestrator) has determined
        # these tools are missing, OR we perform a quick check here.
        # Given the dependency T012a, let's do a quick check to be safe and efficient.
        if check_first:
            checker = RemoteToolChecker(self.node_manager)
            check_result = checker.check_tools(node_ip, tools)
            if check_result.success:
                self.logger.info(f"All tools already present on {node_ip}. Skipping installation.")
                return InstallationResult(
                    node_ip=node_ip,
                    success=True,
                    installed_tools=[],
                    failed_tools=[],
                    error_message="Tools already present",
                    duration_seconds=time.time() - start_time
                )
            
            # Determine which specific tools are missing
            missing_tools = [t for t in tools if not check_result.results.get(t, False)]
            if not missing_tools:
                 # Should not happen if check_result.success is False, but safety check
                 missing_tools = tools
        else:
            missing_tools = tools

        ssh_client = None
        try:
            # Get SSH client from NodeManager
            # Note: NodeManager typically manages connections. We might need to 
            # ensure a connection is established or get an existing one.
            # For simplicity, we assume node_manager can provide a connection or we connect fresh.
            # The NodeManager API surface shows `discover_nodes` and `ping_node`.
            # We will attempt to connect directly using paramiko for the install phase
            # to avoid state complexity, assuming credentials are managed by NodeManager's config.
            
            # We need to get credentials. The NodeManager likely has them or we assume 
            # standard SSH config. For this implementation, we assume the NodeManager 
            # has a way to connect or we use the config.
            # Let's assume we can connect via paramiko directly using standard SSH auth.
            # In a real scenario, we'd pull keys from the config.
            
            # Attempt connection
            self.logger.debug(f"Connecting to {node_ip} for installation...")
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # We need credentials. Since NodeManager is the source of truth for nodes,
            # we might need to pass credentials or assume they are in ~/.ssh/config.
            # For the sake of the task, we assume the environment is configured for SSH access.
            # We will try to connect. If it fails, we raise an error.
            
            # To make this robust without hardcoding creds, we rely on the fact that
            # if the checker worked (T012a), the connection works.
            # We'll try to use the same connection logic if possible, but paramiko is the standard.
            # Let's assume standard SSH key auth is available for the current user.
            
            try:
                ssh_client.connect(
                    hostname=node_ip,
                    timeout=10,
                    banner_timeout=10,
                    auth_timeout=10
                )
            except Exception as conn_err:
                raise ToolInstallationError(f"Could not connect to {node_ip} for installation: {conn_err}")

            # Detect package manager
            pm = self._detect_package_manager(ssh_client)
            if not pm:
                raise ToolInstallationError(f"No supported package manager found on {node_ip}")

            # Install
            installed, failed = self._install_tools_with_pm(ssh_client, pm, missing_tools)

            success = len(failed) == 0
            error_msg = None if success else f"Failed to install: {failed}"

            return InstallationResult(
                node_ip=node_ip,
                success=success,
                installed_tools=installed,
                failed_tools=failed,
                error_message=error_msg,
                duration_seconds=time.time() - start_time
            )

        except ToolInstallationError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during installation on {node_ip}: {e}")
            return InstallationResult(
                node_ip=node_ip,
                success=False,
                installed_tools=[],
                failed_tools=missing_tools,
                error_message=str(e),
                duration_seconds=time.time() - start_time
            )
        finally:
            if ssh_client:
                ssh_client.close()

def create_tool_installer(node_manager: Optional[NodeManager] = None) -> RemoteToolInstaller:
    """
    Factory function to create a RemoteToolInstaller.

    Args:
        node_manager: Optional NodeManager instance. If None, a new one is not created;
                      the caller must provide one.
    """
    if node_manager is None:
        # We cannot create a NodeManager without config.
        # The caller should provide it.
        raise ValueError("NodeManager instance is required to create a RemoteToolInstaller.")
    return RemoteToolInstaller(node_manager)

def main():
    """
    CLI entry point for testing the installer.
    Expects node IPs as arguments or reads from a config.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Install tools on remote nodes")
    parser.add_argument("--nodes", nargs="+", required=True, help="List of node IPs")
    parser.add_argument("--tools", nargs="+", default=["tcpdump", "mpstat"], help="Tools to install")
    parser.add_argument("--config", default="config/orchestrator.yaml", help="Path to config file")
    
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    try:
        # In a real scenario, we would load config and create NodeManager here.
        # For this standalone script, we assume a NodeManager is available or we mock it for testing.
        # However, since we are implementing the real code, we assume the environment is set up.
        # We will attempt to instantiate a NodeManager if possible, but without the config file
        # structure being fully populated in this snippet, we might need to rely on defaults.
        
        # For the purpose of this task, we assume the NodeManager is passed in or we skip the full integration
        # and just demonstrate the logic. But the task requires a runnable script.
        # Let's assume we can create a minimal NodeManager or the user provides one.
        # Since we don't have the full config loading logic here, we will raise a helpful error
        # if we can't proceed, or we assume a mock for demonstration if no real nodes are provided.
        
        # To make it runnable as per requirements, we will try to create a NodeManager.
        # But we don't have the config loading logic in this file.
        # We will assume the user has a config file and we load it.
        
        from orchestrator.config import get_config
        from orchestrator.node_manager import create_node_manager

        config = get_config(args.config)
        if not config:
            logger.error(f"Could not load config from {args.config}")
            sys.exit(1)

        nm = create_node_manager(config)
        
        installer = create_tool_installer(nm)

        for ip in args.nodes:
            result = installer.install_tools(ip, tools=args.tools, check_first=True)
            if result.success:
                logger.info(f"SUCCESS: {result.node_ip} - Installed: {result.installed_tools}")
            else:
                logger.error(f"FAILED: {result.node_ip} - {result.error_message}")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
