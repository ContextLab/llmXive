"""
Remote Instrumentation Module for Mesh Network Supercomputer.

This module handles remote execution of instrumentation commands (tcpdump, mpstat)
on physical nodes via SSH, parses their output, and provides network saturation
detection capabilities.
"""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Dict as TypingDict

import paramiko
from paramiko import SSHClient, AutoAddPolicy, SSHException

from orchestrator.logger import get_logger
from orchestrator.models import PhysicalNode, NodeStatus
from orchestrator.mpstat_parser import parse_mpstat_output, get_aggregated_utilization

# Configure logger
logger = get_logger(__name__)

# Constants for network saturation detection
PACKET_LOSS_THRESHOLD = 0.20  # 20% packet loss threshold
DEFAULT_TIMEOUT = 30  # seconds for SSH command execution
TCPDUMP_DURATION = 10  # seconds to capture packets for saturation check
TCPDUMP_IFACE = "eth0"  # Default interface to monitor

class RemoteInstrumentor:
    """
    Handles remote instrumentation of physical nodes via SSH.
    
    Capabilities:
    - Execute tcpdump for packet capture and loss analysis
    - Execute mpstat for CPU utilization monitoring
    - Detect network saturation based on packet loss
    - Parse and aggregate remote command outputs
    """

    def __init__(self, config: TypingDict[str, Any] = None):
        """
        Initialize the RemoteInstrumentor.
        
        Args:
            config: Optional configuration dictionary. Expected keys:
                    - timeout: SSH command timeout (default: 30)
                    - tcpdump_duration: Duration for packet capture (default: 10)
                    - tcpdump_interface: Network interface to monitor (default: eth0)
                    - packet_loss_threshold: Threshold for saturation detection (default: 0.20)
        """
        self.config = config or {}
        self.timeout = self.config.get('timeout', DEFAULT_TIMEOUT)
        self.tcpdump_duration = self.config.get('tcpdump_duration', TCPDUMP_DURATION)
        self.tcpdump_iface = self.config.get('tcpdump_interface', TCPDUMP_IFACE)
        self.packet_loss_threshold = self.config.get('packet_loss_threshold', PACKET_LOSS_THRESHOLD)
        self._clients: Dict[str, SSHClient] = {}

    def _get_ssh_client(self, node: PhysicalNode) -> SSHClient:
        """
        Establish or retrieve an SSH connection to a node.
        
        Args:
            node: PhysicalNode object containing connection details
            
        Returns:
            SSHClient instance connected to the node
            
        Raises:
            paramiko.AuthenticationException: If authentication fails
            paramiko.SSHException: If connection cannot be established
        """
        if node.hostname in self._clients:
            try:
                # Check if connection is still alive
                self._clients[node.hostname].transport.sock.send(b'\x00')
                return self._clients[node.hostname]
            except Exception:
                # Connection dead, remove and reconnect
                del self._clients[node.hostname]

        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())
        
        try:
            client.connect(
                hostname=node.hostname,
                port=node.port or 22,
                username=node.username or 'root',
                password=node.password,
                key_filename=node.ssh_key_path,
                timeout=self.timeout,
                allow_agent=False,
                look_for_keys=False
            )
            self._clients[node.hostname] = client
            logger.info(f"SSH connection established to {node.hostname}")
        except SSHException as e:
            logger.error(f"Failed to connect to {node.hostname}: {e}")
            raise
        
        return client

    def execute_remote_command(self, node: PhysicalNode, command: str) -> Tuple[int, str, str]:
        """
        Execute a command on a remote node via SSH.
        
        Args:
            node: PhysicalNode object
            command: Shell command to execute
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
            
        Raises:
            SSHException: If command execution fails
        """
        client = self._get_ssh_client(node)
        
        try:
            stdin, stdout, stderr = client.exec_command(command, timeout=self.timeout)
            exit_code = stdout.channel.recv_exit_status()
            stdout_text = stdout.read().decode('utf-8', errors='replace')
            stderr_text = stderr.read().decode('utf-8', errors='replace')
            
            return exit_code, stdout_text, stderr_text
        except Exception as e:
            logger.error(f"Command execution failed on {node.hostname}: {e}")
            raise

    def collect_tcpdump_stats(self, node: PhysicalNode) -> Dict[str, Any]:
        """
        Collect packet statistics from a remote node using tcpdump.
        
        Executes a tcpdump command to capture packets for a specified duration
        and returns statistics about packet counts and potential loss.
        
        Args:
            node: PhysicalNode object
            
        Returns:
            Dictionary containing packet statistics:
            - packets_received: Number of packets received
            - packets_dropped: Number of packets dropped
            - packet_loss_rate: Ratio of dropped packets (0.0 to 1.0)
            - duration: Duration of capture in seconds
            - interface: Network interface monitored
        """
        # tcpdump command with count and duration
        # -c limits total packets, -i specifies interface, -q reduces output verbosity
        # We use a wrapper to count packets and drops
        tcpdump_cmd = (
            f"timeout {self.tcpdump_duration} tcpdump -i {self.tcpdump_iface} -c 10000 -q 2>&1 || true"
        )
        
        try:
            exit_code, stdout, stderr = self.execute_remote_command(node, tcpdump_cmd)
            
            # Parse tcpdump output for packet counts
            # tcpdump typically outputs: "1234 packets captured"
            # and may show: "56 packets dropped by kernel"
            captured_match = re.search(r'(\d+)\s+packets?\s+captured', stdout + stderr, re.IGNORECASE)
            dropped_match = re.search(r'(\d+)\s+packets?\s+dropped', stdout + stderr, re.IGNORECASE)
            
            packets_received = int(captured_match.group(1)) if captured_match else 0
            packets_dropped = int(dropped_match.group(1)) if dropped_match else 0
            
            # Calculate packet loss rate
            total_packets = packets_received + packets_dropped
            if total_packets > 0:
                packet_loss_rate = packets_dropped / total_packets
            else:
                packet_loss_rate = 0.0
            
            return {
                'packets_received': packets_received,
                'packets_dropped': packets_dropped,
                'packet_loss_rate': packet_loss_rate,
                'duration': self.tcpdump_duration,
                'interface': self.tcpdump_iface,
                'timestamp': datetime.now().isoformat(),
                'node_hostname': node.hostname
            }
            
        except Exception as e:
            logger.error(f"Failed to collect tcpdump stats from {node.hostname}: {e}")
            # Return a failure state with high packet loss to trigger abort
            return {
                'packets_received': 0,
                'packets_dropped': 0,
                'packet_loss_rate': 1.0,  # Force saturation detection on error
                'duration': self.tcpdump_duration,
                'interface': self.tcpdump_iface,
                'timestamp': datetime.now().isoformat(),
                'node_hostname': node.hostname,
                'error': str(e)
            }

    def collect_mpstat_stats(self, node: PhysicalNode) -> Dict[str, Any]:
        """
        Collect CPU statistics from a remote node using mpstat.
        
        Args:
            node: PhysicalNode object
            
        Returns:
            Dictionary containing CPU statistics:
            - cpu_utilization_pct: Aggregated CPU utilization percentage
            - per_core_utilization: List of utilization per core
            - timestamp: When the measurement was taken
            - node_hostname: Source node hostname
        """
        # mpstat command: 1 sample, 1 second interval, all CPUs
        mpstat_cmd = "mpstat 1 1 -P ALL 2>&1 || echo 'mpstat not available'"
        
        try:
            exit_code, stdout, stderr = self.execute_remote_command(node, mpstat_cmd)
            
            if "mpstat not available" in stdout:
                logger.warning(f"mpstat not available on {node.hostname}")
                return {
                    'cpu_utilization_pct': 0.0,
                    'per_core_utilization': [],
                    'timestamp': datetime.now().isoformat(),
                    'node_hostname': node.hostname,
                    'error': 'mpstat not available'
                }
            
            # Parse mpstat output
            parsed_data = parse_mpstat_output(stdout)
            aggregated_util = get_aggregated_utilization(parsed_data)
            
            return {
                'cpu_utilization_pct': aggregated_util,
                'per_core_utilization': parsed_data.get('per_core', []),
                'timestamp': datetime.now().isoformat(),
                'node_hostname': node.hostname
            }
            
        except Exception as e:
            logger.error(f"Failed to collect mpstat stats from {node.hostname}: {e}")
            return {
                'cpu_utilization_pct': 0.0,
                'per_core_utilization': [],
                'timestamp': datetime.now().isoformat(),
                'node_hostname': node.hostname,
                'error': str(e)
            }

    def check_network_saturation(self, node: PhysicalNode) -> bool:
        """
        Check if a node's network is saturated (>20% packet loss).
        
        This method collects tcpdump statistics from the remote node and
        determines if the packet loss rate exceeds the configured threshold.
        If saturation is detected, it logs a critical error and returns True.
        
        Args:
            node: PhysicalNode object to check
            
        Returns:
            True if network saturation is detected (packet_loss_rate > 20%),
            False otherwise
            
        Raises:
            RuntimeError: If network saturation is detected (to abort the run)
        """
        logger.info(f"Checking network saturation on {node.hostname}")
        
        stats = self.collect_tcpdump_stats(node)
        packet_loss_rate = stats.get('packet_loss_rate', 0.0)
        
        logger.info(
            f"Node {node.hostname}: packet_loss_rate={packet_loss_rate:.2%}, "
            f"received={stats['packets_received']}, dropped={stats['packets_dropped']}"
        )
        
        if packet_loss_rate > self.packet_loss_threshold:
            error_msg = (
                f"CRITICAL: Network saturation detected on {node.hostname}. "
                f"Packet loss rate: {packet_loss_rate:.2%} (threshold: {self.packet_loss_threshold:.2%}). "
                f"Aborting run to prevent corrupted data."
            )
            logger.critical(error_msg)
            raise RuntimeError(error_msg)
        
        return False

    def collect_node_metrics(self, node: PhysicalNode) -> Dict[str, Any]:
        """
        Collect all instrumentation metrics from a node.
        
        Args:
            node: PhysicalNode object
            
        Returns:
            Dictionary containing both CPU and network metrics
        """
        return {
            'cpu': self.collect_mpstat_stats(node),
            'network': self.collect_tcpdump_stats(node),
            'timestamp': datetime.now().isoformat(),
            'node_hostname': node.hostname
        }

    def close_connections(self):
        """Close all active SSH connections."""
        for hostname, client in self._clients.items():
            try:
                client.close()
                logger.info(f"Closed SSH connection to {hostname}")
            except Exception as e:
                logger.warning(f"Error closing connection to {hostname}: {e}")
        self._clients.clear()

