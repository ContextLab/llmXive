"""
Unit tests for RemoteWallClockTimer.

These tests verify the logic of the wall-clock timer module,
including session management, error handling, and result parsing.
Note: Actual SSH execution tests require a running SSH server.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timezone
import socket
import paramiko

from orchestrator.remote_wall_clock_timer import (
    RemoteWallClockTimer,
    WallClockResult,
    RemoteTimerSession,
    RemoteTimerStartError,
    RemoteTimerStopError,
    RemoteTimerReadError,
    create_remote_wall_clock_timer
)


class TestRemoteWallClockTimer:
    """Test suite for RemoteWallClockTimer class."""

    @pytest.fixture
    def timer(self):
        return create_remote_wall_clock_timer(timeout=5.0)

    def test_init(self, timer):
        assert timer.timeout == 5.0
        assert timer.sessions == {}

    @patch('paramiko.SSHClient')
    def test_start_timer_success(self, mock_ssh_class, timer):
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client
        
        mock_channel = MagicMock()
        mock_client.exec_command.return_value = (MagicMock(), MagicMock(), MagicMock())
        mock_client.exec_command.return_value[1].channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value[1].read.return_value = b"1678886400.123456789"

        result = timer.start_timer("192.168.1.10")

        assert result.success is True
        assert result.node_ip == "192.168.1.10"
        assert result.duration_seconds == 0.0
        assert "192.168.1.10" in timer.sessions
        assert timer.sessions["192.168.1.10"].is_active is True
        mock_client.connect.assert_called_once()

    @patch('paramiko.SSHClient')
    def test_start_timer_connection_failure(self, mock_ssh_class, timer):
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client
        mock_client.connect.side_effect = socket.timeout("Connection timed out")

        result = timer.start_timer("192.168.1.10")

        assert result.success is False
        assert "Connection timed out" in result.error_message
        assert "192.168.1.10" not in timer.sessions

    @patch('paramiko.SSHClient')
    def test_start_timer_invalid_timestamp(self, mock_ssh_class, timer):
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client
        
        mock_channel = MagicMock()
        mock_client.exec_command.return_value = (MagicMock(), MagicMock(), MagicMock())
        mock_client.exec_command.return_value[1].channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value[1].read.return_value = b"invalid_timestamp"

        with pytest.raises(RemoteTimerReadError):
            timer.start_timer("192.168.1.10")

    @patch('paramiko.SSHClient')
    def test_stop_timer_success(self, mock_ssh_class, timer):
        # Setup start
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client
        
        # Start mock
        mock_channel_start = MagicMock()
        mock_client.exec_command.return_value = (MagicMock(), MagicMock(), MagicMock())
        mock_client.exec_command.return_value[1].channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value[1].read.return_value = b"1678886400.0"

        timer.start_timer("192.168.1.10")

        # Stop mock
        mock_client.exec_command.return_value[1].read.return_value = b"1678886410.0"

        result = timer.stop_timer("192.168.1.10")

        assert result.success is True
        assert result.duration_seconds == 10.0
        assert timer.sessions["192.168.1.10"].is_active is False

    def test_stop_timer_no_session(self, timer):
        with pytest.raises(RemoteTimerStopError) as exc_info:
            timer.stop_timer("192.168.1.10")
        assert "No active session found" in str(exc_info.value)

    def test_stop_timer_not_active(self, timer):
        # Create a session manually but mark as inactive
        session = RemoteTimerSession(node_ip="192.168.1.10", is_active=False)
        timer.sessions["192.168.1.10"] = session

        with pytest.raises(RemoteTimerStopError) as exc_info:
            timer.stop_timer("192.168.1.10")
        assert "is not active" in str(exc_info.value)

    def test_get_result_success(self, timer):
        session = RemoteTimerSession(
            node_ip="192.168.1.10",
            start_time=datetime.fromtimestamp(1678886400, tz=timezone.utc),
            end_time=datetime.fromtimestamp(1678886410, tz=timezone.utc),
            duration_seconds=10.0,
            is_active=False
        )
        timer.sessions["192.168.1.10"] = session

        result = timer.get_result("192.168.1.10")

        assert result.success is True
        assert result.duration_seconds == 10.0

    def test_get_result_no_session(self, timer):
        with pytest.raises(RemoteTimerReadError) as exc_info:
            timer.get_result("192.168.1.10")
        assert "No session found" in str(exc_info.value)

    def test_get_result_still_active(self, timer):
        session = RemoteTimerSession(
            node_ip="192.168.1.10",
            start_time=datetime.now(timezone.utc),
            is_active=True
        )
        timer.sessions["192.168.1.10"] = session

        with pytest.raises(RemoteTimerReadError) as exc_info:
            timer.get_result("192.168.1.10")
        assert "still active" in str(exc_info.value)

    def test_close_all(self, timer):
        mock_client = MagicMock()
        session = RemoteTimerSession(node_ip="192.168.1.10", ssh_client=mock_client)
        timer.sessions["192.168.1.10"] = session

        timer.close_all()

        mock_client.close.assert_called_once()
        assert timer.sessions == {}

    def test_wall_clock_result_to_dict(self):
        result = WallClockResult(
            node_ip="192.168.1.10",
            start_time=datetime.fromtimestamp(1678886400, tz=timezone.utc),
            end_time=datetime.fromtimestamp(1678886410, tz=timezone.utc),
            duration_seconds=10.0,
            success=True
        )

        data = result.to_dict()

        assert data["node_ip"] == "192.168.1.10"
        assert data["duration_seconds"] == 10.0
        assert data["success"] is True
        assert "start_time" in data
        assert "end_time" in data