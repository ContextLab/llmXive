from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from orchestrator.logger import get_logger
from orchestrator.node_manager import NodeManager, NodeDiscoveryError

logger = get_logger(__name__)


@dataclass
class InstallationResult:
    """Result of tool installation attempt."""
    success: bool = False
    installed_tools: List[str] = None
    failed_tools: List[str] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.installed_tools is None:
            self.installed_tools = []
        if self.failed_tools is None:
            self.failed_tools = []


class ToolInstallationError(Exception):
    """Raised when tool installation fails."""
    pass


class RemoteToolInstaller:
    """Handles installation of CLI tools on remote nodes."""

    def __init__(self, node_manager: Optional[NodeManager] = None):
        self.node_manager = node_manager or NodeManager()
        self._package_managers = [
            ("apt-get", "apt-get install -y {}"),
            ("yum", "yum install -y {}"),
            ("dnf", "dnf install -y {}"),
        ]

    def install_tools(
        self, node_ip: str, tools: List[str], sudo: bool = True
    ) -> InstallationResult:
        """
        Install tools on a remote node.

        Args:
            node_ip: IP address of the remote node.
            tools: List of tool names to install.
            sudo: Whether to use sudo (default: True).

        Returns:
            InstallationResult with success status and installed tools.
        """
        result = InstallationResult()

        if not tools:
            result.success = True
            return result

        try:
            # Try each package manager
            for pm_name, install_cmd in self._package_managers:
                logger.info(
                    f"Attempting installation on {node_ip} using {pm_name}"
                )

                success = True
                for tool in tools:
                    # Map tool name to package name (simplified)
                    package_name = tool  # In reality, might need mapping

                    cmd = install_cmd.format(package_name)
                    if sudo:
                        cmd = f"sudo {cmd}"

                    try:
                        stdin, stdout, stderr = self.node_manager.execute_command(
                            node_ip, cmd, timeout=60
                        )
                        exit_code = stdout.channel.recv_exit_status()

                        if exit_code != 0:
                            error_output = stderr.read().decode("utf-8", errors="ignore")
                            logger.warning(
                                f"Failed to install {tool} on {node_ip}: {error_output}"
                            )
                            success = False
                            result.failed_tools.append(tool)
                        else:
                            result.installed_tools.append(tool)
                            logger.info(f"Successfully installed {tool} on {node_ip}")

                    except Exception as e:
                        logger.warning(
                            f"Installation error for {tool} on {node_ip}: {e}"
                        )
                        success = False
                        result.failed_tools.append(tool)

                if success and not result.failed_tools:
                    result.success = True
                    break
                elif result.installed_tools:
                    # Partial success - continue with remaining tools
                    remaining_tools = [
                        t for t in tools if t not in result.installed_tools
                    ]
                    if remaining_tools:
                        continue
                    else:
                        break

            if not result.success and not result.installed_tools:
                result.error_message = "All package managers failed"

        except NodeDiscoveryError as e:
            result.error_message = f"Node discovery failed: {str(e)}"
        except Exception as e:
            logger.exception(f"Installation failed on {node_ip}")
            result.error_message = f"Installation failed: {str(e)}"

        return result

    def install_with_retry(
        self, node_ip: str, tools: List[str], max_retries: int = 3
    ) -> InstallationResult:
        """
        Install tools with retry logic.

        Args:
            node_ip: IP address of the remote node.
            tools: List of tool names to install.
            max_retries: Maximum number of retry attempts.

        Returns:
            InstallationResult with success status.
        """
        for attempt in range(max_retries):
            result = self.install_tools(node_ip, tools)
            if result.success:
                return result

            if attempt < max_retries - 1:
                logger.info(
                    f"Retry {attempt + 1}/{max_retries} for {node_ip}"
                )
                time.sleep(2 ** attempt)  # Exponential backoff

        return result


def create_tool_installer(
    node_manager: Optional[NodeManager] = None,
) -> RemoteToolInstaller:
    """Factory function to create a RemoteToolInstaller instance."""
    return RemoteToolInstaller(node_manager=node_manager)


def main():
    """CLI entry point for remote tool installation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Install required tools on remote mesh nodes"
    )
    parser.add_argument(
        "--nodes",
        nargs="+",
        required=True,
        help="List of node IPs to install tools on",
    )
    parser.add_argument(
        "--tools",
        nargs="+",
        default=["tcpdump", "mpstat"],
        help="Tools to install (default: tcpdump mpstat)",
    )
    parser.add_argument(
        "--no-sudo",
        action="store_true",
        help="Don't use sudo for installation",
    )
    parser.add_argument(
        "--retry",
        type=int,
        default=3,
        help="Number of retry attempts (default: 3)",
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

        installer = create_tool_installer(node_manager)

        all_success = True
        for node_ip in args.nodes:
            logger.info(f"Installing tools on {node_ip}")
            result = installer.install_with_retry(
                node_ip,
                args.tools,
                max_retries=args.retry if not args.no_sudo else 1,
            )

            if result.success:
                logger.info(f"  Success: {', '.join(result.installed_tools)}")
            else:
                logger.error(f"  Failed: {result.error_message}")
                if result.failed_tools:
                    logger.error(f"  Failed tools: {', '.join(result.failed_tools)}")
                all_success = False

        if not all_success:
            return 1

        return 0

    except Exception as e:
        logger.exception(f"Installation failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())