"""
Unit tests for environment configuration management.
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from environment_config import (
    load_environment_config,
    save_environment_config,
    get_dataset_ids,
    get_processing_params,
    get_alpha_band,
    get_consistency_threshold,
    get_random_seed,
    validate_config,
    init_default_config,
    DEFAULT_CONFIG,
    CONFIG_PATH
)
from exceptions import DataIntegrityError, MissingMetadataError

@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(DEFAULT_CONFIG))
    return config_file

@pytest.fixture
def mock_project_root(tmp_path):
    """Mock the project root to point to a temporary directory."""
    with patch('environment_config.get_project_root', return_value=tmp_path):
        yield tmp_path

def test_load_environment_config_defaults(mock_project_root):
    """Test loading config when file does not exist returns defaults."""
    config = load_environment_config()
    assert config == DEFAULT_CONFIG
    assert len(config["datasets"]["openneuro_ids"]) == 3

def test_load_environment_config_from_file(mock_project_root, temp_config_file):
    """Test loading config from an existing file."""
    custom_config = {
        "datasets": {
            "openneuro_ids": ["ds000001"],
            "min_subjects": 10
        },
        "processing": DEFAULT_CONFIG["processing"],
        "analysis": DEFAULT_CONFIG["analysis"]
    }
    temp_config_file.write_text(json.dumps(custom_config))
    
    config = load_environment_config()
    assert config["datasets"]["openneuro_ids"] == ["ds000001"]

def test_load_environment_config_malformed(mock_project_root, tmp_path):
    """Test that malformed JSON raises DataIntegrityError."""
    config_file = tmp_path / "config.json"
    config_file.write_text("not valid json")
    
    with patch('environment_config.CONFIG_PATH', str(tmp_path / "config.json")):
        with pytest.raises(DataIntegrityError):
            load_environment_config()

def test_get_dataset_ids(mock_project_root, temp_config_file):
    """Test retrieving dataset IDs."""
    ids = get_dataset_ids()
    assert len(ids) == 3
    assert "ds003865" in ids

def test_get_dataset_ids_empty(mock_project_root):
    """Test that missing dataset IDs raises MissingMetadataError."""
    empty_config = {
        "datasets": {"openneuro_ids": []},
        "processing": DEFAULT_CONFIG["processing"],
        "analysis": DEFAULT_CONFIG["analysis"]
    }
    config_file = mock_project_root / CONFIG_PATH
    config_file.write_text(json.dumps(empty_config))
    
    with pytest.raises(MissingMetadataError):
        get_dataset_ids()

def test_get_processing_params_pipeline_a(mock_project_root, temp_config_file):
    """Test retrieving Pipeline A parameters."""
    params = get_processing_params("pipeline_a")
    assert params["bandpass_low"] == 1.0
    assert params["bandpass_high"] == 45.0
    assert params["ica"]["enabled"] is True

def test_get_processing_params_pipeline_b(mock_project_root, temp_config_file):
    """Test retrieving Pipeline B parameters."""
    params = get_processing_params("pipeline_b")
    assert params["bandpass_low"] == 0.5
    assert params["bandpass_high"] == 40.0
    assert params["ica"]["enabled"] is False

def test_get_processing_params_invalid(mock_project_root, temp_config_file):
    """Test that invalid pipeline name raises MissingMetadataError."""
    with pytest.raises(MissingMetadataError):
        get_processing_params("pipeline_c")

def test_get_alpha_band(mock_project_root, temp_config_file):
    """Test retrieving alpha band."""
    band = get_alpha_band()
    assert band["low"] == 8.0
    assert band["high"] == 13.0

def test_get_consistency_threshold(mock_project_root, temp_config_file):
    """Test retrieving consistency threshold."""
    threshold = get_consistency_threshold()
    assert threshold == 0.5

def test_get_random_seed(mock_project_root, temp_config_file):
    """Test retrieving random seed."""
    seed = get_random_seed()
    assert seed == 42

def test_validate_config_success(mock_project_root, temp_config_file):
    """Test that valid config passes validation."""
    assert validate_config() is True

def test_validate_config_missing_datasets(mock_project_root):
    """Test validation fails when datasets are missing."""
    bad_config = {
        "datasets": {},
        "processing": DEFAULT_CONFIG["processing"],
        "analysis": DEFAULT_CONFIG["analysis"]
    }
    config_file = mock_project_root / CONFIG_PATH
    config_file.write_text(json.dumps(bad_config))
    
    with pytest.raises(DataIntegrityError):
        validate_config()

def test_validate_config_missing_pipelines(mock_project_root):
    """Test validation fails when pipelines are missing."""
    bad_config = {
        "datasets": DEFAULT_CONFIG["datasets"],
        "processing": {},
        "analysis": DEFAULT_CONFIG["analysis"]
    }
    config_file = mock_project_root / CONFIG_PATH
    config_file.write_text(json.dumps(bad_config))
    
    with pytest.raises(DataIntegrityError):
        validate_config()

def test_init_default_config_creates_file(mock_project_root):
    """Test that init_default_config creates the file if missing."""
    config_file = mock_project_root / CONFIG_PATH
    assert not config_file.exists()
    
    init_default_config()
    
    assert config_file.exists()
    with open(config_file) as f:
        data = json.load(f)
    assert "datasets" in data