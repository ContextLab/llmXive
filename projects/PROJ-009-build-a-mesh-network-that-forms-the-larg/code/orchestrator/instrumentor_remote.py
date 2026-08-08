"""
Remote Instrumentor for Mesh Network Supercomputer.

Executes tcpdump and mpstat on remote nodes via SSH, parses output,
checks for network saturation, and captures unmodeled variables.
"""
from __future__ import annotations
import logging
import re
import time
import socket
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

import paramiko
from orchestrator.logger import get_logger
from orchestrator.models import PhysicalNode, NodeStatus
from orchestrator.node_manager import NodeManager, NodeDiscoveryError

class RemoteExecutionError(Exception):
    """Raised when remote command execution fails."""
    pass

class NetworkSaturationError(Exception):
    """Raised when network saturation is detected (>20% packet loss)."""
    pass

@dataclass
class PacketStats:
    """Statistics extracted from tcpdump output."""
    packet_count: int
    dropped: int
    captured: int
    received: int

@dataclass
class CPUStats:
    """Statistics extracted from mpstat output."""
    cpu_utilization_pct: float
    idle_pct: float
    iowait_pct: float
    timestamp: float

@dataclass
class UnmodeledVars:
    """Best-effort capture of unmodeled variables (thermal, OS noise)."""
    thermal_zone: Optional[str] = None
    loadavg_1m: Optional[float] = None
    loadavg_5m: Optional[float] = None
    loadavg_15m: Optional[float] = None
    os_noise_note: Optional[str] = None

@dataclass
class NodeMetrics:
    """Aggregated metrics for a single node execution."""
    node_id: str
    wall_clock_start: float
    wall_clock_end: float
    wall_clock_duration: float
    packet_stats: Optional[PacketStats] = None
    cpu_stats: Optional[CPUStats] = None
    unmodeled_vars: Optional[UnmodeledVars] = None
    is_excluded: bool = False
    exclusion_reason: Optional[str] = None

