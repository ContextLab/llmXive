from __future__ import annotations
import logging
import re
import time
import socket
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
import paramiko
from paramiko import SSHClient, AutoAddPolicy, SSHException

from orchestrator.logger import get_logger
from orchestrator.remote_tools_manager import RemoteToolManager, ToolMissingError
from orchestrator.node_manager import NodeManager, NodeDiscoveryError

logger = get_logger(__name__)

# Regex for strict tcpdump timestamp matching: HH:MM:SS.UUU
TCPDUMP_TIMESTAMP_REGEX = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d+")

@dataclass
class PacketStats:
    count: int
    loss_rate: Optional[float] = None

@dataclass
class CPUStats:
    utilization_pct: float
    user_pct: float = 0.0
    system_pct: float = 0.0

@dataclass
class UnmodeledVars:
    thermal_throttling_detected: bool = False
    os_noise_level: float = 0.0

@dataclass
class NodeMetrics:
    node_id: str
    packet_stats: PacketStats
    cpu_stats: CPUStats
    unmodeled_vars: UnmodeledVars

class RemoteExecutionError(Exception):
    """Raised when remote command execution fails."""
    pass

class NetworkSaturationError(Exception):
    """Raised when network saturation is detected (>20% packet loss)."""
    pass

class InstrumentationFailureError(Exception):
    """Raised when instrumentation tools are missing or fail to produce valid data."""
    pass

