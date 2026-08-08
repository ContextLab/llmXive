"""
Node Manager for Mesh Network Supercomputer.
Handles SSH connections, heartbeat pings, device discovery, and task reassignment.
"""

from __future__ import annotations

import logging
import socket
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

try:
    import paramiko
except ImportError:
    raise ImportError(
        "paramiko is required for SSH connections. Install it via: pip install paramiko"
    )

from orchestrator.logger import get_logger
from orchestrator.config import get_config
from orchestrator.models import PhysicalNode, NodeStatus

logger = get_logger(__name__)

class NodeDiscoveryError(Exception):
    """Raised when node discovery fails completely (all nodes unreachable)."""
    pass


class NodeHeartbeatLost(Exception):
    """Raised when a specific node loses heartbeat during runtime."""
    pass

class NodeTimeoutError(Exception):
    """Raised when a specific operation on a node times out."""
    pass


class NodeReassignError(Exception):
    """Raised when task reassignment fails."""
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
        else:
            self.success_rate = 0.0

class NodeManager:
    """
    Manages SSH connections to physical nodes in the mesh network.
    Handles discovery, heartbeat monitoring, and task reassignment.
    """

    def __init__(self, ssh_timeout: float = 2.0):
        self.ssh_timeout = ssh_timeout
        self._active_connections: Dict[str, paramiko.SSHClient] = {}
        self._node_states: Dict[str, NodeStatus] = {}
        self.logger = get_logger(__name__)

    def discover_nodes(self, ip_list: List[str], 
                       username: str = "root", 
                       password: Optional[str] = None,
                       key_filename: Optional[str] = None) -> NodeDiscoveryResult:
        """
        Attempt to establish SSH connections to a list of IP addresses.
        
        Args:
            ip_list: List of IP addresses to discover.
            username: SSH username.
            password: SSH password (if not using keys).
            key_filename: Path to private key file (if not using password).
        
        Returns:
            NodeDiscoveryResult containing discovered nodes and failures.
        
        Raises:
            NodeDiscoveryError: If ALL nodes in the list are unreachable.
        """
        discovered = []
        failed = []
        
        for ip in ip_list:
            try:
                node = self._connect_node(ip, username, password, key_filename)
                if node:
                    discovered.append(node)
                    self._node_states[ip] = NodeStatus.ACTIVE
                else:
                    failed.append({"ip": ip, "reason": "Connection refused"})
            except AuthenticationException as e:
                failed.append({"ip": ip, "reason": f"Authentication failed: {str(e)}"})
            except socket.timeout as e:
                failed.append({"ip": ip, "reason": f"Connection timeout: {str(e)}"})
            except Exception as e:
                failed.append({"ip": ip, "reason": f"Unexpected error: {str(e)}"})
        
        result = NodeDiscoveryResult(
            discovered_nodes=discovered,
            failed_nodes=failed
        )
        
        if len(discovered) == 0:
            raise NodeDiscoveryError(
                f"Node discovery failed: All {len(ip_list)} nodes are unreachable. "
                f"Failed: {[n['ip'] for n in failed]}"
            )
        
        self.logger.info(f"Discovery complete: {len(discovered)} discovered, {len(failed)} failed")
        return result

    def _connect_node(self, ip: str, username: str, 
                     password: Optional[str], key_filename: Optional[str]) -> Optional[PhysicalNode]:
        """Internal method to establish a single SSH connection."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
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
            
            # Verify connection by executing a simple command
            stdin, stdout, stderr = client.exec_command("echo 'connected'", timeout=self.ssh_timeout)
            status = stdout.read().decode().strip()
            
            if status == "connected":
                node = PhysicalNode(
                    ip_address=ip,
                    status=NodeStatus.ACTIVE,
                    last_seen=datetime.now(),
                    metadata={"ssh_version": client._transport.remote_version}
                )
                self._active_connections[ip] = client
                return node
            
        except paramiko.AuthenticationException:
            raise AuthenticationException(f"Authentication failed for {ip}")
        except socket.timeout:
            raise socket.timeout(f"Connection timed out for {ip}")
        finally:
            # Close client if connection wasn't successful
            if ip not in self._active_connections:
                try:
                    client.close()
                except:
                    pass
        
        return None

    def ping_node(self, ip: str, timeout: float = 2.0) -> bool:
        """
        Send a heartbeat ping to a specific node.
        
        Args:
            ip: IP address of the node.
            timeout: Timeout in seconds for the ping.
        
        Returns:
            True if node responds, False otherwise.
        
        Raises:
            NodeHeartbeatLost: If node was previously active but is now unreachable.
        """
        if ip not in self._active_connections:
            self.logger.warning(f"Cannot ping {ip}: No active connection")
            if self._node_states.get(ip) == NodeStatus.ACTIVE:
                self._node_states[ip] = NodeStatus.INACTIVE
                raise NodeHeartbeatLost(f"Node {ip} heartbeat lost")
            return False

        client = self._active_connections[ip]
        try:
            stdin, stdout, stderr = client.exec_command(
                "echo 'heartbeat'", 
                timeout=timeout
            )
            response = stdout.read().decode().strip()
            
            if response == "heartbeat":
                self._node_states[ip] = NodeStatus.ACTIVE
                self.logger.debug(f"Heartbeat OK: {ip}")
                return True
            else:
                self.logger.warning(f"Unexpected heartbeat response from {ip}: {response}")
                return False
                
        except socket.timeout:
            self.logger.warning(f"Heartbeat timeout: {ip}")
            self._node_states[ip] = NodeStatus.INACTIVE
            raise NodeHeartbeatLost(f"Node {ip} heartbeat timeout")
        except Exception as e:
            self.logger.error(f"Heartbeat error on {ip}: {e}")
            self._node_states[ip] = NodeStatus.INACTIVE
            raise NodeHeartbeatLost(f"Node {ip} heartbeat error: {e}")

    def reassign_task(self, task_id: str, new_ip: str) -> bool:
        """
        Reassign a task to a new node.
        
        Args:
            task_id: ID of the task to reassign.
            new_ip: IP address of the new target node.
        
        Returns:
            True if reassignment was successful.
        
        Raises:
            NodeReassignError: If reassignment fails.
        """
        if new_ip not in self._active_connections:
            # Attempt to reconnect
            config = get_config()
            try:
                self._connect_node(
                    new_ip,
                    config.ssh_username,
                    config.ssh_password,
                    config.ssh_key_path
                )
            except Exception as e:
                raise NodeReassignError(f"Failed to connect to {new_ip} for reassignment: {e}")
        
        if self._node_states.get(new_ip) != NodeStatus.ACTIVE:
            raise NodeReassignError(f"Target node {new_ip} is not active")
        
        # Log the reassignment event
        self.logger.info(f"Reassigning task {task_id} to node {new_ip}")
        
        # In a full implementation, this would send a command to the new node
        # to start the specific task. For now, we log and return success.
        # The actual task execution logic is handled by the scheduler/benchmark modules.
        return True

    def get_node_state(self, ip: str) -> NodeStatus:
        """Get the current state of a node."""
        return self._node_states.get(ip, NodeStatus.UNKNOWN)

    def close_connection(self, ip: str):
        """Close the SSH connection for a specific node."""
        if ip in self._active_connections:
            try:
                self._active_connections[ip].close()
            except Exception as e:
                self.logger.error(f"Error closing connection to {ip}: {e}")
            del self._active_connections[ip]
            self._node_states.pop(ip, None)

    def close_all(self):
        """Close all active SSH connections."""
        for ip in list(self._active_connections.keys()):
            self.close_connection(ip)

def create_node_manager(ssh_timeout: float = 2.0) -> NodeManager:
    """Factory function to create a NodeManager instance."""
    return NodeManager(ssh_timeout=ssh_timeout)

def main():
    """Entry point for CLI testing of NodeManager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Node Manager Discovery")
    parser.add_argument("--ips", nargs="+", required=True, help="List of IP addresses to discover")
    parser.add_argument("--username", default="root", help="SSH username")
    parser.add_argument("--password", default=None, help="SSH password")
    parser.add_argument("--key", default=None, help="Path to SSH key")
    
    args = parser.parse_args()
    
    manager = create_node_manager()
    
    try:
        result = manager.discover_nodes(
            ip_list=args.ips,
            username=args.username,
            password=args.password,
            key_filename=args.key
        )
        
        print(f"Discovery Success Rate: {result.success_rate:.2%}")
        print(f"Discovered Nodes: {len(result.discovered_nodes)}")
        for node in result.discovered_nodes:
            print(f"  - {node.ip_address} (Status: {node.status})")
        
        if result.failed_nodes:
            print(f"Failed Nodes: {len(result.failed_nodes)}")
            for fail in result.failed_nodes:
                print(f"  - {fail['ip']}: {fail['reason']}")
                
    except NodeDiscoveryError as e:
        print(f"CRITICAL: {e}")
        return 1
    finally:
        manager.close_all()
        
    return 0

if __name__ == "__main__":
    exit(main())
