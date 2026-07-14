import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

# Import the module under test
from data.download import (
    attempt_nist_fetch, 
    attempt_fallback_fetch, 
    write_verification_log,
    main,
    NIST_URL,
    MOF_1000_FALLBACK_URL,
    LOG_FILE
)

@pytest.fixture
def mock_response():
    mock = MagicMock()
    mock.status_code = 200
    mock.headers = {'Content-Type': 'text/csv'}
    mock.content = b"col1,col2\n1,2\n3,4"
    return mock

@pytest.fixture
def mock_response_html():
    mock = MagicMock()
    mock.status_code = 200
    mock.headers = {'Content-Type': 'text/html'}
    mock.content = b"<html>...</html>"
    return mock

def test_attempt_nist_fetch_success(mock_response):
    with patch('data.download.requests.get', return_value=mock_response):
        success, data, msg = attempt_nist_fetch()
        assert success is True
        assert isinstance(data, pd.DataFrame)
        assert data.shape[0] == 2
        assert "Successfully fetched" in msg

def test_attempt_nist_fetch_html_fallback(mock_response_html):
    with patch('data.download.requests.get', return_value=mock_response_html):
        success, data, msg = attempt_nist_fetch()
        assert success is False
        assert data is None
        assert "landing page" in msg.lower()

def test_attempt_nist_fetch_network_error():
    with patch('data.download.requests.get', side_effect=Exception("Network Error")):
        success, data, msg = attempt_nist_fetch()
        assert success is False
        assert "Network error" in msg

def test_attempt_fallback_fetch_success(mock_response):
    with patch('data.download.requests.get', return_value=mock_response):
        success, data, msg = attempt_fallback_fetch()
        assert success is True
        assert isinstance(data, pd.DataFrame)
        assert "Fallback" in msg

def test_write_verification_log(tmp_path, monkeypatch):
    # Monkeypatch the LOG_FILE to use a temp directory
    temp_log = tmp_path / "test_log.json"
    monkeypatch.setattr('data.download.LOG_FILE', temp_log)
    
    # Monkeypatch OUTPUT_DIR
    temp_out = tmp_path / "data" / "external"
    monkeypatch.setattr('data.download.OUTPUT_DIR', temp_out)

    write_verification_log(True, "TestSource", "Test message", (10, 5))
    
    assert temp_log.exists()
    with open(temp_log, 'r') as f:
        log_data = json.load(f)
    
    assert log_data['success'] is True
    assert log_data['attempted_source'] == "TestSource"
    assert log_data['data_shape'] == [10, 5]

def test_write_verification_log_failure(tmp_path, monkeypatch):
    temp_log = tmp_path / "test_log_fail.json"
    monkeypatch.setattr('data.download.LOG_FILE', temp_log)
    temp_out = tmp_path / "data" / "external"
    monkeypatch.setattr('data.download.OUTPUT_DIR', temp_out)

    write_verification_log(False, "TestSource", "Failed message")
    
    assert temp_log.exists()
    with open(temp_log, 'r') as f:
        log_data = json.load(f)
    
    assert log_data['success'] is False
    assert log_data['data_shape'] is None
    assert log_data['data_path'] is None

def test_main_flow_success_fallback(tmp_path, monkeypatch, mock_response):
    # Mock NIST to fail, Fallback to succeed
    def mock_nist_fail(*args, **kwargs):
        raise Exception("NIST Down")
    
    def mock_fallback_success(*args, **kwargs):
        return mock_response

    temp_log = tmp_path / "test_log_main.json"
    monkeypatch.setattr('data.download.LOG_FILE', temp_log)
    temp_out = tmp_path / "data" / "external"
    monkeypatch.setattr('data.download.OUTPUT_DIR', temp_out)

    with patch('data.download.attempt_nist_fetch', return_value=(False, None, "NIST Fail")):
        with patch('data.download.attempt_fallback_fetch', return_value=(True, pd.DataFrame([1,2]), "Fallback OK")):
            # Also mock the save to avoid writing to real disk if needed, but here we test logic
            # We need to ensure the file is created in the temp dir
            result = main()
            
            assert result is True
            assert temp_log.exists()
            with open(temp_log, 'r') as f:
                log_data = json.load(f)
            assert log_data['success'] is True
            assert log_data['attempted_source'] == "Fallback"

def test_main_flow_all_fail(tmp_path, monkeypatch):
    temp_log = tmp_path / "test_log_all_fail.json"
    monkeypatch.setattr('data.download.LOG_FILE', temp_log)
    temp_out = tmp_path / "data" / "external"
    monkeypatch.setattr('data.download.OUTPUT_DIR', temp_out)

    with patch('data.download.attempt_nist_fetch', return_value=(False, None, "NIST Fail")):
        with patch('data.download.attempt_fallback_fetch', return_value=(False, None, "Fallback Fail")):
            result = main()
            
            assert result is False
            assert temp_log.exists()
            with open(temp_log, 'r') as f:
                log_data = json.load(f)
            assert log_data['success'] is False
            assert "NIST Fail" in log_data['message']
            assert "Fallback Fail" in log_data['message']
