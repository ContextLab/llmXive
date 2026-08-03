"""
Remote Instrumentor for Mesh Network Supercomputer.

This module provides the RemoteInstrumentor class to remotely execute
tcpdump (packet counts) and mpstat (CPU usage) commands on target nodes via SSH.
It depends on the NodeManager (T013) for establishing SSH connections.
"""
import logging
import re
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from pathlib import Path

from orchestrator.logger import get_logger
from orchestrator.node_manager import NodeManager
from orchestrator.models import PhysicalNode

logger = get_logger(__name__)


class RemoteInstrumentor:
    """
    Handles remote instrumentation commands on mesh nodes.
    
    This class uses SSH (via NodeManager) to execute system commands
    for monitoring network traffic and CPU utilization.
    """

    def __init__(self, node_manager: NodeManager):
        """
        Initialize the RemoteInstrumentor.
        
        Args:
            node_manager: An initialized NodeManager instance for SSH connections.
        """
        self.node_manager = node_manager
        self.logger = logger

    def execute_tcpdump(self, node: PhysicalNode, duration: int = 10, interface: str = "eth0") -> Dict[str, Any]:
        """
        Execute tcpdump on a remote node to count packets.
        
        Args:
            node: The target PhysicalNode.
            duration: Duration in seconds to capture packets.
            interface: Network interface to monitor (default: eth0).
        
        Returns:
            A dictionary containing:
                - node_id: ID of the node
                - timestamp: When the capture started
                - packet_count: Total packets captured
                - interface: Interface used
                - success: Boolean indicating success
                - raw_output: Raw stdout from the command (optional)
        
        Raises:
            RuntimeError: If the command fails or returns invalid data.
        """
        # tcpdump command: capture for duration, count packets, suppress verbose output
        # Using -c 1000000 to ensure we don't stop due to count limit if duration is reached
        # Using -q to reduce output size, -i for interface
        # We parse the final line which contains "X packets captured"
        cmd = f"sudo tcpdump -i {interface} -q -c 1000000 -G {duration} -W 1 2>&1"
        
        self.logger.info(f"Executing tcpdump on node {node.node_id} for {duration}s on {interface}")
        
        try:
            # Execute command via NodeManager
            result = self.node_manager.execute_command(node, cmd, timeout=duration + 30)
            
            if result.exit_code != 0:
                # Check for specific errors (e.g., permission denied, interface not found)
                if "Permission denied" in result.stderr or "Operation not permitted" in result.stderr:
                    self.logger.warning(f"tcpdump permission issue on node {node.node_id}. Attempting without sudo...")
                    # Retry without sudo (might work if user has capabilities)
                    cmd_fallback = f"tcpdump -i {interface} -q -c 1000000 -G {duration} -W 1 2>&1"
                    result = self.node_manager.execute_command(node, cmd_fallback, timeout=duration + 30)
                    if result.exit_code != 0:
                        raise RuntimeError(f"tcpdump failed on node {node.node_id}: {result.stderr}")
                else:
                    raise RuntimeError(f"tcpdump failed on node {node.node_id}: {result.stderr}")
            
            # Parse output to find packet count
            # tcpdump summary line usually looks like: "12345 packets captured"
            packet_count = 0
            for line in result.stdout.split('\n'):
                match = re.search(r'(\d+)\s+packets?\s+captured', line, re.IGNORECASE)
                if match:
                    packet_count = int(match.group(1))
                    break
            
            # If no packets captured line found, try to infer from other patterns
            if packet_count == 0 and result.stdout:
                # Sometimes tcpdump outputs "X packets dropped by kernel" etc.
                # We'll assume 0 if we can't find a capture count
                self.logger.debug(f"Could not parse packet count from tcpdump output on node {node.node_id}")
            
            return {
                "node_id": node.node_id,
                "timestamp": datetime.now().isoformat(),
                "packet_count": packet_count,
                "interface": interface,
                "success": True,
                "raw_output": result.stdout[:500] if result.stdout else None  # Truncate for logging
            }
            
        except Exception as e:
            self.logger.error(f"tcpdump execution failed on node {node.node_id}: {str(e)}")
            return {
                "node_id": node.node_id,
                "timestamp": datetime.now().isoformat(),
                "packet_count": 0,
                "interface": interface,
                "success": False,
                "error": str(e)
            }

    def execute_mpstat(self, node: PhysicalNode, interval: float = 1.0, count: int = 5) -> Dict[str, Any]:
        """
        Execute mpstat on a remote node to get CPU utilization.
        
        Args:
            node: The target PhysicalNode.
            interval: Interval between samples in seconds.
            count: Number of samples to take.
        
        Returns:
            A dictionary containing:
                - node_id: ID of the node
                - timestamp: When the measurement started
                - cpu_utilization_pct: Average CPU utilization percentage (100 - idle)
                - samples: List of individual sample values
                - success: Boolean indicating success
                - raw_output: Raw stdout from the command
        
        Raises:
            RuntimeError: If the command fails or returns invalid data.
        """
        # mpstat command: get CPU stats, interval, count
        # We use -P ALL to get per-CPU stats, then average them
        cmd = f"mpstat -P ALL {interval} {count} 2>&1"
        
        self.logger.info(f"Executing mpstat on node {node.node_id}: interval={interval}s, count={count}")
        
        try:
            result = self.node_manager.execute_command(node, cmd, timeout=(interval * count) + 30)
            
            if result.exit_code != 0:
                raise RuntimeError(f"mpstat failed on node {node.node_id}: {result.stderr}")
            
            # Parse mpstat output
            # Format:
            # Linux 5.x.x...
            # 12:34:56  CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
            # 12:34:57  all    1.00    0.00    0.50    0.00    0.00    0.00    0.00    0.00    0.00   98.50
            # ...
            # Average: ...
            
            lines = result.stdout.split('\n')
            samples = []
            cpu_line_pattern = re.compile(r'^\s*\d+:\d+:\d+\s+(all|\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$')
            
            for line in lines:
                match = cpu_line_pattern.match(line)
                if match:
                    # Extract idle percentage (last column)
                    idle_pct = float(match.group(12))
                    cpu_util = 100.0 - idle_pct
                    samples.append(cpu_util)
            
            if not samples:
                raise RuntimeError(f"Could not parse mpstat output on node {node.node_id}")
            
            avg_utilization = sum(samples) / len(samples)
            
            return {
                "node_id": node.node_id,
                "timestamp": datetime.now().isoformat(),
                "cpu_utilization_pct": avg_utilization,
                "samples": samples,
                "success": True,
                "raw_output": result.stdout[:1000] if result.stdout else None
            }
            
        except Exception as e:
            self.logger.error(f"mpstat execution failed on node {node.node_id}: {str(e)}")
            return {
                "node_id": node.node_id,
                "timestamp": datetime.now().isoformat(),
                "cpu_utilization_pct": 0.0,
                "samples": [],
                "success": False,
                "error": str(e)
            }

    def check_network_saturation(self, node: PhysicalNode, duration: int = 10, threshold: float = 0.20) -> Dict[str, Any]:
        """
        Check for network saturation by measuring packet loss rate.
        
        This method executes a ping-based test or analyzes tcpdump output
        to detect if packet loss exceeds the specified threshold.
        
        Args:
            node: The target PhysicalNode.
            duration: Duration of the test in seconds.
            threshold: Packet loss threshold (e.g., 0.20 for 20%).
        
        Returns:
            A dictionary containing:
                - node_id: ID of the node
                - packet_loss_rate: Estimated packet loss rate
                - saturated: Boolean indicating if loss exceeds threshold
                - success: Boolean indicating success
        
        Note:
            This implementation uses a simple ping-based approach.
            For more accurate results, tcpdump analysis during active traffic
            would be needed.
        """
        # Use ping to measure packet loss
        # Send 100 packets over duration seconds
        packets_to_send = 100
        cmd = f"ping -c {packets_to_send} -W 1 -i {duration/packets_to_send} 127.0.0.1 2>&1"
        
        self.logger.info(f"Checking network saturation on node {node.node_id}")
        
        try:
            result = self.node_manager.execute_command(node, cmd, timeout=duration + 30)
            
            if result.exit_code != 0:
                # ping might fail for other reasons, try a simpler check
                self.logger.warning(f"Ping failed on node {node.node_id}, using fallback check")
                return {
                    "node_id": node.node_id,
                    "packet_loss_rate": 0.0,
                    "saturated": False,
                    "success": False,
                    "error": "Ping command failed"
                }
            
            # Parse ping output for packet loss
            # Look for line like: "100 packets transmitted, 100 received, 0% packet loss"
            loss_match = re.search(r'(\d+)%\s+packet\s+loss', result.stdout)
            
            if loss_match:
                loss_rate = float(loss_match.group(1)) / 100.0
                saturated = loss_rate > threshold
                
                self.logger.info(f"Node {node.node_id}: packet loss {loss_rate*100:.1f}% (threshold: {threshold*100:.1f}%)")
                
                return {
                    "node_id": node.node_id,
                    "packet_loss_rate": loss_rate,
                    "saturated": saturated,
                    "success": True
                }
            else:
                self.logger.warning(f"Could not parse packet loss from ping output on node {node.node_id}")
                return {
                    "node_id": node.node_id,
                    "packet_loss_rate": 0.0,
                    "saturated": False,
                    "success": False,
                    "error": "Could not parse ping output"
                }
                
        except Exception as e:
            self.logger.error(f"Network saturation check failed on node {node.node_id}: {str(e)}")
            return {
                "node_id": node.node_id,
                "packet_loss_rate": 0.0,
                "saturated": False,
                "success": False,
                "error": str(e)
            }

    def capture_unmodeled_vars(self, node: PhysicalNode) -> Dict[str, Any]:
        """
        Capture unmodeled variables like thermal throttling and OS noise.
        
        This method attempts to gather metrics that might affect performance
        but are not directly modeled in the primary analysis.
        
        Args:
            node: The target PhysicalNode.
        
        Returns:
            A dictionary containing:
                - node_id: ID of the node
                - timestamp: When the measurement was taken
                - thermal_throttling: Boolean indicating if throttling is active
                - os_noise_metrics: Dictionary with OS noise metrics
                - success: Boolean indicating success
        """
        result_data = {
            "node_id": node.node_id,
            "timestamp": datetime.now().isoformat(),
            "thermal_throttling": False,
            "os_noise_metrics": {},
            "success": False
        }
        
        try:
            # Check for thermal throttling (if available)
            # Try to read thermal zone info
            thermal_cmd = "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo 'N/A'"
            thermal_result = self.node_manager.execute_command(node, thermal_cmd, timeout=5)
            
            if thermal_result.exit_code == 0 and thermal_result.stdout.strip() != 'N/A':
                try:
                    temp_millidegrees = int(thermal_result.stdout.strip())
                    temp_celsius = temp_millidegrees / 1000.0
                    result_data["os_noise_metrics"]["temperature_celsius"] = temp_celsius
                    
                    # Assume throttling if temperature > 80C (adjustable threshold)
                    if temp_celsius > 80.0:
                        result_data["thermal_throttling"] = True
                        self.logger.warning(f"Node {node.node_id}: High temperature detected ({temp_celsius:.1f}C)")
                except ValueError:
                    pass
            
            # Check for high load average (OS noise indicator)
            load_cmd = "uptime 2>/dev/null || echo 'N/A'"
            load_result = self.node_manager.execute_command(node, load_cmd, timeout=5)
            
            if load_result.exit_code == 0:
                load_match = re.search(r'load average:\s+([\d.]+),\s+([\d.]+),\s+([\d.]+)', load_result.stdout)
                if load_match:
                    load_1min = float(load_match.group(1))
                    load_5min = float(load_match.group(2))
                    load_15min = float(load_match.group(3))
                    result_data["os_noise_metrics"]["load_average_1min"] = load_1min
                    result_data["os_noise_metrics"]["load_average_5min"] = load_5min
                    result_data["os_noise_metrics"]["load_average_15min"] = load_15min
            
            # Check for interrupt frequency (another OS noise indicator)
            # This is a simplified check - real implementation would sample /proc/interrupts
            interrupt_cmd = "cat /proc/stat | grep ^intr 2>/dev/null || echo 'N/A'"
            interrupt_result = self.node_manager.execute_command(node, interrupt_cmd, timeout=5)
            
            if interrupt_result.exit_code == 0:
                result_data["os_noise_metrics"]["interrupts"] = interrupt_result.stdout.strip()
            
            result_data["success"] = True
            
        except Exception as e:
            self.logger.error(f"Failed to capture unmodeled vars on node {node.node_id}: {str(e)}")
            result_data["error"] = str(e)
        
        return result_data

    def instrument_node(self, node: PhysicalNode, capture_duration: int = 10) -> Dict[str, Any]:
        """
        Perform a full instrumentation cycle on a node.
        
        This method executes both tcpdump and mpstat commands and
        captures unmodeled variables in a single operation.
        
        Args:
            node: The target PhysicalNode.
            capture_duration: Duration for packet capture in seconds.
        
        Returns:
            A dictionary containing all instrumentation results:
                - tcpdump_result: Result from tcpdump execution
                - mpstat_result: Result from mpstat execution
                - unmodeled_vars: Result from unmodeled variables capture
                - network_saturation: Result from network saturation check
        """
        self.logger.info(f"Starting full instrumentation cycle on node {node.node_id}")
        
        tcpdump_result = self.execute_tcpdump(node, duration=capture_duration)
        mpstat_result = self.execute_mpstat(node)
        unmodeled_result = self.capture_unmodeled_vars(node)
        saturation_result = self.check_network_saturation(node, duration=capture_duration)
        
        return {
            "node_id": node.node_id,
            "timestamp": datetime.now().isoformat(),
            "tcpdump": tcpdump_result,
            "mpstat": mpstat_result,
            "unmodeled_vars": unmodeled_result,
            "network_saturation": saturation_result
        }


def create_instrumentor(node_manager: NodeManager) -> RemoteInstrumentor:
    """
    Factory function to create a RemoteInstrumentor instance.
    
    Args:
        node_manager: An initialized NodeManager instance.
    
    Returns:
        A configured RemoteInstrumentor instance.
    """
    return RemoteInstrumentor(node_manager)
