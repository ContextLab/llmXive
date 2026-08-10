"""
Unit tests for network_saturation_handler.py
"""
import pytest
from unittest.mock import MagicMock, patch, mock_open
from orchestrator.network_saturation_handler import (
    NetworkSaturationHandler,
    NetworkSaturationSignal,
    TerminationFailedError,
    create_saturation_handler
)
from orchestrator.models import PhysicalNode

@pytest.fixture
def mock_node_manager():
    manager = MagicMock()
    node = PhysicalNode(
        id="node-1",
        ip="192.168.1.10",
        username="user",
        ssh_key_path="/fake/key",
        status="online"
    )
    manager.get_node_by_id.return_value = node
    return manager

@pytest.fixture
def saturation_handler(mock_node_manager):
    return create_saturation_handler(mock_node_manager)

@pytest.fixture
def sample_signal():
    return NetworkSaturationSignal(
        run_id="run-123",
        node_ids=["node-1", "node-2"],
        benchmark_pids={"node-1": 12345, "node-2": 12346},
        timestamp=1234567890.0,
        packet_loss_rate=25.5
    )

def test_handler_creation(mock_node_manager):
    handler = create_saturation_handler(mock_node_manager)
    assert isinstance(handler, NetworkSaturationHandler)
    assert handler.node_manager == mock_node_manager

@patch('paramiko.SSHClient')
def test_handle_saturation_signal_success(mock_ssh_class, saturation_handler, sample_signal):
    # Mock SSH client
    mock_client = MagicMock()
    mock_ssh_class.return_value = mock_client
    
    # Mock successful kill (exit status 0)
    mock_channel = MagicMock()
    mock_channel.recv_exit_status.return_value = 0
    mock_client.exec_command.return_value = (MagicMock(), mock_channel, MagicMock())
    
    # Mock ps check to return non-zero (process gone)
    mock_channel_kill = MagicMock()
    mock_channel_kill.recv_exit_status.return_value = 1 # ps -p <pid> returns 1 if not found
    mock_client.exec_command.return_value = (MagicMock(), mock_channel_kill, MagicMock())

    result = saturation_handler.handle_saturation_signal(sample_signal)
    
    assert result["status"] == "success"
    assert "node-1" in result["terminated_nodes"]
    assert "node-2" in result["terminated_nodes"]
    assert len(result["failed_nodes"]) == 0

@patch('paramiko.SSHClient')
def test_handle_saturation_signal_partial_failure(mock_ssh_class, saturation_handler, sample_signal):
    # Mock SSH client
    mock_client = MagicMock()
    mock_ssh_class.return_value = mock_client
    
    # First call: success
    mock_channel = MagicMock()
    mock_channel.recv_exit_status.return_value = 1 # ps -p returns 1 (not found)
    mock_client.exec_command.return_value = (MagicMock(), mock_channel, MagicMock())
    
    # Second call: simulate failure
    mock_client.exec_command.side_effect = [
        (MagicMock(), mock_channel, MagicMock()), # First node success
        Exception("Connection lost"), # Second node failure
    ]

    result = saturation_handler.handle_saturation_signal(sample_signal)
    
    assert result["status"] == "partial_failure"
    assert "node-1" in result["terminated_nodes"]
    assert "node-2" in result["failed_nodes"]
    assert len(result["error_details"]) > 0

@patch('paramiko.SSHClient')
def test_handle_saturation_signal_termination_failed(mock_ssh_class, saturation_handler, sample_signal):
    # Mock SSH client
    mock_client = MagicMock()
    mock_ssh_class.return_value = mock_client
    
    # Mock kill success but ps check returns 0 (process still there)
    mock_channel_kill = MagicMock()
    mock_channel_kill.recv_exit_status.return_value = 1 # kill success
    
    mock_channel_ps = MagicMock()
    mock_channel_ps.recv_exit_status.return_value = 0 # ps finds process
    
    mock_client.exec_command.side_effect = [
        (MagicMock(), mock_channel_kill, MagicMock()), # Kill command
        (MagicMock(), mock_channel_ps, MagicMock()),   # Check command (found)
        (MagicMock(), mock_channel_kill, MagicMock()), # Kill command retry
        (MagicMock(), mock_channel_ps, MagicMock()),   # Check command retry
        (MagicMock(), mock_channel_kill, MagicMock()), # Kill command retry
        (MagicMock(), mock_channel_ps, MagicMock()),   # Check command retry
    ]

    # Max retries is 3, so it should fail
    with pytest.raises(TerminationFailedError):
        saturation_handler.handle_saturation_signal(sample_signal)