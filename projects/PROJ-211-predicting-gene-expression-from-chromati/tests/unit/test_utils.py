"""
Unit tests for code/utils.py module.

Tests cover:
- checksum_file: valid file, missing file, content change detection
- load_config: valid yaml, missing file, empty config
- retry_request: success on first try, retry on failure, max attempts exceeded
"""
import os
import tempfile
import pytest
import yaml
from unittest.mock import patch, MagicMock
import logging

# Import the module under test
from utils import checksum_file, load_config, retry_request


class TestChecksumFile:
    """Tests for the checksum_file function."""
    
    def test_checksum_file_valid(self, tmp_path):
        """Test checksum calculation on a valid file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = checksum_file(str(test_file))
        
        assert len(checksum) == 64  # SHA256 hex length
        assert isinstance(checksum, str)
        
    def test_checksum_file_missing(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            checksum_file("/nonexistent/path/file.txt")
            
    def test_checksum_file_content_change(self, tmp_path):
        """Test that different content produces different checksums."""
        test_file = tmp_path / "test.txt"
        
        test_file.write_bytes(b"Content A")
        checksum_a = checksum_file(str(test_file))
        
        test_file.write_bytes(b"Content B")
        checksum_b = checksum_file(str(test_file))
        
        assert checksum_a != checksum_b


class TestLoadConfig:
    """Tests for the load_config function."""
    
    def test_load_config_valid(self, tmp_path):
        """Test loading a valid YAML config."""
        config_file = tmp_path / "config.yaml"
        test_config = {
            "setting1": "value1",
            "setting2": 42,
            "nested": {"key": "value"}
        }
        config_file.write_text(yaml.dump(test_config))
        
        loaded = load_config(str(config_file))
        
        assert loaded == test_config
        
    def test_load_config_missing(self):
        """Test that FileNotFoundError is raised for missing config."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.yaml")
            
    def test_load_config_empty(self, tmp_path):
        """Test loading an empty YAML file."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        
        loaded = load_config(str(config_file))
        
        assert loaded == {}


class TestRetryRequest:
    """Tests for the retry_request function."""
    
    def test_retry_success_first_attempt(self):
        """Test successful execution on first attempt."""
        def mock_func():
            return "success"
            
        success, result = retry_request(mock_func, max_attempts=3)
        
        assert success is True
        assert result == "success"
        
    def test_retry_success_after_failure(self):
        """Test successful execution after initial failures."""
        attempt_count = 0
        
        def flaky_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Simulated failure")
            return "success after retries"
            
        with patch('time.sleep'):  # Skip actual sleep in tests
            success, result = retry_request(
                flaky_func, 
                max_attempts=5, 
                delay_seconds=0
            )
            
        assert success is True
        assert result == "success after retries"
        assert attempt_count == 3
        
    def test_retry_max_attempts_exceeded(self):
        """Test failure when all retry attempts are exhausted."""
        def always_fail():
            raise Exception("Always fails")
            
        with patch('time.sleep'):  # Skip actual sleep in tests
            success, result = retry_request(
                always_fail,
                max_attempts=3,
                delay_seconds=0
            )
            
        assert success is False
        assert result is None
