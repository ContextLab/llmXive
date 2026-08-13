from __future__ import annotations

import logging
import re
import time
import socket
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
import paramiko

from orchestrator.logger import get_logger
from orchestrator.remote_tools_manager import RemoteToolManager, ToolMissingError

logger = get_logger(__name__)

class RemoteExecutionError(Exception):
    """Raised when remote command execution fails."""
    pass

class NetworkSaturationError(Exception):
    """Raised when network saturation is detected (>20% packet loss)."""
    pass

class InstrumentationFailureError(Exception):
    """Raised when instrumentation parsing fails or critical tools are missing."""
    pass

@dataclass
class PacketStats:
    packet_count: int
    interface: str
    drops: int
    errors: int

@dataclass
class CPUStats:
    cpu_utilization_pct: Optional[float]
    user_pct: Optional[float]
    system_pct: Optional[float]
    idle_pct: Optional[float]

@dataclass
class UnmodeledVars:
    """Variables not explicitly modeled but captured for analysis."""
    thermal_throttle: bool = False
    os_noise: float = 0.0

@dataclass
class NodeMetrics:
    packet_count: int
    cpu_utilization_pct: Optional[float]
    snr_db: Optional[float] = None
    bandwidth_Mbps: Optional[float] = None
    unmodeled: UnmodeledVars = field(default_factory=UnmodeledVars)

