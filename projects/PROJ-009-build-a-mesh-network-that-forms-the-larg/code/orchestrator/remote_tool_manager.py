from __future__ import annotations
import logging
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path
import paramiko
from paramiko import SSHClient, AutoAddPolicy, SSHException

from orchestrator.logger import get_logger

logger = get_logger(__name__)

class ToolMissingError(Exception):
    """Raised when a required tool is missing and cannot be installed."""
    pass

class ToolInstallationError(Exception):
    """Raised when tool installation fails."""
    pass

@dataclass
class NodeToolStatus:
    node_ip: str
    tool_name: str
    is_present: bool
    installation_attempted: bool = False
    installation_success: Optional[bool] = None
    error_message: Optional[str] = None

class RemoteToolManager:
    """
    Manages verification and installation of CLI tools on remote nodes.
    Consolidates check and install logic.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._cache: Dict[str, Dict[str, bool]] = {} # ip -> {tool: present}

    def _connect(self, ip: str, port: int = 22, username: str = 'root', 
                 key_filename: Optional[str] = None) -> SSHClient:
        """Establish SSH connection."""
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())
        try:
            if key_filename:
                client.connect(ip, port=port, username=username, key_filename=key_filename, timeout=10)
            else:
                client.connect(ip, port=port, username=username, timeout=10)
            return client
        except SSHException as e:
            raise RemoteExecutionError(f"SSH connection failed to {ip}: {e}")

    def check_tool(self, ip: str, tool_name: str, username: str = 'root', 
                   key_filename: Optional[str] = None) -> bool:
        """
        Check if a tool is present on the remote node using `which`.
        Returns True if present, False otherwise.
        """
        client = None
        try:
            client = self._connect(ip, username=username, key_filename=key_filename)
            stdin, stdout, stderr = client.exec_command(f"which {tool_name}", timeout=10)
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8', errors='ignore').strip()
            
            if exit_code == 0 and output:
                self.logger.debug(f"Tool {tool_name} found at {output} on {ip}")
                return True
            else:
                self.logger.debug(f"Tool {tool_name} NOT found on {ip}")
                return False
        except Exception as e:
            self.logger.error(f"Error checking tool {tool_name} on {ip}: {e}")
            return False
        finally:
            if client:
                client.close()

    def install_tool(self, ip: str, tool_name: str, username: str = 'root', 
                     key_filename: Optional[str] = None) -> bool:
        """
        Attempt to install a tool on the remote node.
        Tries apt-get, then yum.
        Returns True if successful, False otherwise.
        """
        client = None
        try:
            client = self._connect(ip, username=username, key_filename=key_filename)
            
            # Try apt-get
            cmd_apt = f"apt-get update && apt-get install -y {tool_name}"
            self.logger.info(f"Attempting to install {tool_name} via apt-get on {ip}")
            stdin, stdout, stderr = client.exec_command(cmd_apt, timeout=120)
            exit_code = stdout.channel.recv_exit_status()
            
            if exit_code == 0:
                self.logger.info(f"Successfully installed {tool_name} via apt-get on {ip}")
                return True
            
            # Try yum
            cmd_yum = f"yum install -y {tool_name}"
            self.logger.info(f"Attempting to install {tool_name} via yum on {ip}")
            stdin, stdout, stderr = client.exec_command(cmd_yum, timeout=120)
            exit_code = stdout.channel.recv_exit_status()
            
            if exit_code == 0:
                self.logger.info(f"Successfully installed {tool_name} via yum on {ip}")
                return True
            
            self.logger.error(f"Failed to install {tool_name} on {ip} via apt-get and yum")
            return False

        except Exception as e:
            self.logger.error(f"Error installing tool {tool_name} on {ip}: {e}")
            return False
        finally:
            if client:
                client.close()

    def check_tools(self, ip: str, tool_names: List[str], username: str = 'root', 
                    key_filename: Optional[str] = None) -> List[NodeToolStatus]:
        """
        Check presence of multiple tools on a node.
        Returns a list of NodeToolStatus.
        """
        results = []
        for tool in tool_names:
            is_present = self.check_tool(ip, tool, username, key_filename)
            status = NodeToolStatus(
                node_ip=ip,
                tool_name=tool,
                is_present=is_present
            )
            results.append(status)
        return results

    def ensure_tools(self, ip: str, tool_names: List[str], username: str = 'root', 
                     key_filename: Optional[str] = None) -> List[NodeToolStatus]:
        """
        Ensure all required tools are present.
        If missing, attempt installation.
        If still missing after install attempt, raise ToolMissingError.
        """
        results = self.check_tools(ip, tool_names, username, key_filename)
        
        for status in results:
            if not status.is_present:
                status.installation_attempted = True
                success = self.install_tool(ip, status.tool_name, username, key_filename)
                status.installation_success = success
                
                if not success:
                    status.error_message = f"Failed to install {status.tool_name}"
                    self.logger.error(status.error_message)
                else:
                    # Re-check
                    status.is_present = self.check_tool(ip, status.tool_name, username, key_filename)
                    if not status.is_present:
                        status.error_message = f"Installation succeeded but tool not found: {status.tool_name}"
                        self.logger.error(status.error_message)
        
        # Check if any tool is still missing
        missing_tools = [r.tool_name for r in results if not r.is_present]
        if missing_tools:
            raise ToolMissingError(f"Missing tools on {ip}: {missing_tools}")
        
        return results

def create_tool_manager() -> RemoteToolManager:
    return RemoteToolManager()

class RemoteExecutionError(Exception):
    """Raised when remote command execution fails."""
    pass

def main():
    """CLI entry point for testing."""
    import argparse
    parser = argparse.ArgumentParser(description="Remote Tool Manager")
    parser.add_argument("--ip", type=str, required=True, help="Target node IP")
    parser.add_argument("--tools", type=str, nargs='+', required=True, help="List of tools to check/install")
    parser.add_argument("--username", type=str, default="root", help="SSH username")
    parser.add_argument("--key", type=str, help="SSH key file")
    args = parser.parse_args()

    manager = create_tool_manager()
    try:
        results = manager.ensure_tools(
            ip=args.ip,
            tool_names=args.tools,
            username=args.username,
            key_filename=args.key
        )
        for r in results:
            print(f"{r.tool_name}: {'Present' if r.is_present else 'Missing'}")
    except ToolMissingError as e:
        print(f"Error: {e}")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
