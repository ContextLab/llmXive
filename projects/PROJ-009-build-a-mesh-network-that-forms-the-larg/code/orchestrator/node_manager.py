"""
Node Manager for Mesh Network Orchestration.

Handles SSH connections, heartbeat pings, device discovery, and task re-assignment.
Uses paramiko.SSHClient with SSH2 protocol.
"""

from __future__ import annotations

import logging
import socket
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

import paramiko
from paramiko import SSHClient, SSHException, AuthenticationException, SocketTimeout

from orchestrator.logger import get_logger
from orchestrator.models import PhysicalNode, NodeStatus, TaskChunk

logger: logging.Logger = get_logger(__name__)


class NodeDiscoveryError(Exception):
    """Raised when node discovery fails completely (all nodes unreachable)."""
    pass


class NodeHeartbeatLost(Exception):
    """Raised when a runtime heartbeat is lost for a specific node."""
    def __init__(self, node_ip: str, message: str = "Heartbeat lost"):
        self.node_ip = node_ip
        super().__init__(f"Node {node_ip}: {message}")


class NodeTimeoutError(Exception):
    """Raised when a specific node operation times out."""
    pass


class NodeReassignError(Exception):
    """Raised when task re-assignment fails."""
    pass


@dataclass
class NodeDiscoveryResult:
    """Result of a node discovery operation."""
    discovered_nodes: List[PhysicalNode] = field(default_factory=list)
    failed_nodes: List[Dict[str, Any]] = field(default_factory=list)
    success_rate: float = 0.0

    def __post_init__(self):
        total = len(self.discovered_nodes) + len(self.failed_nodes)
        if total > 0:
            self.success_rate = len(self.discovered_nodes) / total


