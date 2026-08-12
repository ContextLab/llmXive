"""
Node Profiler Module for Mesh Network Supercomputer.

Measures and records CPU details (speed and model) for heterogeneity calculation
across physical nodes in the mesh network.
"""
from __future__ import annotations
import logging
import re
import socket
import time
import socket
import subprocess
import platform
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

import paramiko
from paramiko import SSHClient, AutoAddPolicy

from orchestrator.logger import get_logger

logger = get_logger(__name__)

@dataclass
class CPUProfile:
    """Data class holding CPU profile information for a node."""
    ip: str
    cpu_speed_mhz: float
    cpu_model: str
    timestamp: str

class ProfilerError(Exception):
    """Base exception for node profiling errors."""
    pass

class CPUFrequencyError(ProfilerError):
    """Raised when CPU frequency cannot be determined."""
    pass


@dataclass
class CPUProfile:
    """
    Represents the CPU profile of a node.

    Attributes:
        cpu_speed_mhz: CPU clock speed in MHz (float).
        cpu_model: CPU model string.
        node_id: Identifier for the node (optional).
        timestamp: Time of profiling (optional).
    """
    cpu_speed_mhz: float
    cpu_model: str
    node_id: Optional[str] = None
    timestamp: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'cpu_speed_mhz': self.cpu_speed_mhz,
            'cpu_model': self.cpu_model,
            'node_id': self.node_id,
            'timestamp': self.timestamp
        }


@dataclass
class NodeProfilerManager:
    """
    Manages a collection of CPU profiles from multiple nodes.

    Attributes:
        profiles: List of CPUProfile instances.
    """
    profiles: List[CPUProfile]

    def add_profile(self, profile: CPUProfile) -> None:
        """Add a CPU profile to the manager."""
        self.profiles.append(profile)

    def get_heterogeneity_metric(self) -> float:
        """
        Calculate the coefficient of variation (CV) of CPU speeds.

        CV = (Standard Deviation / Mean) * 100
        Returns 0.0 if there are fewer than 2 profiles or if all speeds are identical.
        """
        if len(self.profiles) < 2:
            return 0.0

        speeds = [p.cpu_speed_mhz for p in self.profiles if p.cpu_speed_mhz > 0]
        if len(speeds) < 2:
            return 0.0

        mean_speed = sum(speeds) / len(speeds)
        if mean_speed == 0:
            return 0.0

        variance = sum((s - mean_speed) ** 2 for s in speeds) / len(speeds)
        std_dev = variance ** 0.5

        return (std_dev / mean_speed) * 100.0


