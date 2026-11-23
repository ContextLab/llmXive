"""
Integration tests for the Instrumentor module.

These tests verify that the Instrumentor can successfully connect to nodes
and execute monitoring commands via SSH.
"""
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from orchestrator.config import load_config
from orchestrator.instrumentor import Instrumentor, NodeMetrics
from orchestrator.models import PhysicalNode, NodeStatus
from orchestrator.node_manager import NodeManager, SSHConnection


@pytest.fixture
def mock_ssh_client():
    """Create a mock SSH client for testing."""
    mock_client = MagicMock()
    mock_channel = MagicMock()
    mock_stdin = MagicMock()
    mock_stdout = MagicMock()
    mock_stderr = MagicMock()

    mock_client.get_transport.return_value = MagicMock()
    mock_client.get_transport().is_active.return_value = True

    mock_stdout.channel = mock_channel
    mock_channel.recv_exit_status.return_value = 0

    return mock_client, mock_stdout, mock_stderr


@pytest.fixture
def sample_node():
    """Create a sample PhysicalNode for testing."""
    return PhysicalNode(
        node_id="test-node-1",
        hostname="192.168.1.100",
        port=22,
        username="testuser",
        status=NodeStatus.AVAILABLE,
        hardware_spec={"cpu": "Intel i7", "ram_gb": 32, "disk_gb": 500}
    )


