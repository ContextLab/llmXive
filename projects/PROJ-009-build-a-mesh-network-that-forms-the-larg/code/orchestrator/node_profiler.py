from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import paramiko

from orchestrator.logger import get_logger
from orchestrator.remote_tool_checker import RemoteToolChecker, create_tool_checker

logger = get_logger(__name__)


class ProfilerError(Exception):
    """Base exception for profiling failures."""
    pass


class CPUFrequencyError(ProfilerError):
    """Raised when CPU frequency cannot be determined."""
    pass


@dataclass
class CPUProfile:
    """Container for CPU frequency profile data."""
    node_id: str
    cpu_speed_mhz: float
    measurement_timestamp: str
    command_used: str
    raw_output: str


class NodeProfiler:
    """
    Measures and records CPU clock speeds for heterogeneity calculation.
    
    Executes `lscpu | grep 'CPU MHz'` on Linux or `sysctl -n hw.cpufrequency`
    on macOS via SSH.
    """

    def __init__(self, ssh_client: paramiko.SSHClient, node_id: str):
        self.ssh_client = ssh_client
        self.node_id = node_id
        self.logger = get_logger(__name__)

    def _execute_command(self, command: str) -> Tuple[int, str, str]:
        """
        Execute a command on the remote node and return (exit_code, stdout, stderr).
        """
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            stdout_str = stdout.read().decode('utf-8', errors='replace')
            stderr_str = stderr.read().decode('utf-8', errors='replace')
            return exit_code, stdout_str, stderr_str
        except Exception as e:
            raise ProfilerError(f"Failed to execute command on {self.node_id}: {e}")

    def _parse_linux_cpu_mhz(self, raw_output: str) -> float:
        """
        Parse 'CPU MHz' from lscpu output.
        Example line: 'CPU MHz:                2400.000'
        """
        pattern = r"CPU\s+MHz:\s+([\d.]+)"
        match = re.search(pattern, raw_output)
        if not match:
            raise CPUFrequencyError(f"Could not parse CPU MHz from lscpu output: {raw_output}")
        return float(match.group(1))

    def _parse_macos_cpu_mhz(self, raw_output: str) -> float:
        """
        Parse CPU frequency from sysctl output.
        sysctl -n hw.cpufrequency returns Hz, convert to MHz.
        """
        try:
            value = float(raw_output.strip())
            return value / 1_000_000.0
        except ValueError:
            raise CPUFrequencyError(f"Could not parse CPU frequency from sysctl output: {raw_output}")

    def profile_linux(self) -> CPUProfile:
        """Profile Linux node using lscpu."""
        command = "lscpu | grep 'CPU MHz'"
        self.logger.info(f"Profiling CPU on {self.node_id} (Linux): {command}")
        
        start_time = time.time()
        exit_code, stdout, stderr = self._execute_command(command)
        elapsed = time.time() - start_time

        if exit_code != 0:
            raise CPUFrequencyError(f"Command failed on {self.node_id} (exit {exit_code}): {stderr}")

        cpu_speed_mhz = self._parse_linux_cpu_mhz(stdout)
        
        return CPUProfile(
            node_id=self.node_id,
            cpu_speed_mhz=cpu_speed_mhz,
            measurement_timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            command_used=command,
            raw_output=stdout
        )

    def profile_macos(self) -> CPUProfile:
        """Profile macOS node using sysctl."""
        command = "sysctl -n hw.cpufrequency"
        self.logger.info(f"Profiling CPU on {self.node_id} (macOS): {command}")

        start_time = time.time()
        exit_code, stdout, stderr = self._execute_command(command)
        elapsed = time.time() - start_time

        if exit_code != 0:
            raise CPUFrequencyError(f"Command failed on {self.node_id} (exit {exit_code}): {stderr}")

        cpu_speed_mhz = self._parse_macos_cpu_mhz(stdout)

        return CPUProfile(
            node_id=self.node_id,
            cpu_speed_mhz=cpu_speed_mhz,
            measurement_timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            command_used=command,
            raw_output=stdout
        )

    def detect_and_profile(self) -> CPUProfile:
        """
        Detect OS and run the appropriate profiling command.
        Tries Linux first, then macOS.
        """
        # Try Linux first
        try:
            return self.profile_linux()
        except CPUFrequencyError as e_linux:
            self.logger.warning(f"Linux profiling failed on {self.node_id}: {e_linux}")
            
            # Try macOS
            try:
                return self.profile_macos()
            except CPUFrequencyError as e_macos:
                raise CPUFrequencyError(
                    f"Could not profile CPU on {self.node_id}: Linux failed ({e_linux}), macOS failed ({e_macos})"
                )

    def profile(self) -> CPUProfile:
        """
        Public entry point to profile the node.
        """
        return self.detect_and_profile()


class NodeProfilerManager:
    """
    Manages CPU profiling across multiple nodes.
    """

    def __init__(self, ssh_clients: Dict[str, paramiko.SSHClient]):
        """
        :param ssh_clients: Dict mapping node_id -> paramiko.SSHClient
        """
        self.ssh_clients = ssh_clients
        self.logger = get_logger(__name__)

    def profile_all(self) -> List[CPUProfile]:
        """
        Profile all connected nodes and return a list of CPUProfile objects.
        """
        profiles = []
        for node_id, client in self.ssh_clients.items():
            try:
                profiler = NodeProfiler(client, node_id)
                profile = profiler.profile()
                profiles.append(profile)
                self.logger.info(
                    f"Profiled {node_id}: {profile.cpu_speed_mhz:.2f} MHz ({profile.command_used})"
                )
            except CPUFrequencyError as e:
                self.logger.error(f"Failed to profile {node_id}: {e}")
                # Re-raise to fail loudly if any node profiling fails
                raise ProfilerError(f"CPU profiling failed for node {node_id}: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error profiling {node_id}: {e}")
                raise ProfilerError(f"Unexpected error profiling {node_id}: {e}")
        
        return profiles


def create_node_profiler(ssh_client: paramiko.SSHClient, node_id: str) -> NodeProfiler:
    """Factory function to create a NodeProfiler instance."""
    return NodeProfiler(ssh_client, node_id)


def main():
    """
    CLI entry point for testing the profiler.
    Expects SSH credentials via environment variables or default config.
    """
    import os
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m orchestrator.node_profiler <node_id> <host>")
        sys.exit(1)

    node_id = sys.argv[1]
    host = sys.argv[2]
    port = int(os.environ.get("SSH_PORT", 22))
    username = os.environ.get("SSH_USER", "root")
    key_file = os.environ.get("SSH_KEY", None)

    logger.info(f"Connecting to {host} as {username} to profile {node_id}")

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        if key_file and os.path.exists(key_file):
            client.connect(host, port=port, username=username, key_filename=key_file, timeout=10)
        else:
            # Fallback to password if key not provided (for testing)
            password = os.environ.get("SSH_PASSWORD", None)
            if not password:
                raise ValueError("No key file or password provided")
            client.connect(host, port=port, username=username, password=password, timeout=10)

        profiler = NodeProfiler(client, node_id)
        profile = profiler.profile()
        
        print(f"Node: {profile.node_id}")
        print(f"CPU Speed: {profile.cpu_speed_mhz:.2f} MHz")
        print(f"Command: {profile.command_used}")
        print(f"Raw Output: {profile.raw_output.strip()}")

        client.close()

    except Exception as e:
        logger.error(f"Profiling failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
