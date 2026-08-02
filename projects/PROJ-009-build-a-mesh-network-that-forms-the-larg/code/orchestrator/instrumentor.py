"""
Instrumentor module for remote monitoring of physical nodes.

This module provides functionality to remotely execute system monitoring
commands (tcpdump for packet counts, mpstat for CPU utilization) on
target nodes via SSH connections.
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from orchestrator.config import load_config
from orchestrator.logger import get_logger
from orchestrator.models import PhysicalNode
from orchestrator.node_manager import NodeManager, SSHConnection

logger = get_logger(__name__)


@dataclass
class PacketStats:
    """Statistics extracted from tcpdump output."""
    packets_received: int = 0
    packets_sent: int = 0
    bytes_received: int = 0
    bytes_sent: int = 0
    duration_seconds: float = 0.0


@dataclass
class CPUStats:
    """Statistics extracted from mpstat output."""
    cpu_utilization_pct: float = 0.0
    user_pct: float = 0.0
    system_pct: float = 0.0
    idle_pct: float = 0.0
    iowait_pct: float = 0.0
    duration_seconds: float = 0.0


@dataclass
class NodeMetrics:
    """Aggregated metrics for a single node."""
    node_id: str
    packet_stats: Optional[PacketStats] = None
    cpu_stats: Optional[CPUStats] = None
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class Instrumentor:
    """
    Remote instrumentation agent for physical mesh nodes.

    Executes monitoring commands via SSH and parses their output to extract
    network packet counts and CPU utilization metrics.
    """

    # tcpdump interface pattern (captures all interfaces)
    TCPDUMP_CMD = "timeout {duration} tcpdump -i any -c {count} 2>/dev/null"

    # mpstat command: report CPU stats for all CPUs, interval=1, count=5
    # Output format includes a summary line at the end
    MPSTAT_CMD = "mpstat -P ALL 1 {count} 2>/dev/null | tail -n 13"

    def __init__(self, node_manager: Optional[NodeManager] = None):
        """
        Initialize the Instrumentor.

        Args:
            node_manager: Optional NodeManager instance. If not provided,
                        a new one will be created from config.
        """
        self.node_manager = node_manager
        if self.node_manager is None:
            config = load_config()
            self.node_manager = NodeManager(config)
            logger.info("Created new NodeManager for Instrumentor")

    def _execute_ssh_command(
        self,
        connection: SSHConnection,
        command: str,
        timeout: int = 300
    ) -> Tuple[bool, str, str]:
        """
        Execute a command on a remote node via SSH.

        Args:
            connection: Active SSHConnection object
            command: Shell command to execute
            timeout: Command timeout in seconds

        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            logger.debug(f"Executing command on {connection.node_id}: {command}")
            _, stdout, stderr = connection.client.exec_command(
                command,
                timeout=timeout
            )

            exit_status = stdout.channel.recv_exit_status()
            stdout_text = stdout.read().decode('utf-8', errors='replace')
            stderr_text = stderr.read().decode('utf-8', errors='replace')

            if exit_status != 0:
                logger.warning(
                    f"Command failed on {connection.node_id} with exit code {exit_status}: {stderr_text}"
                )
                return False, stdout_text, stderr_text

            return True, stdout_text, stderr_text

        except Exception as e:
            logger.error(f"SSH execution error on {connection.node_id}: {str(e)}")
            return False, "", str(e)

    def _parse_tcpdump_output(self, output: str, duration: float) -> PacketStats:
        """
        Parse tcpdump output to extract packet statistics.

        tcpdump output format (summary line):
        X packets captured
        X packets received by filter
        X packets dropped by kernel

        We count total packets captured.
        """
        stats = PacketStats(duration_seconds=duration)

        # Look for "packets captured" or "packets received by filter"
        captured_match = re.search(r'(\d+)\s+packets? captured', output, re.IGNORECASE)
        received_match = re.search(r'(\d+)\s+packets? received by filter', output, re.IGNORECASE)

        if captured_match:
            stats.packets_received = int(captured_match.group(1))
        elif received_match:
            stats.packets_received = int(received_match.group(1))
        else:
            # If no summary line, count individual packet lines
            # Each packet line starts with a timestamp
            packet_lines = re.findall(r'^\d+\.\d+\s+\d+\.\d+\s+\S+\s+.*$', output, re.MULTILINE)
            stats.packets_received = len(packet_lines)

        # For simplicity, we assume symmetric traffic in this basic implementation
        # In a more sophisticated version, we'd parse individual packet headers
        stats.packets_sent = stats.packets_received
        stats.bytes_received = stats.packets_received * 1500  # Approximate MTU
        stats.bytes_sent = stats.packets_sent * 1500

        logger.debug(f"Parsed tcpdump: {stats.packets_received} packets received")
        return stats

    def _parse_mpstat_output(self, output: str, count: int) -> CPUStats:
        """
        Parse mpstat output to extract CPU utilization statistics.

        mpstat -P ALL output format (last summary line):
        Average: CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
        Average: all    5.23    0.00    1.45    0.12    0.00    0.01    0.00    0.00    0.00    93.19
        """
        stats = CPUStats(duration_seconds=count)

        # Look for the "Average:" line with "all" CPU
        match = re.search(
            r'Average:\s+all\s+([\d.]+)\s+[\d.]+\s+([\d.]+)\s+([\d.]+)\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)',
            output
        )

        if match:
            stats.user_pct = float(match.group(1))
            stats.system_pct = float(match.group(2))
            stats.iowait_pct = float(match.group(3))
            stats.idle_pct = float(match.group(4))
            stats.cpu_utilization_pct = 100.0 - stats.idle_pct
        else:
            # Fallback: try to find any "all" CPU line
            lines = output.strip().split('\n')
            for line in lines:
                if 'all' in line.lower() and not line.startswith('Average:'):
                    parts = line.split()
                    if len(parts) >= 12:
                        try:
                            stats.user_pct = float(parts[2])
                            stats.system_pct = float(parts[4])
                            stats.iowait_pct = float(parts[5])
                            stats.idle_pct = float(parts[11])
                            stats.cpu_utilization_pct = 100.0 - stats.idle_pct
                            break
                        except (ValueError, IndexError):
                            continue

            if stats.cpu_utilization_pct == 0.0:
                logger.warning("Could not parse mpstat output, using default values")

        logger.debug(f"Parsed mpstat: {stats.cpu_utilization_pct:.2f}% CPU utilization")
        return stats

    def measure_packets(
        self,
        node: PhysicalNode,
        duration: int = 10,
        packet_count: int = 1000
    ) -> NodeMetrics:
        """
        Measure packet statistics on a remote node.

        Args:
            node: PhysicalNode to measure
            duration: Duration of capture in seconds
            packet_count: Maximum number of packets to capture

        Returns:
            NodeMetrics containing packet statistics or error
        """
        metrics = NodeMetrics(node_id=node.node_id)

        try:
            with self.node_manager.get_connection(node) as connection:
                command = self.TCPDUMP_CMD.format(
                    duration=duration,
                    count=packet_count
                )

                success, stdout, stderr = self._execute_ssh_command(
                    connection, command, timeout=duration + 10
                )

                if success:
                    metrics.packet_stats = self._parse_tcpdump_output(stdout, duration)
                else:
                    metrics.error = f"tcpdump failed: {stderr}"
                    logger.error(f"tcpdump failed on {node.node_id}: {stderr}")

        except Exception as e:
            metrics.error = f"SSH error during packet measurement: {str(e)}"
            logger.error(f"SSH error on {node.node_id}: {str(e)}")

        return metrics

    def measure_cpu(
        self,
        node: PhysicalNode,
        sample_count: int = 5
    ) -> NodeMetrics:
        """
        Measure CPU utilization on a remote node.

        Args:
            node: PhysicalNode to measure
            sample_count: Number of 1-second samples to collect

        Returns:
            NodeMetrics containing CPU statistics or error
        """
        metrics = NodeMetrics(node_id=node.node_id)

        try:
            with self.node_manager.get_connection(node) as connection:
                command = self.MPSTAT_CMD.format(count=sample_count)

                success, stdout, stderr = self._execute_ssh_command(
                    connection, command, timeout=sample_count + 30
                )

                if success:
                    metrics.cpu_stats = self._parse_mpstat_output(stdout, sample_count)
                else:
                    metrics.error = f"mpstat failed: {stderr}"
                    logger.error(f"mpstat failed on {node.node_id}: {stderr}")

        except Exception as e:
            metrics.error = f"SSH error during CPU measurement: {str(e)}"
            logger.error(f"SSH error on {node.node_id}: {str(e)}")

        return metrics

    def measure_all(
        self,
        node: PhysicalNode,
        packet_duration: int = 10,
        packet_count: int = 1000,
        cpu_samples: int = 5
    ) -> NodeMetrics:
        """
        Measure both packet and CPU statistics on a remote node.

        Args:
            node: PhysicalNode to measure
            packet_duration: Duration of packet capture in seconds
            packet_count: Maximum number of packets to capture
            cpu_samples: Number of CPU samples to collect

        Returns:
            NodeMetrics containing both packet and CPU statistics or error
        """
        # Measure packets first (takes packet_duration seconds)
        packet_metrics = self.measure_packets(node, packet_duration, packet_count)

        # Then measure CPU (takes cpu_samples seconds)
        cpu_metrics = self.measure_cpu(node, cpu_samples)

        # Combine results
        combined = NodeMetrics(
            node_id=node.node_id,
            timestamp=time.time()
        )

        if packet_metrics.error:
            combined.error = packet_metrics.error
        elif cpu_metrics.error:
            combined.error = cpu_metrics.error
        else:
            combined.packet_stats = packet_metrics.packet_stats
            combined.cpu_stats = cpu_metrics.cpu_stats

        return combined


