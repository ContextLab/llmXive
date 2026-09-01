import pytest
from pydantic import ValidationError
import os
import yaml
from datetime import datetime

# Import the models from the implementation
from code.utils.schema_validation import (
    ConfigSchema,
    OutputSchema,
    Metadata,
    ConfigSnapshot,
    FunctionSample,
    StatisticalTests,
    ModelResults,
    Summary,
    validate_config,
    validate_output
)

class TestConfigSchema:
    def test_valid_config(self):
        config_data = {
            "hf_api_key": "hf_1234567890abcdef",
            "random_seed": 42,
            "max_attempts": 400,
            "min_valid_functions": 100,
            "batch_size": 10
        }
        config = ConfigSchema(**config_data)
        assert config.hf_api_key == "hf_1234567890abcdef"
        assert config.random_seed == 42
        assert config.batch_size == 10

    def test_invalid_api_key_prefix(self):
        config_data = {
            "hf_api_key": "invalid_key",
            "random_seed": 42,
            "max_attempts": 400,
            "min_valid_functions": 100,
            "batch_size": 10
        }
        with pytest.raises(ValidationError):
            ConfigSchema(**config_data)

    def test_invalid_batch_size(self):
        config_data = {
            "hf_api_key": "hf_1234567890abcdef",
            "random_seed": 42,
            "max_attempts": 400,
            "min_valid_functions": 100,
            "batch_size": 15  # Max is 10
        }
        with pytest.raises(ValidationError):
            ConfigSchema(**config_data)

    def test_missing_required_field(self):
        config_data = {
            "random_seed": 42,
            "max_attempts": 400,
            "min_valid_functions": 100,
            "batch_size": 10
        }
        with pytest.raises(ValidationError):
            ConfigSchema(**config_data)

class TestOutputSchema:
    def test_valid_output(self):
        output_data = {
            "metadata": {
                "version": "1.0.0",
                "generated_at": datetime.now().isoformat()
            },
            "config_snapshot": {
                "hf_api_key_masked": "hf_***",
                "random_seed": 42,
                "max_attempts": 400,
                "min_valid_functions": 100,
                "batch_size": 10,
                "timestamp": datetime.now().isoformat()
            },
            "data": [
                {
                    "code": "def hello(): pass",
                    "metrics": {"loc": 1},
                    "hash": "abc123",
                    "status": "success"
                }
            ],
            "statistics": {},
            "models": {},
            "summary": {
                "total_functions": 1,
                "valid_functions": 1,
                "primary_test": "paired",
                "significant": True,
                "p_value": 0.01
            }
        }
        output = OutputSchema(**output_data)
        assert len(output.data) == 1
        assert output.summary.total_functions == 1

    def test_empty_data_list(self):
        output_data = {
            "metadata": {
                "version": "1.0.0",
                "generated_at": datetime.now().isoformat()
            },
            "config_snapshot": {
                "hf_api_key_masked": "hf_***",
                "random_seed": 42,
                "max_attempts": 400,
                "min_valid_functions": 100,
                "batch_size": 10,
                "timestamp": datetime.now().isoformat()
            },
            "data": [],
            "statistics": {},
            "models": {},
            "summary": {
                "total_functions": 0,
                "valid_functions": 0,
                "primary_test": "paired",
                "significant": False,
                "p_value": 1.0
            }
        }
        with pytest.raises(ValidationError):
            OutputSchema(**output_data)

class TestValidationFunctions:
    def test_validate_config_success(self):
        data = {
            "hf_api_key": "hf_test",
            "random_seed": 1,
            "max_attempts": 10,
            "min_valid_functions": 1,
            "batch_size": 1
        }
        result = validate_config(data)
        assert isinstance(result, ConfigSchema)

    def test_validate_config_failure(self):
        data = {
            "hf_api_key": "bad",
            "random_seed": 1,
            "max_attempts": 10,
            "min_valid_functions": 1,
            "batch_size": 1
        }
        with pytest.raises(ValidationError):
            validate_config(data)

    def test_validate_output_success(self):
        data = {
            "metadata": {"version": "1.0", "generated_at": "2023-01-01T00:00:00"},
            "config_snapshot": {
                "hf_api_key_masked": "hf_***",
                "random_seed": 1,
                "max_attempts": 10,
                "min_valid_functions": 1,
                "batch_size": 1,
                "timestamp": "2023-01-01T00:00:00"
            },
            "data": [{"code": "x=1", "metrics": {}, "hash": "h", "status": "ok"}],
            "statistics": {},
            "models": {},
            "summary": {
                "total_functions": 1,
                "valid_functions": 1,
                "primary_test": "paired",
                "significant": True,
                "p_value": 0.05
            }
        }
        result = validate_output(data)
        assert isinstance(result, OutputSchema)