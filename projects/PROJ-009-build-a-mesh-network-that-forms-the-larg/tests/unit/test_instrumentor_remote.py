import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from io import StringIO

from orchestrator.instrumentor_remote import (
    RemoteInstrumentor, 
    create_instrumentor,
    RemoteExecutionError,
    NetworkSaturationError,
    PacketStats,
    CPUStats
)
from orchestrator.models import PhysicalNode, NodeStatus
from orchestrator.node_manager import NodeManager
from orchestrator.remote_tool_manager import RemoteToolManager
from orchestrator.remote_wall_clock_timer import RemoteWallClockTimer

class TestRemoteInstrumentor:
    @pytest.fixture
    def mock_node_manager(self):
        manager = Mock(spec=NodeManager)
        manager._get_ssh_client = Mock(return_value=MagicMock())
        return manager

    @pytest.fixture
    def mock_tool_manager(self):
        manager = Mock(spec=RemoteToolManager)
        manager.check_node_tools = Mock(return_value=MagicMock(all_available=True, missing=[]))
        return manager

    @pytest.fixture
    def mock_wall_clock_timer(self):
        timer = Mock(spec=RemoteWallClockTimer)
        timer.start_timer = Mock()
        timer.stop_timer = Mock()
        return timer

    @pytest.fixture
    def instrumentor(self, mock_node_manager, mock_tool_manager, mock_wall_clock_timer):
        return create_instrumentor(mock_node_manager, mock_tool_manager, mock_wall_clock_timer)

    def test_execute_tcpdump_success(self, instrumentor):
        mock_client = instrumentor.node_manager._get_ssh_client("192.168.1.1")
        mock_client.exec_command = Mock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_stdout.read.return_value = b"1000 packets captured\n"
        mock_stderr.read.return_value = b""
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        stats = instrumentor.execute_tcpdump(mock_client, packet_count=1000)
        
        assert stats.total_packets == 1000
        assert stats.lost_packets == 0
        assert stats.loss_rate == 0.0

    def test_execute_tcpdump_loss_detected(self, instrumentor):
        mock_client = instrumentor.node_manager._get_ssh_client("192.168.1.1")
        mock_client.exec_command = Mock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_stdout.read.return_value = b"800 packets captured\n"
        mock_stderr.read.return_value = b""
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        stats = instrumentor.execute_tcpdump(mock_client, packet_count=1000)
        
        assert stats.total_packets == 800
        assert stats.lost_packets == 200
        assert stats.loss_rate == 0.20

    def test_check_network_saturation_below_threshold(self, instrumentor):
        stats = PacketStats(total_packets=800, packets_per_second=800, lost_packets=200, loss_rate=0.20)
        assert instrumentor.check_network_saturation(stats, threshold=0.25) is False

    def test_check_network_saturation_above_threshold(self, instrumentor):
        stats = PacketStats(total_packets=700, packets_per_second=700, lost_packets=300, loss_rate=0.30)
        assert instrumentor.check_network_saturation(stats, threshold=0.20) is True

    def test_check_network_saturation_exactly_threshold(self, instrumentor):
        stats = PacketStats(total_packets=800, packets_per_second=800, lost_packets=200, loss_rate=0.20)
        assert instrumentor.check_network_saturation(stats, threshold=0.20) is False
        assert instrumentor.check_network_saturation(stats, threshold=0.19) is True

    def test_execute_mpstat_success(self, instrumentor):
        mock_client = instrumentor.node_manager._get_ssh_client("192.168.1.1")
        mock_client.exec_command = Mock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        # Simulate mpstat output
        output = """
        Linux 5.4.0-42-generic (node1) 	09/25/2023 	_x86_64_	(4 CPU)
        
        10:00:00 AM     CPU     %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
        10:00:01 AM     all    10.00    0.00    5.00    1.00    0.00    0.00    0.00    0.00    0.00   84.00
        Average:        all    10.00    0.00    5.00    1.00    0.00    0.00    0.00    0.00    0.00   84.00
        """
        mock_stdout.read.return_value = output.encode('utf-8')
        mock_stderr.read.return_value = b""
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        stats = instrumentor.execute_mpstat(mock_client)
        
        assert stats.cpu_utilization_pct == 16.0
        assert stats.idle_pct == 84.0

    def test_remote_execution_error_on_timeout(self, instrumentor):
        mock_client = instrumentor.node_manager._get_ssh_client("192.168.1.1")
        mock_client.exec_command = Mock(side_effect=Exception("SocketTimeout"))
        
        with pytest.raises(RemoteExecutionError):
            instrumentor.execute_tcpdump(mock_client)

    def test_network_saturation_error_raised(self, instrumentor):
        mock_client = instrumentor.node_manager._get_ssh_client("192.168.1.1")
        mock_client.exec_command = Mock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_stdout.read.return_value = b"600 packets captured\n"
        mock_stderr.read.return_value = b""
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)
        
        # Simulate saturation check in instrument_node
        with patch.object(instrumentor, 'check_network_saturation', return_value=True):
            with pytest.raises(NetworkSaturationError):
                instrumentor.instrument_node("192.168.1.1")