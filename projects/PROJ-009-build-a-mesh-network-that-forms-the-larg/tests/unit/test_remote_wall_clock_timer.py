"""
Unit tests for the Remote Wall Clock Timer module.
Tests the logic of time calculation and result formatting without
requiring a live SSH connection (using mocks).
"""
import unittest
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime, timezone
import time

from orchestrator.remote_wall_clock_timer import (
    RemoteWallClockTimer,
    RemoteTimerSession,
    WallClockResult,
    RemoteTimerStartError,
    RemoteTimerStopError,
    create_remote_wall_clock_timer
)

@pytest.fixture
def timer():
    return create_remote_wall_clock_timer(timeout=5)

@pytest.fixture
def mock_ssh_client():
    client = MagicMock()
    mock_stdin = MagicMock()
    mock_stdout = MagicMock()
    mock_stderr = MagicMock()
    
    # Simulate successful timestamp output
    mock_stdout.read.return_value = b"1234567890.123456789"
    mock_stderr.read.return_value = b""
    
    client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
    return client

class TestWallClockResult:
    def test_to_dict(self):
        start = datetime.now(timezone.utc)
        end = start + timedelta(seconds=1.5)
        
        result = WallClockResult(
            node_id="node1",
            task_id="task1",
            start_time=start,
            end_time=end,
            elapsed_seconds=1.5,
            status="completed"
        )
        
        data = result.to_dict()
        
        assert data["node_id"] == "node1"
        assert data["task_id"] == "task1"
        assert data["wall_clock_time"] == 1.5
        assert data["status"] == "completed"
        assert "start_time" in data
        assert "end_time" in data
        assert "error_message" in data

class TestRemoteWallClockTimer(unittest.TestCase):
    """Tests for the RemoteWallClockTimer class."""

    def setUp(self):
        """Set up mock SSH client and timer instance."""
        self.mock_ssh_client = MagicMock()
        self.node_id = "192.168.1.10"
        self.timer = RemoteWallClockTimer(self.mock_ssh_client, self.node_id)

    def test_create_remote_wall_clock_timer(self):
        """Test factory function creates correct instance."""
        timer = create_remote_wall_clock_timer(self.mock_ssh_client, self.node_id)
        self.assertIsInstance(timer, RemoteWallClockTimer)
        self.assertEqual(timer.node_id, self.node_id)

    @patch('paramiko.SSHClient.exec_command')
    def test_start_timer_success(self, mock_exec):
        """Test successful start of remote timer."""
        # Mock the SSH command output
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"1678886400.123456789"
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""

        self.mock_ssh_client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

        session = self.timer.start_timer()

        self.assertIsNotNone(session)
        self.assertTrue(session.is_active)
        self.assertIsNotNone(session.start_time)
        self.assertEqual(self.timer.session, session)

    @patch('paramiko.SSHClient.exec_command')
    def test_start_timer_failure(self, mock_exec):
        """Test start timer failure with non-zero exit status."""
        mock_stdout = MagicMock()
        mock_stdout.channel.recv_exit_status.return_value = 1
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b"Command not found"

        self.mock_ssh_client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

        with self.assertRaises(RemoteTimerStartError):
            self.timer.start_timer()

    @patch('paramiko.SSHClient.exec_command')
    def test_stop_timer_success(self, mock_exec):
        """Test successful stop and calculation of elapsed time."""
        start_time_float = 1678886400.0
        stop_time_float = 1678886402.5
        expected_elapsed = stop_time_float - start_time_float

        # Mock start
        mock_start_stdout = MagicMock()
        mock_start_stdout.read.return_value = f"{start_time_float}".encode()
        mock_start_stdout.channel.recv_exit_status.return_value = 0
        
        # Mock stop
        mock_stop_stdout = MagicMock()
        mock_stop_stdout.read.return_value = f"{stop_time_float}".encode()
        mock_stop_stdout.channel.recv_exit_status.return_value = 0

        self.mock_ssh_client.exec_command.side_effect = [
            (MagicMock(), mock_start_stdout, MagicMock()),
            (MagicMock(), mock_stop_stdout, MagicMock())
        ]

        # Start
        session = self.timer.start_timer()
        
        # Stop
        elapsed = self.timer.stop_timer(session)

        self.assertAlmostEqual(elapsed, expected_elapsed, places=5)
        self.assertFalse(session.is_active)
        self.assertIsNotNone(session.elapsed_seconds)

    def test_stop_timer_no_session(self):
        """Test stopping timer without an active session raises error."""
        with self.assertRaises(RemoteTimerStopError):
            self.timer.stop_timer()

    def test_get_result_success(self):
        """Test retrieving result after successful timer cycle."""
        start_time_float = 1678886400.0
        stop_time_float = 1678886401.0
        expected_elapsed = 1.0

        mock_start_stdout = MagicMock()
        mock_start_stdout.read.return_value = f"{start_time_float}".encode()
        mock_start_stdout.channel.recv_exit_status.return_value = 0

        mock_stop_stdout = MagicMock()
        mock_stop_stdout.read.return_value = f"{stop_time_float}".encode()
        mock_stop_stdout.channel.recv_exit_status.return_value = 0

        self.mock_ssh_client.exec_command.side_effect = [
            (MagicMock(), mock_start_stdout, MagicMock()),
            (MagicMock(), mock_stop_stdout, MagicMock())
        ]

        session = self.timer.start_timer()
        self.timer.stop_timer(session)
        result = self.timer.get_result(session)

        self.assertEqual(result.node_id, self.node_id)
        self.assertAlmostEqual(result.wall_clock_time, expected_elapsed, places=5)
        self.assertEqual(result.status, "success")
        self.assertIsNone(result.error_message)

    def test_get_result_error(self):
        """Test retrieving result when session is incomplete."""
        # Create a session but don't stop it
        session = RemoteTimerSession(
            node_id=self.node_id,
            ssh_client=self.mock_ssh_client,
            start_time=datetime.now(timezone.utc),
            is_active=True
        )
        self.timer.session = session

        result = self.timer.get_result(session)

        self.assertEqual(result.status, "error")
        self.assertIn("Session not completed", result.error_message)
        self.assertEqual(result.wall_clock_time, 0.0)

    def test_to_dict_format(self):
        """Test that to_dict produces correct CSV schema keys."""
        result = WallClockResult(
            node_id="test-1",
            wall_clock_time=1.234,
            status="success"
        )
        data = result.to_dict()

        self.assertIn("node_id", data)
        self.assertIn("wall_clock_time", data)
        self.assertIn("status", data)
        self.assertEqual(data["node_id"], "test-1")
        self.assertEqual(data["wall_clock_time"], 1.234)


if __name__ == "__main__":
    unittest.main()