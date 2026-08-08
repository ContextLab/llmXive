from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from orchestrator.logger import get_logger
from orchestrator.node_manager import NodeManager, NodeDiscoveryError

logger = get_logger(__name__)


@dataclass
class ToolCheckResult:
    """Result of checking tools on a single node."""
    node_ip: str
    success: bool = True
    available_tools: List[str] = field(default_factory=list)
    missing_tools: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class NodeToolCheckResult:
    """Aggregated result for all tools on a node."""
    node_ip: str
    success: bool = True
    tool_results: Dict[str, bool] = field(default_factory=dict)
    available_tools: List[str] = field(default_factory=list)
    missing_tools: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


class ToolMissingError(Exception):
    """Raised when a required tool is missing and cannot be installed."""
    pass


class RemoteToolChecker:
    """Checks for the presence of CLI tools on remote nodes via SSH."""

    def __init__(self, node_manager: Optional[NodeManager] = None):
        self.node_manager = node_manager or NodeManager()

    def check_tools_on_node(
        self, node_ip: str, tools: List[str]
    ) -> ToolCheckResult:
        """
        Check if specified tools are available on a remote node.

        Args:
            node_ip: IP address of the remote node.
            tools: List of tool names to check (e.g., ['tcpdump', 'mpstat']).

        Returns:
            ToolCheckResult with availability status.
        """
        result = ToolCheckResult(node_ip=node_ip)

        try:
            # Use node manager to execute 'which' command
            for tool in tools:
                try:
                    stdin, stdout, stderr = self.node_manager.execute_command(
                        node_ip, f"which {tool}", timeout=5
                    )
                    exit_code = stdout.channel.recv_exit_status()

                    if exit_code == 0:
                        result.available_tools.append(tool)
                        result.tool_results[tool] = True
                    else:
                        result.missing_tools.append(tool)
                        result.tool_results[tool] = False

                except Exception as e:
                    logger.warning(
                        f"Failed to check tool {tool} on {node_ip}: {e}"
                    )
                    result.missing_tools.append(tool)
                    result.tool_results[tool] = False

            if not result.missing_tools:
                result.success = True
            else:
                result.success = False

        except NodeDiscoveryError as e:
            result.success = False
            result.error_message = f"Node discovery failed: {str(e)}"
            result.missing_tools = tools
        except Exception as e:
            logger.exception(f"Error checking tools on {node_ip}")
            result.success = False
            result.error_message = f"Tool check failed: {str(e)}"
            result.missing_tools = tools

        return result

    def check_all_tools(
        self, node_ip: str, tools: List[str]
    ) -> NodeToolCheckResult:
        """
        Check all tools on a node and return aggregated result.

        Args:
            node_ip: IP address of the remote node.
            tools: List of tool names to check.

        Returns:
            NodeToolCheckResult with aggregated status.
        """
        check_result = self.check_tools_on_node(node_ip, tools)

        return NodeToolCheckResult(
            node_ip=node_ip,
            success=check_result.success,
            available_tools=check_result.available_tools,
            missing_tools=check_result.missing_tools,
            error_message=check_result.error_message,
        )


def create_tool_checker(
    node_manager: Optional[NodeManager] = None,
) -> RemoteToolChecker:
    """Factory function to create a RemoteToolChecker instance."""
    return RemoteToolChecker(node_manager=node_manager)


def main():
    """CLI entry point for remote tool checking."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Check for required tools on remote mesh nodes"
    )
    parser.add_argument(
        "--nodes",
        nargs="+",
        required=True,
        help="List of node IPs to check",
    )
    parser.add_argument(
        "--tools",
        nargs="+",
        default=["tcpdump", "mpstat"],
        help="Tools to check (default: tcpdump mpstat)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    try:
        node_manager = NodeManager()
        node_manager.discover_nodes(args.nodes)

        checker = create_tool_checker(node_manager)

        all_available = True
        for node_ip in args.nodes:
            result = checker.check_all_tools(node_ip, args.tools)

            status = "OK" if result.success else "MISSING"
            logger.info(f"Node {node_ip}: {status}")

            if result.available_tools:
                logger.info(f"  Available: {', '.join(result.available_tools)}")
            if result.missing_tools:
                logger.warning(f"  Missing: {', '.join(result.missing_tools)}")
                all_available = False

        if not all_available:
            logger.warning("Some tools are missing on some nodes")
            return 1

        return 0

    except Exception as e:
        logger.exception(f"Tool check failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
