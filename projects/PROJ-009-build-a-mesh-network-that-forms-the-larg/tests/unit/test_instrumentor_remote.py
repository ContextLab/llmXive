import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from orchestrator.instrumentor_remote import RemoteInstrumentor, create_instrumentor, RemoteExecutionError, NetworkSaturationError
from orchestrator.models import PhysicalNode, NodeStatus
from orchestrator.node_manager import NodeManager


class TestRemoteInstrumentor:
    @pytest.fixture
    def mock_node_manager(self):
        manager = Mock(spec=NodeManager)
        manager.get_ssh_client = Mock()
        return manager

    @pytest.fixture
    def mock_ssh_client(self):
        client = Mock()
        client.exec_command = Mock()
        return client

    @pytest.fixture
    def instrumentor(self, mock_node_manager):
        return RemoteInstrumentor(mock_node_manager, packet_count=100, mpstat_interval=1, mpstat_count=3)

    @pytest.fixture
    def test_node(self):
        return PhysicalNode(
            id="test-node-1",
            ip_address="192.168.1.100",
            status=NodeStatus.AVAILABLE,
            hostname="test-node-1",
            ssh_port=22
        )

    def test_instrumentor_initialization(self, mock_node_manager):
        instrumentor = RemoteInstrumentor(mock_node_manager)
        assert instrumentor.node_manager == mock_node_manager
        assert instrumentor.packet_count == 1000  # default
        assert instrumentor.mpstat_interval == 1  # default
        assert instrumentor.mpstat_count == 5  # default

    def test_capture_tcpdump_success(self, instrumentor, mock_ssh_client, test_node):
        # Mock tcpdump output
        mock_output = """
        12:00:00.000000 IP 192.168.1.1.22 > 192.168.1.100.54321: Flags [S], seq 1234567890, win 65535, length 0
        12:00:00.000001 IP 192.168.1.100.54321 > 192.168.1.1.22: Flags [S.], seq 1234567890, ack 1234567891, win 65535, length 0
        100 packets captured
        0 packets dropped by kernel
        """
        mock_stderr = ""
        mock_exit_code = 0

        mock_ssh_client.exec_command.return_value = (
            Mock(read=Mock(return_value=mock_output.encode())),
            Mock(read=Mock(return_value=mock_stderr.encode())),
            Mock(recv_exit_status=Mock(return_value=mock_exit_code))
        )

        # Mock the channel's recv_exit_status to return the exit code
        mock_channel = Mock()
        mock_channel.recv_exit_status.return_value = mock_exit_code
        mock_stdout = Mock()
        mock_stdout.channel = mock_channel
        mock_stdout.read.return_value = mock_output.encode()

        mock_stderr_obj = Mock()
        mock_stderr_obj.read.return_value = mock_stderr.encode()

        mock_ssh_client.exec_command.return_value = (mock_stdout, mock_stderr_obj, mock_exit_code)

        # Actually, let's simplify by patching _execute_remote_command directly
        with patch.object(instrumentor, '_execute_remote_command', return_value=(mock_output, mock_stderr, mock_exit_code)):
            packet_stats = instrumentor.capture_tcpdump(mock_ssh_client)

            assert packet_stats.packet_count == 100
            assert packet_stats.drop_count == 0

    def test_capture_tcpdump_with_drops(self, instrumentor, mock_ssh_client):
        mock_output = """
        12:00:00.000000 IP 192.168.1.1.22 > 192.168.1.100.54321: Flags [S]
        100 packets captured
        25 packets dropped by kernel
        """
        mock_stderr = ""
        mock_exit_code = 0

        with patch.object(instrumentor, '_execute_remote_command', return_value=(mock_output, mock_stderr, mock_exit_code)):
            packet_stats = instrumentor.capture_tcpdump(mock_ssh_client)

            assert packet_stats.packet_count == 100
            assert packet_stats.drop_count == 25

    def test_capture_tcpdump_network_saturation(self, instrumentor, mock_ssh_client):
        # 25% drop rate (>20%)
        mock_output = """
        100 packets captured
        25 packets dropped by kernel
        """
        mock_stderr = ""
        mock_exit_code = 0

        with patch.object(instrumentor, '_execute_remote_command', return_value=(mock_output, mock_stderr, mock_exit_code)):
            with pytest.raises(NetworkSaturationError, match="Network saturation detected"):
                instrumentor.capture_tcpdump(mock_ssh_client)

    def test_capture_tcpdump_execution_failure(self, instrumentor, mock_ssh_client):
        mock_output = ""
        mock_stderr = "tcpdump: interface eth0 not found"
        mock_exit_code = 2

        with patch.object(instrumentor, '_execute_remote_command', return_value=(mock_output, mock_stderr, mock_exit_code)):
            with pytest.raises(RemoteExecutionError, match="tcpdump failed"):
                instrumentor.capture_tcpdump(mock_ssh_client)

    def test_capture_mpstat_success(self, instrumentor, mock_ssh_client):
        mock_output = """
        Linux 5.15.0-76-generic (test-node)  06/15/2024  _x86_64_  (8 CPU)

        12:00:00 PM  CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
        12:00:01 PM  all    5.00    0.00    1.00    0.50    0.00    0.00    0.00    0.00    0.00   93.50
        12:00:02 PM  all    6.00    0.00    1.20    0.60    0.00    0.00    0.00    0.00    0.00   92.20
        12:00:03 PM  all    5.50    0.00    1.10    0.55    0.00    0.00    0.00    0.00    0.00   92.85
        Average:     all    5.50    0.00    1.10    0.55    0.00    0.00    0.00    0.00    0.00   92.85
        """
        mock_stderr = ""
        mock_exit_code = 0

        with patch.object(instrumentor, '_execute_remote_command', return_value=(mock_output, mock_stderr, mock_exit_code)):
            cpu_stats = instrumentor.capture_mpstat(mock_ssh_client)

            # 100 - 92.85 = 7.15%
            assert abs(cpu_stats.cpu_utilization_pct - 7.15) < 0.01

    def test_capture_mpstat_no_average_line(self, instrumentor, mock_ssh_client):
        mock_output = """
        Linux 5.15.0-76-generic (test-node)  06/15/2024  _x86_64_  (8 CPU)

        12:00:00 PM  CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
        12:00:01 PM  all    5.00    0.00    1.00    0.50    0.00    0.00    0.00    0.00    0.00   93.50
        12:00:02 PM  all    6.00    0.00    1.20    0.60    0.00    0.00    0.00    0.00    0.00   92.20
        """
        mock_stderr = ""
        mock_exit_code = 0

        with patch.object(instrumentor, '_execute_remote_command', return_value=(mock_output, mock_stderr, mock_exit_code)):
            cpu_stats = instrumentor.capture_mpstat(mock_ssh_client)

            # Should fall back to last line: 100 - 92.20 = 7.80%
            assert abs(cpu_stats.cpu_utilization_pct - 7.80) < 0.01

    def test_capture_mpstat_execution_failure(self, instrumentor, mock_ssh_client):
        mock_output = ""
        mock_stderr = "mpstat: command not found"
        mock_exit_code = 127

        with patch.object(instrumentor, '_execute_remote_command', return_value=(mock_output, mock_stderr, mock_exit_code)):
            with pytest.raises(RemoteExecutionError, match="mpstat failed"):
                instrumentor.capture_mpstat(mock_ssh_client)

    def test_instrument_node_success(self, instrumentor, mock_ssh_client, test_node):
        mock_tcpdump_output = """
        12:00:00.000000 IP 192.168.1.1.22 > 192.168.1.100.54321: Flags [S]
        100 packets captured
        0 packets dropped by kernel
        """
        mock_mpstat_output = """
        Linux 5.15.0-76-generic (test-node)  06/15/2024  _x86_64_  (8 CPU)

        12:00:00 PM  CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
        12:00:01 PM  all    5.00    0.00    1.00    0.50    0.00    0.00    0.00    0.00    0.00   93.50
        Average:     all    5.00    0.00    1.00    0.50    0.00    0.00    0.00    0.00    0.00   93.50
        """

        def mock_exec_command(cmd, timeout=30):
            if "tcpdump" in cmd:
                return (Mock(read=Mock(return_value=mock_tcpdump_output.encode())),
                        Mock(read=Mock(return_value=b"")),
                        Mock(recv_exit_status=Mock(return_value=0)))
            elif "mpstat" in cmd:
                return (Mock(read=Mock(return_value=mock_mpstat_output.encode())),
                        Mock(read=Mock(return_value=b"")),
                        Mock(recv_exit_status=Mock(return_value=0)))

        mock_ssh_client.exec_command = Mock(side_effect=mock_exec_command)
        instrumentor.node_manager.get_ssh_client.return_value = mock_ssh_client

        result = instrumentor.instrument_node(test_node)

        assert result["node_id"] == test_node.id
        assert result["ip_address"] == test_node.ip_address
        assert result["packet_stats"]["packet_count"] == 100
        assert result["cpu_stats"]["cpu_utilization_pct"] == 6.5  # 100 - 93.5

    def test_instrument_node_unavailable(self, instrumentor, test_node):
        test_node.status = NodeStatus.UNAVAILABLE

        with pytest.raises(RemoteExecutionError, match="not available"):
            instrumentor.instrument_node(test_node)

    def test_create_instrumentor_factory(self, mock_node_manager):
        instrumentor = create_instrumentor(mock_node_manager, packet_count=500)
        assert isinstance(instrumentor, RemoteInstrumentor)
        assert instrumentor.packet_count == 500
        assert instrumentor.node_manager == mock_node_manager
