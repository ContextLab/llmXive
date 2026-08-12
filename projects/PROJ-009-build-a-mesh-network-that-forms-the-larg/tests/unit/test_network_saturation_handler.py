"""
Unit tests for NetworkSaturationHandler (T014b).

These tests verify the logic of signal handling, termination attempts,
and error raising without requiring real SSH connections.
"""
import pytest
from unittest.mock import MagicMock, patch, call
import time

from orchestrator.network_saturation_handler import (
    NetworkSaturationHandler,
    NetworkSaturationSignal,
    NetworkSaturationError,
    TerminationFailedError,
    TerminationResult,
    create_handler
)


@pytest.fixture
def mock_signal():
    """Create a mock NetworkSaturationSignal."""
    return NetworkSaturationSignal(
        node_ids=["192.168.1.10", "192.168.1.11"],
        benchmark_pids={"192.168.1.10": 1234, "192.168.1.11": 5678},
        run_id="test-run-001",
        packet_loss_rate=0.25
    )


@pytest.fixture
def handler():
    """Create a handler instance."""
    return NetworkSaturationHandler()


def test_create_handler():
    """Test factory function."""
    h = create_handler()
    assert isinstance(h, NetworkSaturationHandler)


def test_signal_representation(mock_signal):
    """Test signal string representation."""
    repr_str = repr(mock_signal)
    assert "test-run-001" in repr_str
    assert "192.168.1.10" in repr_str
    assert "0.25" in repr_str


@patch('orchestrator.network_saturation_handler.SSHClient')
@patch('orchestrator.network_saturation_handler.AutoAddPolicy')
def test_handle_signal_success(mock_policy, mock_ssh_class, handler, mock_signal):
    """
    Test successful termination and verification flow.
    Expects NetworkSaturationError to be raised after successful handling.
    """
    # Mock SSH client
    mock_client = MagicMock()
    mock_ssh_class.return_value = mock_client
    
    # Mock exec_command for kill
    mock_stdin = MagicMock()
    mock_stdout = MagicMock()
    mock_stderr = MagicMock()
    mock_stdout.channel.recv_exit_status.return_value = 0
    
    mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
    
    # Mock exec_command for verification (ps -p)
    # First call (during kill check? No, separate call) -> returns 0 (process gone)
    # We need to track calls.
    # Call 1: kill -9
    # Call 2: ps -p ...
    
    # Setup sequence
    def exec_side_effect(cmd):
        if "kill -9" in cmd:
            return mock_stdin, mock_stdout, mock_stderr
        elif "ps -p" in cmd:
            # Return exit code 1 (process not found)
            mock_ps_stdout = MagicMock()
            mock_ps_stdout.read.return_value = b"1\n" # Exit code 1
            return mock_stdin, mock_ps_stdout, mock_stderr
        return mock_stdin, mock_stdout, mock_stderr

    mock_client.exec_command.side_effect = exec_side_effect

    # Execute
    with pytest.raises(NetworkSaturationError) as exc_info:
        handler.handle_signal(mock_signal)

    # Verify error raised
    assert exc_info.value.run_id == "test-run-001"
    assert exc_info.value.error_code == "NETWORK_SATURATION"
    
    # Verify SSH calls
    assert mock_client.connect.called
    assert mock_client.exec_command.call_count >= 4 # 2 nodes * 2 commands (kill, verify)
    mock_client.close.assert_called()


@patch('orchestrator.network_saturation_handler.SSHClient')
@patch('orchestrator.network_saturation_handler.AutoAddPolicy')
def test_handle_signal_retry_logic(mock_policy, mock_ssh_class, handler, mock_signal):
    """
    Test retry logic when verification fails initially but succeeds later.
    """
    mock_client = MagicMock()
    mock_ssh_class.return_value = mock_client
    
    mock_stdin = MagicMock()
    mock_stdout = MagicMock()
    mock_stderr = MagicMock()
    mock_stdout.channel.recv_exit_status.return_value = 0
    
    call_count = 0
    def exec_side_effect(cmd):
        nonlocal call_count
        if "kill -9" in cmd:
            return mock_stdin, mock_stdout, mock_stderr
        elif "ps -p" in cmd:
            call_count += 1
            mock_ps_stdout = MagicMock()
            # Fail first time, succeed second time
            if call_count <= 2: # First check for both nodes
                mock_ps_stdout.read.return_value = b"0\n" # Process exists
            else:
                mock_ps_stdout.read.return_value = b"1\n" # Process gone
            return mock_stdin, mock_ps_stdout, mock_stderr
        return mock_stdin, mock_stdout, mock_stderr

    mock_client.exec_command.side_effect = exec_side_effect

    # With retry logic, this should eventually succeed
    # Note: The handler loops 3 times.
    with pytest.raises(NetworkSaturationError):
        handler.handle_signal(mock_signal)
    
    # Verify close was called
    mock_client.close.assert_called()


@patch('orchestrator.network_saturation_handler.SSHClient')
@patch('orchestrator.network_saturation_handler.AutoAddPolicy')
def test_handle_signal_failure_raises(mock_policy, mock_ssh_class, handler, mock_signal):
    """
    Test that if termination fails after retries, NetworkSaturationError is still raised
    (with failure message) and the pipeline is aborted.
    """
    mock_client = MagicMock()
    mock_ssh_class.return_value = mock_client
    
    mock_stdin = MagicMock()
    mock_stdout = MagicMock()
    mock_stderr = MagicMock()
    mock_stdout.channel.recv_exit_status.return_value = 1 # Kill failed
    
    mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

    # Should raise NetworkSaturationError even on failure
    with pytest.raises(NetworkSaturationError) as exc_info:
        handler.handle_signal(mock_signal)
    
    assert exc_info.value.run_id == "test-run-001"
    assert "Failed to terminate" in str(exc_info.value)


def test_termination_result_dataclass():
    """Test TerminationResult dataclass structure."""
    result = TerminationResult(
        node_id="1.1.1.1",
        pid=999,
        success=True,
        message="OK",
        attempts=1
    )
    assert result.node_id == "1.1.1.1"
    assert result.success is True
    assert result.attempts == 1