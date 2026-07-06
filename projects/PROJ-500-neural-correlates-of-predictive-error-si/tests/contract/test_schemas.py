"""
Contract tests for data schemas used in the Neural Correlates of Predictive Error Signals pipeline.

This module validates that data artifacts produced by the pipeline conform to the
expected schema definitions, ensuring data integrity and traceability.
"""
import json
import os
import sys
import pytest
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path if running standalone
if "code" not in sys.path[0]:
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root / "code"))

from src.utils.config import get_config

# Schema definitions
ALIGNED_DATA_SCHEMA = {
    "required_columns": [
        "subject_id",
        "block_id",
        "mmn_amplitude",
        "accuracy",
        "analysis_mode",
        "source_window_start_trial",
        "timestamp"
    ],
    "optional_columns": [
        "learning_phase",
        "trial_count",
        "artifact_rejection_rate"
    ],
    "column_types": {
        "subject_id": str,
        "block_id": (int, str),
        "mmn_amplitude": (float, int),
        "accuracy": float,
        "analysis_mode": str,
        "source_window_start_trial": int,
        "timestamp": str
    },
    "valid_analysis_modes": ["error_signal", "stimulus_driven"]
}

MODEL_OUTPUT_SCHEMA = {
    "required_keys": [
        "model_type",
        "formula",
        "coefficients",
        "p_values",
        "fdr_corrected_p_values",
        "permutation_test_p_value",
        "subject_count",
        "trial_count",
        "model_fit_metrics"
    ],
    "optional_keys": [
        "sensitivity_analysis",
        "convergence_warnings"
    ],
    "structure": {
        "coefficients": dict,
        "p_values": dict,
        "fdr_corrected_p_values": dict,
        "permutation_test_p_value": float,
        "model_fit_metrics": dict
    }
}

VALIDATION_REPORT_SCHEMA = {
    "required_keys": [
        "analysis_mode",
        "dataset_metadata",
        "variable_check",
        "underpowered_subjects",
        "excluded_subjects"
    ],
    "optional_keys": [
        "preprocessing_summary",
        "artifact_rejection_summary"
    ],
    "structure": {
        "analysis_mode": str,
        "dataset_metadata": dict,
        "variable_check": dict,
        "underpowered_subjects": list,
        "excluded_subjects": list
    }
}

INTERIM_LAGGED_MMNS_SCHEMA = {
    "required_columns": [
        "subject_id",
        "block_id",
        "mmn_amplitude",
        "source_window_start_trial"
    ],
    "optional_columns": [
        "window_end_trial",
        "trial_count_in_window"
    ],
    "column_types": {
        "subject_id": str,
        "block_id": (int, str),
        "mmn_amplitude": (float, int),
        "source_window_start_trial": int
    }
}


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load and return JSON data from a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)


def load_csv_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load CSV file and return as list of dictionaries."""
    import csv
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)


def validate_schema(data: Any, schema: Dict[str, Any], data_type: str) -> List[str]:
    """
    Validate data against a schema definition.
    
    Args:
        data: The data to validate (dict for JSON, list of dicts for CSV)
        schema: The schema definition
        data_type: Type of data being validated ('json' or 'csv')
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    if data_type == 'json':
        if not isinstance(data, dict):
            errors.append(f"Expected JSON data to be a dict, got {type(data).__name__}")
            return errors
        
        # Check required keys
        if 'required_keys' in schema:
            missing_keys = set(schema['required_keys']) - set(data.keys())
            if missing_keys:
                errors.append(f"Missing required keys: {missing_keys}")
        
        # Check structure types
        if 'structure' in schema:
            for key, expected_type in schema['structure'].items():
                if key in data:
                    if isinstance(expected_type, tuple):
                        if not isinstance(data[key], expected_type):
                            errors.append(f"Key '{key}' should be one of {expected_type}, got {type(data[key]).__name__}")
                    elif not isinstance(data[key], expected_type):
                        errors.append(f"Key '{key}' should be {expected_type.__name__}, got {type(data[key]).__name__}")
    
    elif data_type == 'csv':
        if not isinstance(data, list):
            errors.append(f"Expected CSV data to be a list of dicts, got {type(data).__name__}")
            return errors
        
        if len(data) == 0:
            errors.append("CSV file is empty")
            return errors
        
        first_row = data[0]
        
        # Check required columns
        if 'required_columns' in schema:
            missing_cols = set(schema['required_columns']) - set(first_row.keys())
            if missing_cols:
                errors.append(f"Missing required columns: {missing_cols}")
        
        # Check column types
        if 'column_types' in schema:
            for col, expected_type in schema['column_types'].items():
                if col in first_row:
                    # Try to convert and check type
                    value = first_row[col]
                    if isinstance(expected_type, tuple):
                        valid = False
                        for t in expected_type:
                            try:
                                if t == str:
                                    valid = True
                                    break
                                elif t == int:
                                    int(value)
                                    valid = True
                                    break
                                elif t == float:
                                    float(value)
                                    valid = True
                                    break
                            except (ValueError, TypeError):
                                continue
                        if not valid:
                            errors.append(f"Column '{col}' should be one of {expected_type}, got {type(value).__name__}")
                    else:
                        try:
                            if expected_type == str:
                                pass  # All CSV values are strings
                            elif expected_type == int:
                                int(value)
                            elif expected_type == float:
                                float(value)
                        except (ValueError, TypeError):
                            errors.append(f"Column '{col}' should be {expected_type.__name__}, got {type(value).__name__}")
        
        # Check valid analysis modes if applicable
        if 'valid_analysis_modes' in schema and 'analysis_mode' in first_row:
            valid_modes = schema['valid_analysis_modes']
            for row in data:
                if 'analysis_mode' in row and row['analysis_mode'] not in valid_modes:
                    errors.append(f"Invalid analysis_mode: {row['analysis_mode']}. Expected one of {valid_modes}")
                    break
    
    return errors


