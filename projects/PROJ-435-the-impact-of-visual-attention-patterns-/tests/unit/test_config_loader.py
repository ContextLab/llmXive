import pytest
import yaml
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import from the project's utility module
from code.utils.config_loader import load_config, validate_ivt_config, get_validated_config, ConfigError

@pytest.fixture
def temp_config_dir(tmp_path):
    config_dir = tmp_path / "code" / "config"
    config_dir.mkdir(parents=True)
    return config_dir

@pytest.fixture
def sample_ivt_config():
    return {
        "random_seed": 42,
        "dataset_url": "https://example.com/data.parquet",
        "ivt_duration_threshold": 100,
        "idt_dispersion_threshold": 30,
        "roi_definitions": {
            "source_attribution": {"x": 0, "y": 0, "width": 100, "height": 50},
            "headline_body": {"x": 0, "y": 50, "width": 800, "height": 100}
        }
    }

def test_load_config_valid_yaml(temp_config_dir, sample_ivt_config):
    config_path = temp_config_dir / "config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(sample_ivt_config, f)
    
    # Mock the get_project_root to return our temp dir
    with patch('code.utils.config_loader.get_project_root', return_value=temp_config_dir.parent.parent):
        config = load_config("config.yaml")
        assert config["random_seed"] == 42
        assert config["ivt_duration_threshold"] == 100

def test_load_config_missing_file(temp_config_dir):
    with patch('code.utils.config_loader.get_project_root', return_value=temp_config_dir.parent.parent):
        with pytest.raises(FileNotFoundError):
            load_config("non_existent.yaml")

def test_validate_ivt_config_valid(sample_ivt_config):
    is_valid, errors = validate_ivt_config(sample_ivt_config)
    assert is_valid is True
    assert len(errors) == 0

def test_validate_ivt_config_missing_threshold(sample_ivt_config):
    del sample_ivt_config["ivt_duration_threshold"]
    is_valid, errors = validate_ivt_config(sample_ivt_config)
    assert is_valid is False
    assert "ivt_duration_threshold" in errors[0]

def test_validate_ivt_config_invalid_type(sample_ivt_config):
    sample_ivt_config["ivt_duration_threshold"] = "not_a_number"
    is_valid, errors = validate_ivt_config(sample_ivt_config)
    assert is_valid is False
    assert any("integer" in error for error in errors)

def test_get_validated_config_success(sample_ivt_config, temp_config_dir):
    config_path = temp_config_dir / "config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(sample_ivt_config, f)
    
    with patch('code.utils.config_loader.get_project_root', return_value=temp_config_dir.parent.parent):
        config = get_validated_config("config.yaml")
        assert config["ivt_duration_threshold"] == 100

def test_get_validated_config_failure(sample_ivt_config, temp_config_dir):
    del sample_ivt_config["ivt_duration_threshold"]
    config_path = temp_config_dir / "config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(sample_ivt_config, f)
    
    with patch('code.utils.config_loader.get_project_root', return_value=temp_config_dir.parent.parent):
        with pytest.raises(ConfigError):
            get_validated_config("config.yaml")
