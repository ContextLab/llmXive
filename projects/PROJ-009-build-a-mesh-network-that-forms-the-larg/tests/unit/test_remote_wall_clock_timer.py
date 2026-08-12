import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
import time
import sys
import os

# Add code to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from orchestrator.remote_wall_clock_timer import (
    RemoteWallClockTimer,
    WallClockResult,
    RemoteTimerSession,
    WallClockTimerError,
    RemoteTimerStartError,
    RemoteTimerStopError,
    RemoteTimerReadError,
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

class TestRemoteWallClockTimer:
    @patch('orchestrator.remote_wall_clock_timer.SSHClient')
    def test_start_remote_timer_success(self, mock_ssh_class, timer, mock_ssh_client):
        mock_ssh_class.return_value = mock_ssh_client
        
        session = timer.start_remote_timer(
            node_id="node1",
            task_id="task1",
            node_ip="192.168.1.10"
        )
        
        assert session.node_id == "node1"
        assert session.task_id == "task1"
        assert session.start_time is not None
        assert session.ssh_client is not None
        assert "task1" in timer.sessions

    @patch('orchestrator.remote_wall_clock_timer.SSHClient')
    def test_stop_remote_timer_success(self, mock_ssh_class, timer, mock_ssh_client):
        mock_ssh_class.return_value = mock_ssh_client
        
        # Start timer first
        timer.start_remote_timer(
            node_id="node1",
            task_id="task1",
            node_ip="192.168.1.10"
        )
        
        # Stop timer
        session = timer.stop_remote_timer("task1")
        
        assert session.end_time is not None
        assert session.elapsed_seconds >= 0
        assert "task1" not in timer.sessions  # Session removed after stop

    @patch('orchestrator.remote_wall_clock_timer.SSHClient')
    def test_read_timer_result_success(self, mock_ssh_class, timer, mock_ssh_client):
        mock_ssh_class.return_value = mock_ssh_client
        
        # Start and stop timer
        timer.start_remote_timer(
            node_id="node1",
            task_id="task1",
            node_ip="192.168.1.10"
        )
        timer.stop_remote_timer("task1")
        
        # Read result
        result = timer.read_timer_result("task1")
        
        assert result.node_id == "node1"
        assert result.task_id == "task1"
        assert result.elapsed_seconds >= 0
        assert result.status == "completed"

    @patch('orchestrator.remote_wall_clock_timer.SSHClient')
    def test_stop_nonexistent_session(self, mock_ssh_class, timer):
        mock_ssh_class.return_value = mock_ssh_client
        
        with pytest.raises(RemoteTimerStopError):
            timer.stop_remote_timer("nonexistent_task")

    @patch('orchestrator.remote_wall_clock_timer.SSHClient')
    def test_read_nonexistent_session(self, mock_ssh_class, timer):
        mock_ssh_class.return_value = mock_ssh_client
        
        with pytest.raises(RemoteTimerReadError):
            timer.read_timer_result("nonexistent_task")

    @patch('orchestrator.remote_wall_clock_timer.SSHClient')
    def test_ssh_connection_failure(self, mock_ssh_class, timer):
        mock_ssh_class.side_effect = Exception("Connection refused")
        
        with pytest.raises(RemoteTimerStartError):
            timer.start_remote_timer(
                node_id="node1",
                task_id="task1",
                node_ip="192.168.1.10"
            )

    @patch('orchestrator.remote_wall_clock_timer.SSHClient')
    def test_empty_remote_timestamp(self, mock_ssh_class, timer):
        mock_ssh_class.return_value = mock_ssh_client
        mock_ssh_client.exec_command.return_value[1].read.return_value = b""
        
        with pytest.raises(RemoteTimerStartError):
            timer.start_remote_timer(
                node_id="node1",
                task_id="task1",
                node_ip="192.168.1.10"
            )

class TestCreateRemoteWallClockTimer:
    def test_factory_function(self):
        timer = create_remote_wall_clock_timer(timeout=10)
        assert isinstance(timer, RemoteWallClockTimer)
        assert timer.timeout == 10

if __name__ == "__main__":
    pytest.main([__file__, "-v"])