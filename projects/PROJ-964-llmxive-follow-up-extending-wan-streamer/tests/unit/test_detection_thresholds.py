"""
tests/unit/test_detection_thresholds.py - Unit tests for detection thresholds loading and validation.

This module tests the functionality of `code/utils/load_thresholds.py` to ensure
that detection thresholds are correctly loaded from the YAML file and that
schema validation works as expected.

These tests are part of T012a verification to ensure thresholds are present
and non-null before T013 runs.

Imports:
  - pytest
  - code.utils.load_thresholds
  - pathlib.Path
  - tempfile
  - yaml

Public Names:
  - test_load_detection_thresholds
  - test_validate_thresholds_schema_valid
  - test_validate_thresholds_schema_missing_key
  - test_validate_thresholds_schema_null_value
  - test_validate_thresholds_schema_wrong_type
  - test_get_threshold_value
"""
import os
import sys
import pytest
import tempfile
import yaml
from pathlib import Path

# Add the code directory to the path for imports
code_dir = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(code_dir))

from utils.load_thresholds import (
    load_detection_thresholds,
    validate_thresholds_schema,
    get_threshold_value
)

# Sample valid thresholds configuration
VALID_THRESHOLDS_YAML = """
audio_energy:
  speech_presence_db: -40.0
  speech_presence_normalized: 0.01
  interruption_energy_db: -15.0
  interruption_energy_normalized: 0.2
  pause_energy_db: -35.0
  pause_energy_normalized: 0.005
duration:
  min_pause_duration_sec: 0.2
  max_pause_duration_sec: 2.0
  min_interruption_duration_sec: 0.1
latent_delta:
  significant_change_threshold: 0.5
  interruption_threshold: 1.2
detection_algorithm:
  method: "hybrid"
  smoothing_window_frames: 5
  hysteresis_factor: 0.1
schema_check:
  required_keys:
    - "audio_energy.speech_presence_db"
    - "audio_energy.interruption_energy_db"
    - "audio_energy.pause_energy_db"
    - "duration.min_pause_duration_sec"
    - "latent_delta.significant_change_threshold"
    - "detection_algorithm.method"
  type_checks:
    audio_energy.speech_presence_db: float
    audio_energy.interruption_energy_db: float
    audio_energy.pause_energy_db: float
    duration.min_pause_duration_sec: float
    latent_delta.significant_change_threshold: float
    detection_algorithm.method: str
"""

# Sample thresholds configuration with a missing key
MISSING_KEY_YAML = """
audio_energy:
  speech_presence_db: -40.0
  # missing interruption_energy_db
  pause_energy_db: -35.0
duration:
  min_pause_duration_sec: 0.2
latent_delta:
  significant_change_threshold: 0.5
detection_algorithm:
  method: "hybrid"
"""

# Sample thresholds configuration with a null value
NULL_VALUE_YAML = """
audio_energy:
  speech_presence_db: -40.0
  interruption_energy_db: null
  pause_energy_db: -35.0
duration:
  min_pause_duration_sec: 0.2
latent_delta:
  significant_change_threshold: 0.5
detection_algorithm:
  method: "hybrid"
"""

# Sample thresholds configuration with wrong type
WRONG_TYPE_YAML = """
audio_energy:
  speech_presence_db: -40.0
  interruption_energy_db: "not_a_float"
  pause_energy_db: -35.0
duration:
  min_pause_duration_sec: 0.2
latent_delta:
  significant_change_threshold: 0.5
detection_algorithm:
  method: "hybrid"
"""

@pytest.fixture
def valid_thresholds_file(tmp_path):
    """Creates a temporary YAML file with valid thresholds."""
    file_path = tmp_path / "detection_thresholds.yaml"
    file_path.write_text(VALID_THRESHOLDS_YAML)
    return file_path

@pytest.fixture
def missing_key_file(tmp_path):
    """Creates a temporary YAML file with a missing key."""
    file_path = tmp_path / "detection_thresholds.yaml"
    file_path.write_text(MISSING_KEY_YAML)
    return file_path

