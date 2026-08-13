"""
Node Profiler Module

Measures and records CPU details for heterogeneity calculation.
Specifically extracts CPU speed (MHz) and CPU model string via SSH execution
of system commands (lscpu, sysctl, or /proc/cpuinfo).
"""
from __future__ import annotations

import logging
import re
import socket
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

import paramiko

from orchestrator.logger import get_logger
from orchestrator.node_manager import NodeDiscoveryResult, NodeState, create_node_manager

logger = get_logger(__name__)


class ProfilerError(Exception):
    """Base exception for profiler failures."""
    pass


class CPUFrequencyError(ProfilerError):
    """Raised when CPU frequency cannot be determined."""
    pass


@dataclass
class CPUProfile:
    """
    Represents the CPU profile of a single node.
    """
    node_id: str
    cpu_speed_mhz: Optional[float]
    cpu_model: Optional[str]
    os_type: str
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "cpu_speed_mhz": self.cpu_speed_mhz,
            "cpu_model": self.cpu_model,
            "os_type": self.os_type,
            "error": self.error
        }


class NodeProfiler:
    """
    Handles CPU profiling for a specific node via SSH.
    """

    def __init__(self, node_id: str, ssh_client: paramiko.SSHClient):
        self.node_id = node_id
        self.ssh_client = ssh_client
        self.logger = get_logger(__name__)

    def _execute_command(self, command: str, timeout: int = 10) -> Tuple[int, str, str]:
        """
        Execute a command on the remote node and return (exit_code, stdout, stderr).
        """
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', errors='ignore').strip()
            err = stderr.read().decode('utf-8', errors='ignore').strip()
            return exit_code, out, err
        except Exception as e:
            self.logger.error(f"Error executing command on {self.node_id}: {e}")
            return -1, "", str(e)

    def profile_linux(self) -> Dict[str, Any]:
        """
        Profile CPU on a Linux node.
        Uses 'lscpu' for speed and '/proc/cpuinfo' for model.
        """
        # Try lscpu first
        exit_code, stdout, stderr = self._execute_command("lscpu | grep 'CPU MHz'")
        cpu_speed = None
        if exit_code == 0 and stdout:
            # lscpu output format: "CPU MHz: 1234.567"
            match = re.search(r'CPU MHz:\s*([0-9.]+)', stdout)
            if match:
                try:
                    cpu_speed = float(match.group(1))
                except ValueError:
                    self.logger.warning(f"Failed to parse CPU MHz from lscpu: {stdout}")
            else:
                # Fallback: try to parse from /proc/cpuinfo 'cpu MHz'
                self.logger.info("lscpu did not yield MHz, trying /proc/cpuinfo")
                exit_code, stdout, stderr = self._execute_command("grep 'cpu MHz' /proc/cpuinfo | head -1")
                if exit_code == 0 and stdout:
                    match = re.search(r'cpu MHz\s*:\s*([0-9.]+)', stdout)
                    if match:
                        try:
                            cpu_speed = float(match.group(1))
                        except ValueError:
                            pass

        # Get model name
        exit_code, stdout, stderr = self._execute_command("grep 'model name' /proc/cpuinfo | head -1")
        cpu_model = None
        if exit_code == 0 and stdout:
            # Format: "model name  : Intel(R) Core(TM) i7-xxxx"
            match = re.search(r'model name\s*:\s*(.+)', stdout)
            if match:
                cpu_model = match.group(1).strip()

        return {
            "cpu_speed_mhz": cpu_speed,
            "cpu_model": cpu_model
        }

    def profile_macos(self) -> Dict[str, Any]:
        """
        Profile CPU on a macOS node.
        Uses 'sysctl' for speed and model.
        """
        # Get frequency (returns Hz, need to convert to MHz)
        exit_code, stdout, stderr = self._execute_command("sysctl -n hw.cpufrequency")
        cpu_speed = None
        if exit_code == 0 and stdout:
            try:
                hz = float(stdout.strip())
                cpu_speed = hz / 1_000_000.0
            except ValueError:
                pass

        # Get model name
        exit_code, stdout, stderr = self._execute_command("sysctl -n machdep.cpu.brand_string")
        cpu_model = None
        if exit_code == 0 and stdout:
            cpu_model = stdout.strip()

        return {
            "cpu_speed_mhz": cpu_speed,
            "cpu_model": cpu_model
        }

    def profile(self) -> CPUProfile:
        """
        Attempt to profile the node's CPU.
        Returns a CPUProfile object.
        """
        os_type = "unknown"
        # Detect OS
        exit_code, stdout, stderr = self._execute_command("uname -s")
        if exit_code == 0:
            os_type = stdout.strip().lower()

        result = {"cpu_speed_mhz": None, "cpu_model": None}
        error = None

        try:
            if "linux" in os_type:
                result = self.profile_linux()
            elif "darwin" in os_type:
                result = self.profile_macos()
            else:
                error = f"Unsupported OS detected: {os_type}"
                self.logger.warning(error)
        except Exception as e:
            error = str(e)
            self.logger.error(f"Profiling failed for {self.node_id}: {e}")

        return CPUProfile(
            node_id=self.node_id,
            cpu_speed_mhz=result.get("cpu_speed_mhz"),
            cpu_model=result.get("cpu_model"),
            os_type=os_type,
            error=error
        )


