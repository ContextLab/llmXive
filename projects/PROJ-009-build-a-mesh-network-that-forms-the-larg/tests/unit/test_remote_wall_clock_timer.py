"""
Unit tests for RemoteWallClockTimer.

These tests verify the functionality of the wall-clock timer implementation
using mock SSH connections and node managers.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import time
import socket

from orchestrator.remote_wall_clock_timer import (
    RemoteWallClockTimer,
    RemoteTimerSession,
    WallClockResult,
    WallClockTimerError,
    RemoteTimerStartError,
    RemoteTimerStopError,
    RemoteTimerReadError,
    create_remote_wall_clock_timer
)
from orchestrator.node_manager import NodeManager, NodeDiscoveryError
from tests.unit.mock_nodes import MockNodeManager


class TestRemoteWallClockTimer:
    """Test suite for RemoteWallClockTimer class."""

    @pytest.fixture
    def mock_node_manager(self):
        """Create a mock NodeManager for testing."""
        manager = Mock(spec=NodeManager)
        manager.get_ssh_client = Mock()
        return manager

    @pytest.fixture
    def mock_ssh_client(self):
        """Create a mock SSH client."""
        client = Mock()
        # Mock the exec_command method
        stdin = Mock()
        stdout = Mock()
        stderr = Mock()
        stdout.read = Mock(return_value=b"")
        stderr.read = Mock(return_value=b"")
        stdout.channel = Mock()
        stdout.channel.recv_exit_status = Mock(return_value=0)

        client.exec_command = Mock(return_value=(stdin, stdout, stderr))
        return client

    def test_create_remote_wall_clock_timer(self, mock_node_manager):
        """Test factory function creates timer instance."""
        timer = create_remote_wall_clock_timer(mock_node_manager)
        assert isinstance(timer, RemoteWallClockTimer)
        assert timer.node_manager == mock_node_manager

    def test_start_timer_success(self, mock_node_manager, mock_ssh_client):
        """Test successful timer start."""
        mock_node_manager.get_ssh_client.return_value = mock_ssh_client

        timer = RemoteWallClockTimer(mock_node_manager)
        session = timer.start_timer("node_001", task_id="test_task")

        assert isinstance(session, RemoteTimerSession)
        assert session.node_id == "node_001"
        assert session.session_id.startswith("node_001_test_task_")
        assert isinstance(session.start_time, datetime)
        assert session.ssh_client == mock_ssh_client
        assert len(timer._active_sessions) == 1

    def test_start_timer_no_ssh_connection(self, mock_node_manager):
        """Test timer start fails when no SSH connection available."""
        mock_node_manager.get_ssh_client.return_value = None

        timer = RemoteWallClockTimer(mock_node_manager)

        with pytest.raises(RemoteTimerStartError) as exc_info:
            timer.start_timer("node_001", task_id="test_task")

        assert "Failed to get SSH connection" in str(exc_info.value)

    def test_start_timer_ssh_failure(self, mock_node_manager, mock_ssh_client):
        """Test timer start fails on SSH command failure."""
        mock_node_manager.get_ssh_client.return_value = mock_ssh_client

        # Simulate SSH command failure
        mock_ssh_client.exec_command.return_value[1].channel.recv_exit_status.return_value = 1
        mock_ssh_client.exec_command.return_value[2].read.return_value = b"Command failed"

        timer = RemoteWallClockTimer(mock_node_manager)

        with pytest.raises(RemoteTimerStartError) as exc_info:
            timer.start_timer("node_001", task_id="test_task")

        assert "Failed to start timer" in str(exc_info.value)

    def test_stop_timer_success(self, mock_node_manager, mock_ssh_client):
        """Test successful timer stop."""
        mock_node_manager.get_ssh_client.return_value = mock_ssh_client

        timer = RemoteWallClockTimer(mock_node_manager)
        session = timer.start_timer("node_001", task_id="test_task")

        # Small delay to ensure duration > 0
        time.sleep(0.01)

        result = timer.stop_timer(session)

        assert isinstance(result, WallClockResult)
        assert result.node_id == "node_001"
        assert result.success is True
        assert result.duration_seconds > 0
        assert result.error_message is None
        assert len(timer._active_sessions) == 0  # Session cleaned up

    def test_stop_timer_ssh_failure(self, mock_node_manager, mock_ssh_client):
        """Test timer stop fails on SSH command failure."""
        mock_node_manager.get_ssh_client.return_value = mock_ssh_client

        timer = RemoteWallClockTimer(mock_node_manager)
        session = timer.start_timer("node_001", task_id="test_task")

        # Simulate SSH command failure
        mock_ssh_client.exec_command.return_value[1].channel.recv_exit_status.return_value = 1
        mock_ssh_client.exec_command.return_value[2].read.return_value = b"Command failed"

        result = timer.stop_timer(session)

        assert isinstance(result, WallClockResult)
        assert result.success is False
        assert "Failed to stop timer" in result.error_message

    def test_stop_all_timers(self, mock_node_manager, mock_ssh_client):
        """Test stopping all active timers."""
        mock_node_manager.get_ssh_client.return_value = mock_ssh_client

        timer = RemoteWallClockTimer(mock_node_manager)

        # Start multiple timers
        session1 = timer.start_timer("node_001", task_id="task1")
        session2 = timer.start_timer("node_002", task_id="task2")

        assert len(timer._active_sessions) == 2

        results = timer.stop_all_timers()

        assert len(results) == 2
        assert all(r.success for r in results)
        assert len(timer._active_sessions) == 0

    def test_read_timer_file_success(self, mock_node_manager, mock_ssh_client):
        """Test reading timer file from remote node."""
        mock_node_manager.get_ssh_client.return_value = mock_ssh_client

        # Mock successful file read
        mock_ssh_client.exec_command.return_value[1].read.return_value = (
            b"session123_START 1234567890.123456789\n"
            b"session123_END 1234567895.123456789\n"
        )
        mock_ssh_client.exec_command.return_value[1].channel.recv_exit_status.return_value = 0

        timer = RemoteWallClockTimer(mock_node_manager)
        start_ts, end_ts = timer.read_timer_file("node_001", "session123")

        assert start_ts == 1234567890.123456789
        assert end_ts == 1234567895.123456789

    def test_read_timer_file_not_found(self, mock_node_manager, mock_ssh_client):
        """Test reading non-existent timer file."""
        mock_node_manager.get_ssh_client.return_value = mock_ssh_client

        mock_ssh_client.exec_command.return_value[1].read.return_value = b"FILE_NOT_FOUND"
        mock_ssh_client.exec_command.return_value[1].channel.recv_exit_status.return_value = 0

        timer = RemoteWallClockTimer(mock_node_manager)
        start_ts, end_ts = timer.read_timer_file("node_001", "nonexistent")

        assert start_ts is None
        assert end_ts is None

    def test_cleanup_remote_files_success(self, mock_node_manager, mock_ssh_client):
        """Test successful cleanup of remote files."""
        mock_node_manager.get_ssh_client.return_value = mock_ssh_client
        mock_ssh_client.exec_command.return_value[1].channel.recv_exit_status.return_value = 0

        timer = RemoteWallClockTimer(mock_node_manager)
        result = timer.cleanup_remote_files("node_001", "session123")

        assert result is True

    def test_cleanup_remote_files_failure(self, mock_node_manager, mock_ssh_client):
        """Test cleanup failure when SSH command fails."""
        mock_node_manager.get_ssh_client.return_value = mock_ssh_client
        mock_ssh_client.exec_command.return_value[1].channel.recv_exit_status.return_value = 1

        timer = RemoteWallClockTimer(mock_node_manager)
        result = timer.cleanup_remote_files("node_001", "session123")

        assert result is False

    def test_wall_clock_result_to_dict(self):
        """Test WallClockResult serialization."""
        start_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 1, 12, 0, 5, tzinfo=timezone.utc)

        result = WallClockResult(
            node_id="node_001",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=5.0,
            success=True
        )

        result_dict = result.to_dict()

        assert result_dict["node_id"] == "node_001"
        assert result_dict["duration_seconds"] == 5.0
        assert result_dict["success"] is True
        assert "start_time" in result_dict
        assert "end_time" in result_dict

    def test_wall_clock_result_with_error(self):
        """Test WallClockResult with error state."""
        start_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        result = WallClockResult(
            node_id="node_001",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=0.0,
            success=False,
            error_message="Connection lost"
        )

        assert result.success is False
        assert result.error_message == "Connection lost"


class TestRemoteWallClockTimerWithMockNodes:
    """Integration tests using MockNodeManager."""

    @pytest.fixture
    def mock_node_manager_instance(self):
        """Create a real MockNodeManager instance."""
        return MockNodeManager()

    def test_timer_with_mock_nodes(self, mock_node_manager_instance):
        """Test timer operations with mock nodes."""
        # Discover mock nodes
        nodes = mock_node_manager_instance.discover_nodes(["mock_node_1"])
        assert len(nodes) > 0

        timer = RemoteWallClockTimer(mock_node_manager_instance)

        # Start timer on mock node
        session = timer.start_timer("mock_node_1", task_id="test_integration")
        assert session is not None

        # Stop timer
        result = timer.stop_timer(session)
        assert result.success is True
        assert result.duration_seconds >= 0