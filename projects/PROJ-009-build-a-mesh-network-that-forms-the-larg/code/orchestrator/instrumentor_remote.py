"""
Remote Instrumentor for Mesh Network Supercomputer.
Executes tcpdump and mpstat on remote nodes via SSH and parses results.
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
from orchestrator.remote_tools_manager import RemoteToolManager, ToolMissingError
from orchestrator.config import get_config

# Configure logging
logger = get_logger(__name__)

@dataclass
class PacketStats:
    """Statistics derived from tcpdump execution."""
    packet_count: int
    interface: str
    duration_seconds: float

@dataclass
class CPUStats:
    """Statistics derived from mpstat execution."""
    cpu_utilization_pct: float
    user_pct: float
    system_pct: float
    idle_pct: float
    interval_seconds: float

@dataclass
class UnmodeledVars:
    """Best-effort capture of unmodeled variables (thermal, OS noise)."""
    thermal_zone: Optional[float] = None
    loadavg_1m: Optional[float] = None
    loadavg_5m: Optional[float] = None
    loadavg_15m: Optional[float] = None
    warnings: List[str] = field(default_factory=list)

@dataclass
class NodeMetrics:
    """Aggregated metrics from a single remote node."""
    node_id: str
    packet_stats: Optional[PacketStats]
    cpu_stats: Optional[CPUStats]
    unmodeled_vars: UnmodeledVars
    wall_clock_time: float
    instrumentation_status: str  # 'complete', 'partial', 'failed'
    error_message: Optional[str] = None

class RemoteExecutionError(Exception):
    """Raised when remote command execution fails."""
    pass

class NetworkSaturationError(Exception):
    """Raised when network saturation (>20% packet loss) is detected."""
    def __init__(self, message: str, packet_loss_rate: float):
        super().__init__(message)
        self.packet_loss_rate = packet_loss_rate

class RemoteInstrumentor:
    """Handles remote instrumentation via SSH."""

    def __init__(self, tool_manager: RemoteToolManager):
        self.tool_manager = tool_manager
        self.logger = get_logger(__name__)

    def _execute_ssh_command(self, ssh_client: paramiko.SSHClient, command: str, timeout: int = 60) -> Tuple[str, str, int]:
        """Execute a command on the remote host and return stdout, stderr, exit status."""
        try:
            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=timeout)
            exit_status = stdout.channel.recv_exit_status()
            stdout_str = stdout.read().decode('utf-8', errors='ignore')
            stderr_str = stderr.read().decode('utf-8', errors='ignore')
            return stdout_str, stderr_str, exit_status
        except socket.timeout:
            raise RemoteExecutionError(f"SSH command timed out: {command}")
        except Exception as e:
            raise RemoteExecutionError(f"SSH command failed: {e}")

    def check_network_saturation(self, packet_loss_rate: float) -> bool:
        """Check if packet loss exceeds 20% threshold."""
        return packet_loss_rate > 0.20

    def capture_unmodeled_vars(self, ssh_client: paramiko.SSHClient) -> UnmodeledVars:
        """Capture thermal and OS noise metrics on a best-effort basis."""
        unmodeled = UnmodeledVars()

        # Try to get thermal zone
        try:
            stdout, stderr, code = self._execute_ssh_command(
                ssh_client, "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo 'N/A'"
            )
            if code == 0 and stdout.strip() != 'N/A':
                try:
                    # Value is often in millidegrees Celsius
                    val = int(stdout.strip())
                    unmodeled.thermal_zone = val / 1000.0
                except ValueError:
                    unmodeled.warnings.append("Failed to parse thermal zone value")
            else:
                unmodeled.warnings.append("Thermal zone not available")
        except Exception as e:
            unmodeled.warnings.append(f"Thermal zone capture failed: {e}")

        # Try to get load average
        try:
            stdout, stderr, code = self._execute_ssh_command(
                ssh_client, "cat /proc/loadavg"
            )
            if code == 0:
                parts = stdout.strip().split()
                if len(parts) >= 3:
                    unmodeled.loadavg_1m = float(parts[0])
                    unmodeled.loadavg_5m = float(parts[1])
                    unmodeled.loadavg_15m = float(parts[2])
                else:
                    unmodeled.warnings.append("Could not parse load average")
            else:
                unmodeled.warnings.append("Load average not available")
        except Exception as e:
            unmodeled.warnings.append(f"Load average capture failed: {e}")

        return unmodeled

    def run_tcpdump(self, ssh_client: paramiko.SSHClient, interface: str = "any", packet_count: int = 100) -> PacketStats:
        """
        Run tcpdump on remote node and count packets.
        Command: tcpdump -c <count> -i <interface> -n
        """
        # Check if tcpdump is available
        if not self.tool_manager.check_tool("tcpdump", ssh_client):
            raise ToolMissingError("tcpdump")

        start_time = time.time()
        cmd = f"tcpdump -c {packet_count} -i {interface} -n 2>/dev/null"

        stdout, stderr, exit_code = self._execute_ssh_command(ssh_client, cmd, timeout=packet_count + 10)

        duration = time.time() - start_time

        # Parse output: count non-empty lines or lines matching timestamp pattern
        # tcpdump output format: "HH:MM:SS.microseconds IP ..."
        # We count lines that look like tcpdump output
        packet_count_actual = 0
        if stdout:
            # Count lines matching timestamp pattern
            pattern = re.compile(r'^\d{2}:\d{2}:\d{2}\.\d+')
            lines = stdout.strip().split('\n')
            for line in lines:
                if line and (pattern.match(line) or not line.startswith("tcpdump:")):
                    # Skip tcpdump warning lines if any
                    if not line.startswith("tcpdump:"):
                        packet_count_actual += 1

        # If parsing fails or count is 0 but we expect packets, log warning
        if packet_count_actual == 0 and packet_count > 0:
            self.logger.warning(f"tcpdump returned 0 packets. Output: {stdout[:200]}")

        return PacketStats(
            packet_count=packet_count_actual,
            interface=interface,
            duration_seconds=duration
        )

    def run_mpstat(self, ssh_client: paramiko.SSHClient, interval: float = 1.0, count: int = 5) -> CPUStats:
        """
        Run mpstat on remote node and extract CPU utilization.
        Command: mpstat <interval> <count>
        """
        # Check if mpstat is available
        if not self.tool_manager.check_tool("mpstat", ssh_client):
            raise ToolMissingError("mpstat")

        cmd = f"mpstat {interval} {count}"
        stdout, stderr, exit_code = self._execute_ssh_command(ssh_client, cmd, timeout=count * interval + 10)

        # Parse mpstat output
        # Format: "Linux ... \n  CPU    %usr   %nice   %sys   %iowait   %irq   %soft   %steal   %guest   %gnice   %idle\n  all   ...   ...   ...   ...   ...   ...   ...   ...   ...   ..."
        # We need the "Average" line or the last interval line
        cpu_util = 0.0
        user_pct = 0.0
        system_pct = 0.0
        idle_pct = 0.0

        lines = stdout.strip().split('\n')
        avg_line = None
        last_data_line = None

        for line in lines:
            if "Average:" in line:
                avg_line = line
            elif line and not line.startswith("Linux") and not line.startswith("CPU") and not line.startswith(" ") and not line.startswith("all"):
                # This might be a data line
                if last_data_line is None or not avg_line:
                    last_data_line = line

        target_line = avg_line if avg_line else last_data_line

        if target_line:
            parts = target_line.split()
            # Typical mpstat output: "all  1.20  0.00  1.50  0.10  0.00  0.00  0.00  0.00  0.00  97.20"
            # Indices: 0=CPU, 1=usr, 2=nice, 3=sys, 4=iowait, 5=irq, 6=soft, 7=steal, 8=guest, 9=gnice, 10=idle
            if len(parts) >= 11:
                try:
                    user_pct = float(parts[1])
                    system_pct = float(parts[3])
                    idle_pct = float(parts[10])
                    cpu_util = user_pct + system_pct
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Failed to parse mpstat line: {target_line}, error: {e}")
                    cpu_util = 0.0
                    user_pct = 0.0
                    system_pct = 0.0
                    idle_pct = 100.0
            else:
                self.logger.warning(f"mpstat output line has insufficient columns: {target_line}")
        else:
            self.logger.warning("Could not find Average or data line in mpstat output")

        return CPUStats(
            cpu_utilization_pct=cpu_util,
            user_pct=user_pct,
            system_pct=system_pct,
            idle_pct=idle_pct,
            interval_seconds=interval * count
        )

    def instrument_node(self, ssh_client: paramiko.SSHClient, node_id: str, packet_count: int = 100) -> NodeMetrics:
        """
        Execute all instrumentation tasks on a remote node.
        """
        start_wall_clock = time.time()
        packet_stats = None
        cpu_stats = None
        unmodeled = UnmodeledVars()
        error_msg = None
        status = "complete"

        try:
            # Capture unmodeled vars first (best effort)
            unmodeled = self.capture_unmodeled_vars(ssh_client)

            # Run tcpdump
            try:
                packet_stats = self.run_tcpdump(ssh_client, packet_count=packet_count)
            except ToolMissingError:
                self.logger.warning(f"tcpdump not available on {node_id}, skipping packet stats")
                status = "partial"
            except Exception as e:
                self.logger.error(f"tcpdump failed on {node_id}: {e}")
                error_msg = f"tcpdump: {e}"
                status = "failed"

            # Run mpstat
            try:
                cpu_stats = self.run_mpstat(ssh_client)
            except ToolMissingError:
                self.logger.warning(f"mpstat not available on {node_id}, skipping CPU stats")
                if status != "failed":
                    status = "partial"
            except Exception as e:
                self.logger.error(f"mpstat failed on {node_id}: {e}")
                error_msg = f"mpstat: {e}"
                status = "failed"

            # Check for network saturation if we have packet stats
            if packet_stats and packet_stats.packet_count > 0:
                # Estimate packet loss rate (simplified: assume we requested N packets)
                # In a real scenario, we'd compare sent vs received. Here we assume 0 loss unless detected otherwise.
                # For now, we don't have a baseline to compare against, so we skip saturation check
                # unless we have a mechanism to measure loss.
                # TODO: Implement proper loss measurement if needed.
                pass

        except Exception as e:
            self.logger.error(f"Unexpected error during instrumentation of {node_id}: {e}")
            error_msg = str(e)
            status = "failed"

        end_wall_clock = time.time()

        return NodeMetrics(
            node_id=node_id,
            packet_stats=packet_stats,
            cpu_stats=cpu_stats,
            unmodeled_vars=unmodeled,
            wall_clock_time=end_wall_clock - start_wall_clock,
            instrumentation_status=status,
            error_message=error_msg
        )

def create_instrumentor() -> RemoteInstrumentor:
    """Factory function to create a RemoteInstrumentor."""
    tool_manager = RemoteToolManager()
    return RemoteInstrumentor(tool_manager)

def main():
    """Main entry point for testing instrumentation."""
    import argparse
    parser = argparse.ArgumentParser(description="Test remote instrumentation")
    parser.add_argument("--host", required=True, help="Remote host IP")
    parser.add_argument("--user", required=True, help="Remote username")
    parser.add_argument("--key", help="Path to SSH private key")
    parser.add_argument("--password", help="SSH password (if no key)")
    parser.add_argument("--packets", type=int, default=100, help="Number of packets for tcpdump")
    args = parser.parse_args()

    # Create SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if args.key:
            ssh.connect(args.host, username=args.user, key_filename=args.key)
        else:
            ssh.connect(args.host, username=args.user, password=args.password)

        instrumentor = create_instrumentor()
        metrics = instrumentor.instrument_node(ssh, args.host, args.packets)

        print(f"Node: {metrics.node_id}")
        print(f"Status: {metrics.instrumentation_status}")
        print(f"Wall Clock Time: {metrics.wall_clock_time:.2f}s")

        if metrics.packet_stats:
            print(f"Packets: {metrics.packet_stats.packet_count} in {metrics.packet_stats.duration_seconds:.2f}s")
        else:
            print("Packet stats: N/A")

        if metrics.cpu_stats:
            print(f"CPU Util: {metrics.cpu_stats.cpu_utilization_pct:.1f}% (User: {metrics.cpu_stats.user_pct:.1f}%, Sys: {metrics.cpu_stats.system_pct:.1f}%)")
        else:
            print("CPU stats: N/A")

        if metrics.unmodeled_vars.warnings:
            print("Warnings:")
            for w in metrics.unmodeled_vars.warnings:
                print(f"  - {w}")

        if metrics.error_message:
            print(f"Error: {metrics.error_message}")

    except Exception as e:
        print(f"Failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
