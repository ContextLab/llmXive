import pytest
from unittest.mock import MagicMock, patch
import time

from orchestrator.network_saturation_handler import (
    NetworkSaturationHandler,
    NetworkSaturationError,
    TerminationFailedError,
    TerminationResult,
    create_handler
)
from orchestrator.instrumentor_remote import NetworkSaturationSignal


class TestNetworkSaturationHandler:
    """Unit tests for NetworkSaturationHandler."""

    @pytest.fixture
    def handler(self):
        return create_handler(ssh_timeout=1.0, max_termination_retries=2, retry_delay=0.1)

    @pytest.fixture
    def mock_signal(self):
        return NetworkSaturationSignal(
            node_id="node_1",
            packet_loss_rate=25.0,
            message="Test saturation signal"
        )

    @pytest.fixture
    def mock_active_pids(self):
        return {"node_1": 12345, "node_2": 67890}

    @pytest.fixture
    def mock_node_credentials(self):
        return {
            "node_1": {
                "hostname": "192.168.1.10",
                "username": "root",
                "password": "password123",
                "key_filename": None
            },
            "node_2": {
                "hostname": "192.168.1.11",
                "username": "root",
                "password": "password123",
                "key_filename": None
            }
        }

    def test_create_handler(self):
        handler = create_handler()
        assert isinstance(handler, NetworkSaturationHandler)
        assert handler.ssh_timeout == 10.0
        assert handler.max_termination_retries == 3
        assert handler.retry_delay == 1.0

    def test_terminate_remote_process_success(self, handler):
        """Test successful termination and verification."""
        mock_client = MagicMock()
        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()

        # Mock kill command success
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        # Mock ps check (process not found)
        mock_ps_stdout = MagicMock()
        mock_ps_stdout.channel.recv_exit_status.return_value = 1 # Process not found
        mock_ps_stdout.read.return_value = b""
        mock_client.exec_command.side_effect = [
            (mock_stdin, mock_stdout, mock_stderr), # kill
            (mock_stdin, mock_ps_stdout, mock_stderr) # ps
        ]

        with patch.object(handler, '_create_ssh_client', return_value=mock_client):
            result = handler.terminate_remote_process(
                node_id="node_1",
                hostname="192.168.1.10",
                pid=12345,
                username="root",
                password="pass"
            )

        assert result.success is True
        assert result.message == "Process terminated and verified."
        assert result.node_id == "node_1"
        assert result.pid == 12345
        assert result.attempts_made == 1

    def test_terminate_remote_process_failure(self, handler):
        """Test termination failure after retries."""
        mock_client = MagicMock()
        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()

        # Mock kill command success
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        # Mock ps check (process still found)
        mock_ps_stdout = MagicMock()
        mock_ps_stdout.channel.recv_exit_status.return_value = 0 # Process found
        mock_ps_stdout.read.return_value = b"12345 pts/0 00:00:00 bash"
        mock_client.exec_command.side_effect = [
            (mock_stdin, mock_stdout, mock_stderr), # kill
            (mock_stdin, mock_ps_stdout, mock_stderr) # ps
        ] * 3 # Repeat for retries

        with patch.object(handler, '_create_ssh_client', return_value=mock_client):
            result = handler.terminate_remote_process(
                node_id="node_1",
                hostname="192.168.1.10",
                pid=12345,
                username="root",
                password="pass"
            )

        assert result.success is False
        assert "Failed to terminate" in result.message
        assert result.attempts_made == 2 # max_termination_retries is 2

    def test_handle_saturation_signal_success(self, handler, mock_signal, mock_active_pids, mock_node_credentials):
        """Test successful handling of saturation signal."""
        mock_result = TerminationResult(
            success=True,
            message="Process terminated and verified.",
            node_id="node_1",
            pid=12345,
            attempts_made=1
        )

        with patch.object(handler, 'terminate_remote_process', return_value=mock_result):
            with pytest.raises(NetworkSaturationError) as exc_info:
                handler.handle_saturation_signal(mock_signal, mock_active_pids, mock_node_credentials)

            assert "Network saturation detected" in str(exc_info.value)
            assert exc_info.value.signal == mock_signal

    def test_handle_saturation_signal_termination_failure(self, handler, mock_signal, mock_active_pids, mock_node_credentials):
        """Test handling when termination fails."""
        mock_result = TerminationResult(
            success=False,
            message="Failed to terminate process",
            node_id="node_1",
            pid=12345,
            attempts_made=2
        )

        with patch.object(handler, 'terminate_remote_process', return_value=mock_result):
            with pytest.raises(TerminationFailedError) as exc_info:
                handler.handle_saturation_signal(mock_signal, mock_active_pids, mock_node_credentials)

            assert "One or more remote processes failed to terminate" in str(exc_info.value)

    def test_handle_saturation_signal_missing_credentials(self, handler, mock_signal, mock_active_pids):
        """Test handling when credentials are missing for a node."""
        incomplete_credentials = {
            "node_1": {
                "hostname": "192.168.1.10",
                "username": "root",
                "password": "password123",
                "key_filename": None
            }
            # node_2 credentials missing
        }

        with pytest.raises(TerminationFailedError) as exc_info:
            handler.handle_saturation_signal(mock_signal, mock_active_pids, incomplete_credentials)

        assert "One or more remote processes failed to terminate" in str(exc_info.value)
        # Note: The current implementation logs an error and sets all_success=False,
        # which leads to TerminationFailedError being raised before NetworkSaturationError.
        # This aligns with the spec: "If termination fails, log an ERROR and raise TerminationFailedError".
        # However, the spec also says "Raise NetworkSaturationError" to signal abort.
        # The current logic raises TerminationFailedError if ANY termination fails.
        # If we want to raise NetworkSaturationError even if some terminate, we'd need to adjust logic.
        # Based on strict reading: "If termination fails... raise TerminationFailedError".
        # Then "Raise NetworkSaturationError" implies after successful termination.
        # So this test is correct: if termination fails, TerminationFailedError is raised.