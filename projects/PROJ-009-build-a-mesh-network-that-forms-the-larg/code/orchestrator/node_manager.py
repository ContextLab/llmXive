"""
Node Manager for Mesh Network Supercomputer.

Handles SSH connections, heartbeat pings, device discovery, and task reassignment.
Implements robust error handling and recovery logic for node dropouts.
"""
from __future__ import annotations

import logging
import socket
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Callable, Any

# Import SSHClient directly so that tests can patch orchestrator.node_manager.SSHClient
from paramiko import SSHClient, AutoAddPolicy, SSHException
from paramiko.ssh_exception import AuthenticationException, SocketTimeout

from orchestrator.logger import get_logger
from orchestrator.config import get_config

# ----------------------------------------------------------------------
# Custom Exceptions
# ----------------------------------------------------------------------
class NodeDiscoveryError(Exception):
    """Raised when node discovery fails completely (all nodes unreachable)."""

    def __init__(self, message: str, failed_nodes: Optional[List[str]] = None):
        super().__init__(message)
        self.message = message
        self.failed_nodes = failed_nodes or []


class NodeHeartbeatLost(Exception):
    """Raised when a runtime heartbeat is lost for a specific node."""
    pass


class NodeTimeoutError(Exception):
    """Raised when a specific node operation times out."""
    pass


class NodeReassignError(Exception):
    """Raised when task reassignment fails."""
    pass

# ----------------------------------------------------------------------
# Data Classes
# ----------------------------------------------------------------------
@dataclass
class NodeDiscoveryResult:
    """Result of a node discovery operation (legacy, retained for compatibility)."""
    discovered_nodes: List[str] = field(default_factory=list)
    failed_nodes: List[str] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now())


@dataclass
class NodeState:
    """Tracks the runtime state of a node."""
    ip: str
    status: str = "unknown"  # unknown, active, heartbeat_lost, offline
    last_heartbeat: Optional[datetime] = None
    task_queue: List[str] = field(default_factory=list)
    current_task: Optional[str] = None