def create_instrumentor(config: TypingDict[str, Any] = None) -> RemoteInstrumentor:
    """
    Factory function to create a RemoteInstrumentor instance.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured RemoteInstrumentor instance
    """
    return RemoteInstrumentor(config)

def main():
    """
    Main entry point for standalone testing of the RemoteInstrumentor.
    
    This function demonstrates the network saturation check capability
    by attempting to connect to configured nodes and checking their
    network health.
    """
    import argparse
    import yaml
    
    parser = argparse.ArgumentParser(description='Remote Instrumentor - Network Saturation Check')
    parser.add_argument('--config', type=str, help='Path to configuration YAML file')
    parser.add_argument('--nodes', type=str, nargs='+', help='List of node hostnames to check')
    parser.add_argument('--threshold', type=float, default=0.20, help='Packet loss threshold (default: 0.20)')
    
    args = parser.parse_args()
    
    # Load configuration
    config = {}
    if args.config:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f) or {}
    
    # Override with command line args
    config['packet_loss_threshold'] = args.threshold
    
    instrumentor = create_instrumentor(config)
    
    # Define test nodes (in production, these would come from config or node_manager)
    test_nodes = []
    if args.nodes:
        for hostname in args.nodes:
            test_nodes.append(PhysicalNode(
                hostname=hostname,
                port=22,
                username='root',
                password=None,
                ssh_key_path=None
            ))
    else:
        # Default test node for demonstration
        test_nodes.append(PhysicalNode(
            hostname='localhost',
            port=22,
            username='root',
            password=None,
            ssh_key_path=None
        ))
    
    print(f"Checking network saturation on {len(test_nodes)} node(s)...")
    
    saturation_detected = False
    for node in test_nodes:
        try:
            print(f"\nChecking {node.hostname}...")
            instrumentor.check_network_saturation(node)
            print(f"  ✓ {node.hostname}: Network healthy")
        except RuntimeError as e:
            print(f"  ✗ {node.hostname}: {e}")
            saturation_detected = True
        except Exception as e:
            print(f"  ✗ {node.hostname}: Connection error - {e}")
            # Connection errors are treated as saturation to abort the run
            saturation_detected = True
    
    instrumentor.close_connections()
    
    if saturation_detected:
        print("\n⚠ Network saturation detected. Run aborted.")
        exit(1)
    else:
        print("\n✓ All nodes healthy. Network saturation check passed.")
        exit(0)

if __name__ == '__main__':
    main()