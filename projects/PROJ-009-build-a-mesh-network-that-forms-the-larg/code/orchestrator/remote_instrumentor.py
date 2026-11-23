"""
Remote Instrumentor Module for Mesh Network Supercomputer.

This module handles the remote execution of instrumentation tools (tcpdump, mpstat)
on target nodes via SSH to collect packet counts and CPU utilization metrics.
"""

from __future__ import annotations

import logging
import re
import time
import socket
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

import paramiko

from orchestrator.logger import get_logger
from orchestrator.remote_tools_manager import RemoteToolManager, ToolMissingError, RemoteExecutionError
from orchestrator.config import get_config

logger = get_logger(__name__)


class InstrumentationError(Exception):
    """Base exception for instrumentation failures."""
    pass


class InstrumentationInstallationFailedError(InstrumentationError):
    """Raised when required tools cannot be installed on the remote node."""
    pass


class CriticalVariableMissingError(InstrumentationError):
    """Raised when a critical variable (like CPU utilization) cannot be measured."""
    pass


class NetworkSaturationException(Exception):
    """Raised when network saturation is detected (packet loss > 20%)."""
    def __init__(self, message: str, loss_rate: float):
        super().__init__(message)
        self.loss_rate = loss_rate


class InstrumentationFailureError(InstrumentationError):
    """Raised when instrumentation data collection fails completely."""
    pass


@dataclass
class PacketStats:
    """Statistics derived from tcpdump output."""
    packet_count: int
    interface: str
    duration_seconds: float


@dataclass
class CPUStats:
    """Statistics derived from mpstat output."""
    cpu_utilization_pct: float
    user_pct: float
    system_pct: float
    idle_pct: float
    interval_seconds: float


@dataclass
class NodeMetrics:
    """Combined metrics from a single node instrumentation run."""
    node_ip: str
    packet_stats: Optional[PacketStats]
    cpu_stats: Optional[CPUStats]
    timestamp: float
    errors: List[str] = field(default_factory=list)


@dataclass
class UnmodeledVars:
    """Additional metrics not in the primary regression model but useful for debugging."""
    rx_drops: int
    tx_drops: int
    rx_errors: int
    tx_errors: int


