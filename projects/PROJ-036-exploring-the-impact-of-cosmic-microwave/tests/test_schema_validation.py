"""
Tests for schema validation functionality.

These tests verify that:
1. The schema file exists and is valid YAML
2. Valid output data passes validation
3. Invalid output data fails validation with appropriate errors
4. The validator correctly identifies missing required fields
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from utils.schema_validator import (
    load_schema,
    validate_output,
    validate_json_file,
    validate_and_log,
)


@pytest.fixture
def schema_path():
    """Return the path to the CMB-LSS schema file."""
    return Path("contracts/cmb_lss_schema.schema.yaml")


@pytest.fixture
def valid_output_data():
    """Return a valid output data structure."""
    return {
        "metadata": {
            "run_id": "run_12345678",
            "timestamp": "2024-01-15T10:30:00Z",
            "simulation_config": {
                "nbody_resolution": 128,
                "box_size_hinv_mpc": 250,
                "cosmology_model": "anomaly_modified",
                "power_spectrum_source": "CAMB"
            },
            "input_data_hashes": {
                "ic_file_sha256": "a" * 64,
                "mask_file_sha256": "b" * 64,
                "planck_map_sha256": "c" * 64
            }
        },
        "statistics": {
            "power_spectrum": {
                "k_values_h_mpc": [0.01, 0.1, 1.0],
                "p_k_anomaly": [100.0, 50.0, 10.0],
                "p_k_control": [102.0, 51.0, 10.5],
                "delta_p_k": [-2.0, -1.0, -0.5],
                "relative_deviation": [-0.0196, -0.0196, -0.0476],
                "low_ell_deviation": {
                    "max_deviation_percent": 5.0,
                    "mean_deviation_percent": 2.5,
                    "deviation_at_l30": 3.2
                }
            },
            "void_statistics": {
                "void_radii_mpch": [5.0, 10.0, 15.0],
                "count_anomaly": [10, 5, 2],
                "count_control": [12, 6, 3],
                "ks_statistic": 0.2,
                "ks_p_value": 0.15,
                "chi_squared": 1.5,
                "chi_squared_p_value": 0.47
            },
            "diagnostic_tests": {
                "ks_test": {
                    "statistic": 0.2,
                    "p_value": 0.15,
                    "corrected_p_value": 0.15,
                    "is_significant": False
                },
                "chi_squared_test": {
                    "statistic": 1.5,
                    "degrees_of_freedom": 2,
                    "p_value": 0.47,
                    "corrected_p_value": 0.47
                },
                "benjamini_hochberg": {
                    "alpha_threshold": 0.05,
                    "num_tests": 2,
                    "num_rejections": 0,
                    "critical_values": [0.025, 0.05]
                }
            },
            "classification": "diagnostic"
        },
        "execution_metrics": {
            "wall_clock_time_seconds": 3600.5,
            "peak_memory_gb": 5.2,
            "cpu_utilization": 85.0
        }
    }


@pytest.fixture
def invalid_output_data_missing_field():
    """Return invalid data missing a required field."""
    return {
        "metadata": {
            "run_id": "run_12345678",
            "timestamp": "2024-01-15T10:30:00Z",
            "simulation_config": {
                "nbody_resolution": 128,
                "box_size_hinv_mpc": 250,
                "cosmology_model": "anomaly_modified",
                "power_spectrum_source": "CAMB"
            },
            "input_data_hashes": {
                "ic_file_sha256": "a" * 64,
                "mask_file_sha256": "b" * 64,
                "planck_map_sha256": "c" * 64
            }
        },
        "statistics": {
            "power_spectrum": {
                "k_values_h_mpc": [0.01, 0.1, 1.0],
                "p_k_anomaly": [100.0, 50.0, 10.0],
                "p_k_control": [102.0, 51.0, 10.5],
                "delta_p_k": [-2.0, -1.0, -0.5],
                "relative_deviation": [-0.0196, -0.0196, -0.0476],
                "low_ell_deviation": {
                    "max_deviation_percent": 5.0,
                    "mean_deviation_percent": 2.5,
                    "deviation_at_l30": 3.2
                }
            },
            "void_statistics": {
                "void_radii_mpch": [5.0, 10.0, 15.0],
                "count_anomaly": [10, 5, 2],
                "count_control": [12, 6, 3],
                "ks_statistic": 0.2,
                "ks_p_value": 0.15,
                "chi_squared": 1.5,
                "chi_squared_p_value": 0.47
            },
            "diagnostic_tests": {
                "ks_test": {
                    "statistic": 0.2,
                    "p_value": 0.15,
                    "corrected_p_value": 0.15,
                    "is_significant": False
                },
                "chi_squared_test": {
                    "statistic": 1.5,
                    "degrees_of_freedom": 2,
                    "p_value": 0.47,
                    "corrected_p_value": 0.47
                },
                "benjamini_hochberg": {
                    "alpha_threshold": 0.05,
                    "num_tests": 2,
                    "num_rejections": 0,
                    "critical_values": [0.025, 0.05]
                }
            },
            "classification": "diagnostic"
        }
        # Missing "execution_metrics"
    }


@pytest.fixture
def invalid_output_data_bad_hash():
    """Return invalid data with malformed hash."""
    return {
        "metadata": {
            "run_id": "run_12345678",
            "timestamp": "2024-01-15T10:30:00Z",
            "simulation_config": {
                "nbody_resolution": 128,
                "box_size_hinv_mpc": 250,
                "cosmology_model": "anomaly_modified",
                "power_spectrum_source": "CAMB"
            },
            "input_data_hashes": {
                "ic_file_sha256": "short_hash",  # Invalid: not 64 hex chars
                "mask_file_sha256": "b" * 64,
                "planck_map_sha256": "c" * 64
            }
        },
        "statistics": {
            "power_spectrum": {
                "k_values_h_mpc": [0.01, 0.1, 1.0],
                "p_k_anomaly": [100.0, 50.0, 10.0],
                "p_k_control": [102.0, 51.0, 10.5],
                "delta_p_k": [-2.0, -1.0, -0.5],
                "relative_deviation": [-0.0196, -0.0196, -0.0476],
                "low_ell_deviation": {
                    "max_deviation_percent": 5.0,
                    "mean_deviation_percent": 2.5,
                    "deviation_at_l30": 3.2
                }
            },
            "void_statistics": {
                "void_radii_mpch": [5.0, 10.0, 15.0],
                "count_anomaly": [10, 5, 2],
                "count_control": [12, 6, 3],
                "ks_statistic": 0.2,
                "ks_p_value": 0.15,
                "chi_squared": 1.5,
                "chi_squared_p_value": 0.47
            },
            "diagnostic_tests": {
                "ks_test": {
                    "statistic": 0.2,
                    "p_value": 0.15,
                    "corrected_p_value": 0.15,
                    "is_significant": False
                },
                "chi_squared_test": {
                    "statistic": 1.5,
                    "degrees_of_freedom": 2,
                    "p_value": 0.47,
                    "corrected_p_value": 0.47
                },
                "benjamini_hochberg": {
                    "alpha_threshold": 0.05,
                    "num_tests": 2,
                    "num_rejections": 0,
                    "critical_values": [0.025, 0.05]
                }
            },
            "classification": "diagnostic"
        },
        "execution_metrics": {
            "wall_clock_time_seconds": 3600.5,
            "peak_memory_gb": 5.2,
            "cpu_utilization": 85.0
        }
    }


def test_schema_file_exists(schema_path):
    """Test that the schema file exists."""
    assert schema_path.exists(), "Schema file contracts/cmb_lss_schema.schema.yaml not found"


def test_schema_is_valid_yaml(schema_path):
    """Test that the schema file is valid YAML."""
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    assert isinstance(schema, dict), "Schema must be a dictionary"
    assert "$schema" in schema, "Schema must define $schema"
    assert "properties" in schema, "Schema must define properties"


def test_valid_data_passes_validation(valid_output_data, schema_path):
    """Test that valid data passes schema validation."""
    schema = load_schema(schema_path)
    is_valid, error_msg = validate_output(valid_output_data, schema)
    assert is_valid, f"Valid data should pass validation. Error: {error_msg}"


def test_missing_required_field_fails(invalid_output_data_missing_field, schema_path):
    """Test that missing required fields cause validation failure."""
    schema = load_schema(schema_path)
    is_valid, error_msg = validate_output(invalid_output_data_missing_field, schema)
    assert not is_valid, "Missing required field should fail validation"
    assert "execution_metrics" in error_msg or "required" in error_msg.lower(), \
        f"Error should mention missing field: {error_msg}"


def test_bad_hash_format_fails(invalid_output_data_bad_hash, schema_path):
    """Test that malformed hash values cause validation failure."""
    schema = load_schema(schema_path)
    is_valid, error_msg = validate_output(invalid_output_data_bad_hash, schema)
    assert not is_valid, "Bad hash format should fail validation"


def test_validate_json_file_with_valid_data(valid_output_data, schema_path, tmp_path):
    """Test validate_json_file with a valid JSON file."""
    output_file = tmp_path / "valid_output.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(valid_output_data, f)

    is_valid, error_msg = validate_json_file(output_file, schema_path)
    assert is_valid, f"Valid file should pass: {error_msg}"


def test_validate_json_file_with_invalid_data(invalid_output_data_missing_field, schema_path, tmp_path):
    """Test validate_json_file with an invalid JSON file."""
    output_file = tmp_path / "invalid_output.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(invalid_output_data_missing_field, f)

    is_valid, error_msg = validate_json_file(output_file, schema_path)
    assert not is_valid, "Invalid file should fail validation"
    assert error_msg is not None, "Error message should be present"


def test_validate_json_file_not_found(schema_path, tmp_path):
    """Test validate_json_file with a non-existent file."""
    fake_path = tmp_path / "nonexistent.json"
    is_valid, error_msg = validate_json_file(fake_path, schema_path)
    assert not is_valid
    assert "not found" in error_msg.lower()


def test_validate_and_log_valid(valid_output_data, schema_path, tmp_path, caplog):
    """Test validate_and_log with valid data."""
    output_file = tmp_path / "valid_output.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(valid_output_data, f)

    result = validate_and_log(output_file, schema_path)
    assert result is True
    assert "Validation passed" in caplog.text


def test_validate_and_log_invalid(invalid_output_data_missing_field, schema_path, tmp_path, caplog):
    """Test validate_and_log with invalid data."""
    output_file = tmp_path / "invalid_output.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(invalid_output_data_missing_field, f)

    result = validate_and_log(output_file, schema_path)
    assert result is False
    assert "Validation failed" in caplog.text