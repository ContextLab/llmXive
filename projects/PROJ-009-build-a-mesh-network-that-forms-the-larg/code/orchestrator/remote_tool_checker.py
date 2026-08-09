"""
Remote Tool Checker - Legacy module kept for compatibility.

This module provides a simpler interface for checking tools on remote nodes.
It is maintained for backward compatibility but new code should use
RemoteToolManager from remote_tools_manager.py.
"""

from __future__ import annotations

import logging
import socket
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

import paramiko

from orchestrator.logger import get_logger

# Re-export for compatibility
from orchestrator.remote_tools_manager import ToolMissingError

@dataclass
class ToolCheckResult:
    """Result of checking a single tool on a node."""
    tool_name: str
    present: bool
    path: Optional[str] = None
    error: Optional[str] = None

@dataclass
class NodeToolCheckResult:
    """Result of checking all tools on a node."""
    node_id: str
    ip_address: str
    tool_results: List[ToolCheckResult] = field(default_factory=list)
    all_present: bool = True

    def missing_tools(self) -> List[str]:
        return [r.tool_name for r in self.tool_results if not r.present]

class RemoteToolChecker:
    """Simple tool checker for backward compatibility."""

    REQUIRED_TOOLS = {"tcpdump", "mpstat"}

    def __init__(self, node_manager, logger: Optional[logging.Logger] = None):
        self.node_manager = node_manager
        self.logger = logger or get_logger(__name__)

    def check_node(
        self,
        node_id: str,
        ip_address: str,
        timeout: float = 5.0
    ) -> NodeToolCheckResult:
        """Check tools on a single node."""
        result = NodeToolCheckResult(node_id=node_id, ip_address=ip_address)
        client = None

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=ip_address, timeout=timeout)

            for tool in self.REQUIRED_TOOLS:
                tool_result = ToolCheckResult(tool_name=tool, present=False)
                try:
                    stdin, stdout, stderr = client.exec_command(f"which {tool}")
                    exit_code = stdout.channel.recv_exit_status()
                    if exit_code == 0:
                        tool_result.present = True
                        tool_result.path = stdout.read().decode().strip()
                    else:
                        tool_result.error = stderr.read().decode().strip()
                except Exception as e:
                    tool_result.error = str(e)

                result.tool_results.append(tool_result)
                if not tool_result.present:
                    result.all_present = False

        except Exception as e:
            self.logger.error(f"Error checking tools on {node_id}: {e}")
            raise
        finally:
            if client:
                client.close()

        return result

def create_tool_checker(node_manager) -> RemoteToolChecker:
    return RemoteToolChecker(node_manager)

def main():
    import sys
    print("Remote Tool Checker - use RemoteToolManager instead")
    sys.exit(0)

if __name__ == "__main__":
    main()