class NodeManager:
    """
    Manages SSH connections to physical nodes in the mesh network.
    Handles discovery, heartbeat monitoring, and task re-assignment logic.
    """

    def __init__(self, ssh_timeout: float = 2.0, heartbeat_interval: float = 5.0):
        """
        Initialize the NodeManager.

        Args:
            ssh_timeout: Timeout for SSH connections and commands (seconds).
            heartbeat_interval: Interval between heartbeat checks (seconds).
        """
        self.ssh_timeout = ssh_timeout
        self.heartbeat_interval = heartbeat_interval
        self._active_connections: Dict[str, SSHClient] = {}
        self._node_metadata: Dict[str, Dict[str, Any]] = {}
        self._logger = get_logger(__name__)

    def discover_nodes(self, ip_list: List[str], credentials: Optional[Dict[str, Any]] = None) -> NodeDiscoveryResult:
        """
        Attempt to connect to a list of IP addresses to discover active nodes.

        Args:
            ip_list: List of IP addresses to probe.
            credentials: Optional dict containing 'username', 'password', or 'key_filename'.

        Returns:
            NodeDiscoveryResult containing discovered nodes and failures.

        Raises:
            NodeDiscoveryError: If ALL nodes in the list are unreachable.
        """
        discovered = []
        failed = []

        if not ip_list:
            self._logger.warning("Empty IP list provided for discovery.")
            return NodeDiscoveryResult(discovered_nodes=[], failed_nodes=[], success_rate=0.0)

        for ip in ip_list:
            try:
                node = self._connect_and_verify(ip, credentials)
                if node:
                    discovered.append(node)
                    self._active_connections[ip] = node.client
                    self._node_metadata[ip] = {
                        "status": NodeStatus.ACTIVE,
                        "last_seen": datetime.now(),
                        "connection_established": datetime.now()
                    }
                    self._logger.info(f"Discovered active node: {ip}")
                else:
                    failed.append({"ip": ip, "reason": "Connection failed"})
                    self._logger.warning(f"Failed to discover node: {ip}")
            except (AuthenticationException, SocketTimeout, SSHException, OSError) as e:
                failed.append({"ip": ip, "reason": str(e)})
                self._logger.error(f"Discovery failed for {ip}: {e}", exc_info=True)
            except Exception as e:
                # Catch-all for unexpected errors during discovery
                failed.append({"ip": ip, "reason": f"Unexpected error: {e}"})
                self._logger.error(f"Unexpected error during discovery of {ip}: {e}", exc_info=True)

        # Fail Loudly: If ALL nodes are unreachable, raise NodeDiscoveryError
        if len(discovered) == 0 and len(failed) > 0:
            raise NodeDiscoveryError(
                f"Node discovery failed for all {len(failed)} nodes. "
                f"Reasons: {[f['reason'] for f in failed]}"
            )

        return NodeDiscoveryResult(
            discovered_nodes=discovered,
            failed_nodes=failed,
            success_rate=1.0 if len(discovered) + len(failed) == 0 else len(discovered) / (len(discovered) + len(failed))
        )

    def _connect_and_verify(self, ip: str, credentials: Optional[Dict[str, Any]] = None) -> Optional[PhysicalNode]:
        """
        Establish SSH connection and verify basic connectivity.

        Args:
            ip: Target IP address.
            credentials: Auth credentials.

        Returns:
            PhysicalNode object if successful, None otherwise.
        """
        client = SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Default credentials if not provided (for testing/mock scenarios if needed)
        # In production, these should be injected securely
        username = credentials.get("username", "root") if credentials else "root"
        password = credentials.get("password") if credentials else None
        key_filename = credentials.get("key_filename") if credentials else None

        try:
            client.connect(
                hostname=ip,
                username=username,
                password=password,
                key_filename=key_filename,
                timeout=self.ssh_timeout,
                allow_agent=False,
                look_for_keys=False if password else True,
                banner_timeout=self.ssh_timeout
            )
            # Verify connectivity with a simple ping command
            stdin, stdout, stderr = client.exec_command("echo 'pong'", timeout=self.ssh_timeout)
            exit_code = stdout.channel.recv_exit_status()
            
            if exit_code != 0:
                self._logger.warning(f"Node {ip} returned non-zero exit code on verification.")
                return None

            return PhysicalNode(
                ip_address=ip,
                status=NodeStatus.ACTIVE,
                last_heartbeat=datetime.now(),
                client=client # Store client for later use
            )
        except AuthenticationException:
            self._logger.error(f"Authentication failed for {ip}")
            raise
        except SocketTimeout:
            self._logger.error(f"Connection timeout for {ip}")
            raise
        except Exception:
            client.close()
            raise

    def ping_node(self, ip: str, timeout: float = 2.0) -> bool:
        """
        Check if a specific node is responsive via SSH.

        Args:
            ip: Target IP address.
            timeout: Timeout for the ping operation.

        Returns:
            True if node responds, False otherwise.
        """
        client = self._active_connections.get(ip)
        if not client:
            # Attempt to reconnect if connection lost
            try:
                # Reconnection logic would go here, but for ping we assume active connection
                # or that the caller handles reconnection via discover_nodes
                return False
            except Exception:
                return False

        try:
            stdin, stdout, stderr = client.exec_command("echo 'alive'", timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            return exit_code == 0
        except (SSHException, socket.timeout, OSError):
            self._logger.warning(f"Node {ip} ping failed (connection lost or timeout)")
            return False

    def send_heartbeat(self, ip: str) -> bool:
        """
        Send a heartbeat ping to a node and update metadata.

        Args:
            ip: Target IP address.

        Returns:
            True if heartbeat successful, False otherwise.
        """
        if self.ping_node(ip, timeout=self.ssh_timeout):
            if ip in self._node_metadata:
                self._node_metadata[ip]["last_seen"] = datetime.now()
            return True
        return False

    def reassign_task(self, task_id: str, new_ip: str, task_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Re-assign a task chunk to a new node IP.

        This integrates re-queue logic for dropout events.

        Args:
            task_id: Unique identifier for the task.
            new_ip: IP address of the new target node.
            task_data: Optional data payload for the task.

        Returns:
            True if re-assignment successful.

        Raises:
            NodeReassignError: If the new node is unreachable or assignment fails.
        """
        if new_ip not in self._active_connections:
            # Attempt to discover/reconnect to the new node
            try:
                self.discover_nodes([new_ip])
            except NodeDiscoveryError:
                raise NodeReassignError(f"Cannot reassign to {new_ip}: Node unreachable.")

        client = self._active_connections.get(new_ip)
        if not client:
            raise NodeReassignError(f"Active connection not found for {new_ip}.")

        try:
            # Construct the command to re-queue the task
            # In a real scenario, this would send the task payload to the worker
            cmd = f"echo 'Re-queue task {task_id}'"
            if task_data:
                # Serialize task data if needed
                import json
                cmd += f" && echo '{json.dumps(task_data)}'"

            stdin, stdout, stderr = client.exec_command(cmd, timeout=self.ssh_timeout)
            exit_code = stdout.channel.recv_exit_status()

            if exit_code == 0:
                self._logger.info(f"Task {task_id} successfully re-assigned to {new_ip}")
                return True
            else:
                error_msg = stderr.read().decode()
                raise NodeReassignError(f"Task re-assignment failed on {new_ip}: {error_msg}")

        except (SSHException, SocketTimeout, OSError) as e:
            self._logger.error(f"Failed to reassign task {task_id} to {new_ip}: {e}")
            raise NodeReassignError(f"Re-assignment failed: {e}")

    def monitor_heartbeats(self, node_ips: List[str], callback_on_loss: Optional[Callable[[str], None]] = None) -> None:
        """
        Continuous monitoring loop for node heartbeats.
        
        This is intended to be run in a separate thread or loop.
        It preserves try/except for runtime heartbeat monitoring to detect dropouts.

        Args:
            node_ips: List of IPs to monitor.
            callback_on_loss: Function to call when a heartbeat is lost.
        """
        self._logger.info(f"Starting heartbeat monitor for {len(node_ips)} nodes")
        while True:
            for ip in node_ips:
                try:
                    if not self.send_heartbeat(ip):
                        self._logger.warning(f"Heartbeat lost for {ip}")
                        if ip in self._node_metadata:
                            self._node_metadata[ip]["status"] = NodeStatus.DROPPED
                        if callback_on_loss:
                            callback_on_loss(ip)
                        # Trigger re-assignment logic here if integrated
                except Exception as e:
                    self._logger.error(f"Error monitoring heartbeat for {ip}: {e}")
            
            time.sleep(self.heartbeat_interval)

    def close_all_connections(self) -> None:
        """Close all active SSH connections."""
        for ip, client in self._active_connections.items():
            try:
                client.close()
                self._logger.info(f"Closed connection to {ip}")
            except Exception as e:
                self._logger.warning(f"Error closing connection to {ip}: {e}")
        self._active_connections.clear()


def create_node_manager(ssh_timeout: float = 2.0, heartbeat_interval: float = 5.0) -> NodeManager:
    """Factory function to create a NodeManager instance."""
    return NodeManager(ssh_timeout=ssh_timeout, heartbeat_interval=heartbeat_interval)


def main() -> None:
    """
    CLI entry point for testing node discovery and management.
    Reads node list from config or command line arguments.
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Node Manager CLI")
    parser.add_argument("--ips", type=str, required=True, help="Comma-separated list of IPs")
    parser.add_argument("--timeout", type=float, default=2.0, help="SSH timeout in seconds")
    args = parser.parse_args()

    ip_list = [ip.strip() for ip in args.ips.split(",") if ip.strip()]
    
    manager = create_node_manager(ssh_timeout=args.timeout)

    try:
        result = manager.discover_nodes(ip_list)
        print(json.dumps({
            "discovered": [n.ip_address for n in result.discovered_nodes],
            "failed": result.failed_nodes,
            "success_rate": result.success_rate
        }, indent=2))
    except NodeDiscoveryError as e:
        print(json.dumps({"error": str(e)}, indent=2))
        exit(1)
    finally:
        manager.close_all_connections()


if __name__ == "__main__":
    main()
