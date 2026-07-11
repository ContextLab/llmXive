import os
import tempfile
import pytest
from utils import checksum_file, load_config, retry_request
import yaml

class TestChecksumFile:
    def test_checksum_valid_file(self, tmp_path):
        """Test checksum calculation on a valid file."""
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)
        
        checksum = checksum_file(str(test_file))
        assert len(checksum) == 64  # SHA256 hex length
        assert isinstance(checksum, str)
    
    def test_checksum_different_content(self, tmp_path):
        """Test that different content produces different checksums."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_text("Content A")
        file2.write_text("Content B")
        
        checksum1 = checksum_file(str(file1))
        checksum2 = checksum_file(str(file2))
        
        assert checksum1 != checksum2
    
    def test_checksum_same_content(self, tmp_path):
        """Test that same content produces identical checksums."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        content = "Identical Content"
        file1.write_text(content)
        file2.write_text(content)
        
        checksum1 = checksum_file(str(file1))
        checksum2 = checksum_file(str(file2))
        
        assert checksum1 == checksum2
    
    def test_checksum_nonexistent_file(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        with pytest.raises(FileNotFoundError):
            checksum_file("/nonexistent/path/to/file.txt")
    
    def test_checksum_binary_file(self, tmp_path):
        """Test checksum calculation on a binary file."""
        test_file = tmp_path / "binary.bin"
        binary_content = b"\x00\x01\x02\x03\x04\x05"
        test_file.write_bytes(binary_content)
        
        checksum = checksum_file(str(test_file))
        assert len(checksum) == 64
        assert isinstance(checksum, str)

class TestLoadConfig:
    def test_load_valid_yaml(self, tmp_path):
        """Test loading a valid YAML configuration file."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "setting1": "value1",
            "setting2": 42,
            "nested": {
                "key": "value"
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config = load_config(str(config_file))
        
        assert config["setting1"] == "value1"
        assert config["setting2"] == 42
        assert config["nested"]["key"] == "value"
    
    def test_load_empty_yaml(self, tmp_path):
        """Test loading an empty YAML file returns empty dict."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        
        config = load_config(str(config_file))
        assert config == {}
    
    def test_load_nonexistent_config(self):
        """Test that FileNotFoundError is raised for non-existent config."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.yaml")

class TestRetryRequest:
    def test_success_on_first_attempt(self, mocker):
        """Test successful execution on first attempt."""
        mock_func = mocker.Mock(return_value="success")
        
        success, result = retry_request(mock_func)
        
        assert success is True
        assert result == "success"
        mock_func.assert_called_once()
    
    def test_retry_on_failure(self, mocker):
        """Test retry logic on transient failure."""
        import requests
        
        call_count = 0
        def mock_func(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise requests.RequestException("Transient error")
            return "success"
        
        success, result = retry_request(
            mock_func,
            max_attempts=3,
            delay_seconds=0.01  # Fast retry for testing
        )
        
        assert success is True
        assert result == "success"
        assert call_count == 3
    
    def test_failure_after_max_attempts(self, mocker):
        """Test failure after exhausting max attempts."""
        import requests
        
        def mock_func(*args, **kwargs):
            raise requests.RequestException("Persistent error")
        
        success, result = retry_request(
            mock_func,
            max_attempts=2,
            delay_seconds=0.01
        )
        
        assert success is False
        assert result is None