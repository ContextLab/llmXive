"""
Node Manager for Mesh Network Supercomputer.

Handles SSH connections, heartbeat pings, device discovery, and task reassignment.
Implements robust error handling and recovery logic for node dropouts.
"""
from __future__ import annotations

import logging
import socket
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any, Callable
from enum import Enum

import paramiko
from paramiko.ssh_exception import AuthenticationException, SocketTimeout, SSHException

from orchestrator.logger import get_logger
from orchestrator.config import get_config

# Custom Exceptions
class NodeDiscoveryError(Exception):
    """Raised when node discovery fails completely (all nodes unreachable)."""
    pass

class NodeHeartbeatLost(Exception):
    """Raised when a runtime heartbeat is lost for a specific node."""
    pass

class NodeTimeoutError(Exception):
    """Raised when a specific node operation times out."""
    pass

class NodeReassignError(Exception):
    """Raised when task reassignment fails."""
    pass

@dataclass
class NodeDiscoveryResult:
    """Result of a node discovery operation."""
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

class NodeManager:
    """
    Manages SSH connections to physical nodes in the mesh network.
    Handles discovery, heartbeat monitoring, and task reassignment.
    """

    def __init__(self, logger_name: str = "node_manager"):
        self.logger = get_logger(logger_name)
        self.config = get_config()
        self.nodes: Dict[str, NodeState] = {}
        self.ssh_clients: Dict[str, paramiko.SSHClient] = {}
        self.heartbeat_thread: Optional[threading.Thread] = None
        self._stop_heartbeat = False

    def _get_ssh_client(self, ip: str) -> paramiko.SSHClient:
        """Creates or retrieves an SSH client for a specific IP."""
        if ip not in self.ssh_clients:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_clients[ip] = client
        return self.ssh_clients[ip]

    def discover_nodes(self, ip_list: List[str]) -> NodeDiscoveryResult:
        """
        Discovers active nodes by attempting SSH connections.

        Args:
            ip_list: List of IP addresses to probe.

        Returns:
            NodeDiscoveryResult containing discovered and failed nodes.

        Raises:
            NodeDiscoveryError: If ALL nodes in the list are unreachable.
        """
        result = NodeDiscoveryResult()
        unreachable_count = 0

        self.logger.info(f"Starting node discovery for {len(ip_list)} candidates.")

        for ip in ip_list:
            try:
                client = self._get_ssh_client(ip)
                # Attempt connection with strict timeout
                client.connect(
                    hostname=ip,
                    username=self.config.ssh_username,
                    password=self.config.ssh_password,
                    timeout=self.config.node_timeout, # Default 2s per spec
                    allow_agent=False,
                    look_for_keys=False
                )
                result.discovered_nodes.append(ip)
                self.nodes[ip] = NodeState(ip=ip, status="active", last_heartbeat=datetime.now())
                self.logger.info(f"Node discovered: {ip}")
            except AuthenticationException:
                error_msg = "Authentication failed"
                self.logger.error(f"Node {ip}: {error_msg}")
                result.failed_nodes.append(ip)
                result.errors[ip] = error_msg
                unreachable_count += 1
            except SocketTimeout:
                error_msg = "Connection timeout"
                self.logger.error(f"Node {ip}: {error_msg}")
                result.failed_nodes.append(ip)
                result.errors[ip] = error_msg
                unreachable_count += 1
            except SSHException as e:
                error_msg = f"SSH error: {str(e)}"
                self.logger.error(f"Node {ip}: {error_msg}")
                result.failed_nodes.append(ip)
                result.errors[ip] = error_msg
                unreachable_count += 1
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                self.logger.error(f"Node {ip}: {error_msg}")
                result.failed_nodes.append(ip)
                result.errors[ip] = error_msg
                unreachable_count += 1

        # Fail Loudly: If all nodes are unreachable
        if unreachable_count == len(ip_list):
            raise NodeDiscoveryError(
                f"Critical Failure: All {len(ip_list)} nodes are unreachable. "
                f"Cannot proceed with orchestration."
            )

        self.logger.info(f"Discovery complete. Found {len(result.discovered_nodes)} active nodes.")
        return result

    def ping_node(self, ip: str, timeout: float = 2.0) -> bool:
        """
        Pings a specific node to verify connectivity.

        Args:
            ip: Target IP address.
            timeout: Timeout in seconds.

        Returns:
            True if successful, False otherwise.
        """
        if ip not in self.nodes:
            self.logger.warning(f"Cannot ping unknown node: {ip}")
            return False

        try:
            client = self._get_ssh_client(ip)
            # Execute a trivial command to verify connection
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
        Reassigns a task from a dropped node to a new node.

        Args:
            task_id: The ID of the task to reassign.
            new_ip: The IP of the new target node.

        Returns:
            True if reassignment was successful.

        Raises:
            NodeReassignError: If the new node is unavailable or reassignment fails.
        """
        if new_ip not in self.nodes:
            raise NodeReassignError(f"Target node {new_ip} is not in the active node list.")

        if self.nodes[new_ip].status != "active":
            raise NodeReassignError(f"Target node {new_ip} is not active (status: {self.nodes[new_ip].status}).")

        try:
            # Logic to update the scheduler state would happen here.
            # For this module, we mark the task as queued for the new node.
            self.nodes[new_ip].task_queue.append(task_id)
            self.logger.info(f"Task {task_id} reassigned to node {new_ip}.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reassign task {task_id} to {new_ip}: {e}")
            raise NodeReassignError(f"Reassignment failed: {e}")

    def start_heartbeat_monitoring(self, interval: float = 5.0, callback: Optional[Callable[[str], None]] = None):
        """
        Starts a background thread to monitor heartbeats.
        Handles runtime dropouts and triggers re-queue logic.

        Args:
            interval: Time between heartbeat checks.
            callback: Function to call when a node drops (receives IP).
        """
        import threading

        def _monitor_loop():
            while not self._stop_heartbeat:
                for ip, state in list(self.nodes.items()):
                    if state.status == "active":
                        if not self.ping_node(ip):
                            self.logger.warning(f"Heartbeat lost for node {ip}. Triggering recovery.")
                            state.status = "heartbeat_lost"
                            
                            # Re-queue logic: If the node has a current task, mark it for reassignment
                            if state.current_task:
                                task_to_reassign = state.current_task
                                self.logger.info(f"Queuing task {task_to_reassign} for reassignment due to node drop.")
                                # Trigger callback if provided (e.g., to update scheduler)
                                if callback:
                                    callback(ip)
                            
                            # Reset current task to allow reassignment
                            state.current_task = None
                
                time.sleep(interval)

        self._stop_heartbeat = False
        self.heartbeat_thread = threading.Thread(target=_monitor_loop, daemon=True)
        self.heartbeat_thread.start()
        self.logger.info("Heartbeat monitoring started.")

    def stop_heartbeat_monitoring(self):
        """Stops the background heartbeat monitoring thread."""
        self._stop_heartbeat = True
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2.0)
            self.logger.info("Heartbeat monitoring stopped.")

    def get_active_nodes(self) -> List[str]:
        """Returns a list of currently active node IPs."""
        return [ip for ip, state in self.nodes.items() if state.status == "active"]

def create_node_manager() -> NodeManager:
    """Factory function to create a configured NodeManager."""
    return NodeManager()

def main():
    """Entry point for testing/running the node manager directly."""
    import argparse
    parser = argparse.ArgumentParser(description="Node Manager Discovery Test")
    parser.add_argument("--ips", nargs="+", required=True, help="List of node IPs to discover")
    parser.add_argument("--timeout", type=float, default=2.0, help="Connection timeout")
    args = parser.parse_args()

    manager = create_node_manager()
    
    try:
        result = manager.discover_nodes(args.ips)
        print(f"Discovered: {result.discovered_nodes}")
        print(f"Failed: {result.failed_nodes}")
        
        if result.discovered_nodes:
            # Test heartbeat on first discovered node
            first_node = result.discovered_nodes[0]
            if manager.ping_node(first_node, timeout=args.timeout):
                print(f"Successfully pinged {first_node}")
            else:
                print(f"Failed to ping {first_node}")
    except NodeDiscoveryError as e:
        print(f"CRITICAL: {e}")
        exit(1)

if __name__ == "__main__":
    main()