def main():
    """
    CLI entry point for the Instrumentor.

    Usage:
        python -m orchestrator.instrumentor --node-id <id> [--measure packets|cpu|all]
    """
    import argparse

    parser = argparse.ArgumentParser(description="Remote node instrumentation tool")
    parser.add_argument(
        "--node-id",
        required=True,
        help="ID of the node to instrument"
    )
    parser.add_argument(
        "--measure",
        choices=["packets", "cpu", "all"],
        default="all",
        help="What to measure: packets, cpu, or all"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=10,
        help="Duration for packet capture (seconds)"
    )
    parser.add_argument(
        "--packet-count",
        type=int,
        default=1000,
        help="Maximum packets to capture"
    )
    parser.add_argument(
        "--cpu-samples",
        type=int,
        default=5,
        help="Number of CPU samples to collect"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path for JSON results"
    )

    args = parser.parse_args()

    config = load_config()
    node_manager = NodeManager(config)

    # Find the node by ID
    target_node = None
    for node in config.nodes:
        if node.node_id == args.node_id:
            target_node = node
            break

    if target_node is None:
        logger.error(f"Node not found: {args.node_id}")
        return 1

    instrumentor = Instrumentor(node_manager)

    if args.measure in ["packets", "all"]:
        logger.info(f"Measuring packets on {args.node_id} for {args.duration}s")
        packet_metrics = instrumentor.measure_packets(
            target_node,
            args.duration,
            args.packet_count
        )
        logger.info(f"Packet metrics: {packet_metrics}")

    if args.measure in ["cpu", "all"]:
        logger.info(f"Measuring CPU on {args.node_id} with {args.cpu_samples} samples")
        cpu_metrics = instrumentor.measure_cpu(
            target_node,
            args.cpu_samples
        )
        logger.info(f"CPU metrics: {cpu_metrics}")

    if args.measure == "all":
        combined = instrumentor.measure_all(
            target_node,
            args.duration,
            args.packet_count,
            args.cpu_samples
        )
        logger.info(f"Combined metrics: {combined}")

    if args.output:
        import json
        metrics_dict = {
            "node_id": target_node.node_id,
            "packet_stats": vars(combined.packet_stats) if combined.packet_stats else None,
            "cpu_stats": vars(combined.cpu_stats) if combined.cpu_stats else None,
            "error": combined.error,
            "timestamp": combined.timestamp
        }
        with open(args.output, 'w') as f:
            json.dump(metrics_dict, f, indent=2)
        logger.info(f"Results written to {args.output}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
