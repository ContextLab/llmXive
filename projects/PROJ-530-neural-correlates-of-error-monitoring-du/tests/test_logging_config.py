import os
import sys
import yaml
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.logging_config import initialize_logging, log_step, log_preprocessing_parameter, log_artifact, DATA_DIR

@pytest.fixture
def cleanup_yaml():
    """Ensure a clean state for YAML logging tests"""
    yaml_path = DATA_DIR / "preprocessing.yaml"
    if yaml_path.exists():
        yaml_path.unlink()
    yield
    # Cleanup after test if desired, or leave for inspection
    # if yaml_path.exists():
    #     yaml_path.unlink()

def test_initialize_logging_creates_yaml_file(cleanup_yaml):
    """Test that initialize_logging creates the preprocessing.yaml file"""
    logger = initialize_logging("test_init")
    yaml_path = DATA_DIR / "preprocessing.yaml"
    assert yaml_path.exists(), "preprocessing.yaml should be created on initialization"
    
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    
    assert "steps" in data
    assert "parameters" in data

def test_log_step_appends_to_yaml(cleanup_yaml):
    """Test that log_step correctly appends a step to the YAML file"""
    initialize_logging("test_step")
    log_step("Test Step", {"param1": "value1", "param2": 123})
    
    yaml_path = DATA_DIR / "preprocessing.yaml"
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    
    assert len(data["steps"]) == 1
    assert data["steps"][0]["name"] == "Test Step"
    assert data["steps"][0]["details"]["param1"] == "value1"
    assert data["steps"][0]["details"]["param2"] == 123

def test_log_preprocessing_parameter_appends_to_yaml(cleanup_yaml):
    """Test that log_preprocessing_parameter correctly appends a parameter"""
    initialize_logging("test_param")
    log_preprocessing_parameter("filter_cutoff", 30.0, "Highpass filter cutoff")
    
    yaml_path = DATA_DIR / "preprocessing.yaml"
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    
    assert len(data["parameters"]) == 1
    assert data["parameters"][0]["key"] == "filter_cutoff"
    assert data["parameters"][0]["value"] == 30.0
    assert data["parameters"][0]["description"] == "Highpass filter cutoff"

def test_log_artifact_appends_to_yaml(cleanup_yaml):
    """Test that log_artifact correctly appends an artifact entry"""
    initialize_logging("test_artifact")
    log_artifact("Test File", "data/processed/test.csv", "csv")
    
    yaml_path = DATA_DIR / "preprocessing.yaml"
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    
    assert "artifacts" in data
    assert len(data["artifacts"]) == 1
    assert data["artifacts"][0]["name"] == "Test File"
    assert data["artifacts"][0]["path"] == "data/processed/test.csv"
    assert data["artifacts"][0]["type"] == "csv"