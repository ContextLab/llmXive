from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

from orchestrator.logger import get_logger
from orchestrator.node_manager import SSHConnection, NodeManager

logger = get_logger(__name__)


@dataclass
class ImpairmentConfig:
    """Configuration for network impairment injection."""
    latency_ms: Optional[int] = None  # Add latency (e.g., 100)
    jitter_ms: Optional[int] = None   # Add jitter (e.g., 10)
    packet_loss_pct: Optional[float] = None  # Packet loss (e.g., 1.5)
    bandwidth_mbps: Optional[int] = None     # Limit bandwidth (e.g., 10)
    corruption_pct: Optional[float] = None   # Packet corruption (e.g., 0.01)


@dataclass
class ImpairmentResult:
    """Result of an impairment injection attempt."""
    success: bool
    node_id: str
    command: str
    error_message: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None


class NetworkImpairments:
    """
    Manages network impairment injection on remote nodes via SSH.
    Uses `tc` (traffic control) and `netem` (network emulation) commands.
    """

    def __init__(self, node_manager: NodeManager):
        self.node_manager = node_manager
        self.logger = get_logger(__name__)

    def _build_tc_netem_command(
        self,
        interface: str = "eth0",
        config: Optional[ImpairmentConfig] = None
    ) -> str:
        """
        Constructs the 'tc qdisc' command for netem.
        If config is None, returns the command to remove all impairments.
        """
        if config is None:
            # Flush all qdiscs on the interface to reset
            return f"tc qdisc del dev {interface} root 2>/dev/null || true"

        parts = ["tc qdisc add dev", interface, "root", "netem"]

        if config.latency_ms is not None:
            parts.append(f"delay {config.latency_ms}ms")
            if config.jitter_ms is not None:
                parts[-1] += f" {config.jitter_ms}ms"

        if config.packet_loss_pct is not None:
            parts.append(f"loss {config.packet_loss_pct}%")

        if config.bandwidth_mbps is not None:
            # Rate limiting requires a different qdisc (tbf) or handle
            # For simplicity in this context, we append 'rate' to netem if supported
            # or note that it might require a separate tbf qdisc.
            # Standard netem supports rate limiting in newer kernels.
            parts.append(f"rate {config.bandwidth_mbps}mbit")

        if config.corruption_pct is not None:
            parts.append(f"corrupt {config.corruption_pct}%")

        return " ".join(parts)

    def inject_impairment(
        self,
        node_id: str,
        config: ImpairmentConfig,
        interface: str = "eth0"
    ) -> ImpairmentResult:
        """
        Injects network impairments on a specific node.

        Args:
            node_id: The ID of the target node.
            config: The ImpairmentConfig object defining the impairments.
            interface: The network interface to apply rules to (default: eth0).

        Returns:
            ImpairmentResult indicating success or failure.
        """
        command = self._build_tc_netem_command(interface, config)
        self.logger.info(f"Injecting impairment on {node_id}: {command}")

        try:
            conn = self.node_manager.get_connection(node_id)
            if not conn or not conn.is_connected():
                return ImpairmentResult(
                    success=False,
                    node_id=node_id,
                    command=command,
                    error_message="SSH connection not available"
                )

            # Execute the command
            # We use sudo because tc usually requires root privileges
            full_command = f"sudo {command}"

            stdout, stderr, exit_code = conn.exec_command(full_command)

            if exit_code == 0:
                self.logger.info(f"Impairment injected successfully on {node_id}")
                return ImpairmentResult(
                    success=True,
                    node_id=node_id,
                    command=command,
                    stdout=stdout.read().decode(),
                    stderr=stderr.read().decode()
                )
            else:
                err_msg = stderr.read().decode()
                self.logger.error(f"Failed to inject impairment on {node_id}: {err_msg}")
                return ImpairmentResult(
                    success=False,
                    node_id=node_id,
                    command=command,
                    error_message=err_msg,
                    stderr=err_msg
                )

        except Exception as e:
            self.logger.error(f"Exception during impairment injection on {node_id}: {e}", exc_info=True)
            return ImpairmentResult(
                success=False,
                node_id=node_id,
                command=command,
                error_message=str(e)
            )

    def clear_impairments(
        self,
        node_id: str,
        interface: str = "eth0"
    ) -> ImpairmentResult:
        """
        Clears all network impairments on a specific node.

        Args:
            node_id: The ID of the target node.
            interface: The network interface to clear rules from.

        Returns:
            ImpairmentResult indicating success or failure.
        """
        return self.inject_impairment(node_id, ImpairmentConfig(), interface)

    def apply_impairments_to_nodes(
        self,
        node_ids: List[str],
        config: ImpairmentConfig,
        interface: str = "eth0"
    ) -> List[ImpairmentResult]:
        """
        Applies the same impairment configuration to a list of nodes.

        Args:
            node_ids: List of node IDs to target.
            config: The ImpairmentConfig object.
            interface: The network interface.

        Returns:
            List of ImpairmentResult objects.
        """
        results = []
        for node_id in node_ids:
            result = self.inject_impairment(node_id, config, interface)
            results.append(result)
        return results


def main():
    """
    CLI entry point for testing network impairment injection.
    Usage: python -m orchestrator.network_impairments --node-id NODE_ID --latency 100 --loss 1.0
    """
    import argparse

    parser = argparse.ArgumentParser(description="Inject network impairments via SSH")
    parser.add_argument("--node-id", type=str, required=True, help="Target node ID")
    parser.add_argument("--latency", type=int, default=None, help="Latency in ms")
    parser.add_argument("--jitter", type=int, default=None, help="Jitter in ms")
    parser.add_argument("--loss", type=float, default=None, help="Packet loss percentage")
    parser.add_argument("--bandwidth", type=int, default=None, help="Bandwidth limit in Mbps")
    parser.add_argument("--clear", action="store_true", help="Clear all impairments")
    parser.add_argument("--config-yaml", type=str, default=None, help="Path to YAML config file")

    args = parser.parse_args()

    # Initialize logger
    init_logger()

    # Load config if provided
    config = ImpairmentConfig()
    if args.config_yaml:
        import yaml
        with open(args.config_yaml, 'r') as f:
            data = yaml.safe_load(f)
            config = ImpairmentConfig(**data)
    else:
        config = ImpairmentConfig(
            latency_ms=args.latency,
            jitter_ms=args.jitter,
            packet_loss_pct=args.loss,
            bandwidth_mbps=args.bandwidth
        )

    if args.clear:
        config = ImpairmentConfig()

    # Initialize NodeManager (assumes config file exists at default location or env vars)
    # For CLI testing, we might need to pass a specific config file path
    from orchestrator.config import load_config
    try:
        project_config = load_config()
        node_manager = NodeManager(project_config)
        node_manager.connect_all()
    except Exception as e:
        logger.error(f"Failed to initialize NodeManager: {e}")
        return 1

    impairments = NetworkImpairments(node_manager)

    if args.clear:
        logger.info(f"Clearing impairments on {args.node_id}")
        result = impairments.clear_impairments(args.node_id)
    else:
        logger.info(f"Injecting impairments on {args.node_id}")
        result = impairments.inject_impairment(args.node_id, config)

    if result.success:
        logger.info(f"Success: {result.command}")
        return 0
    else:
        logger.error(f"Failed: {result.error_message}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
