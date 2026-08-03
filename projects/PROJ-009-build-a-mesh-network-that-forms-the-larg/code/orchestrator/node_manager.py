"""
Node Manager for Mesh Network Supercomputer.
Handles SSH connections, heartbeat pings, and device discovery.
"""
import logging
import socket
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

import paramiko

from orchestrator.models import PhysicalNode, NodeStatus
from orchestrator.logger import get_logger, heartbeat
from orchestrator.config import get_config

# Ensure required dependencies are available
try:
    import paramiko
except ImportError:
    raise ImportError("paramiko is required for SSH connections. Install via: pip install paramiko")

@dataclass
class NodeDiscoveryResult:
    """Result of a node discovery operation."""
    discovered_nodes: List[PhysicalNode]
    failed_nodes: List[Dict[str, Any]]
    timestamp: datetime
    success_count: int
    failure_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "discovered_nodes": [node.to_dict() for node in self.discovered_nodes],
            "failed_nodes": self.failed_nodes,
            "timestamp": self.timestamp.isoformat(),
            "success_count": self.success_count,
            "failure_count": self.failure_count
        }

class NodeManager:
    """
    Manages SSH connections to physical nodes in the mesh network.
    Handles discovery, heartbeat monitoring, and connection lifecycle.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the NodeManager.

        Args:
            config_path: Optional path to config file. If None, uses default config.
        """
        self.logger = get_logger(__name__)
        self.config = get_config(config_path)
        self.active_connections: Dict[str, paramiko.SSHClient] = {}
        self.node_states: Dict[str, NodeStatus] = {}

    def discover_nodes(self) -> NodeDiscoveryResult:
        """
        Discover and validate nodes from the configuration.

        Returns:
            NodeDiscoveryResult containing discovered and failed nodes.
        """
        self.logger.info("Starting node discovery process")
        discovered = []
        failed = []
        timestamp = datetime.now()

        node_configs = self.config.get("nodes", [])
        if not node_configs:
            self.logger.warning("No nodes found in configuration")
            return NodeDiscoveryResult(
                discovered_nodes=[],
                failed_nodes=[],
                timestamp=timestamp,
                success_count=0,
                failure_count=0
            )

        for node_cfg in node_configs:
            node_id = node_cfg.get("id")
            if not node_id:
                self.logger.error("Node configuration missing 'id' field")
                failed.append({"id": node_id, "reason": "Missing ID field"})
                continue

            try:
                # Validate connectivity and create PhysicalNode object
                node = self._validate_and_create_node(node_cfg)
                discovered.append(node)
                self.node_states[node_id] = NodeStatus.ONLINE
                self.logger.info(f"Discovered node: {node_id} at {node.host}:{node.port}")
            except Exception as e:
                error_msg = str(e)
                self.logger.error(f"Failed to discover node {node_id}: {error_msg}")
                failed.append({"id": node_id, "reason": error_msg})
                self.node_states[node_id] = NodeStatus.OFFLINE

        result = NodeDiscoveryResult(
            discovered_nodes=discovered,
            failed_nodes=failed,
            timestamp=timestamp,
            success_count=len(discovered),
            failure_count=len(failed)
        )

        self.logger.info(
            f"Discovery complete: {result.success_count} successful, "
            f"{result.failure_count} failed"
        )
        return result

    def _validate_and_create_node(self, node_cfg: Dict[str, Any]) -> PhysicalNode:
        """
        Validate a node configuration and create a PhysicalNode object.

        Args:
            node_cfg: Dictionary containing node configuration.

        Returns:
            PhysicalNode object if validation succeeds.

        Raises:
            ConnectionRefusedError: If SSH connection fails.
            ValueError: If configuration is invalid.
        """
        node_id = node_cfg.get("id")
        host = node_cfg.get("host")
        port = node_cfg.get("port", 22)
        username = node_cfg.get("username")
        key_path = node_cfg.get("key_path")

        if not all([node_id, host, username]):
            raise ValueError(f"Invalid node config for {node_id}: missing required fields")

        # Attempt SSH connection to validate
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            if key_path:
                key = paramiko.RSAKey.from_private_key_file(key_path)
                client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    pkey=key,
                    timeout=5
                )
            else:
                # Fallback to password if no key (not recommended for production)
                password = node_cfg.get("password")
                if not password:
                    raise ValueError(f"No authentication method for node {node_id}")
                client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    password=password,
                    timeout=5
                )

            # Execute a simple command to verify shell access
            stdin, stdout, stderr = client.exec_command("echo 'connection_ok'")
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode().strip()

            if exit_status != 0 or "connection_ok" not in output:
                raise ConnectionRefusedError(f"Node {node_id} shell access failed")

            # Store connection for later use
            self.active_connections[node_id] = client

            # Create PhysicalNode object
            return PhysicalNode(
                id=node_id,
                host=host,
                port=port,
                username=username,
                status=NodeStatus.ONLINE,
                last_heartbeat=datetime.now(),
                cpu_cores=node_cfg.get("cpu_cores", 4),
                ram_gb=node_cfg.get("ram_gb", 8),
                storage_gb=node_cfg.get("storage_gb", 100)
            )

        except (socket.timeout, paramiko.AuthenticationException, 
                paramiko.SSHException, ConnectionRefusedError) as e:
            if node_id in self.active_connections:
                del self.active_connections[node_id]
            raise e
        finally:
            # Do not close the connection here; it will be used for commands
            pass

    def ping_node(self, node_id: str) -> bool:
        """
        Send a heartbeat ping to a specific node.

        Args:
            node_id: The ID of the node to ping.

        Returns:
            True if node responds, False otherwise.
        """
        if node_id not in self.active_connections:
            self.logger.warning(f"Node {node_id} not in active connections")
            return False

        client = self.active_connections.get(node_id)
        if not client:
            return False

        try:
            stdin, stdout, stderr = client.exec_command("echo 'ping'")
            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                self.node_states[node_id] = NodeStatus.ONLINE
                heartbeat(node_id, "ping_success")
                return True
            else:
                self.node_states[node_id] = NodeStatus.UNRESPONSIVE
                heartbeat(node_id, "ping_failed")
                return False
        except Exception as e:
            self.logger.error(f"Ping failed for node {node_id}: {e}")
            self.node_states[node_id] = NodeStatus.OFFLINE
            heartbeat(node_id, "ping_exception", str(e))
            return False

    def check_heartbeats(self) -> Dict[str, bool]:
        """
        Check heartbeats for all active nodes.

        Returns:
            Dictionary mapping node_id to ping status.
        """
        results = {}
        for node_id in list(self.active_connections.keys()):
            results[node_id] = self.ping_node(node_id)
        return results

    def disconnect_node(self, node_id: str) -> bool:
        """
        Gracefully disconnect from a specific node.

        Args:
            node_id: The ID of the node to disconnect.

        Returns:
            True if disconnected successfully, False otherwise.
        """
        if node_id in self.active_connections:
            try:
                self.active_connections[node_id].close()
                del self.active_connections[node_id]
                self.logger.info(f"Disconnected from node {node_id}")
                return True
            except Exception as e:
                self.logger.error(f"Error disconnecting node {node_id}: {e}")
                return False
        return False

    def disconnect_all(self) -> None:
        """Disconnect from all active nodes."""
        for node_id in list(self.active_connections.keys()):
            self.disconnect_node(node_id)
        self.logger.info("Disconnected from all nodes")

    def execute_command(self, node_id: str, command: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a command on a specific node.

        Args:
            node_id: The ID of the node.
            command: The shell command to execute.
            timeout: Command execution timeout in seconds.

        Returns:
            Dictionary with 'exit_code', 'stdout', 'stderr'.

        Raises:
            ValueError: If node is not connected.
            TimeoutError: If command exceeds timeout.
        """
        if node_id not in self.active_connections:
            raise ValueError(f"Node {node_id} is not connected")

        client = self.active_connections[node_id]
        try:
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            exit_status = stdout.channel.recv_exit_status()
            
            # Read output
            stdout_data = stdout.read().decode(errors='replace')
            stderr_data = stderr.read().decode(errors='replace')

            return {
                "exit_code": exit_status,
                "stdout": stdout_data,
                "stderr": stderr_data
            }
        except socket.timeout:
            raise TimeoutError(f"Command on node {node_id} timed out after {timeout}s")
        except Exception as e:
            self.logger.error(f"Command execution failed on {node_id}: {e}")
            raise

    def get_node_status(self, node_id: str) -> Optional[NodeStatus]:
        """Get the current status of a node."""
        return self.node_states.get(node_id)

    def get_all_statuses(self) -> Dict[str, NodeStatus]:
        """Get status of all known nodes."""
        return self.node_states.copy()

    def detect_dropout_events(self, threshold_seconds: int = 60) -> List[Dict[str, Any]]:
        """
        Detect nodes that have entered a dropout state (sleep/lost power).
        
        Args:
            threshold_seconds: Time in seconds after which a node is considered dropped.

        Returns:
            List of dropout events with node_id, timestamp, and reason.
        """
        events = []
        current_time = datetime.now()

        for node_id, status in self.node_states.items():
            if status == NodeStatus.OFFLINE or status == NodeStatus.UNRESPONSIVE:
                # Check if this is a recent change or a persistent state
                # For now, we assume if it's offline, it's a dropout
                events.append({
                    "node_id": node_id,
                    "timestamp": current_time.isoformat(),
                    "reason": f"Node {node_id} is {status.value}",
                    "duration_seconds": threshold_seconds
                })
                self.logger.warning(f"Dropout event detected for node {node_id}")

        return events

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure all connections are closed."""
        self.disconnect_all()
        return False