class TestInstrumentor:
    """Integration tests for the Instrumentor class."""

    def test_instrumentor_initialization(self, sample_node):
        """Test that Instrumentor initializes correctly."""
        with patch('orchestrator.instrumentor.NodeManager') as MockNodeManager:
            mock_manager = MagicMock()
            MockNodeManager.return_value = mock_manager

            instrumentor = Instrumentor(node_manager=mock_manager)

            assert instrumentor.node_manager == mock_manager

    def test_instrumentor_initialization_from_config(self):
        """Test that Instrumentor can initialize from config."""
        with patch('orchestrator.instrumentor.NodeManager') as MockNodeManager:
            with patch('orchestrator.instrumentor.load_config') as MockLoadConfig:
                MockLoadConfig.return_value = MagicMock()
                instrumentor = Instrumentor()

                MockLoadConfig.assert_called_once()
                MockNodeManager.assert_called_once()

    @patch('orchestrator.instrumentor.NodeManager')
    def test_measure_packets_success(
        self,
        MockNodeManager,
        sample_node,
        mock_ssh_client
    ):
        """Test successful packet measurement."""
        mock_client, mock_stdout, mock_stderr = mock_ssh_client

        # Mock tcpdump output
        tcpdump_output = """
        16:01:23.456789 IP 192.168.1.1.12345 > 192.168.1.2.80: Flags [S], seq 123456
        16:01:23.456790 IP 192.168.1.2.80 > 192.168.1.1.12345: Flags [S.], seq 789012
        16:01:23.456791 IP 192.168.1.1.12345 > 192.168.1.2.80: Flags [.], ack 789013
        16:01:23.456792 IP 192.168.1.2.80 > 192.168.1.1.12345: Flags [P.], seq 1:100
        16:01:23.456793 IP 192.168.1.1.12345 > 192.168.1.2.80: Flags [.], ack 100
        10 packets captured
        """

        mock_stdout.read.return_value = tcpdump_output.encode('utf-8')

        mock_manager = MagicMock()
        mock_connection = MagicMock()
        mock_connection.client = mock_client
        mock_manager.get_connection.return_value.__enter__.return_value = mock_connection

        MockNodeManager.return_value = mock_manager

        instrumentor = Instrumentor(node_manager=mock_manager)
        metrics = instrumentor.measure_packets(sample_node, duration=10, packet_count=100)

        assert metrics.node_id == sample_node.node_id
        assert metrics.error is None
        assert metrics.packet_stats is not None
        assert metrics.packet_stats.packets_received == 10
        assert metrics.packet_stats.packets_sent == 10

    @patch('orchestrator.instrumentor.NodeManager')
    def test_measure_cpu_success(
        self,
        MockNodeManager,
        sample_node,
        mock_ssh_client
    ):
        """Test successful CPU measurement."""
        mock_client, mock_stdout, mock_stderr = mock_ssh_client

        # Mock mpstat output
        mpstat_output = """
        Linux 5.4.0-42-generic (test-node)  09/15/2023  _x86_64_  (4 CPU)

        09:30:00     CPU     %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
        09:30:01     all     5.23    0.00    1.45    0.12    0.00    0.01    0.00    0.00    0.00    93.19
        09:30:02     all     5.45    0.00    1.32    0.15    0.00    0.02    0.00    0.00    0.00    93.06
        09:30:03     all     5.67    0.00    1.28    0.10    0.00    0.01    0.00    0.00    0.00    92.94
        09:30:04     all     5.89    0.00    1.35    0.18    0.00    0.03    0.00    0.00    0.00    92.55
        09:30:05     all     5.12    0.00    1.42    0.14    0.00    0.02    0.00    0.00    0.00    93.30

        Average:     CPU     %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
        Average:     all     5.47    0.00    1.36    0.14    0.00    0.02    0.00    0.00    0.00    93.01
        """

        mock_stdout.read.return_value = mpstat_output.encode('utf-8')

        mock_manager = MagicMock()
        mock_connection = MagicMock()
        mock_connection.client = mock_client
        mock_manager.get_connection.return_value.__enter__.return_value = mock_connection

        MockNodeManager.return_value = mock_manager

        instrumentor = Instrumentor(node_manager=mock_manager)
        metrics = instrumentor.measure_cpu(sample_node, sample_count=5)

        assert metrics.node_id == sample_node.node_id
        assert metrics.error is None
        assert metrics.cpu_stats is not None
        assert metrics.cpu_stats.cpu_utilization_pct > 0
        assert metrics.cpu_stats.cpu_utilization_pct < 100
        assert abs(metrics.cpu_stats.cpu_utilization_pct - 6.99) < 0.1

    @patch('orchestrator.instrumentor.NodeManager')
    def test_measure_packets_failure(
        self,
        MockNodeManager,
        sample_node,
        mock_ssh_client
    ):
        """Test packet measurement failure handling."""
        mock_client, mock_stdout, mock_stderr = mock_ssh_client

        # Mock failed tcpdump output
        mock_stdout.read.return_value = b""
        mock_stderr.read.return_value = b"tcpdump: command not found"
        mock_stdout.channel.recv_exit_status.return_value = 127

        mock_manager = MagicMock()
        mock_connection = MagicMock()
        mock_connection.client = mock_client
        mock_manager.get_connection.return_value.__enter__.return_value = mock_connection

        MockNodeManager.return_value = mock_manager

        instrumentor = Instrumentor(node_manager=mock_manager)
        metrics = instrumentor.measure_packets(sample_node, duration=10)

        assert metrics.node_id == sample_node.node_id
        assert metrics.error is not None
        assert "tcpdump" in metrics.error.lower()

    @patch('orchestrator.instrumentor.NodeManager')
    def test_measure_all_success(
        self,
        MockNodeManager,
        sample_node,
        mock_ssh_client
    ):
        """Test combined measurement of packets and CPU."""
        mock_client, mock_stdout, mock_stderr = mock_ssh_client

        # First call: tcpdump
        tcpdump_output = """
        16:01:23.456789 IP 192.168.1.1.12345 > 192.168.1.2.80: Flags [S]
        5 packets captured
        """

        # Second call: mpstat
        mpstat_output = """
        Linux 5.4.0-42-generic (test-node)

        09:30:00     CPU     %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
        09:30:01     all     5.23    0.00    1.45    0.12    0.00    0.01    0.00    0.00    0.00    93.19
        09:30:02     all     5.45    0.00    1.32    0.15    0.00    0.02    0.00    0.00    0.00    93.06
        09:30:03     all     5.67    0.00    1.28    0.10    0.00    0.01    0.00    0.00    0.00    92.94
        09:30:04     all     5.89    0.00    1.35    0.18    0.00    0.03    0.00    0.00    0.00    92.55
        09:30:05     all     5.12    0.00    1.42    0.14    0.00    0.02    0.00    0.00    0.00    93.30

        Average:     all     5.47    0.00    1.36    0.14    0.00    0.02    0.00    0.00    0.00    93.01
        """

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                mock_stdout.read.return_value = tcpdump_output.encode('utf-8')
            else:
                mock_stdout.read.return_value = mpstat_output.encode('utf-8')
            return mock_stdout, mock_stdout, mock_stderr

        mock_client.exec_command.side_effect = side_effect

        mock_manager = MagicMock()
        mock_connection = MagicMock()
        mock_connection.client = mock_client
        mock_manager.get_connection.return_value.__enter__.return_value = mock_connection

        MockNodeManager.return_value = mock_manager

        instrumentor = Instrumentor(node_manager=mock_manager)
        metrics = instrumentor.measure_all(
            sample_node,
            packet_duration=10,
            packet_count=100,
            cpu_samples=5
        )

        assert metrics.node_id == sample_node.node_id
        assert metrics.error is None
        assert metrics.packet_stats is not None
        assert metrics.cpu_stats is not None
        assert metrics.packet_stats.packets_received == 5
        assert metrics.cpu_stats.cpu_utilization_pct > 0

    @patch('orchestrator.instrumentor.NodeManager')
    def test_ssh_connection_error(
        self,
        MockNodeManager,
        sample_node
    ):
        """Test handling of SSH connection errors."""
        mock_manager = MagicMock()
        mock_manager.get_connection.side_effect = Exception("SSH connection failed")

        MockNodeManager.return_value = mock_manager

        instrumentor = Instrumentor(node_manager=mock_manager)
        metrics = instrumentor.measure_packets(sample_node)

        assert metrics.node_id == sample_node.node_id
        assert metrics.error is not None
        assert "SSH" in metrics.error

    def test_main_function_with_args(self, sample_node):
        """Test the main function with command line arguments."""
        import sys
        from io import StringIO

        # Mock sys.argv
        original_argv = sys.argv
        sys.argv = [
            'instrumentor.py',
            '--node-id', sample_node.node_id,
            '--measure', 'all',
            '--duration', '5',
            '--packet-count', '50',
            '--cpu-samples', '3'
        ]

        try:
            # This will fail because the node doesn't exist in real config,
            # but we're testing that the argument parsing works
            with patch('orchestrator.instrumentor.load_config') as MockLoadConfig:
                with patch('orchestrator.instrumentor.NodeManager') as MockNodeManager:
                    mock_manager = MagicMock()
                    MockNodeManager.return_value = mock_manager
                    MockLoadConfig.return_value = MagicMock(nodes=[sample_node])

                    # Mock the node lookup
                    mock_manager.nodes = [sample_node]

                    result = instrumentor_module_main()
                    # Should return 1 because node lookup fails in mock
                    assert result == 1
        finally:
            sys.argv = original_argv


def instrumentor_module_main():
    """Helper to call main() from tests."""
    from orchestrator.instrumentor import main
    return main()