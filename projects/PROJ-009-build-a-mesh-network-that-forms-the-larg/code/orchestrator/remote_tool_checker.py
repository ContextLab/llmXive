"""
Remote Tool Checker for Mesh Network Supercomputer.

This module implements the logic to verify the presence of required CLI tools
(tcpdump, mpstat) on remote nodes via SSH. It strictly separates the checking
logic from installation logic as per task T012a.

If tools are missing, it raises ToolMissingError immediately and does NOT
attempt installation or proceed with execution.
"""
from __future__ import annotations

import logging
import socket
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path

try:
    import paramiko
except ImportError:
    raise ImportError(
        "The 'paramiko' library is required for remote tool checking. "
        "Install it via: pip install paramiko"
    )

from orchestrator.logger import get_logger
from orchestrator.node_manager import NodeDiscoveryError

# Configure logger
logger = get_logger(__name__)


class ToolMissingError(Exception):
    """Raised when a required tool is missing on a remote node and cannot be installed."""
    pass


@dataclass
class ToolCheckResult:
    """Result of checking a single tool on a single node."""
    tool_name: str
    is_present: bool
    path: Optional[str] = None
    error: Optional[str] = None



@dataclass
class NodeToolCheckResult:
    """Result of checking all required tools on a specific node."""
    node_id: str
    ip_address: str
    all_tools_present: bool
    tool_results: List[ToolCheckResult] = field(default_factory=list)
    error: Optional[str] = None


