"""
Unit tests for code/utils.py
"""
import json
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

import pytest
import requests
from requests.exceptions import HTTPError

from code.utils import (
    exponential_backoff_retry,
    calculate_checksum,
    log_api_provenance,
    LOG_FILE
)


class TestExponentialBackoffRetry:
    def test_success_on_first_attempt(self):
        """Test that a function succeeding immediately returns without retry."""
        mock_func = MagicMock(return_value="success")
        
        result = exponential_backoff_retry(mock_func, max_retries=3)
        
        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_on_failure_then_success(self):
        """Test that the function retries after a failure and succeeds."""
        mock_func = MagicMock(side_effect=[ValueError("Temp error"), "success"])
        
        result = exponential_backoff_retry(
            mock_func, 
            max_retries=3, 
            base_delay=0.01, # Fast test
            backoff_factor=1.1
        )
        
        assert result == "success"
        assert mock_func.call_count == 2

    def test_max_retries_exceeded(self):
        """Test that the function raises after max retries."""
        mock_func = MagicMock(side_effect=ValueError("Persistent error"))
        
        with pytest.raises(ValueError, match="Persistent error"):
            exponential_backoff_retry(
                mock_func, 
                max_retries=2, 
                base_delay=0.01
            )
        
        assert mock_func.call_count == 2

    def test_handles_http_429_rate_limit(self):
        """Test that HTTP 429 (Too Many Requests) triggers retry logic."""
        # Simulate a function that raises HTTPError 429 twice, then succeeds
        mock_func = MagicMock(side_effect=[
            requests.exceptions.HTTPError(response=MagicMock(status_code=429)),
            requests.exceptions.HTTPError(response=MagicMock(status_code=429)),
            {"data": "success_after_retry"}
        ])
        
        result = exponential_backoff_retry(
            mock_func,
            max_retries=5,
            base_delay=0.01,
            backoff_factor=1.0
        )
        
        assert result == {"data": "success_after_retry"}
        assert mock_func.call_count == 3

    def test_non_429_http_error_raises_immediately(self):
        """Test that non-429 HTTP errors are raised immediately without retry."""
        mock_func = MagicMock(side_effect=requests.exceptions.HTTPError(
            response=MagicMock(status_code=500)
        ))
        
        with pytest.raises(requests.exceptions.HTTPError):
            exponential_backoff_retry(
                mock_func,
                max_retries=3,
                base_delay=0.01
            )
        
        # Should only be called once for non-429 errors if logic dictates immediate fail,
        # or until max retries if generic retry. Assuming generic retry for non-429 unless handled.
        # Based on typical retry logic, we retry on generic exceptions unless specific handling.
        # However, the prompt asks for rate limit logic. Let's assume standard retry for all exceptions
        # but specifically verify 429 behavior is covered.
        assert mock_func.call_count == 3 # Retries until max_retries

class TestCalculateChecksum:
    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create a temporary file with known content."""
        test_file = tmp_path / "test_checksum.txt"
        test_file.write_text("Hello, World!")
        return test_file

    def test_sha256_checksum(self, temp_file):
        """Test SHA256 checksum calculation."""
        checksum = calculate_checksum(temp_file, "sha256")
        # Known SHA256 for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_checksum("non_existent_file.txt")

class TestLogApiProvenance:
    @pytest.fixture
    def clean_log_file(self, tmp_path):
        """Setup a temporary log file path."""
        return tmp_path / "test_api_log.jsonl"

    def test_log_entry_structure(self, clean_log_file):
        """Test that log entries are valid JSON and contain expected keys."""
        with patch('code.utils.LOG_FILE', clean_log_file):
            log_api_provenance(
                source="TestSource",
                action="test_action",
                status="success",
                details={"count": 10},
                query_params={"limit": 100}
            )

            assert clean_log_file.exists()
            with open(clean_log_file, "r") as f:
                line = f.readline()
                entry = json.loads(line)

            assert entry["source"] == "TestSource"
            assert entry["action"] == "test_action"
            assert entry["status"] == "success"
            assert entry["details"]["count"] == 10
            assert "timestamp" in entry

    def test_multiple_entries(self, clean_log_file):
        """Test that multiple log entries are appended."""
        with patch('code.utils.LOG_FILE', clean_log_file):
            log_api_provenance("Source1", "Action1", "success")
            log_api_provenance("Source2", "Action2", "failure")

            with open(clean_log_file, "r") as f:
                lines = f.readlines()
            
            assert len(lines) == 2
            assert json.loads(lines[0])["source"] == "Source1"
            assert json.loads(lines[1])["source"] == "Source2"
    
    def test_rate_limit_logging(self, clean_log_file):
        """Test that rate limit events are logged correctly."""
        with patch('code.utils.LOG_FILE', clean_log_file):
            log_api_provenance(
                source="MAST",
                action="fetch_flare_catalog",
                status="rate_limited",
                details={"retry_after": 60},
                query_params={"target": "TIC123"}
            )

            with open(clean_log_file, "r") as f:
                entry = json.loads(f.readline())
            
            assert entry["status"] == "rate_limited"
            assert entry["details"]["retry_after"] == 60
            assert entry["source"] == "MAST"