"""
Tests for T076: Unity Simulation Fidelity Verification.
"""
import json
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module to test
# We need to ensure the path is set up correctly if running as a script
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.unity_verification import (
    load_reference_config,
    validate_blend_shape_keys,
    validate_blend_shape_ranges,
    validate_salience_mapping,
    verify_fidelity_tolerance,
    log_actual_parameters,
    write_versioned_artifact,
    save_verification_report,
    verify_simulation_fidelity
)
from code.config import get_path


@pytest.fixture
def mock_reference_config():
    """Provide a mock reference configuration."""
    return {
        "version": "1.0",
        "mappings": {
            "story_001": {
                "salience_level": "high",
                "blend_shape_params": {
                    "jawOpen": 0.85,
                    "browLower": 0.90
                }
            },
            "story_006": {
                "salience_level": "low",
                "blend_shape_params": {
                    "jawOpen": 0.10,
                    "browLower": 0.15
                }
            }
        }
    }


@pytest.fixture
def mock_simulated_config(mock_reference_config):
    """Provide a simulated config that matches reference (valid case)."""
    # Slightly modify to test tolerance
    config = mock_reference_config.copy()
    config["mappings"] = {
        "story_001": {
            "salience_level": "high",
            "blend_shape_params": {
                "jawOpen": 0.8501, # Within tolerance
                "browLower": 0.9001
            }
        },
        "story_006": {
            "salience_level": "low",
            "blend_shape_params": {
                "jawOpen": 0.10,
                "browLower": 0.15
            }
        }
    }
    return config


def test_validate_blend_shape_keys_valid():
    sim = {"a": 1, "b": 2}
    ref = {"a": 1, "b": 2}
    valid, errors = validate_blend_shape_keys(sim, ref)
    assert valid is True
    assert len(errors) == 0


def test_validate_blend_shape_keys_missing():
    sim = {"a": 1}
    ref = {"a": 1, "b": 2}
    valid, errors = validate_blend_shape_keys(sim, ref)
    assert valid is False
    assert "Missing keys" in errors[0]


def test_validate_blend_shape_ranges_valid():
    params = {"jawOpen": 0.5}
    valid, errors = validate_blend_shape_ranges(params, "jawOpen")
    assert valid is True


def test_validate_blend_shape_ranges_invalid():
    params = {"jawOpen": 1.5}
    valid, errors = validate_blend_shape_ranges(params, "jawOpen")
    assert valid is False
    assert "out of range" in errors[0]


def test_validate_salience_mapping_valid(mock_reference_config, mock_simulated_config):
    # Use the inner mappings
    ref = mock_reference_config["mappings"]
    sim = mock_simulated_config["mappings"]
    valid, errors = validate_salience_mapping(sim, ref)
    assert valid is True


def test_validate_salience_mapping_mismatch(mock_reference_config):
    ref = mock_reference_config["mappings"]
    # Create a mismatch
    sim = {
        "story_001": {
            "salience_level": "low", # Mismatch: ref is "high"
            "blend_shape_params": {"jawOpen": 0.85}
        }
    }
    valid, errors = validate_salience_mapping(sim, ref)
    assert valid is False
    assert "Salience level mismatch" in errors[0]


def test_verify_fidelity_tolerance_valid(mock_reference_config, mock_simulated_config):
    ref = mock_reference_config["mappings"]
    sim = mock_simulated_config["mappings"]
    valid, errors, devs = verify_fidelity_tolerance(sim, ref)
    assert valid is True
    assert len(errors) == 0


def test_verify_fidelity_tolerance_fail(mock_reference_config):
    ref = mock_reference_config["mappings"]
    sim = {
        "story_001": {
            "salience_level": "high",
            "blend_shape_params": {
                "jawOpen": 0.99 # Deviates significantly from 0.85
            }
        }
    }
    valid, errors, devs = verify_fidelity_tolerance(sim, ref)
    assert valid is False
    assert len(errors) > 0
    assert "deviates" in errors[0]


def test_log_actual_parameters_creates_file(tmp_path):
    # Temporarily override the log path
    original_log_path = "data/logs/simulation_params.log"
    test_log_path = str(tmp_path / "test_params.log")

    mappings = {
        "story_001": {
            "salience_level": "high",
            "blend_shape_params": {"jawOpen": 0.85}
        }
    }

    # We need to patch the get_path or the file writing logic
    # Since log_actual_parameters uses get_path internally, we patch get_path
    with patch('code.data.unity_verification.get_path', return_value=test_log_path):
        log_actual_parameters(mappings)

    assert os.path.exists(test_log_path)
    with open(test_log_path, 'r') as f:
        lines = f.readlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["story_id"] == "story_001"
    assert entry["salience_level"] == "high"


def test_write_versioned_artifact_creates_file(tmp_path):
    test_out_path = str(tmp_path / "test_run_params.yaml")
    mappings = {"story_001": {"salience_level": "high"}}

    with patch('code.data.unity_verification.get_path', return_value=test_out_path):
        write_versioned_artifact(mappings)

    assert os.path.exists(test_out_path)
    with open(test_out_path, 'r') as f:
        data = yaml.safe_load(f)
    assert "parameters" in data
    assert "story_001" in data["parameters"]


def test_save_verification_report_creates_file(tmp_path):
    test_out_path = str(tmp_path / "test_fidelity.yaml")
    with patch('code.data.unity_verification.get_path', return_value=test_out_path):
        save_verification_report(True, ["All good"], {})

    assert os.path.exists(test_out_path)
    with open(test_out_path, 'r') as f:
        data = yaml.safe_load(f)
    assert data["status"] == "pass"