# ----------------------------------------------------------------------
# Core Manager
# ----------------------------------------------------------------------
class NodeManager:
    """
    Manages SSH connections to physical nodes in the mesh network.
    Handles discovery, heartbeat monitoring, and task reassignment.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, logger_name: str = "node_manager"):
        """
        Parameters
        ----------
        config : dict, optional
            Configuration dictionary used in tests. Keys may include:
            - ``ssh_timeout`` (seconds, default 5)
            - ``ssh_port`` (default 22)
            - ``username`` (default from global config)
            - ``password`` (optional)
        logger_name : str
            Name of the logger instance.
        """
        self.logger = get_logger(logger_name)

        # Merge test‑provided config with the global configuration.
        global_cfg = get_config()
        self.ssh_timeout: int = 5
        self.ssh_port: int = 22
        self.ssh_username: Optional[str] = getattr(global_cfg, "ssh_username", None)
        self.ssh_password: Optional[str] = getattr(global_cfg, "ssh_password", None)

        if config:
            self.ssh_timeout = config.get("ssh_timeout", self.ssh_timeout)
            self.ssh_port = config.get("ssh_port", self.ssh_port)
            self.ssh_username = config.get("username", self.ssh_username)
            self.ssh_password = config.get("password", self.ssh_password)

        self.nodes: Dict[str, NodeState] = {}
        self.ssh_clients: Dict[str, SSHClient] = {}
        self.heartbeat_thread: Optional[threading.Thread] = None
        self._stop_heartbeat = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_ssh_client(self, ip: str) -> SSHClient:
        """Creates or retrieves an SSH client for a specific IP."""
        if ip not in self.ssh_clients:
            client = SSHClient()
            client.set_missing_host_key_policy(AutoAddPolicy())
            self.ssh_clients[ip] = client
        return self.ssh_clients[ip]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def discover_nodes(self, ip_list: List[str]) -> List[Dict[str, Any]]:
        """
        Discover nodes by attempting SSH connections.

        Returns a list of dictionaries, each containing:
            - ``ip`` (str)
            - ``status`` (``online`` or ``offline``)
            - ``hostname`` (str; falls back to IP if unavailable)

        Raises
        ------
        NodeDiscoveryError
            If *all* supplied IPs are unreachable.
        """
        if not ip_list:
            return []

        results: List[Dict[str, Any]] = []
        failed_nodes: List[str] = []

        self.logger.info(f"Starting node discovery for {len(ip_list)} candidates.")

        for ip in ip_list:
            node_record: Dict[str, Any] = {"ip": ip, "status": "offline", "hostname": ip}
            try:
                client = self._get_ssh_client(ip)
                client.connect(
                    hostname=ip,
                    port=self.ssh_port,
                    username=self.ssh_username,
                    password=self.ssh_password,
                    timeout=self.ssh_timeout,
                    allow_agent=False,
                    look_for_keys=False,
                )
                # Connection succeeded – attempt to fetch hostname
                try:
                    stdin, stdout, stderr = client.exec_command("hostname")
                    raw = stdout.read()
                    hostname = raw.decode().strip() if raw else ip
                except Exception as e:
                    self.logger.warning(f"Hostname command failed on {ip}: {e}")
                    hostname = ip

                node_record["status"] = "online"
                node_record["hostname"] = hostname
                self.nodes[ip] = NodeState(ip=ip, status="active", last_heartbeat=datetime.now())
                self.logger.info(f"Node discovered: {ip} ({hostname})")
            except AuthenticationException:
                err = "Authentication failed"
                self.logger.error(f"Node {ip}: {err}")
                failed_nodes.append(ip)
                node_record["status"] = "offline"
                node_record["hostname"] = ip
            except SocketTimeout:
                err = "Connection timeout"
                self.logger.error(f"Node {ip}: {err}")
                failed_nodes.append(ip)
            except SSHException as e:
                err = f"SSH error: {e}"
                self.logger.error(f"Node {ip}: {err}")
                failed_nodes.append(ip)
            except Exception as e:
                err = f"Unexpected error: {e}"
                self.logger.error(f"Node {ip}: {err}")
                failed_nodes.append(ip)

            results.append(node_record)

        if len(failed_nodes) == len(ip_list):
            raise NodeDiscoveryError(
                f"Discovery failed for all {len(ip_list)} nodes.",
                failed_nodes=failed_nodes,
            )

        self.logger.info(f"Discovery complete. {len([r for r in results if r['status']=='online'])} online, {len(failed_nodes)} offline.")
        return results

    def ping_node(self, ip: str, timeout: float = 2.0) -> bool:
        """
        Verify connectivity to a node by executing a trivial command.

        Returns ``True`` on success, ``False`` otherwise.
        """
        if ip not in self.nodes:
            self.logger.warning(f"Cannot ping unknown node: {ip}")
            return False

        try:
            client = self._get_ssh_client(ip)
            stdin, stdout, stderr = client.exec_command('echo "ping"', timeout=timeout)
            stdout.channel.recv_exit_status()
            self.nodes[ip].last_heartbeat = datetime.now()
            self.nodes[ip].status = "active"
            return True
        except (SocketTimeout, SSHException) as e:
            self.logger.warning(f"Node {ip} ping failed: {e}")
            self.nodes[ip].status = "heartbeat_lost"
            return False

    def reassign_task(self, task_id: str, new_ip: str) -> bool:
        """
        Reassign a task from a dropped node to a new node.

        Returns ``True`` on success; raises :class:`NodeReassignError` on failure.
        """
        if new_ip not in self.nodes:
            raise NodeReassignError(f"Target node {new_ip} is not in the active node list.")

        if self.nodes[new_ip].status != "active":
            raise NodeReassignError(f"Target node {new_ip} is not active (status: {self.nodes[new_ip].status}).")

        try:
            self.nodes[new_ip].task_queue.append(task_id)
            self.logger.info(f"Task {task_id} reassigned to node {new_ip}.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reassign task {task_id} to {new_ip}: {e}")
            raise NodeReassignError(f"Reassignment failed: {e}")

    def start_heartbeat_monitoring(self, interval: float = 5.0, callback: Optional[Callable[[str], None]] = None):
        """
        Start a background thread that periodically pings all active nodes.
        If a node fails to respond, its status is set to ``heartbeat_lost`` and
        an optional ``callback`` is invoked with the node IP.
        """
        def _monitor_loop():
            while not self._stop_heartbeat:
                for ip, state in list(self.nodes.items()):
                    if state.status == "active":
                        if not self.ping_node(ip):
                            self.logger.warning(f"Heartbeat lost for node {ip}. Triggering recovery.")
                            state.status = "heartbeat_lost"

                            if state.current_task:
                                task_to_reassign = state.current_task
                                self.logger.info(f"Queuing task {task_to_reassign} for reassignment due to node drop.")
                                if callback:
                                    callback(ip)

                                state.current_task = None
                time.sleep(interval)

        self._stop_heartbeat = False
        self.heartbeat_thread = threading.Thread(target=_monitor_loop, daemon=True)
        self.heartbeat_thread.start()
        self.logger.info("Heartbeat monitoring started.")

    def stop_heartbeat_monitoring(self):
        """Stop the background heartbeat monitoring thread."""
        self._stop_heartbeat = True
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2.0)
            self.logger.info("Heartbeat monitoring stopped.")

    def get_active_nodes(self) -> List[str]:
        """Return a list of IPs for nodes whose status is ``active``."""
        return [ip for ip, state in self.nodes.items() if state.status == "active"]

# ----------------------------------------------------------------------
# Factory
# ----------------------------------------------------------------------
def create_node_manager(config: Optional[Dict[str, Any]] = None) -> NodeManager:
    """Factory function to create a configured ``NodeManager``."""
    return NodeManager(config)

# ----------------------------------------------------------------------
# CLI entry point (for manual testing)
# ----------------------------------------------------------------------
def main():
    """Entry point for testing/running the node manager directly."""
    import argparse

    parser = argparse.ArgumentParser(description="Node Manager Discovery Test")
    parser.add_argument("--ips", nargs="+", required=True, help="List of node IPs to discover")
    parser.add_argument("--timeout", type=float, default=2.0, help="Connection timeout")
    args = parser.parse_args()

    manager = create_node_manager()
    try:
        results = manager.discover_nodes(args.ips)
        print("Discovered:", results)
    except NodeDiscoveryError as e:
        print(f"CRITICAL: {e.message}")
        exit(1)

    if results:
        first_node = results[0]["ip"]
        if manager.ping_node(first_node, timeout=args.timeout):
            print(f"Successfully pinged {first_node}")
        else:
            print(f"Failed to ping {first_node}")

if __name__ == "__main__":
    main()