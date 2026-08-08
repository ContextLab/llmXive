from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path

from orchestrator.logger import get_logger
from orchestrator.node_manager import NodeManager, NodeDiscoveryError
from orchestrator.remote_tool_checker import (
    RemoteToolChecker,
    ToolMissingError,
    ToolCheckResult,
    NodeToolCheckResult,
    create_tool_checker,
)
from orchestrator.remote_tool_installer import (
    RemoteToolInstaller,
    ToolInstallationError,
    InstallationResult,
    create_tool_installer,
)

logger = get_logger(__name__)

CRITICAL_TOOLS = {"tcpdump", "mpstat"}
OPTIONAL_TOOLS = {"tc", "iotop"}


@dataclass
class NodeToolStatus:
    """Status of tool installation on a specific node."""
    node_ip: str
    tools_available: Set[str] = field(default_factory=set)
    tools_missing: Set[str] = field(default_factory=set)
    tools_installed: Set[str] = field(default_factory=set)
    installation_failures: Dict[str, str] = field(default_factory=dict)
    is_available: bool = True
    error_message: Optional[str] = None


class RemoteToolManager:
    """
    Manages verification and installation of required CLI tools on remote nodes.
    Coordinates between the checker and installer components to ensure nodes
    are ready for instrumentation.
    """

    def __init__(
        self,
        node_manager: NodeManager,
        tool_checker: Optional[RemoteToolChecker] = None,
        tool_installer: Optional[RemoteToolInstaller] = None,
    ):
        self.node_manager = node_manager
        self.tool_checker = tool_checker or create_tool_checker()
        self.tool_installer = tool_installer or create_tool_installer()
        self._node_status_cache: Dict[str, NodeToolStatus] = {}

    def verify_and_install_tools(
        self,
        node_ips: List[str],
        critical_tools: Optional[Set[str]] = None,
        optional_tools: Optional[Set[str]] = None,
        force_reinstall: bool = False,
    ) -> Dict[str, NodeToolStatus]:
        """
        Verify tools on remote nodes and install missing ones.

        Args:
            node_ips: List of node IP addresses to check.
            critical_tools: Set of critical tools (defaults to CRITICAL_TOOLS).
            optional_tools: Set of optional tools (defaults to OPTIONAL_TOOLS).
            force_reinstall: If True, reinstall even if tools are present.

        Returns:
            Dictionary mapping node IP to NodeToolStatus.

        Raises:
            ToolMissingError: If any critical tool is missing and cannot be installed.
        """
        critical = critical_tools or CRITICAL_TOOLS
        optional = optional_tools or OPTIONAL_TOOLS
        all_tools = critical | optional

        results: Dict[str, NodeToolStatus] = {}

        for node_ip in node_ips:
            logger.info(f"Checking tools on node {node_ip}")
            status = self._process_node(
                node_ip, all_tools, critical, optional, force_reinstall
            )
            results[node_ip] = status

            if not status.is_available and status.error_message:
                logger.error(
                    f"Node {node_ip} unavailable: {status.error_message}"
                )

        # Raise if any critical tool is missing on any node
        for node_ip, status in results.items():
            if status.tools_missing:
                missing_critical = status.tools_missing & critical
                if missing_critical:
                    raise ToolMissingError(
                        f"Critical tools missing on {node_ip} and cannot be installed: {missing_critical}"
                    )

        return results

    def _process_node(
        self,
        node_ip: str,
        all_tools: Set[str],
        critical: Set[str],
        optional: Set[str],
        force_reinstall: bool,
    ) -> NodeToolStatus:
        """Process a single node for tool verification and installation."""
        status = NodeToolStatus(node_ip=node_ip)

        try:
            # Check existing tools
            check_result = self.tool_checker.check_tools_on_node(
                node_ip, list(all_tools)
            )

            if not check_result.success:
                status.is_available = False
                status.error_message = check_result.error_message
                status.tools_missing = all_tools
                return status

            status.tools_available = set(check_result.available_tools)
            status.tools_missing = set(check_result.missing_tools)

            if not status.tools_missing:
                logger.debug(f"All tools present on {node_ip}")
                return status

            # Attempt installation for missing tools
            missing_critical = status.tools_missing & critical
            missing_optional = status.tools_missing & optional

            if missing_critical:
                logger.info(
                    f"Installing critical tools on {node_ip}: {missing_critical}"
                )
                install_result = self.tool_installer.install_tools(
                    node_ip, list(missing_critical)
                )

                if install_result.success:
                    status.tools_installed = set(install_result.installed_tools)
                    status.tools_available |= status.tools_installed
                    status.tools_missing -= status.tools_installed

                    # Re-check to confirm
                    final_check = self.tool_checker.check_tools_on_node(
                        node_ip, list(status.tools_missing)
                    )
                    if final_check.missing_tools:
                        still_missing = set(final_check.missing_tools)
                        status.tools_missing = still_missing
                        for tool in still_missing:
                            status.installation_failures[tool] = (
                                "Installation succeeded but tool not found"
                            )
                    else:
                        status.tools_missing.clear()
                else:
                    # Installation failed
                    for tool in missing_critical:
                        status.installation_failures[tool] = (
                            install_result.error_message or "Unknown error"
                        )
                    status.tools_missing = missing_critical
                    status.is_available = False
                    status.error_message = (
                        f"Failed to install critical tools: {missing_critical}"
                    )

            # Handle optional tools (don't fail if they can't be installed)
            if missing_optional:
                logger.info(
                    f"Attempting to install optional tools on {node_ip}: {missing_optional}"
                )
                install_result = self.tool_installer.install_tools(
                    node_ip, list(missing_optional)
                )
                if install_result.success:
                    status.tools_installed.update(install_result.installed_tools)
                    status.tools_available |= status.tools_installed
                    status.tools_missing -= status.tools_installed
                else:
                    for tool in missing_optional:
                        status.installation_failures[tool] = (
                            install_result.error_message or "Unknown error"
                        )
                    # Don't mark node unavailable for optional tool failures

        except NodeDiscoveryError as e:
            status.is_available = False
            status.error_message = f"Node discovery failed: {str(e)}"
            status.tools_missing = all_tools
        except Exception as e:
            logger.exception(f"Unexpected error processing node {node_ip}")
            status.is_available = False
            status.error_message = f"Unexpected error: {str(e)}"
            status.tools_missing = all_tools

        return status

    def get_available_nodes(
        self, node_ips: List[str], critical_tools: Optional[Set[str]] = None
    ) -> List[str]:
        """
        Get list of nodes that have all critical tools available.

        Args:
            node_ips: List of node IP addresses.
            critical_tools: Set of critical tools to check (defaults to CRITICAL_TOOLS).

        Returns:
            List of node IPs that are available.
        """
        critical = critical_tools or CRITICAL_TOOLS
        results = self.verify_and_install_tools(node_ips, critical_tools=critical)

        return [
            ip
            for ip, status in results.items()
            if status.is_available and not (status.tools_missing & critical)
        ]

    def invalidate_cache(self, node_ip: Optional[str] = None):
        """Invalidate tool status cache for a node or all nodes."""
        if node_ip:
            self._node_status_cache.pop(node_ip, None)
        else:
            self._node_status_cache.clear()