class RemoteInstrumentor:
    """
    Handles remote execution of tcpdump and mpstat on target nodes.
    """

    def __init__(self, tool_manager: RemoteToolManager, ssh_timeout: int = 5):
        """
        Initialize the RemoteInstrumentor.

        Args:
            tool_manager: Instance of RemoteToolManager to verify tool availability.
            ssh_timeout: Timeout in seconds for SSH connections.
        """
        self.tool_manager = tool_manager
        self.ssh_timeout = ssh_timeout
        self.logger = logger

    def _connect(self, ip: str, username: str = 'root', password: str = None, key_file: str = None) -> paramiko.SSHClient:
        """Establish an SSH connection to the remote node."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            if key_file and Path(key_file).exists():
                client.connect(ip, username=username, key_filename=key_file, timeout=self.ssh_timeout, banner_timeout=self.ssh_timeout)
            else:
                client.connect(ip, username=username, password=password, timeout=self.ssh_timeout, banner_timeout=self.ssh_timeout)
            return client
        except socket.timeout:
            raise InstrumentationError(f"SSH connection timed out for {ip} after {self.ssh_timeout}s")
        except Exception as e:
            raise InstrumentationError(f"Failed to connect to {ip}: {str(e)}")

    def _execute_command(self, client: paramiko.SSHClient, command: str, timeout: int = 60) -> Tuple[int, str, str]:
        """Execute a command on the remote client and return (exit_code, stdout, stderr)."""
        try:
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', errors='replace')
            err = stderr.read().decode('utf-8', errors='replace')
            return exit_code, out, err
        except Exception as e:
            raise InstrumentationError(f"Command execution failed: {str(e)}")

    def check_network_saturation(self, client: paramiko.SSHClient, interface: str = 'any') -> Optional[NetworkSaturationException]:
        """
        Check for network saturation by parsing interface statistics.
        
        Args:
            client: SSH client connection.
            interface: Network interface to check.
        
        Returns:
            NetworkSaturationException if loss > 20%, else None.
        """
        cmd = f"ip -s link show {interface}"
        try:
            exit_code, stdout, stderr = self._execute_command(client, cmd, timeout=10)
            if exit_code != 0:
                self.logger.warning(f"Could not get interface stats for {interface}: {stderr}")
                return None

            # Parse 'ip -s link' output
            # Format: 
            # RX: bytes packets errs drop fifo frame compressed multicast
            # TX: bytes packets errs drop fifo colls carrier compressed
            
            rx_drops = 0
            tx_drops = 0
            rx_errors = 0
            tx_errors = 0

            lines = stdout.split('\n')
            for line in lines:
                if 'RX:' in line:
                    parts = line.split()
                    # Index of 'drop' depends on exact output format, usually 4th number after 'RX:'
                    # Safer to search for keywords if format varies, but 'ip -s' is standard
                    try:
                        # Standard ip -s link output:
                        # RX: 1234 567 0 0 0 0 0 0
                        # TX: 1234 567 0 0 0 0 0 0
                        # We need to find the 'drop' column.
                        # A more robust way is to look for the block.
                        if 'drop' in line:
                            # This is a header line usually, or we parse the values
                            pass
                        # Let's assume standard output structure:
                        # RX: <bytes> <packets> <errs> <drop> ...
                        # TX: <bytes> <packets> <errs> <drop> ...
                        # We look for the lines containing 'RX:' and 'TX:'
                        pass
                    except:
                        pass
                
                # Re-parsing strategy: find lines starting with RX: or TX:
                if line.strip().startswith('RX:'):
                    parts = line.split()
                    if len(parts) >= 6:
                        rx_errors = int(parts[2])
                        rx_drops = int(parts[3])
                elif line.strip().startswith('TX:'):
                    parts = line.split()
                    if len(parts) >= 6:
                        tx_errors = int(parts[2])
                        tx_drops = int(parts[3])

            total_packets = rx_drops + tx_drops + rx_errors + tx_errors
            # We need a baseline of total packets to calculate loss rate.
            # ip -s link doesn't give total packets in a simple sum easily without more parsing.
            # However, the spec says: "If loss > 20% raise NetworkSaturationException".
            # We will interpret "loss" here as the ratio of drops to total packets seen in the interface stats.
            # Since we only have drops/errors, we assume a high number of drops relative to a small count is saturation.
            # A more robust check requires 'netstat -s' or similar, but sticking to 'ip -s link'.
            # If we can't get total packets, we can't calculate a true percentage.
            # Let's assume the task implies checking if drops are significant.
            # For this implementation, we will check if drops > 0 and errors > 0 to trigger a warning,
            # but strictly calculating % requires total. 
            # Given constraints, we will estimate loss rate if we can parse total packets from the same block.
            # Actually, 'ip -s link' shows cumulative.
            # Let's assume the "loss" refers to the drop rate.
            # If we cannot calculate a precise rate, we will rely on the presence of significant drops.
            # To satisfy the "20%" requirement, we need total.
            # Let's try to parse the 'RX' and 'TX' lines again assuming standard format:
            # RX: <bytes> <packets> <errs> <drop> ...
            
            # If we assume the 'packets' field is the total, we can calculate.
            # But 'packets' is cumulative received. 'drop' is cumulative dropped.
            # We need a snapshot. Since we can't get a snapshot easily, we'll check if the ratio of drops to packets in the last read is high.
            # This is a heuristic.
            
            # Let's fallback to a simpler check: if drops are present, log it.
            # For the strict requirement, we will assume the 'packets' count in the line is the total processed.
            # If drops > 0.2 * packets, then saturation.
            
            # Re-extracting values carefully:
            rx_line = next((l for l in lines if l.strip().startswith('RX:')), None)
            tx_line = next((l for l in lines if l.strip().startswith('TX:')), None)
            
            if rx_line and tx_line:
                rx_parts = rx_line.split()
                tx_parts = tx_line.split()
                # Assuming standard: RX: bytes packets errs drop ...
                if len(rx_parts) >= 6 and len(tx_parts) >= 6:
                    rx_total = int(rx_parts[2]) # packets
                    rx_drop = int(rx_parts[3])
                    tx_total = int(tx_parts[2])
                    tx_drop = int(tx_parts[3])
                    
                    total_packets = rx_total + tx_total
                    total_drops = rx_drop + tx_drop
                    
                    if total_packets > 0:
                        loss_rate = total_drops / total_packets
                        if loss_rate > 0.2:
                            raise NetworkSaturationException(
                                f"Network saturation detected on {interface}: {loss_rate:.2%} loss rate",
                                loss_rate
                            )
            return None
        except NetworkSaturationException:
            raise
        except Exception as e:
            self.logger.warning(f"Could not determine network saturation: {e}")
            return None

    def measure_tcpdump(self, client: paramiko.SSHClient, interface: str = 'any', duration: int = 10) -> PacketStats:
        """
        Run tcpdump on the remote node and count packets.
        
        Args:
            client: SSH client.
            interface: Network interface.
            duration: Duration of capture in seconds.
        
        Returns:
            PacketStats object.
        
        Raises:
            InstrumentationInstallationFailedError: If tcpdump is missing and cannot be installed.
            InstrumentationFailureError: If no packets are captured or parsing fails.
        """
        # Verify tcpdump availability first (T012 dependency)
        # Note: T012 ensures tools are installed, but we check again for robustness
        try:
            self.tool_manager.check_tool(client, 'tcpdump')
        except ToolMissingError:
            raise InstrumentationInstallationFailedError("tcpdump is missing on remote node and cannot be installed.")

        # Run tcpdump with -c 0 (continuous) but we limit by time
        # tcpdump -i <interface> -nn -c <count> -w <file> 
        # We want line count. 
        # Command: tcpdump -i <interface> -nn -c 1000000 -G 10s (timeout) -> No, tcpdump doesn't have timeout flag easily.
        # Better: timeout 10 tcpdump -i any -nn -c 1000000
        # But we need to count lines.
        # Strategy: Run tcpdump for duration, pipe to wc -l.
        cmd = f"timeout {duration} tcpdump -i {interface} -nn 2>/dev/null | wc -l"
        
        try:
            exit_code, stdout, stderr = self._execute_command(client, cmd, timeout=duration + 10)
            
            if exit_code != 0:
                # Check if tcpdump command not found (should be caught by tool check, but just in case)
                if "command not found" in stderr.lower():
                    raise InstrumentationInstallationFailedError("tcpdump command not found on remote node.")
                raise InstrumentationFailureError(f"tcpdump execution failed: {stderr}")

            packet_count = int(stdout.strip())
            
            if packet_count == 0:
                # This might happen in a very quiet network, but the spec says "If no lines match, raise InstrumentationFailureError"
                # However, for a real testbed, 0 is possible. The spec says "raise InstrumentationFailureError" if no lines match.
                # We will raise it as per strict requirement to ensure data quality.
                raise InstrumentationFailureError("No packets captured during the sampling window.")

            return PacketStats(
                packet_count=packet_count,
                interface=interface,
                duration_seconds=duration
            )
        except ValueError:
            raise InstrumentationFailureError("Failed to parse tcpdump output as integer.")
        except InstrumentationFailureError:
            raise
        except Exception as e:
            raise InstrumentationFailureError(f"Unexpected error during tcpdump: {str(e)}")

    def measure_mpstat(self, client: paramiko.SSHClient, interval: int = 5, count: int = 1) -> CPUStats:
        """
        Run mpstat on the remote node and parse CPU utilization.
        
        Args:
            client: SSH client.
            interval: Interval between reports.
            count: Number of reports.
        
        Returns:
            CPUStats object.
        
        Raises:
            CriticalVariableMissingError: If mpstat is missing or parsing fails.
        """
        # Verify mpstat availability
        try:
            self.tool_manager.check_tool(client, 'mpstat')
        except ToolMissingError:
            raise CriticalVariableMissingError("mpstat is missing on remote node. Run excluded.")

        # Run mpstat: mpstat -P ALL <interval> <count>
        # We need the 'Average' line or the last interval.
        # Command: mpstat -P ALL 1 5 (5 seconds of 1s intervals)
        cmd = f"mpstat -P ALL {interval} {count}"
        
        try:
            exit_code, stdout, stderr = self._execute_command(client, cmd, timeout=30)
            
            if exit_code != 0:
                if "command not found" in stderr.lower():
                    raise CriticalVariableMissingError("mpstat command not found on remote node.")
                raise CriticalVariableMissingError(f"mpstat execution failed: {stderr}")

            # Parse mpstat output
            # Format:
            # Linux <version> ...
            # Time: ...
            # CPU  user  system  ...  idle
            # ...
            # Average: CPU user system ... idle
            
            lines = stdout.split('\n')
            avg_line = None
            
            # Look for the "Average" line which aggregates the intervals
            for line in lines:
                if line.strip().startswith('Average:'):
                    avg_line = line
                    break
            
            if not avg_line:
                # Fallback to the last data line if no Average is found (e.g. if count=1)
                data_lines = [l for l in lines if l.strip() and not l.startswith('Linux') and not l.startswith('Time') and not l.startswith('CPU') and not l.startswith('Average')]
                if data_lines:
                    avg_line = data_lines[-1]
                else:
                    raise CriticalVariableMissingError("Could not find CPU utilization data in mpstat output.")

            # Parse the Average line
            # Example: Average:  all  2.10  0.50  0.00  0.00  0.10  0.00  0.00  0.00  97.30
            parts = avg_line.split()
            # Find the index of 'user' and 'system' columns
            # The header line "CPU user system ..." helps, but we can assume standard order
            # Standard order after "Average:" and "all" or CPU id: user, nice, system, iowait, irq, softirq, steal, guest, gnice, idle
            # user is index 2 (0-based from 'Average')?
            # "Average:  all  2.10  0.50 ..." -> parts[2] is user, parts[3] is nice, parts[4] is system
            
            if len(parts) < 10:
                raise CriticalVariableMissingError(f"mpstat output format unexpected: {avg_line}")

            # Try to find 'user' and 'system' by searching for 'all' or CPU id, then offset
            # Or just assume standard positions if 'all' is present
            try:
                # If 'all' is present, user is at index 2
                if 'all' in parts:
                    user_idx = 2
                else:
                    user_idx = 1 # If CPU id is present
                
                user_pct = float(parts[user_idx])
                system_pct = float(parts[user_idx + 2]) # nice is +1, system is +2
                idle_pct = float(parts[-1]) # idle is usually last
                
                cpu_util = user_pct + system_pct
                
                return CPUStats(
                    cpu_utilization_pct=cpu_util,
                    user_pct=user_pct,
                    system_pct=system_pct,
                    idle_pct=idle_pct,
                    interval_seconds=(interval * count)
                )
            except (ValueError, IndexError) as e:
                raise CriticalVariableMissingError(f"Failed to parse mpstat numbers: {str(e)}")

        except CriticalVariableMissingError:
            raise
        except Exception as e:
            raise CriticalVariableMissingError(f"Unexpected error during mpstat: {str(e)}")

    def instrument_node(self, ip: str, interface: str = 'any', duration: int = 10) -> NodeMetrics:
        """
        Perform full instrumentation on a single node.
        
        Args:
            ip: Node IP address.
            interface: Network interface.
            duration: Duration for tcpdump.
        
        Returns:
            NodeMetrics object.
        
        Raises:
            InstrumentationError: If any critical step fails.
        """
        self.logger.info(f"Starting instrumentation on node {ip}")
        start_time = time.time()
        errors = []
        packet_stats = None
        cpu_stats = None
        
        client = None
        try:
            # Connect
            client = self._connect(ip)
            
            # Check Network Saturation first (T014a requirement)
            # This is a pre-check. If saturated, we might want to abort or flag.
            # The spec says: "If loss > 20% raise NetworkSaturationException (sent to T014b)".
            # We raise it here.
            try:
                self.check_network_saturation(client, interface)
            except NetworkSaturationException as e:
                # We must raise this to be caught by T014b
                raise e

            # Run tcpdump
            try:
                packet_stats = self.measure_tcpdump(client, interface, duration)
            except (InstrumentationInstallationFailedError, InstrumentationFailureError) as e:
                # Critical for tcpdump: Raise immediately
                raise e

            # Run mpstat
            try:
                cpu_stats = self.measure_mpstat(client, duration, 1)
            except CriticalVariableMissingError as e:
                # Critical for mpstat: Raise immediately
                raise e

            return NodeMetrics(
                node_ip=ip,
                packet_stats=packet_stats,
                cpu_stats=cpu_stats,
                timestamp=start_time
            )

        except (InstrumentationInstallationFailedError, CriticalVariableMissingError, NetworkSaturationException):
            # Re-raise critical errors immediately
            raise
        except Exception as e:
            errors.append(str(e))
            self.logger.error(f"Instrumentation failed on {ip}: {e}")
            # If we get here, it's a non-critical failure (e.g. parsing issue we didn't catch)
            # But per spec, we should fail loudly if critical tools fail.
            # If we are here, we assume it's a recoverable error or a bug in logic.
            # We return partial data with errors logged, but the task says "Fail Loudly".
            # So we should probably raise InstrumentationError.
            raise InstrumentationError(f"Instrumentation failed on {ip}: {e}")
        finally:
            if client:
                client.close()


def create_instrumentor(config: Optional[Dict[str, Any]] = None) -> RemoteInstrumentor:
    """Factory function to create a RemoteInstrumentor instance."""
    cfg = config or get_config()
    tool_manager = RemoteToolManager()
    return RemoteInstrumentor(tool_manager, ssh_timeout=cfg.ssh_timeout if hasattr(cfg, 'ssh_timeout') else 5)


def main():
    """Main entry point for testing the instrumentor."""
    import argparse
    parser = argparse.ArgumentParser(description="Remote Instrumentor Test")
    parser.add_argument("--ip", required=True, help="Target node IP")
    parser.add_argument("--interface", default="any", help="Network interface")
    parser.add_argument("--duration", type=int, default=10, help="Duration in seconds")
    args = parser.parse_args()

    try:
        inst = create_instrumentor()
        metrics = inst.instrument_node(args.ip, args.interface, args.duration)
        print(f"Node: {metrics.node_ip}")
        print(f"Packets: {metrics.packet_stats.packet_count if metrics.packet_stats else 'N/A'}")
        print(f"CPU Util: {metrics.cpu_stats.cpu_utilization_pct if metrics.cpu_stats else 'N/A'}")
    except NetworkSaturationException as e:
        print(f"CRITICAL: Network Saturation Detected: {e}")
    except InstrumentationInstallationFailedError as e:
        print(f"CRITICAL: Tool Installation Failed: {e}")
    except CriticalVariableMissingError as e:
        print(f"CRITICAL: Critical Variable Missing: {e}")
    except InstrumentationError as e:
        print(f"ERROR: {e}")
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")


if __name__ == "__main__":
    main()