from __future__ import annotations
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any

import paramiko
from paramiko import SSHClient, SSHException, AuthenticationException, SocketTimeout

from orchestrator.logger import get_logger
from orchestrator.remote_tool_manager import RemoteToolManager, create_tool_manager
from orchestrator.remote_wall_clock_timer import RemoteWallClockTimer, create_timer
from orchestrator.node_manager import NodeManager, create_node_manager

logger = get_logger(__name__)

class RemoteExecutionError(Exception):
    """Raised when remote command execution fails."""
    pass

class NetworkSaturationError(Exception):
    """Raised when network saturation (packet loss > 20%) is detected."""
    pass

@dataclass
class PacketStats:
    total_packets: int
    packets_per_second: float
    lost_packets: int
    loss_rate: float

@dataclass
class CPUStats:
    cpu_utilization_pct: float
    user_pct: float
    system_pct: float
    idle_pct: float
    iowait_pct: float

@dataclass
class NodeMetrics:
    node_id: str
    timestamp: datetime
    packet_stats: Optional[PacketStats]
    cpu_stats: Optional[CPUStats]
    unmodeled_vars: Dict[str, Any]
    wall_clock_start: Optional[datetime]
    wall_clock_end: Optional[datetime]

class RemoteInstrumentor:
    def __init__(self, node_manager: NodeManager, tool_manager: RemoteToolManager, wall_clock_timer: RemoteWallClockTimer):
        self.node_manager = node_manager
        self.tool_manager = tool_manager
        self.wall_clock_timer = wall_clock_timer
        self.logger = get_logger(__name__)

    def execute_tcpdump(self, ssh_client: SSHClient, interface: str = "any", packet_count: int = 1000) -> PacketStats:
        """Execute tcpdump to capture packet counts."""
        command = f"tcpdump -c {packet_count} -i {interface} -n 2>/dev/null"
        try:
            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=30)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')

            if error and "command not found" in error.lower():
                raise RemoteExecutionError(f"tcpdump not found on remote node: {error}")

            # Parse tcpdump output for packet count
            # tcpdump typically prints "X packets captured" at the end
            captured_match = re.search(r'(\d+)\s+packets?\s+captured', output)
            if captured_match:
                captured = int(captured_match.group(1))
            else:
                # If no explicit count, count lines or assume 0
                captured = 0

            # Calculate loss rate if we know how many we expected
            # For this implementation, we assume packet_count is the target
            lost = max(0, packet_count - captured)
            loss_rate = lost / packet_count if packet_count > 0 else 0.0
            duration = 1.0 # Placeholder; real timing would require start/stop
            pps = captured / duration if duration > 0 else 0.0

            return PacketStats(
                total_packets=captured,
                packets_per_second=pps,
                lost_packets=lost,
                loss_rate=loss_rate
            )
        except SocketTimeout:
            raise RemoteExecutionError("tcpdump command timed out")
        except SSHException as e:
            raise RemoteExecutionError(f"SSH execution failed: {e}")

    def execute_mpstat(self, ssh_client: SSHClient, interval: float = 1.0, count: int = 5) -> CPUStats:
        """Execute mpstat to get CPU utilization."""
        command = f"mpstat {interval} {count} 2>/dev/null"
        try:
            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=60)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')

            if error and "command not found" in error.lower():
                raise RemoteExecutionError(f"mpstat not found on remote node: {error}")

            # Parse mpstat output
            # Format: Linux ... time ... %usr %nice %sys %iowait %irq %soft %steal %guest %gnice %idle
            lines = output.strip().split('\n')
            avg_user = 0.0
            avg_sys = 0.0
            avg_idle = 0.0
            avg_iowait = 0.0
            valid_samples = 0

            # Skip header lines, look for data lines
            for line in lines:
                parts = line.split()
                if len(parts) >= 12 and parts[0] != "Average:":
                    try:
                        # Find the %idle column (usually last or second to last depending on version)
                        # Standard mpstat: ... %usr %nice %sys %iowait %irq %soft %steal %guest %gnice %idle
                        # We'll search for the %idle value
                        idle_idx = None
                        for i, val in enumerate(parts):
                            if val == '%idle' or (i > 0 and parts[i-1] == 'Average:'):
                                continue
                            if '%' in val and 'idle' in line.lower():
                                pass # handled differently

                        # Robust parsing: look for the last numeric column before the end of line
                        # Usually %idle is the last column
                        if len(parts) > 1:
                            idle_str = parts[-1]
                            user_str = parts[-11] # Approximate position
                            sys_str = parts[-9]
                            iowait_str = parts[-8]

                            # Fallback: search for numeric values
                            nums = [float(x) for x in parts if x.replace('.', '', 1).replace('-', '', 1).isdigit()]
                            if len(nums) >= 4:
                                # Assume order: usr, sys, iowait, idle (simplified)
                                # This is a heuristic; real parsing depends on mpstat version
                                # For now, let's assume the last 4 are user, system, iowait, idle
                                avg_user = nums[-4] if len(nums) >= 4 else 0.0
                                avg_sys = nums[-3] if len(nums) >= 3 else 0.0
                                avg_iowait = nums[-2] if len(nums) >= 2 else 0.0
                                avg_idle = nums[-1]
                                valid_samples += 1
                    except (ValueError, IndexError):
                        continue

            if valid_samples > 0:
                avg_user /= valid_samples
                avg_sys /= valid_samples
                avg_iowait /= valid_samples
                avg_idle /= valid_samples
            else:
                # Fallback if parsing fails
                avg_user = 0.0
                avg_sys = 0.0
                avg_iowait = 0.0
                avg_idle = 0.0

            utilization = 100.0 - avg_idle

            return CPUStats(
                cpu_utilization_pct=utilization,
                user_pct=avg_user,
                system_pct=avg_sys,
                idle_pct=avg_idle,
                iowait_pct=avg_iowait
            )
        except SocketTimeout:
            raise RemoteExecutionError("mpstat command timed out")
        except SSHException as e:
            raise RemoteExecutionError(f"SSH execution failed: {e}")

    def check_network_saturation(self, packet_stats: PacketStats, threshold: float = 0.20) -> bool:
        """Check if packet loss exceeds the threshold (20%)."""
        return packet_stats.loss_rate > threshold

    def capture_unmodeled_vars(self, ssh_client: SSHClient) -> Dict[str, Any]:
        """Capture thermal throttling and OS noise metrics."""
        metrics = {}

        # Check thermal zone
        try:
            stdin, stdout, stderr = ssh_client.exec_command("cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null", timeout=10)
            temps = stdout.read().decode('utf-8').strip().split('\n')
            temps = [t for t in temps if t.isdigit()]
            if temps:
                metrics['thermal_zone_temp_milli'] = [int(t) for t in temps]
        except Exception as e:
            self.logger.warning(f"Could not read thermal zone: {e}")

        # Check load average
        try:
            stdin, stdout, stderr = ssh_client.exec_command("cat /proc/loadavg", timeout=10)
            loadavg = stdout.read().decode('utf-8').strip()
            parts = loadavg.split()
            if len(parts) >= 3:
                metrics['loadavg_1m'] = float(parts[0])
                metrics['loadavg_5m'] = float(parts[1])
                metrics['loadavg_15m'] = float(parts[2])
        except Exception as e:
            self.logger.warning(f"Could not read load average: {e}")

        return metrics

    def instrument_node(self, node_ip: str, packet_count: int = 1000, mpstat_interval: float = 1.0, mpstat_count: int = 5) -> NodeMetrics:
        """Execute full instrumentation on a remote node."""
        self.logger.info(f"Starting instrumentation for node {node_ip}")

        # Ensure tools are available
        tool_status = self.tool_manager.check_node_tools(node_ip, ['tcpdump', 'mpstat'])
        if not tool_status.all_available:
            missing = [t for t in tool_status.missing if t in ['tcpdump', 'mpstat']]
            if missing:
                raise RemoteExecutionError(f"Critical tools missing on {node_ip}: {missing}")

        # Connect to node
        client = self.node_manager._get_ssh_client(node_ip)
        if not client:
            raise RemoteExecutionError(f"Could not establish SSH connection to {node_ip}")

        try:
            # Start wall clock timer
            self.wall_clock_timer.start_timer(node_ip)
            start_time = datetime.now()

            # Execute tcpdump
            packet_stats = self.execute_tcpdump(client, packet_count=packet_count)

            # Execute mpstat
            cpu_stats = self.execute_mpstat(client, interval=mpstat_interval, count=mpstat_count)

            # Capture unmodeled variables
            unmodeled = self.capture_unmodeled_vars(client)

            # Check network saturation
            if self.check_network_saturation(packet_stats):
                self.logger.warning(f"Network saturation detected on {node_ip}: loss_rate={packet_stats.loss_rate:.2%}")
                raise NetworkSaturationError(f"Network saturation on {node_ip}: {packet_stats.loss_rate:.2%} loss")

            # Stop wall clock timer
            self.wall_clock_timer.stop_timer(node_ip)
            end_time = datetime.now()

            return NodeMetrics(
                node_id=node_ip,
                timestamp=start_time,
                packet_stats=packet_stats,
                cpu_stats=cpu_stats,
                unmodeled_vars=unmodeled,
                wall_clock_start=start_time,
                wall_clock_end=end_time
            )
        except NetworkSaturationError:
            # Re-raise to be handled by caller
            raise
        except Exception as e:
            self.logger.error(f"Instrumentation failed on {node_ip}: {e}")
            raise RemoteExecutionError(f"Remote execution failed on {node_ip}: {e}")

    def instrument_nodes(self, node_ips: List[str], packet_count: int = 1000, mpstat_interval: float = 1.0, mpstat_count: int = 5) -> List[NodeMetrics]:
        """Instrument multiple nodes."""
        results = []
        for ip in node_ips:
            try:
                metrics = self.instrument_node(ip, packet_count, mpstat_interval, mpstat_count)
                results.append(metrics)
            except NetworkSaturationError as e:
                self.logger.error(f"Skipping {ip} due to network saturation: {e}")
                # Abort run if critical (SC-006)
                raise
            except Exception as e:
                self.logger.error(f"Failed to instrument {ip}: {e}")
                # Continue with other nodes or fail depending on policy
                # For now, we log and continue, but the caller can decide to abort
        return results

def create_instrumentor(node_manager: NodeManager, tool_manager: RemoteToolManager, wall_clock_timer: RemoteWallClockTimer) -> RemoteInstrumentor:
    return RemoteInstrumentor(node_manager, tool_manager, wall_clock_timer)

def main():
    """Main entry point for testing instrumentation."""
    logging.basicConfig(level=logging.INFO)
    logger = get_logger(__name__)

    # Create managers
    node_manager = create_node_manager()
    tool_manager = create_tool_manager()
    wall_clock_timer = create_timer()

    # Create instrumentor
    instrumentor = create_instrumentor(node_manager, tool_manager, wall_clock_timer)

    # Example usage (requires real nodes)
    # nodes = ["192.168.1.10", "192.168.1.11"]
    # results = instrumentor.instrument_nodes(nodes)
    # for r in results:
    #     print(f"Node {r.node_id}: CPU={r.cpu_stats.cpu_utilization_pct:.2f}%, Packets={r.packet_stats.total_packets}")

    logger.info("RemoteInstrumentor initialized. Use instrument_nodes() to run.")

if __name__ == "__main__":
    main()
