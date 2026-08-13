"""
Unit tests for NetworkSaturationHandler (T014b)
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from orchestrator.network_saturation_handler import (
    NetworkSaturationHandler,
    TerminationFailedError,
    NetworkSaturationError,
    TerminationResult,
    create_handler
)

@pytest.fixture
def mock_config():
    return {
        "ssh_timeout": 5,
        "termination_retries": 2,
        "termination_delay": 0.1
    }

@pytest.fixture
def mock_logger():
    logger = Mock()
    logger.debug = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.info = Mock()
    logger.critical = Mock()
    return logger

@pytest.fixture
def temp_status_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write(json.dumps({"runs": {}}))
        path = f.name
    yield path
    if os.path.exists(path):
        os.remove(path)

@pytest.fixture
def handler(mock_logger, mock_config, temp_status_file):
    h = NetworkSaturationHandler(
        logger=mock_logger,
        config=mock_config,
        validation_status_path=Path(temp_status_file)
    )
    return h

def test_termination_result_creation():
    result = TerminationResult(
        node_id="user@192.168.1.1",
        pid=12345,
        success=True,
        message="Success"
    )
    assert result.node_id == "user@192.168.1.1"
    assert result.pid == 12345
    assert result.success is True
    assert result.message == "Success"

@patch('paramiko.SSHClient')
def test_terminate_remote_process_success(mock_ssh_client, handler, mock_logger):
    # Mock the SSH client behavior
    mock_client_instance = Mock()
    mock_ssh_client.return_value = mock_client_instance
    
    # Mock exec_command to return success
    mock_channel = Mock()
    mock_channel.recv_exit_status.return_value = 0 # Process not found after kill
    
    mock_stdout = Mock()
    mock_stdout.channel = mock_channel
    mock_stderr = Mock()
    
    # First call (kill -15), second call (check), third call (kill -9), fourth call (check)
    mock_client_instance.exec_command.side_effect = [
        (Mock(), mock_stdout, mock_stderr), # kill -15
        (Mock(), mock_stdout, mock_stderr), # check
        (Mock(), mock_stdout, mock_stderr), # kill -9
        (Mock(), mock_stdout, mock_stderr)  # check final
    ]
    
    result = handler.terminate_remote_process(
        node_ip="192.168.1.1",
        node_username="testuser",
        benchmark_pid=12345
    )
    
    assert result.success is True
    assert "terminated successfully" in result.message
    mock_client_instance.connect.assert_called_once()
    mock_client_instance.close.assert_called_once()

@patch('paramiko.SSHClient')
def test_terminate_remote_process_failure(mock_ssh_client, handler):
    mock_client_instance = Mock()
    mock_ssh_client.return_value = mock_client_instance
    
    # Simulate process always existing (exit status 0 for ps check)
    mock_channel = Mock()
    mock_channel.recv_exit_status.return_value = 0 
    
    mock_stdout = Mock()
    mock_stdout.channel = mock_channel
    
    # Mock connection failure
    mock_client_instance.connect.side_effect = Exception("Connection refused")
    
    result = handler.terminate_remote_process(
        node_ip="192.168.1.1",
        node_username="testuser",
        benchmark_pid=12345
    )
    
    assert result.success is False
    assert "error" in result.message.lower()

def test_update_validation_status(handler, temp_status_file):
    run_id = "test_run_123"
    failed_terminations = [
        {"node_id": "user@1.1.1.1", "pid": 999, "error": "Connection timeout"}
    ]
    
    handler._update_validation_status(run_id, failed_terminations)
    
    # Verify file content
    with open(temp_status_file, 'r') as f:
        data = json.load(f)
    
    assert run_id in data["runs"]
    assert data["runs"][run_id]["status"] == "excluded"
    assert data["runs"][run_id]["error_code"] == "NETWORK_SATURATION"
    assert "saturation_event" in data["runs"][run_id]["details"]

@patch('paramiko.SSHClient')
def test_handle_saturation_event_success(mock_ssh_client, handler):
    mock_client_instance = Mock()
    mock_ssh_client.return_value = mock_client_instance
    
    # Mock successful termination
    mock_channel = Mock()
    mock_channel.recv_exit_status.return_value = 0 
    mock_stdout = Mock()
    mock_stdout.channel = mock_channel
    
    mock_client_instance.exec_command.side_effect = [
        (Mock(), mock_stdout, Mock()), # kill
        (Mock(), mock_stdout, Mock()), # check
        (Mock(), mock_stdout, Mock()), # kill -9
        (Mock(), mock_stdout, Mock())  # check
    ]
    
    node_details = [{"ip": "192.168.1.1", "username": "user"}]
    benchmark_pids = {"user@192.168.1.1": 12345}
    
    with pytest.raises(NetworkSaturationError) as exc_info:
        handler.handle_saturation_event(
            node_details=node_details,
            benchmark_pids=benchmark_pids,
            run_id="run_456"
        )
    
    assert "Network saturation detected" in str(exc_info.value)

@patch('paramiko.SSHClient')
def test_handle_saturation_event_partial_failure(mock_ssh_client, handler):
    mock_client_instance = Mock()
    mock_ssh_client.return_value = mock_client_instance
    
    # First node fails
    mock_client_instance.connect.side_effect = Exception("SSH Error")
    
    node_details = [{"ip": "192.168.1.1", "username": "user"}]
    benchmark_pids = {"user@192.168.1.1": 12345}
    
    with pytest.raises(TerminationFailedError) as exc_info:
        handler.handle_saturation_event(
            node_details=node_details,
            benchmark_pids=benchmark_pids,
            run_id="run_789"
        )
    
    assert "Failed to terminate processes" in str(exc_info.value)

def test_create_handler(mock_config):
    with patch('orchestrator.network_saturation_handler.get_logger') as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        h = create_handler(mock_config)
        
        assert isinstance(h, NetworkSaturationHandler)
        assert h.ssh_timeout == 5
        assert h.termination_retries == 2
        assert h.termination_delay == 0.1
        mock_get_logger.assert_called_once()