class RemoteInstrumentor:
    """
    Manages remote execution of instrumentation commands (tcpdump, mpstat)
    on physical nodes via SSH.
    """
    def __init__(self, node_manager: NodeManager, logger: Optional[logging.Logger] = None):
        self.node_manager = node_manager
        self.logger = logger or get_logger(__name__)
        self.tcpdump_cmd = "tcpdump -c {count} -i any -n"
        self.mpstat_cmd = "mpstat 1 5"  # interval=1, count=5
        self.saturation_threshold = 0.20  # 20%

    def _execute_remote_command(self, ssh_client: paramiko.SSHClient, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """
        Execute a command on the remote node.
        Returns (exit_code, stdout, stderr).
        """
        try:
            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', errors='ignore')
            err = stderr.read().decode('utf-8', errors='ignore')
            return exit_code, out, err
        except socket.timeout:
            raise RemoteExecutionError(f"Command timed out: {command}")
        except Exception as e:
            raise RemoteExecutionError(f"Remote command execution failed: {e}")

    def run_tcpdump(self, ssh_client: paramiko.SSHClient, count: int = 1000) -> PacketStats:
        """
        Execute tcpdump remotely and parse packet counts.
        """
        cmd = self.tcpdump_cmd.format(count=count)
        exit_code, stdout, stderr = self._execute_remote_command(ssh_client, cmd, timeout=60)
        
        if exit_code != 0:
            # tcpdump often exits non-zero if no packets found or interface issue, but we parse output
            self.logger.warning(f"tcpdump exit code {exit_code}: {stderr}")

        # Parse output: usually ends with "X packets captured; Y packets received by filter; Z packets dropped by kernel"
        # Example: "1000 packets captured, 1002 packets received by filter, 0 packets dropped by kernel"
        captured = 0
        received = 0
        dropped = 0

        # Regex to find numbers near keywords
        captured_match = re.search(r'(\d+)\s+packets?\s+captured', stdout)
        received_match = re.search(r'(\d+)\s+packets?\s+(?:received by filter|received)', stdout)
        dropped_match = re.search(r'(\d+)\s+packets?\s+dropped', stdout)

        if captured_match:
            captured = int(captured_match.group(1))
        if received_match:
            received = int(received_match.group(1))
        if dropped_match:
            dropped = int(dropped_match.group(1))

        # If parsing fails, try to infer from stderr or default
        if captured == 0 and count > 0:
            # Fallback: assume captured count if we sent a count and got some output
            # This is a heuristic; real tcpdump output is preferred
            pass

        return PacketStats(packet_count=captured, dropped=dropped, captured=captured, received=received)

    def run_mpstat(self, ssh_client: paramiko.SSHClient) -> CPUStats:
        """
        Execute mpstat remotely and parse CPU utilization.
        """
        cmd = self.mpstat_cmd
        exit_code, stdout, stderr = self._execute_remote_command(ssh_client, cmd, timeout=60)

        if exit_code != 0:
            raise RemoteExecutionError(f"mpstat failed with exit code {exit_code}: {stderr}")

        # Parse mpstat output
        # Format: Linux <date> ... <host> ... <cpu> ... %idle ...
        # We want the last row (average or specific interval)
        lines = stdout.strip().split('\n')
        cpu_util = 0.0
        idle = 0.0
        iowait = 0.0
        
        # Find the line with 'Average' or the last data line
        data_lines = []
        for line in lines:
            if 'Average' in line or (line and line[0].isdigit()):
                data_lines.append(line)

        if not data_lines:
            raise RemoteExecutionError("Could not parse mpstat output: no data lines found")

        # Parse the last data line (usually 'Average' or the last interval)
        last_line = data_lines[-1]
        parts = last_line.split()
        
        # Typical mpstat output:
        # Linux ... ... cpu ... %usr ... %sys ... %iowait ... %idle ...
        # Indices depend on version, but usually %idle is near the end
        # We'll search for the %idle column by name if possible, or use heuristics
        
        # Simple heuristic: look for the column header to map indices
        # For robustness, we assume standard output format
        # If 'Average' line, it's: cpu, usr, sys, idle, ...
        # We'll search for the %idle keyword in the line
        try:
            # Find the index of %idle in the header or data
            # If the line starts with numbers, it's data
            # We'll assume the last few columns are percentages
            # Common format: cpu, usr, nice, sys, iowait, irq, softirq, steal, guest, idle
            # So %idle is often the last column
            idle_str = parts[-1]
            idle = float(idle_str)
            cpu_util = 100.0 - idle
            
            # Try to find %iowait
            # In many versions, iowait is 4th or 5th column after cpu
            # We'll search for it in the line
            iowait_match = re.search(r'(\d+\.?\d*)\s*%', last_line)
            if iowait_match:
                # This is a very rough heuristic; better to parse headers
                pass
            
            # For now, we'll just set iowait to 0 if not found
            # In a real implementation, we'd parse the header row to map columns
            iowait = 0.0

        except (ValueError, IndexError) as e:
            self.logger.error(f"Failed to parse mpstat line: {last_line}, error: {e}")
            raise RemoteExecutionError(f"Failed to parse mpstat output: {e}")

        return CPUStats(
            cpu_utilization_pct=cpu_util,
            idle_pct=idle,
            iowait_pct=iowait,
            timestamp=time.time()
        )

    def check_network_saturation(self, packet_stats: PacketStats) -> bool:
        """
        Check if network saturation (>20% packet loss) is detected.
        """
        if packet_stats.captured == 0:
            return False  # No packets to lose
        
        loss_rate = packet_stats.dropped / packet_stats.captured
        if loss_rate > self.saturation_threshold:
            self.logger.warning(f"Network saturation detected: {loss_rate:.2%} packet loss")
            return True
        return False

    def capture_unmodeled_vars(self, ssh_client: paramiko.SSHClient) -> UnmodeledVars:
        """
        Best-effort capture of unmodeled variables (thermal, OS noise).
        """
        thermal_zone = None
        loadavg_1m = None
        loadavg_5m = None
        loadavg_15m = None
        os_noise_note = None

        # Try to read thermal zone
        try:
            exit_code, stdout, _ = self._execute_remote_command(ssh_client, "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null", timeout=5)
            if exit_code == 0 and stdout.strip():
                thermal_zone = stdout.strip()
        except Exception as e:
            self.logger.warning(f"Could not read thermal zone: {e}")

        # Try to read loadavg
        try:
            exit_code, stdout, _ = self._execute_remote_command(ssh_client, "cat /proc/loadavg", timeout=5)
            if exit_code == 0 and stdout.strip():
                parts = stdout.strip().split()
                if len(parts) >= 3:
                    loadavg_1m = float(parts[0])
                    loadavg_5m = float(parts[1])
                    loadavg_15m = float(parts[2])
        except Exception as e:
            self.logger.warning(f"Could not read loadavg: {e}")

        # If both failed, note that
        if thermal_zone is None and loadavg_1m is None:
            os_noise_note = "Thermal and loadavg metrics unavailable (e.g., mobile device or restricted container)"

        return UnmodeledVars(
            thermal_zone=thermal_zone,
            loadavg_1m=loadavg_1m,
            loadavg_5m=loadavg_5m,
            loadavg_15m=loadavg_15m,
            os_noise_note=os_noise_note
        )

    def instrument_node(self, node: PhysicalNode, packet_count: int = 1000) -> NodeMetrics:
        """
        Run full instrumentation suite on a node:
        1. Start wall-clock timer
        2. Run tcpdump
        3. Run mpstat
        4. Capture unmodeled vars
        5. Stop wall-clock timer
        6. Check for saturation and flag exclusion if needed
        """
        self.logger.info(f"Instrumenting node {node.ip_address}...")
        
        # Establish SSH connection
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Use node_manager to get credentials or connection info if needed
            # For now, assume node has username/password or key configured
            ssh_client.connect(
                hostname=node.ip_address,
                username=node.username,
                password=node.password,
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
        except Exception as e:
            raise RemoteExecutionError(f"Failed to connect to node {node.ip_address}: {e}")

        metrics = NodeMetrics(
            node_id=node.node_id,
            wall_clock_start=time.time(),
            wall_clock_end=0.0,
            wall_clock_duration=0.0
        )

        try:
            # 1. Run tcpdump
            packet_stats = self.run_tcpdump(ssh_client, count=packet_count)
            metrics.packet_stats = packet_stats

            # 2. Run mpstat
            cpu_stats = self.run_mpstat(ssh_client)
            metrics.cpu_stats = cpu_stats

            # 3. Capture unmodeled vars
            unmodeled = self.capture_unmodeled_vars(ssh_client)
            metrics.unmodeled_vars = unmodeled

            # 4. Check network saturation
            if self.check_network_saturation(packet_stats):
                metrics.is_excluded = True
                metrics.exclusion_reason = f"Network saturation: {packet_stats.dropped / packet_stats.captured:.2%} packet loss"
                self.logger.warning(f"Node {node.node_id} excluded due to network saturation.")

        finally:
            # 5. Stop wall-clock timer
            metrics.wall_clock_end = time.time()
            metrics.wall_clock_duration = metrics.wall_clock_end - metrics.wall_clock_start
            ssh_client.close()

        return metrics

def create_instrumentor(node_manager: NodeManager) -> RemoteInstrumentor:
    """Factory function to create a RemoteInstrumentor."""
    return RemoteInstrumentor(node_manager)

def main():
    """
    Main entry point for standalone execution.
    Demonstrates instrumentation of a single node.
    """
    logging.basicConfig(level=logging.INFO)
    logger = get_logger(__name__)

    # Example usage (would be replaced by actual node list in production)
    # node = PhysicalNode(node_id="node1", ip_address="192.168.1.10", username="user", password="pass")
    # node_manager = NodeManager([node])
    # instrumentor = create_instrumentor(node_manager)
    # metrics = instrumentor.instrument_node(node)
    # print(f"Node Metrics: {metrics}")
    logger.info("RemoteInstrumentor main() called. Use as a library or integrate with scheduler.")

if __name__ == "__main__":
    main()
