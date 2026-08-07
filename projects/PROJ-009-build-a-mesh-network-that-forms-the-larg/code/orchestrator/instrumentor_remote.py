from __future__ import annotations

import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import paramiko

from orchestrator.logger import get_logger
from orchestrator.models import PhysicalNode, NodeStatus

# Custom Exceptions
class RemoteExecutionError(Exception):
    """Raised when remote command execution fails."""
    pass

class NetworkSaturationError(Exception):
    """Raised when packet loss exceeds the saturation threshold (20%)."""
    pass

@dataclass
class PacketStats:
    packet_count: int
    interface: str
    timestamp: datetime

@dataclass
class CPUStats:
    cpu_utilization_pct: float
    timestamp: datetime
    node_id: str

@dataclass
class NodeMetrics:
    node_id: str
    packet_stats: Optional[PacketStats]
    cpu_stats: Optional[CPUStats]
    timestamp: datetime
    raw_tcpdump_output: Optional[str] = None
    raw_mpstat_output: Optional[str] = None

class RemoteInstrumentor:
    """
    Handles remote execution of tcpdump and mpstat on target nodes via SSH.
    Depends on T013 (NodeManager) for SSH client management and T012b for tool availability.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or get_logger(__name__)
        self.tcpdump_cmd = "tcpdump -c {count} -i any -n"
        self.mpstat_cmd = "mpstat {interval} 5"
        self.saturation_threshold = 0.20  # 20%

    def execute_remote_command(
        self, 
        ssh_client: paramiko.SSHClient, 
        command: str, 
        timeout: int = 60
    ) -> Tuple[str, str]:
        """
        Executes a command on the remote SSH client.
        Returns (stdout, stderr).
        Raises RemoteExecutionError on failure.
        """
        try:
            self.logger.debug(f"Executing remote command: {command}")
            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=timeout)
            stdout_text = stdout.read().decode('utf-8', errors='replace')
            stderr_text = stderr.read().decode('utf-8', errors='replace')
            
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                raise RemoteExecutionError(
                    f"Command '{command}' failed with exit code {exit_status}: {stderr_text}"
                )
            return stdout_text, stderr_text
        except paramiko.SSHException as e:
            raise RemoteExecutionError(f"SSH execution failed: {str(e)}")
        except Exception as e:
            raise RemoteExecutionError(f"Unexpected error during remote execution: {str(e)}")

    def run_tcpdump(
        self, 
        ssh_client: paramiko.SSHClient, 
        packet_count: int = 100, 
        timeout: int = 120
    ) -> PacketStats:
        """
        Runs tcpdump remotely to capture packet counts.
        """
        cmd = self.tcpdump_cmd.format(count=packet_count)
        stdout, stderr = self.execute_remote_command(ssh_client, cmd, timeout)
        
        # Parse packet count from output (tcpdump usually prints "X packets captured")
        # Standard tcpdump output: "X packets captured" at the end or in summary
        packet_count_found = 0
        lines = stdout.strip().split('\n')
        for line in lines:
            match = re.search(r'(\d+)\s+packets\s+captured', line, re.IGNORECASE)
            if match:
                packet_count_found = int(match.group(1))
                break
        
        # Fallback: if no explicit capture count, count lines if it's a raw dump (less reliable but handles edge cases)
        if packet_count_found == 0:
            # Count non-empty lines that look like packet data
            packet_count_found = len([l for l in lines if l.strip() and not l.startswith('listening on') and not l.startswith('tcpdump')])
            # Adjust if it's just a summary line
            if packet_count_found == 1 and "packets" in stdout.lower():
                # Try to find the number before "packets"
                match = re.search(r'(\d+)\s+packets', stdout, re.IGNORECASE)
                if match:
                    packet_count_found = int(match.group(1))

        if packet_count_found <= 0:
            self.logger.warning(f"No packets captured on remote host. Output: {stdout[:200]}")

        return PacketStats(
            packet_count=packet_count_found,
            interface="any",
            timestamp=datetime.now()
        )

    def check_network_saturation(self, packet_stats: PacketStats, expected_packets: int) -> None:
        """
        Checks if packet loss exceeds 20%.
        Raises NetworkSaturationError if saturated.
        Note: This assumes we sent a request for `expected_packets` and got `packet_stats.packet_count`.
        In a real scenario, we might compare sent vs received, but here we infer from capture count vs request.
        If capture count is significantly lower than requested count, it implies drop/loss or interface issues.
        For this specific task, we check if the ratio of captured to requested is < 0.8.
        """
        if expected_packets > 0:
            loss_ratio = 1.0 - (packet_stats.packet_count / expected_packets)
            if loss_ratio > self.saturation_threshold:
                raise NetworkSaturationError(
                    f"Network saturation detected: {loss_ratio:.2%} packet loss (>{self.saturation_threshold:.0%}). "
                    f"Requested: {expected_packets}, Captured: {packet_stats.packet_count}"
                )

    def run_mpstat(
        self, 
        ssh_client: paramiko.SSHClient, 
        interval: int = 1, 
        count: int = 5,
        timeout: int = 120
    ) -> CPUStats:
        """
        Runs mpstat remotely to capture CPU usage.
        Format: mpstat <interval> <count>
        """
        cmd = self.mpstat_cmd.format(interval=interval)
        stdout, stderr = self.execute_remote_command(ssh_client, cmd, timeout)
        
        # Parse mpstat output
        # Typical format:
        # Linux 5.x.x (hostname)    date    time
        # Average:   CPU    %usr   %nice   %sys   %iowait   %irq   %soft   %steal   %guest   %gnice   %idle
        # Average:   all    5.00   0.00    2.00   0.50      0.00   0.00    0.00     0.00     0.00     92.50
        
        cpu_utilization = 0.0
        lines = stdout.strip().split('\n')
        
        # Find the "Average:" line which summarizes the run
        avg_line = None
        for line in lines:
            if line.strip().startswith("Average:"):
                avg_line = line
                break
        
        if not avg_line:
            # Fallback: try to parse the last data line if no average summary
            # This is less robust but handles cases where mpstat version differs
            for line in reversed(lines):
                if "all" in line.lower() or line.strip().isdigit():
                    # Check if it looks like data
                    if re.search(r'\d+\.\d+', line):
                        avg_line = line
                        break

        if avg_line:
            # Split by whitespace
            parts = avg_line.split()
            # mpstat columns: CPU, %usr, %nice, %sys, %iowait, %irq, %soft, %steal, %guest, %gnice, %idle
            # We want 100 - %idle
            try:
                # Find the index of %idle. Usually it's the last column.
                # Standard order: CPU %usr %nice %sys %iowait %irq %soft %steal %guest %gnice %idle
                # If 'all' is first, indices shift.
                
                # Simple heuristic: look for the last float that is likely idle
                floats = [float(x) for x in parts if re.match(r'^\d+\.?\d*$', x)]
                if floats:
                    idle_pct = floats[-1] # Last number is usually %idle
                    cpu_utilization = 100.0 - idle_pct
            except (ValueError, IndexError) as e:
                self.logger.warning(f"Failed to parse mpstat idle value: {e}. Output: {avg_line}")
        else:
            self.logger.warning("Could not find Average or data line in mpstat output.")

        return CPUStats(
            cpu_utilization_pct=round(cpu_utilization, 2),
            timestamp=datetime.now(),
            node_id="" # Will be set by caller
        )

    def instrument_node(
        self, 
        node: PhysicalNode, 
        ssh_client: paramiko.SSHClient,
        packet_count: int = 100,
        mpstat_interval: int = 1,
        mpstat_count: int = 5
    ) -> NodeMetrics:
        """
        Orchestrates the full instrumentation of a single node.
        """
        self.logger.info(f"Instrumenting node {node.ip_address} (ID: {node.id})")
        
        packet_stats = None
        cpu_stats = None
        raw_tcpdump = ""
        raw_mpstat = ""

        try:
            # 1. Run tcpdump
            packet_stats = self.run_tcpdump(ssh_client, packet_count=packet_count)
            raw_tcpdump = f"Captured {packet_stats.packet_count} packets"
            
            # Check saturation
            self.check_network_saturation(packet_stats, packet_count)

            # 2. Run mpstat
            cpu_stats = self.run_mpstat(
                ssh_client, 
                interval=mpstat_interval, 
                count=mpstat_count
            )
            cpu_stats.node_id = node.id
            raw_mpstat = f"CPU Utilization: {cpu_stats.cpu_utilization_pct}%"

        except NetworkSaturationError:
            raise
        except RemoteExecutionError as e:
            self.logger.error(f"Remote instrumentation failed for node {node.id}: {e}")
            raise

        return NodeMetrics(
            node_id=node.id,
            packet_stats=packet_stats,
            cpu_stats=cpu_stats,
            timestamp=datetime.now(),
            raw_tcpdump_output=raw_tcpdump,
            raw_mpstat_output=raw_mpstat
        )

def create_instrumentor() -> RemoteInstrumentor:
    return RemoteInstrumentor()

def main():
    """
    CLI entry point for testing the instrumentor.
    Usage: python -m code.orchestrator.instrumentor_remote --ip <ip> --user <user>
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Remote Instrumentor for Mesh Network")
    parser.add_argument('--ip', required=True, help='Target node IP')
    parser.add_argument('--user', default='root', help='SSH User')
    parser.add_argument('--key', default=None, help='Path to SSH private key')
    parser.add_argument('--packet-count', type=int, default=100, help='Number of packets for tcpdump')
    parser.add_argument('--interval', type=int, default=1, help='mpstat interval')
    parser.add_argument('--count', type=int, default=5, help='mpstat count')
    
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Create a mock node for the test
    node = PhysicalNode(
        id=f"test_node_{args.ip.replace('.', '_')}",
        ip_address=args.ip,
        status=NodeStatus.AVAILABLE,
        hostname="test-host"
    )

    instrumentor = create_instrumentor()
    
    # Setup SSH
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        if args.key:
            ssh_client.connect(
                hostname=args.ip, 
                username=args.user, 
                key_filename=args.key, 
                timeout=10
            )
        else:
            # Fallback to password if no key (not recommended for prod, but useful for CLI)
            import getpass
            password = getpass.getpass(f"Password for {args.user}@{args.ip}: ")
            ssh_client.connect(
                hostname=args.ip, 
                username=args.user, 
                password=password, 
                timeout=10
            )

        metrics = instrumentor.instrument_node(
            node, 
            ssh_client, 
            packet_count=args.packet_count,
            mpstat_interval=args.interval,
            mpstat_count=args.count
        )

        print(f"\n--- Results for {node.id} ---")
        print(f"Packet Count: {metrics.packet_stats.packet_count}")
        print(f"CPU Utilization: {metrics.cpu_stats.cpu_utilization_pct}%")
        print(f"Timestamp: {metrics.timestamp}")

    except NetworkSaturationError as e:
        print(f"CRITICAL: {e}")
        sys.exit(1)
    except RemoteExecutionError as e:
        print(f"EXECUTION ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(1)
    finally:
        ssh_client.close()

if __name__ == "__main__":
    main()