class NodeProfiler:
    """
    Profiler for a single node to extract CPU characteristics.

    Supports both local execution (for testing) and remote execution via SSH.
    """

    def __init__(self, node_id: Optional[str] = None, ssh_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the NodeProfiler.

        Args:
            node_id: Unique identifier for the node.
            ssh_config: Optional dictionary containing SSH connection parameters
                        (hostname, username, password/key_filename, port).
        """
        self.node_id = node_id or socket.gethostname()
        self.ssh_config = ssh_config
        self.logger = get_logger(__name__)

    def _run_local_command(self, command: str) -> str:
        """
        Execute a command locally and return the output.

        Args:
            command: Shell command to execute.

        Returns:
            Standard output of the command.

        Raises:
            ProfilerError: If command execution fails.
        """
        import subprocess
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise ProfilerError(f"Command failed: {command}\nError: {result.stderr}")
            return result.stdout
        except subprocess.TimeoutExpired:
            raise ProfilerError(f"Command timed out: {command}")
        except Exception as e:
            raise ProfilerError(f"Failed to execute local command: {e}")

    def _run_remote_command(self, command: str) -> str:
        """
        Execute a command on a remote node via SSH and return the output.

        Args:
            command: Shell command to execute remotely.

        Returns:
            Standard output of the command.

        Raises:
            ProfilerError: If SSH connection or command execution fails.
        """
        if not self.ssh_config:
            raise ProfilerError("SSH configuration not provided for remote profiling.")

        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())

        try:
            client.connect(
                hostname=self.ssh_config.get('hostname'),
                username=self.ssh_config.get('username'),
                password=self.ssh_config.get('password'),
                key_filename=self.ssh_config.get('key_filename'),
                port=self.ssh_config.get('port', 22),
                timeout=10
            )
            stdin, stdout, stderr = client.exec_command(command, timeout=10)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')

            if stdout.channel.recv_exit_status() != 0:
                raise ProfilerError(f"Remote command failed: {command}\nError: {error}")

            return output
        except Exception as e:
            raise ProfilerError(f"Failed to execute remote command via SSH: {e}")
        finally:
            client.close()

    def _execute_profiling_command(self, command: str) -> str:
        """Execute a command either locally or remotely based on configuration."""
        if self.ssh_config:
            return self._run_remote_command(command)
        else:
            return self._run_local_command(command)

    def get_cpu_speed_mhz(self) -> float:
        """
        Determine the CPU clock speed in MHz.

        Tries Linux (/proc/cpuinfo) first, then macOS (sysctl).
        Falls back to a default value if detection fails (with a warning).

        Returns:
            CPU speed in MHz.

        Raises:
            CPUFrequencyError: If the speed cannot be determined from any source.
        """
        output = ""
        detected = False

        # Try Linux method
        try:
            output = self._execute_profiling_command("grep 'cpu MHz' /proc/cpuinfo | head -n 1")
            match = re.search(r'cpu MHz\s*:\s*([\d.]+)', output)
            if match:
                speed = float(match.group(1))
                self.logger.info(f"Detected CPU speed (Linux): {speed} MHz")
                detected = True
                return speed
        except Exception as e:
            self.logger.debug(f"Linux method failed: {e}")

        # Try macOS method
        try:
            output = self._execute_profiling_command("sysctl -n hw.cpufrequency")
            if output.strip():
                # Output is in Hz, convert to MHz
                speed_hz = float(output.strip())
                speed_mhz = speed_hz / 1_000_000.0
                self.logger.info(f"Detected CPU speed (macOS): {speed_mhz} MHz")
                detected = True
                return speed_mhz
        except Exception as e:
            self.logger.debug(f"macOS method failed: {e}")

        if not detected:
            # Fallback: try 'lscpu' which might work on some systems
            try:
                output = self._execute_profiling_command("lscpu | grep 'CPU MHz' | head -n 1")
                match = re.search(r'([\d.]+)', output)
                if match:
                    speed = float(match.group(1))
                    self.logger.warning(f"Retrieved CPU speed via lscpu: {speed} MHz")
                    return speed
            except Exception as e:
                self.logger.debug(f"lscpu method failed: {e}")

        raise CPUFrequencyError(
            f"Could not determine CPU frequency for node {self.node_id}. "
            "Tried /proc/cpuinfo, sysctl, and lscpu without success."
        )

    def get_cpu_model(self) -> str:
        """
        Determine the CPU model string.

        Tries Linux (/proc/cpuinfo) first, then macOS (sysctl).
        Falls back to 'Unknown' if detection fails.

        Returns:
            CPU model string.
        """
        output = ""

        # Try Linux method
        try:
            output = self._execute_profiling_command("grep 'model name' /proc/cpuinfo | head -n 1")
            match = re.search(r'model name\s*:\s*(.+)', output)
            if match:
                model = match.group(1).strip()
                self.logger.info(f"Detected CPU model (Linux): {model}")
                return model
        except Exception as e:
            self.logger.debug(f"Linux method failed: {e}")

        # Try macOS method
        try:
            output = self._execute_profiling_command("sysctl -n machdep.cpu.brand_string")
            if output.strip():
                model = output.strip()
                self.logger.info(f"Detected CPU model (macOS): {model}")
                return model
        except Exception as e:
            self.logger.debug(f"macOS method failed: {e}")

        self.logger.warning(f"Could not determine CPU model for node {self.node_id}. Returning 'Unknown'.")
        return "Unknown"

    def profile(self) -> CPUProfile:
        """
        Perform full CPU profiling for the node.

        Returns:
            CPUProfile object containing speed and model.

        Raises:
            ProfilerError: If critical profiling steps fail.
        """
        self.logger.info(f"Profiling node: {self.node_id}")
        start_time = time.time()

        try:
            speed = self.get_cpu_speed_mhz()
            model = self.get_cpu_model()

            profile = CPUProfile(
                cpu_speed_mhz=speed,
                cpu_model=model,
                node_id=self.node_id,
                timestamp=start_time
            )

            self.logger.info(
                f"Profiling complete for {self.node_id}: "
                f"{profile.cpu_speed_mhz} MHz, Model: {profile.cpu_model}"
            )
            return profile

        except CPUFrequencyError as e:
            self.logger.error(f"Failed to get CPU speed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during profiling: {e}")
            raise ProfilerError(f"Profiling failed: {e}")


def create_node_profiler(
    node_id: Optional[str] = None,
    ssh_config: Optional[Dict[str, Any]] = None
) -> NodeProfiler:
    """
    Factory function to create a NodeProfiler instance.

    Args:
        node_id: Unique identifier for the node.
        ssh_config: Optional SSH connection configuration.

    Returns:
        NodeProfiler instance.
    """
    return NodeProfiler(node_id=node_id, ssh_config=ssh_config)


def profile_nodes(
    node_ids: List[str],
    ssh_configs: Optional[Dict[str, Dict[str, Any]]] = None
) -> NodeProfilerManager:
    """
    Profile multiple nodes and aggregate results.

    Args:
        node_ids: List of node identifiers.
        ssh_configs: Optional dictionary mapping node_id to SSH config.

    Returns:
        NodeProfilerManager containing all profiles.

    Raises:
        ProfilerError: If profiling fails for all nodes.
    """
    manager = NodeProfilerManager(profiles=[])
    failed_count = 0

    for node_id in node_ids:
        config = ssh_configs.get(node_id) if ssh_configs else None
        profiler = create_node_profiler(node_id=node_id, ssh_config=config)

        try:
            profile = profiler.profile()
            manager.add_profile(profile)
        except Exception as e:
            failed_count += 1
            logger.error(f"Failed to profile node {node_id}: {e}")

    if failed_count == len(node_ids):
        raise ProfilerError("Failed to profile all nodes.")

    return manager


def main() -> None:
    """
    Main entry point for command-line execution.

    Usage:
        python -m orchestrator.node_profiler [--nodes node1,node2,...] [--config config.yaml]
    """
    import argparse
    import yaml

    parser = argparse.ArgumentParser(description="Profile CPU characteristics of mesh nodes.")
    parser.add_argument(
        '--nodes',
        type=str,
        default='localhost',
        help='Comma-separated list of node IDs (default: localhost)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to YAML file containing SSH configurations per node'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path to save JSON output of profiles'
    )

    args = parser.parse_args()

    node_ids = [n.strip() for n in args.nodes.split(',')]
    ssh_configs = None

    if args.config:
        try:
            with open(args.config, 'r') as f:
                ssh_configs = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            return

    try:
        manager = profile_nodes(node_ids, ssh_configs)

        # Print summary
        print(f"Successfully profiled {len(manager.profiles)} nodes.")
        print(f"Heterogeneity Metric (CV): {manager.get_heterogeneity_metric():.2f}%")

        for profile in manager.profiles:
            print(f"  - {profile.node_id}: {profile.cpu_speed_mhz} MHz ({profile.cpu_model})")

        # Save to file if requested
        if args.output:
            import json
            with open(args.output, 'w') as f:
                json.dump({
                    'heterogeneity_metric': manager.get_heterogeneity_metric(),
                    'profiles': [p.to_dict() for p in manager.profiles]
                }, f, indent=2)
            print(f"Results saved to {args.output}")

    except ProfilerError as e:
        logger.error(f"Profiling failed: {e}")
        exit(1)


if __name__ == '__main__':
    main()
