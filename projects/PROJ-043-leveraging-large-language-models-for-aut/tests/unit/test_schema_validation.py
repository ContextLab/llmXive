"""
Unit tests for schema validation logic.
"""
import json
import pytest
from pathlib import Path
from datetime import datetime

from utils.schema_validation import (
    validate_config,
    validate_output,
    validate_config_from_env,
    validate_json_file,
    ConfigSchema,
    OutputSchema,
    ConfigSnapshot,
    Metadata,
    Statistics,
    ModelResults,
    PairedTTestResult,
    StatisticalTests
)

class TestConfigValidation:
    def test_valid_config(self):
        data = {
            "hf_api_key": "test-key-123",
            "random_seed": 42,
            "max_attempts": 50,
            "min_valid_functions": 100,
            "batch_size": 10,
            "log_level": "INFO"
        }
        result = validate_config(data)
        assert result.hf_api_key == "test-key-123"
        assert result.random_seed == 42
        assert result.log_level == "INFO"

    def test_invalid_log_level(self):
        data = {
            "hf_api_key": "test-key",
            "random_seed": 42,
            "max_attempts": 50,
            "min_valid_functions": 100,
            "batch_size": 10,
            "log_level": "INVALID"
        }
        with pytest.raises(ValueError) as exc_info:
            validate_config(data)
        assert "Invalid log_level" in str(exc_info.value)

    def test_missing_required_field(self):
        data = {
            "hf_api_key": "test-key",
            "random_seed": 42,
            # missing max_attempts
            "min_valid_functions": 100,
            "batch_size": 10,
            "log_level": "INFO"
        }
        with pytest.raises(ValueError):
            validate_config(data)

    def test_env_validation(self):
        env = {
            "HF_API_KEY": "env-key",
            "RANDOM_SEED": "123",
            "MAX_ATTEMPTS": "20",
            "MIN_VALID_FUNCTIONS": "50",
            "BATCH_SIZE": "5",
            "LOG_LEVEL": "DEBUG"
        }
        result = validate_config_from_env(env)
        assert result.hf_api_key == "env-key"
        assert result.random_seed == 123
        assert result.log_level == "DEBUG"

class TestOutputValidation:
    def test_valid_output(self):
        data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "config_snapshot": {
                    "random_seed": 42,
                    "max_attempts": 50,
                    "min_valid_functions": 100,
                    "batch_size": 10
                }
            },
            "statistics": {
                "total_samples": 200,
                "valid_samples": 150,
                "refactoring_success_rate": 0.85
            },
            "model_results": {
                "adjusted_r2": 0.75,
                "predictors": ["loc", "nesting"],
                "coefficients": {"loc": 0.5, "nesting": -0.2},
                "cross_validation_mean_coefficients": {"loc": 0.48, "nesting": -0.22}
            },
            "statistical_tests": {
                "complexity_delta": {"t_statistic": 2.5, "p_value": 0.01, "significant": True},
                "pylint_delta": {"t_statistic": -1.5, "p_value": 0.15, "significant": False},
                "maintainability_delta": {"t_statistic": 3.0, "p_value": 0.002, "significant": True}
            }
        }
        result = validate_output(data)
        assert result.statistics.refactoring_success_rate == 0.85
        assert result.model_results.adjusted_r2 == 0.75

    def test_invalid_success_rate(self):
        data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "config_snapshot": {
                    "random_seed": 42,
                    "max_attempts": 50,
                    "min_valid_functions": 100,
                    "batch_size": 10
                }
            },
            "statistics": {
                "total_samples": 200,
                "valid_samples": 150,
                "refactoring_success_rate": 1.5  # Invalid
            },
            "model_results": {
                "adjusted_r2": 0.75,
                "predictors": ["loc"],
                "coefficients": {"loc": 0.5},
                "cross_validation_mean_coefficients": {"loc": 0.48}
            },
            "statistical_tests": {
                "complexity_delta": {"t_statistic": 2.5, "p_value": 0.01, "significant": True},
                "pylint_delta": {"t_statistic": -1.5, "p_value": 0.15, "significant": False},
                "maintainability_delta": {"t_statistic": 3.0, "p_value": 0.002, "significant": True}
            }
        }
        with pytest.raises(ValueError) as exc_info:
            validate_output(data)
        assert "refactoring_success_rate" in str(exc_info.value)

    def test_missing_metadata(self):
        data = {
            "statistics": {
                "total_samples": 200,
                "valid_samples": 150,
                "refactoring_success_rate": 0.85
            },
            "model_results": {
                "adjusted_r2": 0.75,
                "predictors": ["loc"],
                "coefficients": {"loc": 0.5},
                "cross_validation_mean_coefficients": {"loc": 0.48}
            },
            "statistical_tests": {
                "complexity_delta": {"t_statistic": 2.5, "p_value": 0.01, "significant": True},
                "pylint_delta": {"t_statistic": -1.5, "p_value": 0.15, "significant": False},
                "maintainability_delta": {"t_statistic": 3.0, "p_value": 0.002, "significant": True}
            }
        }
        with pytest.raises(ValueError):
            validate_output(data)

class TestJsonFileValidation:
    def test_validate_config_file(self, tmp_path):
        config_data = {
            "hf_api_key": "file-key",
            "random_seed": 99,
            "max_attempts": 10,
            "min_valid_functions": 5,
            "batch_size": 2,
            "log_level": "ERROR"
        }
        file_path = tmp_path / "config.json"
        file_path.write_text(json.dumps(config_data))
        
        result = validate_json_file(str(file_path), schema_type='config')
        assert result['hf_api_key'] == "file-key"

    def test_validate_output_file(self, tmp_path):
        output_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "config_snapshot": {
                    "random_seed": 42,
                    "max_attempts": 50,
                    "min_valid_functions": 100,
                    "batch_size": 10
                }
            },
            "statistics": {
                "total_samples": 100,
                "valid_samples": 90,
                "refactoring_success_rate": 0.9
            },
            "model_results": {
                "adjusted_r2": 0.8,
                "predictors": ["loc"],
                "coefficients": {"loc": 0.1},
                "cross_validation_mean_coefficients": {"loc": 0.1}
            },
            "statistical_tests": {
                "complexity_delta": {"t_statistic": 1.0, "p_value": 0.5, "significant": False},
                "pylint_delta": {"t_statistic": 1.0, "p_value": 0.5, "significant": False},
                "maintainability_delta": {"t_statistic": 1.0, "p_value": 0.5, "significant": False}
            }
        }
        file_path = tmp_path / "output.json"
        file_path.write_text(json.dumps(output_data))
        
        result = validate_json_file(str(file_path), schema_type='output')
        assert result['statistics']['total_samples'] == 100

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            validate_json_file(str(tmp_path / "nonexistent.json"))

    def test_invalid_json(self, tmp_path):
        file_path = tmp_path / "bad.json"
        file_path.write_text("not valid json {")
        with pytest.raises(json.JSONDecodeError):
            validate_json_file(str(file_path))