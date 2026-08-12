from __future__ import annotations
import logging
import socket
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import paramiko
from paramiko import SSHClient, AutoAddPolicy, SSHException

from orchestrator.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ToolCheckResult:
    tool_name: str
    is_present: bool
    path: Optional[str] = None
    error: Optional[str] = None

@dataclass
class NodeToolCheckResult:
    node_ip: str
    tool_results: List[ToolCheckResult]

class RemoteToolChecker:
    """Checks for the presence of tools on remote nodes."""

    def __init__(self):
        self.logger = get_logger(__name__)

    def _connect(self, ip: str, port: int = 22, username: str = 'root', 
                 key_filename: Optional[str] = None) -> SSHClient:
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())
        try:
            if key_filename:
                client.connect(ip, port=port, username=username, key_filename=key_filename, timeout=10)
            else:
                client.connect(ip, port=port, username=username, timeout=10)
            return client
        except SSHException as e:
            raise RuntimeError(f"SSH connection failed to {ip}: {e}")

    def check_tool(self, ip: str, tool_name: str, username: str = 'root', 
                   key_filename: Optional[str] = None) -> ToolCheckResult:
        client = None
        try:
            client = self._connect(ip, username=username, key_filename=key_filename)
            stdin, stdout, stderr = client.exec_command(f"which {tool_name}", timeout=10)
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8', errors='ignore').strip()
            
            if exit_code == 0 and output:
                self.logger.debug(f"Tool {tool_name} found at {output} on {ip}")
                return ToolCheckResult(tool_name=tool_name, is_present=True, path=output)
            else:
                self.logger.debug(f"Tool {tool_name} NOT found on {ip}")
                return ToolCheckResult(tool_name=tool_name, is_present=False, error="Not found")
        except Exception as e:
            self.logger.error(f"Error checking tool {tool_name} on {ip}: {e}")
            return ToolCheckResult(tool_name=tool_name, is_present=False, error=str(e))
        finally:
            if client:
                client.close()

    def check_tools(self, ip: str, tool_names: List[str], username: str = 'root', 
                    key_filename: Optional[str] = None) -> NodeToolCheckResult:
        results = []
        for tool in tool_names:
            result = self.check_tool(ip, tool, username, key_filename)
            results.append(result)
        return NodeToolCheckResult(node_ip=ip, tool_results=results)

def create_tool_checker() -> RemoteToolChecker:
    return RemoteToolChecker()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Remote Tool Checker")
    parser.add_argument("--ip", type=str, required=True, help="Target node IP")
    parser.add_argument("--tools", type=str, nargs='+', required=True, help="List of tools to check")
    parser.add_argument("--username", type=str, default="root", help="SSH username")
    parser.add_argument("--key", type=str, help="SSH key file")
    args = parser.parse_args()

    checker = create_tool_checker()
    result = checker.check_tools(args.ip, args.tools, args.username, args.key)
    for tr in result.tool_results:
        print(f"{tr.tool_name}: {'Present' if tr.is_present else 'Missing'}")

if __name__ == "__main__":
    main()