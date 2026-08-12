from __future__ import annotations
import logging
import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import paramiko
from paramiko import SSHClient, AutoAddPolicy, SSHException

from orchestrator.logger import get_logger

logger = get_logger(__name__)

class ToolInstallationError(Exception):
    """Raised when tool installation fails."""
    pass

@dataclass
class InstallationResult:
    success: bool
    message: str
    exit_code: Optional[int] = None

class RemoteToolInstaller:
    """Handles installation of tools on remote nodes."""

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
            raise ToolInstallationError(f"SSH connection failed to {ip}: {e}")

    def install(self, ip: str, tool_name: str, username: str = 'root', 
                key_filename: Optional[str] = None) -> InstallationResult:
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
                return InstallationResult(success=True, message=f"Installed {tool_name} via apt-get", exit_code=exit_code)
            
            # Try yum
            cmd_yum = f"yum install -y {tool_name}"
            self.logger.info(f"Attempting to install {tool_name} via yum on {ip}")
            stdin, stdout, stderr = client.exec_command(cmd_yum, timeout=120)
            exit_code = stdout.channel.recv_exit_status()
            
            if exit_code == 0:
                self.logger.info(f"Successfully installed {tool_name} via yum on {ip}")
                return InstallationResult(success=True, message=f"Installed {tool_name} via yum", exit_code=exit_code)
            
            self.logger.error(f"Failed to install {tool_name} on {ip} via apt-get and yum")
            return InstallationResult(success=False, message=f"Failed to install {tool_name}", exit_code=exit_code)

        except Exception as e:
            self.logger.error(f"Error installing tool {tool_name} on {ip}: {e}")
            return InstallationResult(success=False, message=str(e))
        finally:
            if client:
                client.close()

def create_tool_installer() -> RemoteToolInstaller:
    return RemoteToolInstaller()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Remote Tool Installer")
    parser.add_argument("--ip", type=str, required=True, help="Target node IP")
    parser.add_argument("--tool", type=str, required=True, help="Tool to install")
    parser.add_argument("--username", type=str, default="root", help="SSH username")
    parser.add_argument("--key", type=str, help="SSH key file")
    args = parser.parse_args()

    installer = create_tool_installer()
    result = installer.install(args.ip, args.tool, args.username, args.key)
    print(f"Installation Result: {result}")

if __name__ == "__main__":
    main()
