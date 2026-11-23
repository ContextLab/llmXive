"""
Unit tests for instrumentor_remote.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from orchestrator.instrumentor_remote import (
    RemoteInstrumentor,
    PacketStats,
    CPUStats,
    UnmodeledVars,
    NodeMetrics,
    RemoteExecutionError,
    NetworkSaturationError,
    create_instrumentor
)
from orchestrator.remote_tools_manager import RemoteToolManager

@pytest.fixture
def mock_tool_manager():
    manager = Mock(spec=RemoteToolManager)
    manager.check_tool = Mock(return_value=True)
    return manager

@pytest.fixture
def instrumentor(mock_tool_manager):
    return RemoteInstrumentor(mock_tool_manager)

@pytest.fixture
def mock_ssh_client():
    client = MagicMock()
    return client

def test_tcpdump_parsing(instrumentor, mock_ssh_client):
    """Test tcpdump output parsing with standard format."""
    mock_output = """10:23:45.123456 IP 192.168.1.1.80 > 192.168.1.10.54321: Flags [S], seq 1234567890, win 65535, options [mss 1460], length 0
    10:23:45.123789 IP 192.168.1.10.54321 > 192.168.1.1.80: Flags [S.], seq 987654321, ack 1234567891, win 65535, options [mss 1460], length 0
    10:23:45.124012 IP 192.168.1.1.80 > 192.168.1.10.54321: Flags [.], ack 1, win 65535, length 0
    """
    mock_ssh_client.exec_command.return_value = (
        Mock(read=Mock(return_value=mock_output.encode())),
        Mock(read=Mock(return_value=b"")),
        Mock(recv_exit_status=Mock(return_value=0))
    )
    mock_ssh_client.exec_command.return_value[0].channel.recv_exit_status = Mock(return_value=0)

    with patch.object(instrumentor, '_execute_ssh_command', return_value=(mock_output, "", 0)):
        result = instrumentor.run_tcpdump(mock_ssh_client, packet_count=100)

    assert result.packet_count == 3
    assert result.interface == "any"
    assert result.duration_seconds > 0

def test_tcpdump_parsing_with_warnings(instrumentor, mock_ssh_client):
    """Test tcpdump output with warning lines."""
    mock_output = """tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    10:23:45.123456 IP 192.168.1.1.80 > 192.168.1.10.54321: Flags [S], seq 1234567890, win 65535, length 0
    10:23:45.123789 IP 192.168.1.10.54321 > 192.168.1.1.80: Flags [S.], seq 987654321, ack 1234567891, win 65535, length 0
    """
    with patch.object(instrumentor, '_execute_ssh_command', return_value=(mock_output, "", 0)):
        result = instrumentor.run_tcpdump(mock_ssh_client, packet_count=100)

    # Should skip the tcpdump: line
    assert result.packet_count == 2

def test_tcpdump_empty_output(instrumentor, mock_ssh_client):
    """Test tcpdump with empty output."""
    with patch.object(instrumentor, '_execute_ssh_command', return_value=("", "", 0)):
        result = instrumentor.run_tcpdump(mock_ssh_client, packet_count=100)

    assert result.packet_count == 0

def test_mpstat_parsing_average_line(instrumentor, mock_ssh_client):
    """Test mpstat parsing with Average line."""
    mock_output = """Linux 5.4.0-42-generic (node1)       10/23/2023      _x86_64_        (4)

    10:23:45     CPU     %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
    10:23:46     all     1.20    0.00    1.50    0.10    0.00    0.00    0.00    0.00    0.00   97.20
    10:23:47     all     2.10    0.00    2.30    0.20    0.00    0.00    0.00    0.00    0.00   95.40
    Average:     all     1.65    0.00    1.90    0.15    0.00    0.00    0.00    0.00    0.00   96.30
    """
    with patch.object(instrumentor, '_execute_ssh_command', return_value=(mock_output, "", 0)):
        result = instrumentor.run_mpstat(mock_ssh_client)

    assert abs(result.cpu_utilization_pct - 3.55) < 0.01  # 1.65 + 1.90
    assert abs(result.user_pct - 1.65) < 0.01
    assert abs(result.system_pct - 1.90) < 0.01
    assert abs(result.idle_pct - 96.30) < 0.01

def test_mpstat_parsing_last_line(instrumentor, mock_ssh_client):
    """Test mpstat parsing when no Average line exists."""
    mock_output = """Linux 5.4.0-42-generic (node1)       10/23/2023      _x86_64_        (4)

    10:23:45     CPU     %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
    10:23:46     all     5.00    0.00    3.00    0.10    0.00    0.00    0.00    0.00    0.00   91.90
    10:23:47     all     6.00    0.00    4.00    0.20    0.00    0.00    0.00    0.00    0.00   89.80
    """
    with patch.object(instrumentor, '_execute_ssh_command', return_value=(mock_output, "", 0)):
        result = instrumentor.run_mpstat(mock_ssh_client)

    # Should use the last data line
    assert abs(result.cpu_utilization_pct - 10.0) < 0.01  # 6.00 + 4.00
    assert abs(result.user_pct - 6.00) < 0.01
    assert abs(result.system_pct - 4.00) < 0.01

def test_mpstat_invalid_output(instrumentor, mock_ssh_client):
    """Test mpstat with invalid/missing data."""
    mock_output = """Linux 5.4.0-42-generic (node1)
    """
    with patch.object(instrumentor, '_execute_ssh_command', return_value=(mock_output, "", 0)):
        result = instrumentor.run_mpstat(mock_ssh_client)

    assert result.cpu_utilization_pct == 0.0
    assert result.idle_pct == 100.0

def test_check_network_saturation(instrumentor):
    """Test network saturation detection."""
    assert instrumentor.check_network_saturation(0.15) is False
    assert instrumentor.check_network_saturation(0.20) is False
    assert instrumentor.check_network_saturation(0.21) is True
    assert instrumentor.check_network_saturation(0.50) is True

def test_capture_unmodeled_vars(instrumentor, mock_ssh_client):
    """Test capture of unmodeled variables."""
    thermal_output = "45000"
    loadavg_output = "0.50 0.45 0.40 2/150 12345"

    def mock_exec(cmd, *args, **kwargs):
        if "thermal_zone0/temp" in cmd:
            return thermal_output, "", 0
        elif "loadavg" in cmd:
            return loadavg_output, "", 0
        return "", "", 1

    with patch.object(instrumentor, '_execute_ssh_command', side_effect=mock_exec):
        result = instrumentor.capture_unmodeled_vars(mock_ssh_client)

    assert result.thermal_zone == 45.0
    assert result.loadavg_1m == 0.50
    assert result.loadavg_5m == 0.45
    assert result.loadavg_15m == 0.40
    assert len(result.warnings) == 0

def test_capture_unmodeled_vars_missing(instrumentor, mock_ssh_client):
    """Test capture of unmodeled variables when data is missing."""
    def mock_exec(cmd, *args, **kwargs):
        return "N/A", "", 0

    with patch.object(instrumentor, '_execute_ssh_command', side_effect=mock_exec):
        result = instrumentor.capture_unmodeled_vars(mock_ssh_client)

    assert result.thermal_zone is None
    assert result.loadavg_1m is None
    assert len(result.warnings) > 0

def test_instrument_node_success(instrumentor, mock_ssh_client):
    """Test full node instrumentation success."""
    with patch.object(instrumentor, 'capture_unmodeled_vars', return_value=UnmodeledVars()):
        with patch.object(instrumentor, 'run_tcpdump', return_value=PacketStats(100, "any", 1.0)):
            with patch.object(instrumentor, 'run_mpstat', return_value=CPUStats(50.0, 30.0, 20.0, 50.0, 5.0)):
                result = instrumentor.instrument_node(mock_ssh_client, "node1")

    assert result.node_id == "node1"
    assert result.instrumentation_status == "complete"
    assert result.packet_stats.packet_count == 100
    assert result.cpu_stats.cpu_utilization_pct == 50.0
    assert result.wall_clock_time > 0

def test_instrument_node_partial(instrumentor, mock_ssh_client):
    """Test node instrumentation with missing tools."""
    with patch.object(instrumentor, 'capture_unmodeled_vars', return_value=UnmodeledVars()):
        with patch.object(instrumentor, 'run_tcpdump', side_effect=Exception("tcpdump missing")):
            with patch.object(instrumentor, 'run_mpstat', return_value=CPUStats(50.0, 30.0, 20.0, 50.0, 5.0)):
                result = instrumentor.instrument_node(mock_ssh_client, "node1")

    assert result.instrumentation_status == "partial"
    assert result.packet_stats is None
    assert result.cpu_stats is not None

def test_create_instrumentor():
    """Test factory function."""
    with patch('orchestrator.instrumentor_remote.RemoteToolManager'):
        inst = create_instrumentor()
        assert isinstance(inst, RemoteInstrumentor)