class RemoteToolChecker:
    """
    Handles SSH connections to remote nodes to verify the presence of CLI tools.
    """

    REQUIRED_TOOLS = ["tcpdump", "mpstat"]

    def __init__(self, timeout: float = 2.0):
        """
        Initialize the RemoteToolChecker.

        Args:
            timeout: Connection timeout in seconds for SSH operations.
        """
        self.timeout = timeout
        self.logger = get_logger(__name__)

    def _create_ssh_client(self, ip_address: str, username: str = "root", password: Optional[str] = None) -> paramiko.SSHClient:
        """
        Create and configure an SSH client.

        Args:
            ip_address: The IP address of the remote node.
            username: SSH username.
            password: SSH password (optional, key-based auth preferred).

        Returns:
            Configured paramiko.SSHClient instance.

        Raises:
            NodeDiscoveryError: If connection fails.
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Attempt connection with timeout
            client.connect(
                hostname=ip_address,
                username=username,
                password=password,
                timeout=self.timeout,
                allow_agent=False,
                look_for_keys=False,
            )
            return client
        except (paramiko.AuthenticationException, socket.timeout, socket.error, paramiko.SSHException) as e:
            self.logger.error(f"Failed to connect to node {ip_address}: {e}")
            raise NodeDiscoveryError(f"Could not establish SSH connection to {ip_address}: {e}")

    def check_tool(self, client: paramiko.SSHClient, tool_name: str) -> ToolCheckResult:
        """
        Check if a specific tool exists on the remote node using 'which'.

        Args:
            client: Active paramiko.SSHClient connection.
            tool_name: Name of the tool to check.

        Returns:
            ToolCheckResult object.
        """
        try:
            stdin, stdout, stderr = client.exec_command(f"which {tool_name}", timeout=self.timeout)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode("utf-8").strip()
            error_output = stderr.read().decode("utf-8").strip()

            if exit_status == 0 and output:
                self.logger.debug(f"Tool '{tool_name}' found at '{output}' on node.")
                return ToolCheckResult(tool_name=tool_name, is_present=True, path=output)
            else:
                self.logger.warning(f"Tool '{tool_name}' NOT found on node. Exit code: {exit_status}. Error: {error_output}")
                return ToolCheckResult(tool_name=tool_name, is_present=False, error=error_output)

        except socket.timeout:
            self.logger.error(f"Timeout checking tool '{tool_name}' on node.")
            return ToolCheckResult(tool_name=tool_name, is_present=False, error="SSH command timed out")
        except Exception as e:
            self.logger.error(f"Error checking tool '{tool_name}': {e}")
            return ToolCheckResult(tool_name=tool_name, is_present=False, error=str(e))

    def check_node(self, node_id: str, ip_address: str, username: str = "root", password: Optional[str] = None) -> NodeToolCheckResult:
        """
        Check all required tools on a specific node.

        Args:
            node_id: Unique identifier for the node.
            ip_address: IP address of the node.
            username: SSH username.
            password: SSH password.

        Returns:
            NodeToolCheckResult containing status of all tools.
        """
        self.logger.info(f"Checking tools on node {node_id} ({ip_address})...")
        client = None
        try:
            client = self._create_ssh_client(ip_address, username, password)
            tool_results = []
            all_present = True

            for tool in self.REQUIRED_TOOLS:
                result = self.check_tool(client, tool)
                tool_results.append(result)
                if not result.is_present:
                    all_present = False

            return NodeToolCheckResult(
                node_id=node_id,
                ip_address=ip_address,
                all_tools_present=all_present,
                tool_results=tool_results
            )

        except NodeDiscoveryError as e:
            self.logger.error(f"Node {node_id} unreachable during tool check: {e}")
            return NodeToolCheckResult(
                node_id=node_id,
                ip_address=ip_address,
                all_tools_present=False,
                error=str(e)
            )
        finally:
            if client:
                try:
                    client.close()
                except Exception:
                    pass

    def check_all_nodes(
        self,
        nodes: List[Dict[str, str]],
        username: str = "root",
        password: Optional[str] = None
    ) -> List[NodeToolCheckResult]:
        """
        Check all required tools on a list of nodes.

        Args:
            nodes: List of dicts containing 'id' and 'ip'.
            username: SSH username.
            password: SSH password.

        Returns:
            List of NodeToolCheckResult objects.

        Raises:
            ToolMissingError: If ANY required tool is missing on ANY node.
        """
        results = []
        missing_tools_report = []

        for node in nodes:
            node_id = node.get("id")
            ip = node.get("ip")
            if not node_id or not ip:
                self.logger.warning(f"Skipping invalid node config: {node}")
                continue

            result = self.check_node(node_id, ip, username, password)
            results.append(result)

            if not result.all_tools_present:
                missing_tools_report.append(result)

        if missing_tools_report:
            error_msg = self._format_missing_tools_error(missing_tools_report)
            self.logger.critical(error_msg)
            raise ToolMissingError(error_msg)

        self.logger.info("All required tools verified on all nodes.")
        return results

    def _format_missing_tools_error(self, results: List[NodeToolCheckResult]) -> str:
        """Format a detailed error message for missing tools."""
        lines = ["Remote Tool Check Failed: Required tools missing on the following nodes:"]
        for res in results:
            lines.append(f"  Node {res.node_id} ({res.ip_address}):")
            for tool_res in res.tool_results:
                if not tool_res.is_present:
                    lines.append(f"    - {tool_res.tool_name}: MISSING ({tool_res.error})")
            if res.error:
                lines.append(f"    Connection Error: {res.error}")
        lines.append("Please ensure 'tcpdump' and 'mpstat' are installed on all nodes or run the installer task.")
        return "\n".join(lines)


def create_tool_checker(timeout: float = 2.0) -> RemoteToolChecker:
    """Factory function to create a RemoteToolChecker instance."""
    return RemoteToolChecker(timeout=timeout)


def main():
    """
    CLI entry point for remote tool checking.
    Expects a JSON file with node list or command line arguments.
    """
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Check for required tools on remote nodes.")
    parser.add_argument("--config", type=str, help="Path to JSON config file with nodes")
    parser.add_argument("--nodes", type=str, help="JSON string of node list")
    parser.add_argument("--username", type=str, default="root", help="SSH username")
    parser.add_argument("--password", type=str, default=None, help="SSH password")
    parser.add_argument("--timeout", type=float, default=2.0, help="SSH timeout")

    args = parser.parse_args()

    nodes = []
    if args.config:
        try:
            with open(args.config, "r") as f:
                data = json.load(f)
                nodes = data.get("nodes", [])
        except Exception as e:
            print(f"Error loading config file: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.nodes:
        try:
            nodes = json.loads(args.nodes)
        except Exception as e:
            print(f"Error parsing nodes JSON: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: Provide --config or --nodes", file=sys.stderr)
        sys.exit(1)

    if not nodes:
        print("Error: No nodes provided", file=sys.stderr)
        sys.exit(1)

    checker = create_tool_checker(timeout=args.timeout)
    try:
        checker.check_all_nodes(nodes, username=args.username, password=args.password)
        print("SUCCESS: All tools present on all nodes.")
        sys.exit(0)
    except ToolMissingError as e:
        print(f"FAILURE: {e}", file=sys.stderr)
        sys.exit(1)
    except NodeDiscoveryError as e:
        print(f"CRITICAL: Node discovery failed: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    exit(main())
