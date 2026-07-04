import os
import tempfile
import pytest
from code.utils import checksum_file, load_config

def test_checksum_file():
    """Test checksum_file function with a known file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        checksum = checksum_file(temp_path)
        assert len(checksum) == 64  # SHA256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)
    finally:
        os.unlink(temp_path)

def test_checksum_file_not_found():
    """Test that checksum_file raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        checksum_file("/nonexistent/file.txt")

def test_load_config():
    """Test load_config function with a valid YAML file."""
    config_content = """
    key1: value1
    key2: 123
    nested:
      subkey: subvalue
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name
    
    try:
        config = load_config(temp_path)
        assert config["key1"] == "value1"
        assert config["key2"] == 123
        assert config["nested"]["subkey"] == "subvalue"
    finally:
        os.unlink(temp_path)

def test_load_config_not_found():
    """Test that load_config raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/config.yaml")