def create_tool_manager(
    node_manager: Optional[NodeManager] = None,
) -> RemoteToolManager:
    """Factory function to create a RemoteToolManager instance."""
    if node_manager is None:
        # Create a default node manager if not provided
        node_manager = NodeManager()
    return RemoteToolManager(node_manager=node_manager)


def main():
    """CLI entry point for remote tool management."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify and install tools on remote mesh nodes"
    )
    parser.add_argument(
        "--nodes",
        nargs="+",
        required=True,
        help="List of node IPs to check",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reinstall of existing tools",
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
        # Create node manager with provided nodes
        node_manager = NodeManager()
        node_manager.discover_nodes(args.nodes)

        # Create tool manager
        tool_manager = create_tool_manager(node_manager)

        # Verify and install
        results = tool_manager.verify_and_install_tools(
            args.nodes, force_reinstall=args.force
        )

        # Print summary
        available_count = sum(1 for r in results.values() if r.is_available)
        logger.info(
            f"Node availability: {available_count}/{len(results)} nodes ready"
        )

        for ip, status in results.items():
            status_str = "READY" if status.is_available else "UNAVAILABLE"
            logger.info(f"  {ip}: {status_str}")
            if status.tools_available:
                logger.info(f"    Available: {', '.join(status.tools_available)}")
            if status.tools_missing:
                logger.warning(f"    Missing: {', '.join(status.tools_missing)}")
            if status.installation_failures:
                logger.error(f"    Failures: {status.installation_failures}")

    except ToolMissingError as e:
        logger.error(f"Critical tools missing: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Tool management failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
