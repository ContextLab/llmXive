"""
Unit tests for src.lib.utils
"""

import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest
import yaml

from src.lib.utils import (
    setup_logging,
    set_random_seed,
    load_json,
    save_json,
    load_csv,
    save_csv,
    load_yaml,
    save_yaml,
    compute_file_checksum,
    ensure_directory,
    get_config_paths,
)


def test_setup_logging_console_only(caplog):
    """Test logging setup with only console output."""
    logger = setup_logging(log_level="INFO", name="test_console")
    logger.info("Test message")
    assert "Test message" in caplog.text


def test_setup_logging_with_file(tmp_path):
    """Test logging setup with file output."""
    log_file = tmp_path / "test.log"
    logger = setup_logging(log_level="DEBUG", log_file=log_file, name="test_file")
    logger.debug("Debug message")
    
    assert log_file.exists()
    content = log_file.read_text()
    assert "Debug message" in content


def test_set_random_seed():
    """Test that random seed is set correctly."""
    set_random_seed(123)
    val1 = random.random()
    
    set_random_seed(123)
    val2 = random.random()
    
    assert val1 == val2


def test_save_and_load_json(tmp_path):
    """Test JSON save and load round-trip."""
    data = {"key": "value", "number": 42, "list": [1, 2, 3]}
    file_path = tmp_path / "test.json"
    
    save_json(data, file_path)
    loaded = load_json(file_path)
    
    assert loaded == data


def test_load_json_not_found():
    """Test loading a non-existent JSON file."""
    with pytest.raises(FileNotFoundError):
        load_json("non_existent.json")


def test_save_and_load_csv(tmp_path):
    """Test CSV save and load round-trip."""
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    file_path = tmp_path / "test.csv"
    
    save_csv(df, file_path)
    loaded = load_csv(file_path)
    
    assert loaded.equals(df)


def test_load_csv_not_found():
    """Test loading a non-existent CSV file."""
    with pytest.raises(FileNotFoundError):
        load_csv("non_existent.csv")


def test_save_and_load_yaml(tmp_path):
    """Test YAML save and load round-trip."""
    data = {"config": "test", "values": [1, 2, 3]}
    file_path = tmp_path / "test.yaml"
    
    save_yaml(data, file_path)
    loaded = load_yaml(file_path)
    
    assert loaded == data


def test_load_yaml_not_found():
    """Test loading a non-existent YAML file."""
    with pytest.raises(FileNotFoundError):
        load_yaml("non_existent.yaml")


def test_compute_file_checksum(tmp_path):
    """Test file checksum computation."""
    file_path = tmp_path / "checksum_test.txt"
    file_path.write_text("Hello, World!")
    
    checksum = compute_file_checksum(file_path)
    assert len(checksum) == 64  # SHA256 hex length


def test_compute_file_checksum_not_found():
    """Test checksum on non-existent file."""
    with pytest.raises(FileNotFoundError):
        compute_file_checksum("non_existent.txt")


def test_ensure_directory(tmp_path):
    """Test directory creation."""
    new_dir = tmp_path / "new" / "nested" / "dir"
    result = ensure_directory(new_dir)
    
    assert result.exists()
    assert result.is_dir()


def test_get_config_paths():
    """Test that config paths are retrieved correctly."""
    paths = get_config_paths()
    
    assert "data_raw" in paths
    assert "data_processed" in paths
    assert "artifacts" in paths
    assert isinstance(paths["data_raw"], Path)
