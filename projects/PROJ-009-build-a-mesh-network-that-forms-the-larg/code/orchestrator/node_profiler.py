from __future__ import annotations

import logging
import re
import socket
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from orchestrator.node_manager import NodeManager, NodeDiscoveryResult, NodeState
from orchestrator.remote_tools_manager import RemoteToolManager, ToolMissingError

logger = logging.getLogger(__name__)


class ProfilerError(Exception):
    """Base exception for profiler failures."""
    pass


class CPUFrequencyError(ProfilerError):
    """Raised when CPU frequency cannot be determined."""
    pass


@dataclass
class CPUProfile:
    """Container for CPU profiling results."""
    cpu_speed_mhz: float
    cpu_model: str


class NodeProfiler:
    """
    Profiles a single remote node to determine CPU heterogeneity metrics.
    Executes remote commands to extract CPU speed and model name.
    """

    def __init__(self, node_manager: NodeManager, tool_manager: RemoteToolManager):
        self.node_manager = node_manager
        self.tool_manager = tool_manager

    def profile_node(self, ip: str) -> CPUProfile:
        """
        Profiles a specific node by IP address.
        
        Args:
            ip: The IP address of the target node.
            
        Returns:
            CPUProfile containing speed and model.
            
        Raises:
            ProfilerError: If profiling fails on this node.
        """
        if not self.node_manager.is_node_available(ip):
            raise ProfilerError(f"Node {ip} is not available for profiling.")

        # Ensure tools are present (specifically basic shell utilities, though 
        # we rely on standard system files like /proc/cpuinfo)
        try:
            self.tool_manager.verify_tools(ip, [])
        except ToolMissingError as e:
            # Basic shell access is assumed; if tools are missing that block 
            # this, we fail loud.
            raise ProfilerError(f"Required tools missing on {ip}: {e}")

        # 1. Get CPU Speed
        speed = self._get_cpu_speed_mhz(ip)
        
        # 2. Get CPU Model
        model = self._get_cpu_model(ip)

        return CPUProfile(cpu_speed_mhz=speed, cpu_model=model)

    def _get_cpu_speed_mhz(self, ip: str) -> float:
        """
        Retrieves CPU speed in MHz.
        Tries Linux /proc/cpuinfo, then lscpu, then macOS sysctl.
        """
        # Primary: Linux /proc/cpuinfo 'cpu MHz'
        cmd = "grep -m1 'cpu MHz' /proc/cpuinfo | awk '{print $4}'"
        stdout, stderr, exit_code = self.node_manager.execute_remote_command(ip, cmd)

        if exit_code == 0 and stdout.strip():
            try:
                return float(stdout.strip())
            except ValueError:
                logger.warning(f"Could not parse speed from /proc/cpuinfo on {ip}: {stdout}")

        # Fallback 1: lscpu (Linux)
        cmd = "lscpu | grep 'CPU MHz' | awk '{print $4}'"
        stdout, stderr, exit_code = self.node_manager.execute_remote_command(ip, cmd)
        if exit_code == 0 and stdout.strip():
            try:
                return float(stdout.strip())
            except ValueError:
                pass

        # Fallback 2: macOS sysctl
        cmd = "sysctl -n hw.cpufrequency"
        stdout, stderr, exit_code = self.node_manager.execute_remote_command(ip, cmd)
        if exit_code == 0 and stdout.strip():
            try:
                # sysctl returns Hz, convert to MHz
                return float(stdout.strip()) / 1_000_000.0
            except ValueError:
                pass

        # Fallback 3: macOS sysctl (brand string fallback for speed if MHz fails)
        # If we are here, we failed to get numeric speed.
        raise CPUFrequencyError(f"Failed to determine CPU speed on {ip} after all attempts.")

    def _get_cpu_model(self, ip: str) -> str:
        """
        Retrieves the CPU model string.
        Tries Linux /proc/cpuinfo 'model name', then macOS sysctl.
        """
        # Primary: Linux /proc/cpuinfo 'model name'
        cmd = "grep -m1 'model name' /proc/cpuinfo | cut -d':' -f2 | xargs"
        stdout, stderr, exit_code = self.node_manager.execute_remote_command(ip, cmd)

        if exit_code == 0 and stdout.strip():
            return stdout.strip()

        # Fallback: macOS sysctl
        cmd = "sysctl -n machdep.cpu.brand_string"
        stdout, stderr, exit_code = self.node_manager.execute_remote_command(ip, cmd)

        if exit_code == 0 and stdout.strip():
            return stdout.strip()

        return "Unknown CPU Model"


