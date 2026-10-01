import pytest
import json
import os
import tempfile
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from orchestrator.network_saturation_handler import (
    NetworkSaturationHandler,
    TerminationFailedError,
    NetworkSaturationSignal,
    create_handler,
    TerminationResult
)


class TestNetworkSaturationHandler:

    @pytest.fixture
    def handler(self):
        with patch('orchestrator.network_saturation_handler.get_config') as mock_config:
            mock_config.return_value = {
                "data_paths": {"raw": tempfile.mkdtemp()}
            }
            return create_handler()

    def test_terminate_remote_process_success(self, handler):
        """Test successful termination and verification."""
        mock_ssh = MagicMock()
        
        # Mock kill command success
        mock_ssh.exec_command.return_value = (MagicMock(), MagicMock(), MagicMock())
        mock_ssh.exec_command.return_value[0].channel.recv_exit_status.return_value = 0
        
        # Mock verify command failure (process gone)
        mock_ssh.exec_command.return_value[1].channel.recv_exit_status.return_value = 1

        result = handler.terminate_remote_process("node_1", 12345, mock_ssh)
        
        assert result.success is True
        assert result.node_id == "node_1"
        assert result.pid == 12345
        assert "successfully" in result.message

    def test_terminate_remote_process_failure(self, handler):
        """Test failure to terminate after retries."""
        mock_ssh = MagicMock()
        
        # Mock kill command success
        mock_ssh.exec_command.return_value = (MagicMock(), MagicMock(), MagicMock())
        mock_ssh.exec_command.return_value[0].channel.recv_exit_status.return_value = 0
        
        # Mock verify command success (process still there) for all retries
        mock_ssh.exec_command.return_value[1].channel.recv_exit_status.return_value = 0

        with patch.object(handler, 'max_retries', 1):
            with patch.object(handler, 'retry_delay', 0.01):
                result = handler.terminate_remote_process("node_1", 12345, mock_ssh)
                
        assert result.success is False
        assert "Failed to terminate" in result.message

    def test_handle_saturation_event_logs_failure(self, handler):
        """Test that handle_saturation_event logs to validation_status.json."""
        mock_ssh = MagicMock()
        mock_ssh.exec_command.return_value = (MagicMock(), MagicMock(), MagicMock())
        mock_ssh.exec_command.return_value[0].channel.recv_exit_status.return_value = 0
        mock_ssh.exec_command.return_value[1].channel.recv_exit_status.return_value = 1 # Process gone

        active_nodes = [
            {"node_id": "node_1", "ssh_client": mock_ssh}
        ]
        benchmark_pids = {"node_1": 12345}

        # The handler should raise NetworkSaturationSignal
        with pytest.raises(NetworkSaturationSignal):
            handler.handle_saturation_event(
                Exception("Saturation"),
                active_nodes,
                benchmark_pids
            )

        # Check that validation_status.json was updated
        status_file = os.path.join(handler.validation_status_path, "validation_status.json")
        assert os.path.exists(status_file)

        with open(status_file, 'r') as f:
            data = json.load(f)
        
        assert data["status"] == "excluded"
        assert any("NETWORK_SATURATION" in w for w in data.get("warnings", []))

    def test_handle_saturation_event_missing_ssh(self, handler):
        """Test that missing SSH client raises ValueError."""
        active_nodes = [
            {"node_id": "node_1", "ssh_client": None}
        ]
        benchmark_pids = {"node_1": 12345}

        with pytest.raises(ValueError, match="ssh_client is required"):
            handler.handle_saturation_event(
                Exception("Saturation"),
                active_nodes,
                benchmark_pids
            )

    def test_create_handler_factory(self):
        """Test the factory function."""
        with patch('orchestrator.network_saturation_handler.get_config') as mock_config:
            mock_config.return_value = {"data_paths": {"raw": "/tmp"}}
            h = create_handler()
            assert isinstance(h, NetworkSaturationHandler)