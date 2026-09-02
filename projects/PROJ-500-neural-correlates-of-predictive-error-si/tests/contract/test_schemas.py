"""
Contract tests for data schemas (T009, T012, T019, T027).
Validates that generated artifacts conform to the YAML schemas defined in contracts/.
"""
import json
import os
import pytest
from pathlib import Path
import yaml

# Helper to load schema
def load_schema(schema_path: str):
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

# Helper to validate data against schema (simple check for required fields and types)
def validate_json_against_schema(data: dict, schema: dict, path_prefix: str = ""):
    errors = []
    
    # Check required fields
    if "required" in schema:
        for field in schema["required"]:
            if field not in data:
                errors.append(f"Missing required field: {path_prefix}.{field}")
    
    # Check properties
    if "properties" in schema:
        for key, value in data.items():
            if key in schema["properties"]:
                prop_schema = schema["properties"][key]
                # Type check
                if "type" in prop_schema:
                    expected_type = prop_schema["type"]
                    if expected_type == "string" and not isinstance(value, str):
                        errors.append(f"Type mismatch at {path_prefix}.{key}: expected string, got {type(value).__name__}")
                    elif expected_type == "integer" and not isinstance(value, int):
                        errors.append(f"Type mismatch at {path_prefix}.{key}: expected integer, got {type(value).__name__}")
                    elif expected_type == "number":
                        if not isinstance(value, (int, float)):
                            errors.append(f"Type mismatch at {path_prefix}.{key}: expected number, got {type(value).__name__}")
                    elif expected_type == "array" and not isinstance(value, list):
                        errors.append(f"Type mismatch at {path_prefix}.{key}: expected array, got {type(value).__name__}")
                    elif expected_type == "object" and not isinstance(value, dict):
                        errors.append(f"Type mismatch at {path_prefix}.{key}: expected object, got {type(value).__name__}")
            
    return errors

class TestSchemas:
    """Contract tests for T009 schemas."""

    @pytest.fixture
    def contracts_dir(self):
        return Path(__file__).parent.parent.parent / "contracts"

    def test_aligned_data_schema_exists(self, contracts_dir):
        """Verify aligned_data.schema.yaml exists."""
        path = contracts_dir / "aligned_data.schema.yaml"
        assert path.exists(), f"Schema file missing: {path}"

    def test_model_output_schema_exists(self, contracts_dir):
        """Verify model_output.schema.yaml exists."""
        path = contracts_dir / "model_output.schema.yaml"
        assert path.exists(), f"Schema file missing: {path}"

    def test_aligned_data_schema_valid_syntax(self, contracts_dir):
        """Verify aligned_data.schema.yaml is valid YAML."""
        path = contracts_dir / "aligned_data.schema.yaml"
        try:
            schema = load_schema(str(path))
            assert "properties" in schema
            assert "required" in schema
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in aligned_data.schema.yaml: {e}")

    def test_model_output_schema_valid_syntax(self, contracts_dir):
        """Verify model_output.schema.yaml is valid YAML."""
        path = contracts_dir / "model_output.schema.yaml"
        try:
            schema = load_schema(str(path))
            assert "properties" in schema
            assert "required" in schema
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in model_output.schema.yaml: {e}")

    def test_validate_mock_aligned_data(self, contracts_dir, tmp_path):
        """Test validation logic against a mock aligned_data record."""
        schema = load_schema(str(contracts_dir / "aligned_data.schema.yaml"))
        
        mock_data = {
            "subject_id": "sub-001",
            "block_id": 1,
            "mmn_amplitude": 2.5,
            "source_window_start_trial": 50,
            "analysis_mode": "error_signal",
            "block_accuracy": 85.0,
            "n_trials_valid": 45,
            "electrode_set": ["CP3", "CP4", "C3", "C4"],
            "timestamp": "2023-10-27T10:00:00Z"
        }
        
        errors = validate_json_against_schema(mock_data, schema)
        assert len(errors) == 0, f"Validation failed for mock aligned_data: {errors}"

    def test_validate_mock_model_output(self, contracts_dir, tmp_path):
        """Test validation logic against a mock model_output record."""
        schema = load_schema(str(contracts_dir / "model_output.schema.yaml"))
        
        mock_data = {
            "model_type": "Gaussian LME",
            "formula": "MMN_Amplitude ~ Accuracy + Learning_Phase + (1|Subject)",
            "coefficients": {
                "Intercept": {
                    "estimate": 1.2,
                    "std_error": 0.1,
                    "t_value": 12.0,
                    "p_value": 0.001,
                    "p_value_fdr": 0.002
                }
            },
            "permutation_test": {
                "n_permutations": 1000,
                "p_value": 0.005,
                "observed_statistic": 1.2,
                "null_distribution_stats": {
                    "mean": 0.0,
                    "std": 0.5
                }
            },
            "robustness_metrics": {
                "time_window_sweep": [
                    {
                        "window_range": "140-240ms",
                        "coefficient_change_percent": 2.1
                    }
                ]
            },
            "metadata": {
                "generated_at": "2023-10-27T10:00:00Z",
                "input_file": "data/aligned_data.csv",
                "subjects_included": 25,
                "subjects_excluded": [],
                "total_rows": 500
            }
        }
        
        errors = validate_json_against_schema(mock_data, schema)
        assert len(errors) == 0, f"Validation failed for mock model_output: {errors}"