class NodeProfilerManager:
    """
    Manages profiling across a list of nodes.
    """

    def __init__(self, node_manager: NodeManager, tool_manager: RemoteToolManager):
        self.node_manager = node_manager
        self.tool_manager = tool_manager
        self.profiler = NodeProfiler(node_manager, tool_manager)

    def profile_nodes(self, ip_list: List[str]) -> Dict[str, CPUProfile]:
        """
        Profiles all reachable nodes in the provided list.
        
        Args:
            ip_list: List of IP addresses to profile.
            
        Returns:
            Dictionary mapping IP to CPUProfile.
        """
        results = {}
        
        # First, ensure we know which nodes are online
        # Note: node_manager.discover_nodes is expected to handle the initial discovery logic
        # as per T013a, but we rely on the manager's state here.
        
        for ip in ip_list:
            try:
                logger.info(f"Profiling CPU for node: {ip}")
                profile = self.profiler.profile_node(ip)
                results[ip] = profile
                logger.info(f"Node {ip}: {profile.cpu_model} @ {profile.cpu_speed_mhz} MHz")
            except ProfilerError as e:
                logger.error(f"Failed to profile node {ip}: {e}")
                # We do not raise here to allow partial success if the orchestrator 
                # can handle partial data, but for strict T049 requirements, 
                # we log the failure clearly.
                results[ip] = None

        # Filter out None values if we want strict results, but typically 
        # we return the map and let the consumer handle missing keys.
        return {k: v for k, v in results.items() if v is not None}


def create_node_profiler(node_manager: NodeManager, tool_manager: RemoteToolManager) -> NodeProfilerManager:
    """Factory function to create a NodeProfilerManager."""
    return NodeProfilerManager(node_manager, tool_manager)


def profile_nodes(ip_list: List[str]) -> Dict[str, CPUProfile]:
    """
    Convenience function to profile nodes without explicit manager instantiation.
    Requires node_manager and tool_manager to be available in the context 
    (typically loaded from config).
    
    For standalone execution (e.eg. CLI), this assumes standard config loading.
    """
    # In a real execution context, we would load config here.
    # For the module implementation, we expect the manager to be passed in.
    # This function is a wrapper for the CLI entry point.
    raise NotImplementedError("Use create_node_profiler with initialized managers.")


def main():
    """CLI entry point for profiling nodes."""
    import argparse
    from orchestrator.config import get_config
    from orchestrator.node_manager import create_node_manager
    from orchestrator.remote_tools_manager import create_tool_manager

    parser = argparse.ArgumentParser(description="Profile CPU details of mesh nodes.")
    parser.add_argument("--ips", nargs="+", required=True, help="List of node IPs")
    parser.add_argument("--config", default="config/sweep_config.yaml", help="Path to config file")
    args = parser.parse_args()

    config = get_config(args.config)
    
    # Initialize managers
    # Note: We assume SSH keys and credentials are configured in the config
    node_mgr = create_node_manager(config)
    tool_mgr = create_tool_manager(config)

    manager = create_node_profiler(node_mgr, tool_mgr)
    profiles = manager.profile_nodes(args.ips)

    # Output results
    import json
    output = {
        ip: {
            "cpu_speed_mhz": profile.cpu_speed_mhz,
            "cpu_model": profile.cpu_model
        }
        for ip, profile in profiles.items()
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()