class NodeProfilerManager:
    """
    Manages profiling across multiple nodes.
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.profiles: List[CPUProfile] = []

    def profile_nodes(self, node_ips: List[str]) -> List[CPUProfile]:
        """
        Connect to a list of node IPs, profile their CPUs, and return results.
        This function is designed to be called by the orchestrator or data collector.
        """
        profiles = []
        for ip in node_ips:
            node_id = ip  # Using IP as node_id for simplicity
            self.logger.info(f"Profiling node: {node_id}")
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                # Attempt connection with a short timeout
                client.connect(hostname=ip, username='root', timeout=5, allow_agent=False, look_for_keys=False)
                
                profiler = NodeProfiler(node_id, client)
                profile = profiler.profile()
                profiles.append(profile)
                client.close()
                
                if profile.error:
                    self.logger.warning(f"Profile for {node_id} has errors: {profile.error}")
                else:
                    self.logger.info(f"Profiled {node_id}: {profile.cpu_model} @ {profile.cpu_speed_mhz} MHz")
            except Exception as e:
                self.logger.error(f"Failed to profile {node_id}: {e}")
                profiles.append(CPUProfile(
                    node_id=node_id,
                    cpu_speed_mhz=None,
                    cpu_model=None,
                    os_type="unknown",
                    error=str(e)
                ))
        
        self.profiles = profiles
        return profiles

    def get_heterogeneity_score(self) -> float:
        """
        Calculate a simple heterogeneity score based on CPU speeds.
        Score = Standard Deviation of speeds / Mean of speeds (Coefficient of Variation).
        Returns 0.0 if insufficient data.
        """
        speeds = [p.cpu_speed_mhz for p in self.profiles if p.cpu_speed_mhz is not None]
        if len(speeds) < 2:
            return 0.0
        
        mean_speed = sum(speeds) / len(speeds)
        if mean_speed == 0:
            return 0.0
        
        variance = sum((s - mean_speed) ** 2 for s in speeds) / len(speeds)
        std_dev = variance ** 0.5
        
        return std_dev / mean_speed


def create_node_profiler() -> NodeProfilerManager:
    """Factory function to create a NodeProfilerManager."""
    return NodeProfilerManager()


def profile_nodes(ip_list: List[str]) -> List[Dict[str, Any]]:
    """
    Convenience function to profile a list of IPs and return a list of dicts.
    Matches the expected output format for T049.
    """
    manager = create_node_profiler()
    profiles = manager.profile_nodes(ip_list)
    return [p.to_dict() for p in profiles]


def main():
    """
    CLI entry point for testing the profiler directly.
    Usage: python -m orchestrator.node_profiler --ips 192.168.1.10,192.168.1.11
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Profile CPU details of mesh nodes.")
    parser.add_argument('--ips', type=str, required=True, help='Comma-separated list of node IPs')
    args = parser.parse_args()

    ips = [ip.strip() for ip in args.ips.split(',')]
    results = profile_nodes(ips)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()