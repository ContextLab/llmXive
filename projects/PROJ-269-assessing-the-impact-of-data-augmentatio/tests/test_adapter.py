"""
Tests for the adapter module (T004b).
"""
import os
import json
import tempfile
import yaml
from pathlib import Path
import pytest
from unittest.mock import patch, mock_open

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from adapter import (
    load_fetch_count_log,
    get_fetched_dataset_names,
    adapt_config,
    DEFAULT_DATASETS,
    MIN_EXPECTED_DATASETS
)

@pytest.fixture
def temp_config_file():
    """Create a temporary config.yaml file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_content = {
            "simulation": {
                "default_datasets": DEFAULT_DATASETS,
                "datasets": [],
                "iterations": 1000
            },
            "runtime": {
                "adaptation_applied": False,
                "deviation_reason": None,
                "actual_dataset_count": 0
            }
        }
        yaml.dump(config_content, f)
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_fetch_log_file():
    """Create a temporary fetch_count.log file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        # Simulate a log where one dataset deviated
        log_content = [
            {
                "dataset_name": "pima",
                "status": "deviation",
                "message": "Checksum mismatch",
                "timestamp": "2023-10-01T00:00:00"
            },
            {
                "dataset_name": "wine",
                "status": "deviation",
                "message": "URL not reachable",
                "timestamp": "2023-10-01T00:00:01"
            }
        ]
        json.dump(log_content, f)
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)

def test_load_fetch_count_log_file_not_found():
    """Test that load_fetch_count_log returns None if file doesn't exist."""
    result = load_fetch_count_log(Path("/nonexistent/path/file.log"))
    assert result is None

def test_load_fetch_count_log_success(temp_fetch_log_file):
    """Test successful loading of fetch count log."""
    result = load_fetch_count_log(temp_fetch_log_file)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["dataset_name"] == "pima"

def test_get_fetched_dataset_names():
    """Test extraction of fetched dataset names from deviation records."""
    deviation_records = [
        {"dataset_name": "pima", "status": "deviation", "message": "Error"},
        {"dataset_name": "wine", "status": "deviation", "message": "Error"}
    ]
    # Verified datasets are: breast_cancer, ionosphere, heart_disease
    fetched = get_fetched_dataset_names(deviation_records)
    assert fetched == ["breast_cancer", "heart_disease", "ionosphere"]

def test_get_fetched_dataset_names_all_deviated():
    """Test when all verified datasets have deviations."""
    deviation_records = [
        {"dataset_name": "breast_cancer", "status": "deviation", "message": "Error"},
        {"dataset_name": "ionosphere", "status": "deviation", "message": "Error"},
        {"dataset_name": "heart_disease", "status": "deviation", "message": "Error"}
    ]
    fetched = get_fetched_dataset_names(deviation_records)
    assert fetched == []

def test_adapt_config_when_count_less_than_5(temp_config_file, temp_fetch_log_file):
    """Test config adaptation when dataset count < 5."""
    deviation_records = [
        {"dataset_name": "pima", "status": "deviation", "message": "Error"},
        {"dataset_name": "wine", "status": "deviation", "message": "Error"}
    ]
    fetched = get_fetched_dataset_names(deviation_records)
    # fetched = ["breast_cancer", "heart_disease", "ionosphere"] -> count=3 < 5

    config = adapt_config(temp_config_file, fetched, deviation_records)

    assert config["simulation"]["datasets"] == fetched
    assert config["runtime"]["adaptation_applied"] is True
    assert config["runtime"]["actual_dataset_count"] == 3
    assert config["runtime"]["deviation_reason"] is not None

def test_adapt_config_when_count_meets_5(temp_config_file):
    """Test config adaptation when dataset count >= 5."""
    # Simulate 5 fetched datasets (hypothetically)
    fetched = DEFAULT_DATASETS  # All 5 default datasets
    deviation_records = []  # No deviations

    config = adapt_config(temp_config_file, fetched, deviation_records)

    assert config["simulation"]["datasets"] == DEFAULT_DATASETS
    assert config["runtime"]["adaptation_applied"] is False
    assert config["runtime"]["actual_dataset_count"] == 5
    assert config["runtime"]["deviation_reason"] is None

def test_adapt_config_file_not_found():
    """Test that adapt_config raises FileNotFoundError if config doesn't exist."""
    with pytest.raises(FileNotFoundError):
        adapt_config(Path("/nonexistent/config.yaml"), [], [])