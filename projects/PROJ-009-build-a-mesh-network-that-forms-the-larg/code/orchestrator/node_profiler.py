from __future__ import annotations
import logging
import re
import time
import socket
import subprocess
import platform
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from pathlib import Path

from orchestrator.logger import get_logger
from orchestrator.node_manager import NodeManager, NodeDiscoveryError, create_node_manager

logger = get_logger(__name__)

@dataclass
class CPUProfile:
    """Data class holding CPU profile information for a node."""
    ip: str
    cpu_speed_mhz: float
    cpu_model: str
    timestamp: str

class ProfilerError(Exception):
    """Base exception for profiler errors."""
    pass

class CPUFrequencyError(ProfilerError):
    """Raised when CPU frequency cannot be determined."""
    pass

class CPUModelError(ProfilerError):
    """Raised when CPU model string cannot be determined."""
    pass

class NodeProfilerManager:
    """
    Manages CPU profiling for physical nodes in the mesh network.
    Specifically measures CPU speed (MHz) and extracts CPU model strings
    to calculate heterogeneity metrics.
    """

    def __init__(self, node_manager: Optional[NodeManager] = None):
        self.node_manager = node_manager or create_node_manager()
        self.logger = logger

    def _run_local_command(self, cmd: List[str], timeout: int = 10) -> str:
        """Run a command locally and return stdout."""
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            if result.returncode != 0:
                raise ProfilerError(f"Command failed: {result.stderr.strip()}")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise ProfilerError(f"Command timed out: {' '.join(cmd)}")
        except Exception as e:
            raise ProfilerError(f"Error running command: {e}")

    def _run_remote_command(self, ssh_client, cmd: str, timeout: int = 10) -> str:
        """Run a command on a remote node via SSH and return stdout."""
        try:
            stdin, stdout, stderr = ssh_client.exec_command(cmd, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8').strip()
            err = stderr.read().decode('utf-8').strip()
            
            if exit_code != 0:
                raise ProfilerError(f"Remote command failed (exit {exit_code}): {err}")
            return out
        except Exception as e:
            raise ProfilerError(f"Error executing remote command: {e}")

    def profile_local_node(self) -> CPUProfile:
        """
        Profile the local machine's CPU.
        
        Returns:
            CPUProfile containing speed (MHz) and model string.
        """
        system = platform.system()
        cpu_speed_mhz = 0.0
        cpu_model = "Unknown"

        try:
            if system == "Linux":
                # Linux: /proc/cpuinfo
                cpuinfo = self._run_local_command(["cat", "/proc/cpuinfo"])
                
                # Extract Model Name
                model_match = re.search(r"model name\s*:\s*(.+)", cpuinfo, re.MULTILINE)
                if model_match:
                    cpu_model = model_match.group(1).strip()
                else:
                    raise CPUModelError("Could not find 'model name' in /proc/cpuinfo")

                # Extract MHz (MHz is usually in 'cpu MHz')
                # Some systems might use 'cpu MHz' or 'clock'
                speed_match = re.search(r"cpu MHz\s*:\s*([\d.]+)", cpuinfo, re.MULTILINE)
                if speed_match:
                    cpu_speed_mhz = float(speed_match.group(1))
                else:
                    # Fallback: try 'clock' in /proc/cpuinfo or sysctl if available
                    # Attempt to read from /proc/cpuinfo 'clock' line if present
                    clock_match = re.search(r"clock\s*:\s*([\d.]+)MHz", cpuinfo, re.MULTILINE)
                    if clock_match:
                        cpu_speed_mhz = float(clock_match.group(1))
                    else:
                        # Last resort: try lscpu
                        lscpu_out = self._run_local_command(["lscpu"])
                        lscpu_match = re.search(r"CPU MHz\s*:\s*([\d.]+)", lscpu_out, re.MULTILINE)
                        if lscpu_match:
                            cpu_speed_mhz = float(lscpu_match.group(1))
                        else:
                            raise CPUFrequencyError("Could not determine CPU frequency via /proc/cpuinfo or lscpu")

            elif system == "Darwin":  # macOS
                # macOS: sysctl
                cpu_model = self._run_local_command(["sysctl", "-n", "machdep.cpu.brand_string"])
                # Frequency in Hz usually, convert to MHz
                freq_hz = self._run_local_command(["sysctl", "-n", "hw.cpufrequency"])
                cpu_speed_mhz = float(freq_hz) / 1_000_000.0

            elif system == "Windows":
                # Windows: wmic
                cpu_model = self._run_local_command(["wmic", "cpu", "get", "name", "/value"])
                # Extract value after =
                name_match = re.search(r"Name=(.+)", cpu_model)
                if name_match:
                    cpu_model = name_match.group(1).strip()
                
                # Frequency
                freq = self._run_local_command(["wmic", "cpu", "get", "CurrentClockSpeed", "/value"])
                freq_match = re.search(r"CurrentClockSpeed=(\d+)", freq)
                if freq_match:
                    cpu_speed_mhz = float(freq_match.group(1))
                else:
                    raise CPUFrequencyError("Could not determine CPU frequency on Windows")
            else:
                raise ProfilerError(f"Unsupported operating system: {system}")

            if cpu_speed_mhz <= 0:
                raise CPUFrequencyError("Detected CPU frequency is non-positive")

            return CPUProfile(
                ip="127.0.0.1",
                cpu_speed_mhz=cpu_speed_mhz,
                cpu_model=cpu_model,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            )

        except ProfilerError:
            raise
        except Exception as e:
            raise ProfilerError(f"Unexpected error profiling local node: {e}")

    def profile_remote_node(self, ip: str, username: str = "root", key_filename: Optional[str] = None) -> CPUProfile:
        """
        Profile a remote node via SSH.
        
        Args:
            ip: IP address of the node.
            username: SSH username.
            key_filename: Path to SSH private key.
        
        Returns:
            CPUProfile for the remote node.
        
        Raises:
            ProfilerError: If SSH connection fails or remote profiling fails.
        """
        try:
            ssh = self.node_manager._get_ssh_connection(ip, username, key_filename)
            if not ssh:
                raise ProfilerError(f"Could not establish SSH connection to {ip}")
            
            system = platform.system()
            cpu_speed_mhz = 0.0
            cpu_model = "Unknown"

            # Determine command set based on remote OS detection or assume Linux first
            # We'll try Linux first, then fall back to others if commands fail
            
            # Try Linux /proc/cpuinfo first
            try:
                cpuinfo = self._run_remote_command(ssh, "cat /proc/cpuinfo")
                model_match = re.search(r"model name\s*:\s*(.+)", cpuinfo, re.MULTILINE)
                if model_match:
                    cpu_model = model_match.group(1).strip()
                
                speed_match = re.search(r"cpu MHz\s*:\s*([\d.]+)", cpuinfo, re.MULTILINE)
                if speed_match:
                    cpu_speed_mhz = float(speed_match.group(1))
                else:
                    # Try lscpu on remote
                    lscpu_out = self._run_remote_command(ssh, "lscpu")
                    lscpu_match = re.search(r"CPU MHz\s*:\s*([\d.]+)", lscpu_out, re.MULTILINE)
                    if lscpu_match:
                        cpu_speed_mhz = float(lscpu_match.group(1))
                    else:
                        raise CPUFrequencyError("Could not determine CPU frequency on remote Linux node")
            except ProfilerError as pe:
                # If Linux method fails, try macOS
                try:
                    cpu_model = self._run_remote_command(ssh, "sysctl -n machdep.cpu.brand_string")
                    freq_hz = self._run_remote_command(ssh, "sysctl -n hw.cpufrequency")
                    cpu_speed_mhz = float(freq_hz) / 1_000_000.0
                except ProfilerError:
                    # Try Windows
                    try:
                        cpu_model_out = self._run_remote_command(ssh, "wmic cpu get name /value")
                        name_match = re.search(r"Name=(.+)", cpu_model_out)
                        if name_match:
                            cpu_model = name_match.group(1).strip()
                        
                        freq_out = self._run_remote_command(ssh, "wmic cpu get CurrentClockSpeed /value")
                        freq_match = re.search(r"CurrentClockSpeed=(\d+)", freq_out)
                        if freq_match:
                            cpu_speed_mhz = float(freq_match.group(1))
                        else:
                            raise CPUFrequencyError("Could not determine CPU frequency on remote Windows node")
                    except ProfilerError:
                        raise ProfilerError("Could not determine OS or CPU info on remote node")

            if cpu_speed_mhz <= 0:
                raise CPUFrequencyError("Remote detected CPU frequency is non-positive")

            return CPUProfile(
                ip=ip,
                cpu_speed_mhz=cpu_speed_mhz,
                cpu_model=cpu_model,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            )

        except ProfilerError:
            raise
        except Exception as e:
            raise ProfilerError(f"Unexpected error profiling remote node {ip}: {e}")

    def profile_nodes(self, ip_list: List[str], username: str = "root", key_filename: Optional[str] = None) -> List[CPUProfile]:
        """
        Profile a list of nodes.
        
        Args:
            ip_list: List of IP addresses.
            username: SSH username.
            key_filename: Path to SSH private key.
        
        Returns:
            List of CPUProfile objects.
        """
        profiles = []
        for ip in ip_list:
            try:
                profile = self.profile_remote_node(ip, username, key_filename)
                profiles.append(profile)
                self.logger.info(f"Profiled node {ip}: {profile.cpu_model} @ {profile.cpu_speed_mhz:.2f} MHz")
            except ProfilerError as e:
                self.logger.error(f"Failed to profile node {ip}: {e}")
                # Continue with other nodes
        return profiles

def create_node_profiler(node_manager: Optional[NodeManager] = None) -> NodeProfilerManager:
    """Factory function to create a NodeProfilerManager."""
    return NodeProfilerManager(node_manager=node_manager)

def main():
    """CLI entry point for profiling nodes."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Profile CPU details of mesh nodes.")
    parser.add_argument("--ips", nargs="+", required=True, help="List of node IPs to profile.")
    parser.add_argument("--username", default="root", help="SSH username.")
    parser.add_argument("--key", help="Path to SSH private key.")
    parser.add_argument("--local", action="store_true", help="Profile only the local machine.")
    
    args = parser.parse_args()

    profiler = create_node_profiler()

    if args.local:
        try:
            profile = profiler.profile_local_node()
            print(json.dumps({
                "ip": profile.ip,
                "cpu_speed_mhz": profile.cpu_speed_mhz,
                "cpu_model": profile.cpu_model,
                "timestamp": profile.timestamp
            }, indent=2))
        except ProfilerError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        profiles = profiler.profile_nodes(args.ips, args.username, args.key)
        if not profiles:
            print("No profiles collected.", file=sys.stderr)
            sys.exit(1)
        
        results = [
            {
                "ip": p.ip,
                "cpu_speed_mhz": p.cpu_speed_mhz,
                "cpu_model": p.cpu_model,
                "timestamp": p.timestamp
            }
            for p in profiles
        ]
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
