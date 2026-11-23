"""
Unit tests for the RemoteWallClockTimer module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import paramiko

from orchestrator.remote_wall_clock_timer import (
    RemoteWallClockTimer,
    create_timer,
    WallClockMeasurement,
    WallClockBatchResult
)
from orchestrator.models import PhysicalNode


class TestWallClockMeasurement:
    """Tests for the WallClockMeasurement dataclass."""

    def test_to_dict(self):
        start = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 12, 0, 1, tzinfo=timezone.utc)
        
        measurement = WallClockMeasurement(
            node_id="node-1",
            node_ip="192.168.1.1",
            task_id="task-1",
            start_timestamp=start,
            end_timestamp=end,
            duration_seconds=1.0,
            success=True
        )

        data = measurement.to_dict()
        assert data["node_id"] == "node-1"
        assert data["duration_seconds"] == 1.0
        assert data["success"] is True
        assert "2023-01-01T12:00:00" in data["start_timestamp"]


class TestRemoteWallClockTimer:
    """Tests for the RemoteWallClockTimer class."""

    @pytest.fixture
    def timer(self):
        return RemoteWallClockTimer(ssh_timeout=2.0)

    @pytest.fixture
    def mock_node(self):
        return PhysicalNode(
            node_id="test-node",
            ip_address="10.0.0.1",
            port=22,
            username="user",
            password="pass",
            ssh_key_path=None,
            status=None
        )

    @patch('paramiko.SSHClient')
    def test_measure_single_success(self, mock_ssh_client_cls, timer, mock_node):
        # Setup mock SSH client
        mock_client = Mock()
        mock_ssh_client_cls.return_value = mock_client
        
        # Mock the exec_command response for date
        mock_transport = Mock()
        mock_client.get_transport.return_value = mock_transport
        
        # Mock the channel and file object for stdout
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        
        # Return a valid date string
        mock_stdout.read.return_value = b"2023-01-01T12:00:00.123Z\n"
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        measurement = timer._measure_single(mock_node, "task-1")

        assert measurement.success is True
        assert measurement.node_id == "test-node"
        assert measurement.duration_seconds > 0.0
        mock_client.connect.assert_called_once()
        mock_client.close.assert_called_once()

    @patch('paramiko.SSHClient')
    def test_measure_single_auth_failure(self, mock_ssh_client_cls, timer, mock_node):
        mock_client = Mock()
        mock_ssh_client_cls.return_value = mock_client
        mock_client.connect.side_effect = paramiko.AuthenticationException("Bad password")

        measurement = timer._measure_single(mock_node, "task-1")

        assert measurement.success is False
        assert "AuthenticationException" in measurement.error_message
        mock_client.close.assert_called_once()

    @patch('paramiko.SSHClient')
    def test_measure_single_socket_timeout(self, mock_ssh_client_cls, timer, mock_node):
        mock_client = Mock()
        mock_ssh_client_cls.return_value = mock_client
        mock_client.connect.side_effect = paramiko.SocketTimeout("Connection timed out")

        measurement = timer._measure_single(mock_node, "task-1")

        assert measurement.success is False
        assert "SocketTimeout" in measurement.error_message

    def test_measure_batch_empty_list(self, timer):
        result = timer.measure_batch([], "task-1")
        assert len(result.measurements) == 0
        assert result.get_success_rate() == 0.0

    def test_measure_batch_success_rate(self, timer):
        # This test would require mocking multiple nodes and connections
        # For unit testing, we rely on the single measurement mocks above
        # Here we just verify the aggregation logic
        result = WallClockBatchResult()
        m1 = WallClockMeasurement("n1", "1.1.1.1", "t1", datetime.now(timezone.utc), datetime.now(timezone.utc), 1.0, True)
        m2 = WallClockMeasurement("n2", "2.2.2.2", "t1", datetime.now(timezone.utc), datetime.now(timezone.utc), 0.0, False)
        
        result.add_measurement(m1)
        result.add_measurement(m2)

        assert result.get_success_rate() == 0.5
        assert len(result.failed_nodes) == 1


class TestCreateTimer:
    """Tests for the factory function."""

    def test_create_timer_default(self):
        timer = create_timer()
        assert isinstance(timer, RemoteWallClockTimer)
        assert timer.ssh_timeout == 5.0

    def test_create_timer_custom(self):
        timer = create_timer(ssh_timeout=10.0)
        assert timer.ssh_timeout == 10.0