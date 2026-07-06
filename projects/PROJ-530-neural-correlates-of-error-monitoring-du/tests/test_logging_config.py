import os
import yaml
import pytest
from pathlib import Path
import logging

from code.logging_config import (
    initialize_logging,
    get_logger,
    log_step,
    log_preprocessing_parameter,
    log_artifact,
    PREPROCESSING_LOG_PATH,
    LOG_DIR
)

@pytest.fixture
def setup_logging():
    """Fixture to initialize logging before each test."""
    # Clean up any existing log files for test isolation
    if PREPROCESSING_LOG_PATH.exists():
        PREPROCESSING_LOG_PATH.unlink()
    if (LOG_DIR / "pipeline.log").exists():
        (LOG_DIR / "pipeline.log").unlink()
    
    logger = initialize_logging()
    return logger

def test_initialize_logging_creates_files(setup_logging):
    """Test that initialize_logging creates necessary log files."""
    assert PREPROCESSING_LOG_PATH.exists(), "preprocessing.yaml should be created"
    assert (LOG_DIR / "pipeline.log").exists(), "pipeline.log should be created"

def test_get_logger_returns_valid_instance(setup_logging):
    """Test that get_logger returns a valid logger instance."""
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"
    assert len(logger.handlers) > 0, "Logger should have handlers"

def test_log_step_writes_to_yaml(setup_logging):
    """Test that log_step correctly writes step information to YAML."""
    log_step("filtering", {"bandpass": [1, 45], "notch": 60})
    
    assert PREPROCESSING_LOG_PATH.exists()
    with open(PREPROCESSING_LOG_PATH, 'r') as f:
        data = yaml.safe_load(f)
    
    assert "pipeline_run" in data
    assert "steps" in data["pipeline_run"]
    assert len(data["pipeline_run"]["steps"]) == 1
    assert data["pipeline_run"]["steps"][0]["step"] == "filtering"
    assert data["pipeline_run"]["steps"][0]["details"]["bandpass"] == [1, 45]

def test_log_preprocessing_parameter(setup_logging):
    """Test that log_preprocessing_parameter correctly writes parameters."""
    log_preprocessing_parameter("ica_components_removed", 5)
    
    with open(PREPROCESSING_LOG_PATH, 'r') as f:
        data = yaml.safe_load(f)
    
    assert "parameters" in data
    assert "ica_components_removed" in data["parameters"]
    assert data["parameters"]["ica_components_removed"]["value"] == 5

def test_log_artifact(setup_logging):
    """Test that log_artifact correctly records artifact information."""
    test_path = "data/processed/test_epochs.fif"
    log_artifact("test_epochs", test_path, {"n_epochs": 100})
    
    with open(PREPROCESSING_LOG_PATH, 'r') as f:
        data = yaml.safe_load(f)
    
    assert "artifacts" in data
    assert len(data["artifacts"]) == 1
    assert data["artifacts"][0]["name"] == "test_epochs"
    assert data["artifacts"][0]["path"] == test_path
    assert data["artifacts"][0]["metadata"]["n_epochs"] == 100

def test_multiple_steps_accumulate(setup_logging):
    """Test that multiple log_step calls accumulate in the YAML file."""
    log_step("step1", {"param": 1})
    log_step("step2", {"param": 2})
    log_step("step3", {"param": 3})
    
    with open(PREPROCESSING_LOG_PATH, 'r') as f:
        data = yaml.safe_load(f)
    
    assert len(data["pipeline_run"]["steps"]) == 3
    assert data["pipeline_run"]["steps"][0]["step"] == "step1"
    assert data["pipeline_run"]["steps"][2]["step"] == "step3"

def test_logger_output_formats_correctly(setup_logging):
    """Test that logger output includes required fields."""
    logger = get_logger("format_test")
    
    # Capture log output by checking handlers
    assert len(logger.handlers) >= 2  # Console and file handlers
    
    console_handler = next((h for h in logger.handlers if isinstance(h, logging.StreamHandler)), None)
    file_handler = next((h for h in logger.handlers if isinstance(h, logging.FileHandler)), None)
    
    assert console_handler is not None
    assert file_handler is not None
    
    # Check formatters
    assert console_handler.formatter is not None
    assert file_handler.formatter is not None