class RemoteInstrumentor:
    """
    Handles remote execution of tcpdump and mpstat via SSH.
    Implements strict error handling for critical vs non-critical tools.
    """

    def __init__(self, ssh_client: paramiko.SSHClient, remote_tool_manager: RemoteToolManager):
        self.ssh = ssh_client
        self.tool_manager = remote_tool_manager
        self.logger = get_logger(__name__)

    def _execute_command(self, command: str, timeout: int = 60) -> Tuple[int, str, str]:
        """Execute a command on the remote node and return (exit_code, stdout, stderr)."""
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            out_str = stdout.read().decode('utf-8', errors='replace')
            err_str = stderr.read().decode('utf-8', errors='replace')
            return exit_code, out_str, err_str
        except socket.timeout:
            raise RemoteExecutionError(f"Command timed out after {timeout}s")
        except Exception as e:
            raise RemoteExecutionError(f"SSH execution failed: {str(e)}")

    def _run_tcpdump(self, interface: str = "any", count: int = 0) -> PacketStats:
        """
        Run tcpdump to capture packet counts.
        Critical tool: must succeed or raise InstrumentationFailureError.
        """
        # Check if tcpdump is available
        try:
            self.tool_manager.verify_tool_installed("tcpdump")
        except ToolMissingError:
            raise InstrumentationFailureError("tcpdump is missing and could not be installed (Critical).")

        # Run tcpdump with line counter
        # -i any: capture on all interfaces
        # -nn: no name resolution
        # -c 0: continuous (or a large number if 0 is restricted)
        # We use -c 100000 for a burst to simulate a run, then count lines.
        # In a real long-running scenario, we might pipe to a file, but here we count lines.
        cmd = f"tcpdump -i {interface} -nn -c 100000 2>/dev/null | wc -l"
        
        exit_code, stdout, stderr = self._execute_command(cmd, timeout=120)

        if exit_code != 0:
            self.logger.warning(f"tcpdump command failed: {stderr}")
            # If tcpdump itself failed (not just 0 packets), it's an instrumentation failure
            raise InstrumentationFailureError(f"tcpdump execution failed with code {exit_code}: {stderr}")

        try:
            packet_count = int(stdout.strip())
        except ValueError:
            raise InstrumentationFailureError(f"Failed to parse tcpdump line count: {stdout}")

        # Get drops/errors for saturation check
        # Parse interface stats
        iface_stats_cmd = f"ip -s link show {interface} 2>/dev/null || ip -s link show 2>/dev/null | head -20"
        _, stats_out, _ = self._execute_command(iface_stats_cmd, timeout=10)
        
        drops = 0
        errors = 0
        # Simple regex to find RX/TX drop lines
        # Format usually: RX: bytes packets errors dropped overr frame ...
        rx_match = re.search(r'RX:\s+\d+\s+\d+\s+\d+\s+(\d+)', stats_out)
        tx_match = re.search(r'TX:\s+\d+\s+\d+\s+\d+\s+(\d+)', stats_out)
        
        if rx_match:
            drops += int(rx_match.group(1))
        if tx_match:
            drops += int(tx_match.group(1)) # Assuming TX drops are also relevant

        # Check for errors
        err_match = re.search(r'(RX|TX):\s+\d+\s+\d+\s+(\d+)', stats_out)
        if err_match:
            errors = int(err_match.group(2))

        return PacketStats(packet_count=packet_count, interface=interface, drops=drops, errors=errors)

    def _run_mpstat(self) -> CPUStats:
        """
        Run mpstat to get CPU usage.
        Non-critical tool: if missing, return None for CPU stats and log warning.
        """
        try:
            self.tool_manager.verify_tool_installed("mpstat")
        except ToolMissingError:
            self.logger.warning("mpstat is missing. CPU utilization will be null.")
            return CPUStats(cpu_utilization_pct=None, user_pct=None, system_pct=None, idle_pct=None)

        # Run mpstat for 1 second, 1 interval
        cmd = "mpstat 1 1"
        exit_code, stdout, stderr = self._execute_command(cmd, timeout=30)

        if exit_code != 0:
            self.logger.warning(f"mpstat execution failed: {stderr}")
            return CPUStats(cpu_utilization_pct=None, user_pct=None, system_pct=None, idle_pct=None)

        # Parse the "Average" line or the last interval line
        # Format: CPU   %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
        lines = stdout.strip().split('\n')
        cpu_line = None
        
        # Look for the line with "Average" or the last line before footer
        for line in reversed(lines):
            if line.strip().startswith("Average:") or (line.strip() and not line.startswith("Linux")):
                # Check if it looks like a CPU line (has % signs or numbers)
                if re.search(r'%', line) or re.match(r'^CPU', line):
                    cpu_line = line
                    break

        if not cpu_line:
            self.logger.warning("Could not find CPU stats line in mpstat output.")
            return CPUStats(cpu_utilization_pct=None, user_pct=None, system_pct=None, idle_pct=None)

        # Parse numbers
        parts = cpu_line.split()
        # Skip header or "Average"
        if parts[0] == "Average":
            parts = parts[1:]
        
        # Expected: CPU, %usr, %nice, %sys, %iowait, %irq, %soft, %steal, %guest, %gnice, %idle
        # We need user + system (usr + sys)
        if len(parts) >= 4:
            try:
                user_pct = float(parts[1])
                sys_pct = float(parts[3])
                idle_pct = float(parts[-1]) # Usually last
                
                total_util = user_pct + sys_pct
                return CPUStats(
                    cpu_utilization_pct=total_util,
                    user_pct=user_pct,
                    system_pct=sys_pct,
                    idle_pct=idle_pct
                )
            except ValueError:
                self.logger.warning("Failed to parse mpstat numbers.")
                return CPUStats(cpu_utilization_pct=None, user_pct=None, system_pct=None, idle_pct=None)

        return CPUStats(cpu_utilization_pct=None, user_pct=None, system_pct=None, idle_pct=None)

    def check_network_saturation(self, packet_stats: PacketStats) -> bool:
        """
        Check if network saturation is detected based on drops.
        Uses ip -s link show to get drops/total ratio.
        Threshold: >20% loss.
        """
        # We need total packets to calculate rate. 
        # Since we only have drops from the stats command, we estimate total from tcpdump count + drops?
        # Or rely on the ip stats directly.
        # Let's re-fetch ip stats to be precise about total packets seen by kernel.
        iface = packet_stats.interface
        cmd = f"ip -s link show {iface} 2>/dev/null || ip -s link show 2>/dev/null | head -20"
        _, stats_out, _ = self._execute_command(cmd, timeout=10)

        # Parse RX and TX packets and drops
        # RX: packets drops ...
        rx_match = re.search(r'RX:\s+(\d+)\s+\d+\s+\d+\s+(\d+)', stats_out)
        tx_match = re.search(r'TX:\s+(\d+)\s+\d+\s+\d+\s+(\d+)', stats_out)

        if rx_match:
            rx_total = int(rx_match.group(1))
            rx_drops = int(rx_match.group(2))
        else:
            rx_total = 0
            rx_drops = 0

        if tx_match:
            tx_total = int(tx_match.group(1))
            tx_drops = int(tx_match.group(2))
        else:
            tx_total = 0
            tx_drops = 0

        total_packets = rx_total + tx_total
        total_drops = rx_drops + tx_drops

        if total_packets == 0:
            return False

        loss_rate = total_drops / total_packets
        return loss_rate > 0.20

    def collect_metrics(self, interface: str = "any") -> NodeMetrics:
        """
        Main entry point to collect all metrics.
        """
        self.logger.info(f"Collecting metrics on remote node (interface={interface})")

        # 1. Packet Stats (Critical)
        try:
            packet_stats = self._run_tcpdump(interface)
        except InstrumentationFailureError as e:
            self.logger.error(f"Critical instrumentation failure: {e}")
            raise e

        # 2. Check Saturation
        if self.check_network_saturation(packet_stats):
            self.logger.error("Network saturation detected (>20% loss).")
            raise NetworkSaturationError("Network saturation detected.")

        # 3. CPU Stats (Non-Critical)
        cpu_stats = self._run_mpstat()

        return NodeMetrics(
            packet_count=packet_stats.packet_count,
            cpu_utilization_pct=cpu_stats.cpu_utilization_pct,
            unmodeled=UnmodeledVars()
        )

def create_instrumentor(ssh_client: paramiko.SSHClient, tool_manager: RemoteToolManager) -> RemoteInstrumentor:
    return RemoteInstrumentor(ssh_client, tool_manager)

def main():
    """
    Example usage for testing.
    Requires SSH config or command line args to connect.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Remote Instrumentor")
    parser.add_argument('--host', required=True, help='Remote host IP')
    parser.add_argument('--user', default='root', help='SSH user')
    parser.add_argument('--key', help='Path to private key')
    args = parser.parse_args()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        if args.key:
            ssh.connect(args.host, username=args.user, key_filename=args.key, timeout=10)
        else:
            ssh.connect(args.host, username=args.user, timeout=10)
        
        tool_mgr = RemoteToolManager(ssh)
        instrumentor = create_instrumentor(ssh, tool_mgr)
        
        metrics = instrumentor.collect_metrics()
        print(f"Metrics: {metrics}")
        
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        raise
    finally:
        ssh.close()

if __name__ == '__main__':
    main()