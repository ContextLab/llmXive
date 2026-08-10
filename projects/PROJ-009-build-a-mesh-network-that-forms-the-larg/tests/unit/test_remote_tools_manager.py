"""
Unit tests for remote_tools_manager.py.

These tests mock the SSH connection to verify logic without needing real nodes.
"""

import unittest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os

# Add code to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from orchestrator.remote_tools_manager import RemoteToolManager, ToolMissingError, NodeToolStatus
from orchestrator.config import Config


class MockChannel:
    """Mock SSH Channel for testing exec_command."""
    def __init__(self, exit_code=0, stdout=b"", stderr=b""):
        self.exit_code = exit_code
        self.stdout_data = stdout
        self.stderr_data = stderr
        self.recv_count = 0

    def recv_exit_status(self):
        return self.exit_code

    def recv(self, bufsize):
        # Simulate reading stdout
        if self.recv_count < len(self.stdout_data):
            data = self.stdout_data[self.recv_count:self.recv_count + bufsize]
            self.recv_count += len(data)
            return data
        return b""


class MockSSHClient:
    """Mock SSH Client for testing."""
    def __init__(self, mock_stdout=b""):
        self.mock_stdout = mock_stdout
        self.connected = False

    def set_missing_host_key_policy(self, policy):
        pass

    def connect(self, hostname, **kwargs):
        self.connected = True
        return True

    def exec_command(self, cmd):
        # Mock stdin, stdout, stderr
        stdin = MagicMock()
        stdout = MagicMock()
        stderr = MagicMock()
        
        stdout.channel = MockChannel(exit_code=0, stdout=self.mock_stdout)
        stderr.read.return_value = b""
        
        return stdin, stdout, stderr

    def close(self):
        self.connected = False


class TestRemoteToolManager(unittest.TestCase):

    def setUp(self):
        self.manager = RemoteToolManager()
        # Mock config to avoid file loading issues
        self.manager.config = {"ssh_timeout": 5}

    @patch('orchestrator.remote_tools_manager.SSHClient')
    def test_tool_found(self, mock_ssh_class):
        """Test successful detection of an existing tool."""
        mock_client = MockSSHClient(mock_stdout=b"/usr/bin/tcpdump\n")
        mock_ssh_class.return_value = mock_client

        status = self.manager.verify_and_install_node("192.168.1.10")
        
        self.assertTrue(status.tcpdump_available)
        self.assertFalse(status.tcpdump_installed)
        self.assertIsNone(status.error_message)

    @patch('orchestrator.remote_tools_manager.SSHClient')
    def test_tool_missing_and_install_success(self, mock_ssh_class):
        """Test installation when tool is missing."""
        # First call (which) returns non-zero (not found)
        # Second call (apt-get) returns zero (success)
        
        # We need a more complex mock for the sequence of calls
        # Since exec_command is called multiple times, we mock the return value dynamically
        
        call_count = [0]
        
        def mock_exec_command(cmd):
            stdin = MagicMock()
            stdout = MagicMock()
            stderr = MagicMock()
            
            if "which" in cmd:
                # Simulate 'which' failing
                stdout.channel = MockChannel(exit_code=1, stdout=b"")
            else:
                # Simulate installation succeeding
                stdout.channel = MockChannel(exit_code=0, stdout=b"Installing...\n")
            
            return stdin, stdout, stderr

        mock_client = MockSSHClient()
        mock_client.exec_command = mock_exec_command
        mock_ssh_class.return_value = mock_client

        status = self.manager.verify_and_install_node("192.168.1.10")

        self.assertTrue(status.tcpdump_installed)
        self.assertTrue(status.tcpdump_available)

    @patch('orchestrator.remote_tools_manager.SSHClient')
    def test_installation_fails(self, mock_ssh_class):
        """Test handling when installation fails."""
        # Simulate 'which' failing and all install attempts failing
        
        def mock_exec_command(cmd):
            stdin = MagicMock()
            stdout = MagicMock()
            stderr = MagicMock()
            
            if "which" in cmd:
                stdout.channel = MockChannel(exit_code=1, stdout=b"")
            else:
                # Simulate failure
                stdout.channel = MockChannel(exit_code=1, stdout=b"")
                stderr.read.return_value = b"Permission denied"
            
            return stdin, stdout, stderr

        mock_client = MockSSHClient()
        mock_client.exec_command = mock_exec_command
        mock_ssh_class.return_value = mock_client

        status = self.manager.verify_and_install_node("192.168.1.10")

        self.assertFalse(status.tcpdump_available)
        self.assertFalse(status.tcpdump_installed)
        self.assertIn("installation failed", status.error_message)

    @patch('orchestrator.remote_tools_manager.SSHClient')
    def test_ssh_connection_failure(self, mock_ssh_class):
        """Test handling of SSH connection errors."""
        from paramiko import SSHException
        
        mock_ssh_class.return_value.connect.side_effect = SSHException("Connection refused")

        status = self.manager.verify_and_install_node("192.168.1.10")

        self.assertFalse(status.tcpdump_available)
        self.assertIn("SSH connection failed", status.error_message)

    def test_raise_if_critical_missing(self):
        """Test that exception is raised if all nodes are missing tools."""
        results = [
            NodeToolStatus(node_ip="1.1.1.1", tcpdump_available=False, mpstat_available=False),
            NodeToolStatus(node_ip="1.1.1.2", tcpdump_available=False, mpstat_available=False),
        ]
        
        with self.assertRaises(ToolMissingError):
            self.manager.raise_if_critical_missing(results)

    def test_no_raise_if_some_ready(self):
        """Test that no exception is raised if at least one node is ready."""
        results = [
            NodeToolStatus(node_ip="1.1.1.1", tcpdump_available=False, mpstat_available=False),
            NodeToolStatus(node_ip="1.1.1.2", tcpdump_available=True, mpstat_available=False),
        ]
        
        # Should not raise
        self.manager.raise_if_critical_missing(results)


if __name__ == '__main__':
    unittest.main()