@pytest.fixture
def null_value_file(tmp_path):
    """Creates a temporary YAML file with a null value."""
    file_path = tmp_path / "detection_thresholds.yaml"
    file_path.write_text(NULL_VALUE_YAML)
    return file_path

@pytest.fixture
def wrong_type_file(tmp_path):
    """Creates a temporary YAML file with a wrong type."""
    file_path = tmp_path / "detection_thresholds.yaml"
    file_path.write_text(WRONG_TYPE_YAML)
    return file_path

def test_load_detection_thresholds(valid_thresholds_file):
    """Test that valid thresholds are loaded correctly."""
    thresholds = load_detection_thresholds(valid_thresholds_file)
    
    assert 'audio_energy' in thresholds
    assert 'duration' in thresholds
    assert 'latent_delta' in thresholds
    assert 'detection_algorithm' in thresholds
    
    assert thresholds['audio_energy']['speech_presence_db'] == -40.0
    assert thresholds['detection_algorithm']['method'] == "hybrid"

def test_load_detection_thresholds_file_not_found():
    """Test that FileNotFoundError is raised if file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_detection_thresholds(Path("/nonexistent/path/file.yaml"))

def test_validate_thresholds_schema_valid(valid_thresholds_file):
    """Test that schema validation passes for valid thresholds."""
    thresholds = load_detection_thresholds(valid_thresholds_file)
    # Should not raise any exception
    result = validate_thresholds_schema(thresholds)
    assert result is True

def test_validate_thresholds_schema_missing_key(missing_key_file):
    """Test that ValueError is raised for missing key."""
    thresholds = load_detection_thresholds(missing_key_file)
    with pytest.raises(ValueError) as exc_info:
        validate_thresholds_schema(thresholds)
    assert "Missing required threshold key" in str(exc_info.value)

def test_validate_thresholds_schema_null_value(null_value_file):
    """Test that ValueError is raised for null value."""
    thresholds = load_detection_thresholds(null_value_file)
    with pytest.raises(ValueError) as exc_info:
        validate_thresholds_schema(thresholds)
    assert "is null" in str(exc_info.value)

def test_validate_thresholds_schema_wrong_type(wrong_type_file):
    """Test that ValueError is raised for wrong type."""
    thresholds = load_detection_thresholds(wrong_type_file)
    with pytest.raises(ValueError) as exc_info:
        validate_thresholds_schema(thresholds)
    assert "has type" in str(exc_info.value)

def test_get_threshold_value(valid_thresholds_file):
    """Test that get_threshold_value retrieves correct values."""
    thresholds = load_detection_thresholds(valid_thresholds_file)
    
    assert get_threshold_value(thresholds, 'audio_energy.speech_presence_db') == -40.0
    assert get_threshold_value(thresholds, 'detection_algorithm.method') == "hybrid"
    assert get_threshold_value(thresholds, 'nonexistent.key', default="default") == "default"
    assert get_threshold_value(thresholds, 'audio_energy.nonexistent', default=100) == 100

def test_schema_check_from_config(valid_thresholds_file):
    """Test that schema validation uses schema_check from config if present."""
    thresholds = load_detection_thresholds(valid_thresholds_file)
    # This should use the schema_check from the config file
    result = validate_thresholds_schema(thresholds)
    assert result is True

def test_default_schema_validation(tmp_path):
    """Test that default schema is used if schema_check is missing."""
    # Create a file without schema_check
    no_schema_yaml = """
    audio_energy:
      speech_presence_db: -40.0
      interruption_energy_db: -15.0
      pause_energy_db: -35.0
    duration:
      min_pause_duration_sec: 0.2
    latent_delta:
      significant_change_threshold: 0.5
    detection_algorithm:
      method: "hybrid"
    """
    file_path = tmp_path / "detection_thresholds.yaml"
    file_path.write_text(no_schema_yaml)
    
    thresholds = load_detection_thresholds(file_path)
    # Should use default schema and pass
    result = validate_thresholds_schema(thresholds)
    assert result is True