class TestAlignedDataSchema:
    """Contract tests for the aligned_data.csv schema."""
    
    @pytest.fixture
    def sample_aligned_data(self) -> List[Dict[str, Any]]:
        """Create sample aligned data that conforms to the schema."""
        return [
            {
                "subject_id": "sub-001",
                "block_id": "1",
                "mmn_amplitude": -2.45,
                "accuracy": 0.85,
                "analysis_mode": "error_signal",
                "source_window_start_trial": 10,
                "timestamp": "2024-01-15T10:30:00Z",
                "learning_phase": "early"
            },
            {
                "subject_id": "sub-001",
                "block_id": "2",
                "mmn_amplitude": -3.12,
                "accuracy": 0.92,
                "analysis_mode": "error_signal",
                "source_window_start_trial": 60,
                "timestamp": "2024-01-15T10:35:00Z",
                "learning_phase": "late"
            }
        ]
    
    def test_aligned_data_schema_valid(self, sample_aligned_data):
        """Test that valid aligned data passes schema validation."""
        errors = validate_schema(sample_aligned_data, ALIGNED_DATA_SCHEMA, 'csv')
        assert len(errors) == 0, f"Valid data failed validation: {errors}"
    
    def test_aligned_data_missing_required_columns(self):
        """Test that missing required columns are detected."""
        invalid_data = [
            {
                "subject_id": "sub-001",
                "block_id": "1",
                # Missing mmn_amplitude, accuracy, etc.
            }
        ]
        errors = validate_schema(invalid_data, ALIGNED_DATA_SCHEMA, 'csv')
        assert len(errors) > 0
        assert any("Missing required columns" in e for e in errors)
    
    def test_aligned_data_invalid_analysis_mode(self):
        """Test that invalid analysis_mode values are detected."""
        invalid_data = [
            {
                "subject_id": "sub-001",
                "block_id": "1",
                "mmn_amplitude": -2.45,
                "accuracy": 0.85,
                "analysis_mode": "invalid_mode",
                "source_window_start_trial": 10,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        ]
        errors = validate_schema(invalid_data, ALIGNED_DATA_SCHEMA, 'csv')
        assert len(errors) > 0
        assert any("Invalid analysis_mode" in e for e in errors)
    
    @pytest.mark.skipif(not Path("data/aligned_data.csv").exists(), reason="aligned_data.csv not generated yet")
    def test_real_aligned_data_conforms(self):
        """Test that the actual aligned_data.csv file conforms to the schema."""
        data = load_csv_file(Path("data/aligned_data.csv"))
        errors = validate_schema(data, ALIGNED_DATA_SCHEMA, 'csv')
        assert len(errors) == 0, f"Real aligned_data.csv failed validation: {errors}"


class TestModelOutputSchema:
    """Contract tests for the model_output.json schema."""
    
    @pytest.fixture
    def sample_model_output(self) -> Dict[str, Any]:
        """Create sample model output that conforms to the schema."""
        return {
            "model_type": "GaussianLME",
            "formula": "MMN_Amplitude ~ Accuracy + Learning_Phase + (1|Subject)",
            "coefficients": {
                "Intercept": 0.5,
                "Accuracy": -2.3,
                "Learning_Phase": 0.8
            },
            "p_values": {
                "Intercept": 0.001,
                "Accuracy": 0.02,
                "Learning_Phase": 0.15
            },
            "fdr_corrected_p_values": {
                "Intercept": 0.001,
                "Accuracy": 0.03,
                "Learning_Phase": 0.15
            },
            "permutation_test_p_value": 0.045,
            "subject_count": 25,
            "trial_count": 1500,
            "model_fit_metrics": {
                "AIC": 1250.5,
                "BIC": 1280.3,
                "log_likelihood": -620.2
            }
        }
    
    def test_model_output_schema_valid(self, sample_model_output):
        """Test that valid model output passes schema validation."""
        errors = validate_schema(sample_model_output, MODEL_OUTPUT_SCHEMA, 'json')
        assert len(errors) == 0, f"Valid data failed validation: {errors}"
    
    def test_model_output_missing_required_keys(self):
        """Test that missing required keys are detected."""
        invalid_data = {
            "model_type": "GaussianLME",
            # Missing many required keys
        }
        errors = validate_schema(invalid_data, MODEL_OUTPUT_SCHEMA, 'json')
        assert len(errors) > 0
        assert any("Missing required keys" in e for e in errors)
    
    def test_model_output_invalid_structure(self):
        """Test that invalid structure types are detected."""
        invalid_data = {
            "model_type": "GaussianLME",
            "formula": "MMN ~ Acc",
            "coefficients": "not_a_dict",  # Should be dict
            "p_values": {},
            "fdr_corrected_p_values": {},
            "permutation_test_p_value": "not_a_float",  # Should be float
            "subject_count": 25,
            "trial_count": 1500,
            "model_fit_metrics": {}
        }
        errors = validate_schema(invalid_data, MODEL_OUTPUT_SCHEMA, 'json')
        assert len(errors) > 0
    
    @pytest.mark.skipif(not Path("analysis/results/model_output.json").exists(), reason="model_output.json not generated yet")
    def test_real_model_output_conforms(self):
        """Test that the actual model_output.json file conforms to the schema."""
        data = load_json_file(Path("analysis/results/model_output.json"))
        errors = validate_schema(data, MODEL_OUTPUT_SCHEMA, 'json')
        assert len(errors) == 0, f"Real model_output.json failed validation: {errors}"


class TestValidationReportSchema:
    """Contract tests for the validation_report.json schema."""
    
    @pytest.fixture
    def sample_validation_report(self) -> Dict[str, Any]:
        """Create sample validation report that conforms to the schema."""
        return {
            "analysis_mode": "error_signal",
            "dataset_metadata": {
                "source": "OpenNeuro",
                "dataset_id": "ds001234",
                "subject_count": 30
            },
            "variable_check": {
                "stimulus_type": True,
                "response_correctness": True
            },
            "underpowered_subjects": ["sub-001", "sub-002"],
            "excluded_subjects": ["sub-001", "sub-002"]
        }
    
    def test_validation_report_schema_valid(self, sample_validation_report):
        """Test that valid validation report passes schema validation."""
        errors = validate_schema(sample_validation_report, VALIDATION_REPORT_SCHEMA, 'json')
        assert len(errors) == 0, f"Valid data failed validation: {errors}"
    
    def test_validation_report_missing_required_keys(self):
        """Test that missing required keys are detected."""
        invalid_data = {
            "analysis_mode": "error_signal",
            # Missing other required keys
        }
        errors = validate_schema(invalid_data, VALIDATION_REPORT_SCHEMA, 'json')
        assert len(errors) > 0
        assert any("Missing required keys" in e for e in errors)
    
    @pytest.mark.skipif(not Path("data/validation_report.json").exists(), reason="validation_report.json not generated yet")
    def test_real_validation_report_conforms(self):
        """Test that the actual validation_report.json file conforms to the schema."""
        data = load_json_file(Path("data/validation_report.json"))
        errors = validate_schema(data, VALIDATION_REPORT_SCHEMA, 'json')
        assert len(errors) == 0, f"Real validation_report.json failed validation: {errors}"


class TestInterimLaggedMMNsSchema:
    """Contract tests for the interim_lagged_mmns.csv schema."""
    
    @pytest.fixture
    def sample_interim_data(self) -> List[Dict[str, Any]]:
        """Create sample interim lagged MMN data that conforms to the schema."""
        return [
            {
                "subject_id": "sub-001",
                "block_id": "1",
                "mmn_amplitude": -2.45,
                "source_window_start_trial": 10,
                "window_end_trial": 59,
                "trial_count_in_window": 50
            },
            {
                "subject_id": "sub-001",
                "block_id": "2",
                "mmn_amplitude": -3.12,
                "source_window_start_trial": 60,
                "window_end_trial": 109,
                "trial_count_in_window": 50
            }
        ]
    
    def test_interim_data_schema_valid(self, sample_interim_data):
        """Test that valid interim data passes schema validation."""
        errors = validate_schema(sample_interim_data, INTERIM_LAGGED_MMNS_SCHEMA, 'csv')
        assert len(errors) == 0, f"Valid data failed validation: {errors}"
    
    def test_interim_data_missing_required_columns(self):
        """Test that missing required columns are detected."""
        invalid_data = [
            {
                "subject_id": "sub-001",
                "block_id": "1",
                # Missing mmn_amplitude, source_window_start_trial
            }
        ]
        errors = validate_schema(invalid_data, INTERIM_LAGGED_MMNS_SCHEMA, 'csv')
        assert len(errors) > 0
        assert any("Missing required columns" in e for e in errors)
    
    @pytest.mark.skipif(not Path("data/interim_lagged_mmns.csv").exists(), reason="interim_lagged_mmns.csv not generated yet")
    def test_real_interim_data_conforms(self):
        """Test that the actual interim_lagged_mmns.csv file conforms to the schema."""
        data = load_csv_file(Path("data/interim_lagged_mmns.csv"))
        errors = validate_schema(data, INTERIM_LAGGED_MMNS_SCHEMA, 'csv')
        assert len(errors) == 0, f"Real interim_lagged_mmns.csv failed validation: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])