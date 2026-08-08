"""
Unit Tests for Remote Wall Clock Timer Module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import time
import paramiko

from orchestrator.remote_wall_clock_timer import (
    RemoteWallClockTimer,
    RemoteTimerSession,
    WallClockResult,
    RemoteTimerStartError,
    RemoteTimerStopError,
    RemoteTimerReadError
)
from orchestrator.node_manager import NodeManager


@pytest.fixture
def mock_manager():
    """Create a mock NodeManager with a mock node."""
    manager = Mock(spec=NodeManager)
    manager.get_node_info = Mock(return_value=Mock(
        ip_address="192.168.1.100",
        username="testuser",
        ssh_key_path="/tmp/key.pem"
    ))
    return manager


@pytest.fixture
def mock_ssh_client():
    """Create a mock SSH client."""
    client = Mock(spec=paramiko.SSHClient)
    transport = Mock()
    transport.is_active = Mock(return_value=True)
    client.get_transport = Mock(return_value=transport)
    return client


@pytest.fixture
def mock_channel():
    """Create a mock SSH channel for command execution."""
    channel = Mock()
    channel.recv_exit_status = Mock(return_value=0)
    return channel


@pytest.fixture
def mock_stdout():
    """Create a mock stdout with specific output."""
    stdout = Mock()
    stdout.channel = Mock()
    stdout.read = Mock(return_value=b"ID:START\n1678886400.123456\nID:STOP\n1678886410.654321")
    return stdout


@pytest.fixture
def mock_stderr():
    """Create a mock stderr."""
    stderr = Mock()
    stderr.read = Mock(return_value=b"")
    return stderr


class TestRemoteTimerSession:
    def test_init(self, mock_manager):
        session = RemoteTimerSession(node_id="node-1", manager=mock_manager)
        assert session.node_id == "node-1"
        assert session._session_active is False

    @patch('orchestrator.remote_wall_clock_timer.paramiko.SSHClient')
    def test_start_timer_success(self, mock_ssh_class, mock_manager, mock_ssh_client, mock_channel, mock_stdout, mock_stderr):
        mock_ssh_class.return_value = mock_ssh_client
        mock_ssh_client.exec_command = Mock(return_value=(Mock(), mock_stdout, mock_stderr))
        
        session = RemoteTimerSession(node_id="node-1", manager=mock_manager)
        
        start_time = session.start_timer()
        
        assert start_time is not None
        assert session._session_active is True
        mock_ssh_client.connect.assert_called_once()

    @patch('orchestrator.remote_wall_clock_timer.paramiko.SSHClient')
    def test_start_timer_connection_failure(self, mock_ssh_class, mock_manager):
        mock_ssh_class.return_value = Mock()
        mock_ssh_class.return_value.connect = Mock(side_effect=Exception("Connection refused"))
        
        session = RemoteTimerSession(node_id="node-1", manager=mock_manager)
        
        with pytest.raises(RemoteTimerStartError):
            session.start_timer()

    @patch('orchestrator.remote_wall_clock_timer.paramiko.SSHClient')
    def test_stop_timer_success(self, mock_ssh_class, mock_manager, mock_ssh_client, mock_channel, mock_stdout, mock_stderr):
        mock_ssh_class.return_value = mock_ssh_client
        mock_ssh_client.exec_command = Mock(return_value=(Mock(), mock_stdout, mock_stderr))
        
        session = RemoteTimerSession(node_id="node-1", manager=mock_manager)
        session._session_active = True
        session._start_time_utc = datetime.now(timezone.utc)
        
        stop_time = session.stop_timer()
        
        assert stop_time is not None
        assert session._session_active is False

    @patch('orchestrator.remote_wall_clock_timer.paramiko.SSHClient')
    def test_stop_timer_not_active(self, mock_ssh_class, mock_manager):
        session = RemoteTimerSession(node_id="node-1", manager=mock_manager)
        
        with pytest.raises(RemoteTimerStopError):
            session.stop_timer()

    @patch('orchestrator.remote_wall_clock_timer.paramiko.SSHClient')
    def test_get_elapsed_time_success(self, mock_ssh_class, mock_manager, mock_ssh_client, mock_channel, mock_stdout, mock_stderr):
        mock_ssh_class.return_value = mock_ssh_client
        mock_ssh_client.exec_command = Mock(return_value=(Mock(), mock_stdout, mock_stderr))
        
        session = RemoteTimerSession(node_id="node-1", manager=mock_manager)
        session._session_active = True
        
        elapsed = session.get_elapsed_time()
        
        assert elapsed == pytest.approx(10.530865, abs=0.000001)

    @patch('orchestrator.remote_wall_clock_timer.paramiko.SSHClient')
    def test_get_elapsed_time_incomplete_data(self, mock_ssh_class, mock_manager, mock_ssh_client, mock_channel, mock_stderr):
        # Mock stdout that returns incomplete data
        mock_stdout = Mock()
        mock_stdout.channel = Mock()
        mock_stdout.read = Mock(return_value=b"ID:START\n1678886400.123456") # Missing STOP
        
        mock_ssh_class.return_value = mock_ssh_client
        mock_ssh_client.exec_command = Mock(return_value=(Mock(), mock_stdout, mock_stderr))
        
        session = RemoteTimerSession(node_id="node-1", manager=mock_manager)
        session._session_active = True
        
        with pytest.raises(RemoteTimerReadError):
            session.get_elapsed_time()

    @patch('orchestrator.remote_wall_clock_timer.paramiko.SSHClient')
    def test_close(self, mock_ssh_class, mock_manager, mock_ssh_client):
        mock_ssh_class.return_value = mock_ssh_client
        
        session = RemoteTimerSession(node_id="node-1", manager=mock_manager)
        session._ssh_client = mock_ssh_client
        
        session.close()
        
        mock_ssh_client.close.assert_called_once()
        assert session._ssh_client is None


class TestRemoteWallClockTimer:
    def test_init(self, mock_manager):
        timer = RemoteWallClockTimer(mock_manager)
        assert timer.manager == mock_manager
        assert len(timer.sessions) == 0

    def test_create_session(self, mock_manager):
        timer = RemoteWallClockTimer(mock_manager)
        session = timer.create_session("node-1")
        
        assert "node-1" in timer.sessions
        assert timer.sessions["node-1"] is session

    @patch('orchestrator.remote_wall_clock_timer.RemoteTimerSession.start_timer')
    def test_start_all_success(self, mock_start, mock_manager):
        mock_start.return_value = datetime.now(timezone.utc)
        timer = RemoteWallClockTimer(mock_manager)
        
        results = timer.start_all(["node-1", "node-2"])
        
        assert len(results) == 2
        assert all(r.success for r in results.values())

    @patch('orchestrator.remote_wall_clock_timer.RemoteTimerSession.stop_timer')
    def test_stop_all_success(self, mock_stop, mock_manager):
        mock_stop.return_value = datetime.now(timezone.utc)
        timer = RemoteWallClockTimer(mock_manager)
        timer.create_session("node-1")
        timer.create_session("node-2")
        
        results = timer.stop_all(["node-1", "node-2"])
        
        assert len(results) == 2
        assert all(r.success for r in results.values())

    @patch('orchestrator.remote_wall_clock_timer.RemoteTimerSession.get_elapsed_time')
    def test_read_all_success(self, mock_read, mock_manager):
        mock_read.return_value = 10.5
        timer = RemoteWallClockTimer(mock_manager)
        timer.create_session("node-1")
        
        results = timer.read_all(["node-1"])
        
        assert len(results) == 1
        assert results["node-1"].success is True
        assert results["node-1"].elapsed_seconds == 10.5

    @patch('orchestrator.remote_wall_clock_timer.time.sleep')
    @patch('orchestrator.remote_wall_clock_timer.RemoteWallClockTimer.start_all')
    @patch('orchestrator.remote_wall_clock_timer.RemoteWallClockTimer.stop_all')
    @patch('orchestrator.remote_wall_clock_timer.RemoteWallClockTimer.read_all')
    def test_run_timing_session(self, mock_read, mock_stop, mock_start, mock_sleep, mock_manager):
        mock_read.return_value = {"node-1": WallClockResult(node_id="node-1", success=True, elapsed_seconds=5.0)}
        
        timer = RemoteWallClockTimer(mock_manager)
        results = timer.run_timing_session(["node-1"], task_duration_seconds=1.0)
        
        mock_start.assert_called_once_with(["node-1"])
        mock_sleep.assert_called_once_with(1.0)
        mock_stop.assert_called_once_with(["node-1"])
        mock_read.assert_called_once_with(["node-1"])
        assert results["node-1"].elapsed_seconds == 5.0

    def test_cleanup(self, mock_manager):
        timer = RemoteWallClockTimer(mock_manager)
        session_mock = Mock()
        timer.sessions["node-1"] = session_mock
        
        timer.cleanup()
        
        session_mock.close.assert_called_once()
        assert len(timer.sessions) == 0