class RemoteInstrumentor:
    def __init__(self, ssh_client: paramiko.SSHClient, node_id: str):
        self.ssh = ssh_client
        self.node_id = node_id
        self.logger = get_logger(__name__)

    def _execute_command(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """Execute a command on the remote node and return (exit_code, stdout, stderr)."""
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            stdout_str = stdout.read().decode('utf-8', errors='ignore')
            stderr_str = stderr.read().decode('utf-8', errors='ignore')
            return exit_code, stdout_str, stderr_str
        except socket.timeout:
            raise RemoteExecutionError(f"Command timed out on {self.node_id}")
        except Exception as e:
            raise RemoteExecutionError(f"Failed to execute command on {self.node_id}: {e}")

    def check_network_saturation(self, packet_loss_rate: float) -> None:
        """Check if network saturation threshold is exceeded."""
        if packet_loss_rate > 0.20:
            self.logger.warning(f"Network saturation detected on {self.node_id}: {packet_loss_rate*100:.1f}% loss")
            raise NetworkSaturationError(f"Network saturation detected on {self.node_id}: {packet_loss_rate*100:.1f}% loss")

    def instrument_tcpdump(self, duration: int = 10, interface: str = "any") -> PacketStats:
        """
        Run tcpdump remotely and count packets matching strict timestamp regex.
        Command: tcpdump -i <interface> -nn -c 0 (continuous)
        We run it for a fixed duration and count matching lines.
        """
        # tcpdump runs continuously (-c 0), we kill it after duration
        # Note: tcpdump output is often buffered. We use -U for packet-buffered output.
        cmd = f"timeout {duration} tcpdump -i {interface} -nn -U -c 0"
        
        try:
            exit_code, stdout, stderr = self._execute_command(cmd, timeout=duration + 10)
            
            # Count lines matching the strict timestamp regex
            packet_count = 0
            for line in stdout.splitlines():
                if TCPDUMP_TIMESTAMP_REGEX.match(line):
                    packet_count += 1

            if packet_count == 0:
                # Check if it was a tool missing issue or just no packets
                if "command not found" in stderr.lower() or "not found" in stderr.lower():
                    raise InstrumentationFailureError(f"tcpdump not found or failed on {self.node_id}")
                self.logger.warning(f"No packets captured matching regex on {self.node_id} in {duration}s")

            # Estimate loss rate if we have a baseline (simplified: assume 0 if not provided)
            # In a real scenario, we might compare sent vs received, but here we just return 0.0
            # unless we have a way to measure loss. For now, loss_rate is None or 0.
            return PacketStats(count=packet_count, loss_rate=0.0)

        except Exception as e:
            if isinstance(e, (InstrumentationFailureError, NetworkSaturationError)):
                raise
            raise InstrumentationFailureError(f"tcpdump execution failed on {self.node_id}: {e}")

    def instrument_mpstat(self, interval: float = 1.0, count: int = 5) -> CPUStats:
        """
        Run mpstat remotely and parse the 'Average' line or last interval.
        Extracts CPU% (user + system).
        """
        cmd = f"mpstat -P ALL {interval} {count}"
        
        try:
            exit_code, stdout, stderr = self._execute_command(cmd, timeout=count * interval + 10)
            
            if exit_code != 0:
                if "command not found" in stderr.lower() or "not found" in stderr.lower():
                    self.logger.warning(f"mpstat not found on {self.node_id}, setting CPU utilization to 0")
                    return CPUStats(utilization_pct=0.0, user_pct=0.0, system_pct=0.0)
                raise InstrumentationFailureError(f"mpstat execution failed on {self.node_id}: {stderr}")

            lines = stdout.splitlines()
            avg_line = None
            
            # Look for the 'Average' line which summarizes the interval
            for line in lines:
                if "Average:" in line:
                    avg_line = line
                    break
            
            if not avg_line:
                # Fallback to the last data line if no average is present
                for line in reversed(lines):
                    if re.search(r'\d{2}:\d{2}:\d{2}', line) and 'CPU' not in line:
                        avg_line = line
                        break

            user_pct = 0.0
            system_pct = 0.0
            
            if avg_line:
                parts = avg_line.split()
                # mpstat output format: CPU  %usr  %nice  %sys  %iowait  %irq  %soft  %steal  %guest  %gnice  %idle
                # We need to find indices dynamically or assume standard layout.
                # Standard layout (Linux) usually: CPU, usr, nice, sys, iowait, irq, soft, steal, guest, gnice, idle
                # We'll try to find 'idle' and calculate 100 - idle, or sum usr+sys.
                
                # Heuristic: Find 'idle' column index
                try:
                    idle_idx = None
                    usr_idx = None
                    sys_idx = None
                    
                    for i, part in enumerate(parts):
                        if part == '%idle':
                            idle_idx = i
                        elif part == '%usr':
                            usr_idx = i
                        elif part == '%sys':
                            sys_idx = i
                    
                    if idle_idx is not None:
                        idle_val = float(parts[idle_idx])
                        # Handle 'all' CPU row where CPU column is 'all'
                        # The values start after 'all'
                        # Standard: CPU %usr %nice %sys %iowait %irq %soft %steal %guest %gnice %idle
                        # If line starts with 'all', indices shift.
                        # Let's assume standard numeric columns follow.
                        # A safer way: sum of user + system
                        if usr_idx is not None and sys_idx is not None:
                            user_pct = float(parts[usr_idx])
                            system_pct = float(parts[sys_idx])
                        else:
                            # Fallback: 100 - idle
                            user_pct = 0.0
                            system_pct = 100.0 - idle_val
                    elif usr_idx is not None and sys_idx is not None:
                        user_pct = float(parts[usr_idx])
                        system_pct = float(parts[sys_idx])
                    else:
                        self.logger.warning(f"Could not parse CPU stats from: {avg_line}")
                except (ValueError, IndexError):
                    self.logger.warning(f"Could not parse numeric values from: {avg_line}")

            total_util = user_pct + system_pct
            return CPUStats(utilization_pct=total_util, user_pct=user_pct, system_pct=system_pct)

        except Exception as e:
            if isinstance(e, InstrumentationFailureError):
                raise
            self.logger.warning(f"mpstat execution failed on {self.node_id}: {e}")
            return CPUStats(utilization_pct=0.0, user_pct=0.0, system_pct=0.0)

    def get_unmodeled_vars(self) -> UnmodeledVars:
        """
        Attempt to detect thermal throttling and OS noise.
        Best-effort only.
        """
        thermal_detected = False
        os_noise = 0.0

        # Check for thermal info (simplified)
        try:
            cmd = "cat /proc/acpi/thermal_zone/*/temperature 2>/dev/null || echo 'N/A'"
            exit_code, stdout, _ = self._execute_command(cmd, timeout=5)
            if "N/A" not in stdout and "not found" not in stdout.lower():
                # Parse temperatures
                temps = re.findall(r'\d+', stdout)
                if temps:
                    max_temp = max(int(t) for t in temps)
                    if max_temp > 90: # High temperature threshold
                        thermal_detected = True
                        self.logger.warning(f"Thermal throttling suspected on {self.node_id}: {max_temp}C")
        except Exception:
            pass

        return UnmodeledVars(thermal_throttling_detected=thermal_detected, os_noise_level=os_noise)

    def instrument(self, duration: int = 10) -> NodeMetrics:
        """Run all instrumentation tasks and return aggregated metrics."""
        self.logger.info(f"Starting instrumentation on {self.node_id}")
        
        packet_stats = self.instrument_tcpdump(duration=duration)
        cpu_stats = self.instrument_mpstat()
        unmodeled = self.get_unmodeled_vars()

        # Check for network saturation
        if packet_stats.loss_rate is not None:
            self.check_network_saturation(packet_stats.loss_rate)

        return NodeMetrics(
            node_id=self.node_id,
            packet_stats=packet_stats,
            cpu_stats=cpu_stats,
            unmodeled_vars=unmodeled
        )

def create_instrumentor(ssh_client: paramiko.SSHClient, node_id: str) -> RemoteInstrumentor:
    return RemoteInstrumentor(ssh_client, node_id)

def main():
    """
    Main entry point for testing remote instrumentation.
    Expects NODE_IP and NODE_USER environment variables or arguments.
    """
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Test remote instrumentation")
    parser.add_argument("--host", required=True, help="Target node IP")
    parser.add_argument("--user", default="root", help="SSH user")
    parser.add_argument("--key", default=None, help="Path to SSH private key")
    parser.add_argument("--duration", type=int, default=10, help="Duration in seconds")
    args = parser.parse_args()

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        key_path = args.key or os.path.expanduser("~/.ssh/id_rsa")
        pkey = None
        if os.path.exists(key_path):
            try:
                pkey = paramiko.RSAKey.from_private_key_file(key_path)
            except Exception:
                try:
                    pkey = paramiko.Ed25519Key.from_private_key_file(key_path)
                except Exception:
                    pass

        client.connect(args.host, username=args.user, pkey=pkey, timeout=10)
        
        instrumentor = create_instrumentor(client, args.host)
        metrics = instrumentor.instrument(duration=args.duration)
        
        print(f"Node: {metrics.node_id}")
        print(f"Packets: {metrics.packet_stats.count}")
        print(f"CPU Util: {metrics.cpu_stats.utilization_pct:.2f}%")
        print(f"Throttling: {metrics.unmodeled_vars.thermal_throttling_detected}")
        
        client.close()
    except Exception as e:
        logger.error(f"Failed: {e}")
        raise

if __name__ == "__main__":
    main()