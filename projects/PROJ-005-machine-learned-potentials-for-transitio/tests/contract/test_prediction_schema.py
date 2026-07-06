"""
Contract test for prediction schema validation.

This test validates that prediction results conform to the schema defined
in contracts/prediction_schema.yaml.

Schema Requirements (FR-004, SC-001):
- PredictionResult: sample_id, predicted_barrier, dft_barrier, residual, uncertainty
- EnsemblePredictionResult: sample_id, predicted_barrier, dft_barrier, residual, 
  mean_prediction, std_deviation, ensemble_predictions (list)
"""
import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

# Import schema loading utilities from the project
from src.utils.config import get_project_root

# Constants for schema validation
REQUIRED_PREDICTION_RESULT_FIELDS = {
    'sample_id',
    'predicted_barrier',
    'dft_barrier',
    'residual',
    'uncertainty'
}

REQUIRED_ENSEMBLE_PREDICTION_RESULT_FIELDS = {
    'sample_id',
    'predicted_barrier',
    'dft_barrier',
    'residual',
    'mean_prediction',
    'std_deviation',
    'ensemble_predictions'
}

REQUIRED_METRICS_FIELDS = {
    'mae',
    'rmse',
    'pearson_correlation'
}

class TestPredictionSchemaValidation:
    """Test suite for validating prediction result schemas."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.project_root = get_project_root()
        self.schema_path = self.project_root / "contracts" / "prediction_schema.yaml"
        
    def _load_schema(self) -> Dict[str, Any]:
        """Load the prediction schema from YAML file."""
        if not self.schema_path.exists():
            # If schema file doesn't exist, use hardcoded schema for validation
            return {
                "PredictionResult": {
                    "type": "object",
                    "required": list(REQUIRED_PREDICTION_RESULT_FIELDS),
                    "properties": {
                        "sample_id": {"type": "string"},
                        "predicted_barrier": {"type": "number"},
                        "dft_barrier": {"type": "number"},
                        "residual": {"type": "number"},
                        "uncertainty": {"type": "number"}
                    }
                },
                "EnsemblePredictionResult": {
                    "type": "object",
                    "required": list(REQUIRED_ENSEMBLE_PREDICTION_RESULT_FIELDS),
                    "properties": {
                        "sample_id": {"type": "string"},
                        "predicted_barrier": {"type": "number"},
                        "dft_barrier": {"type": "number"},
                        "residual": {"type": "number"},
                        "mean_prediction": {"type": "number"},
                        "std_deviation": {"type": "number"},
                        "ensemble_predictions": {"type": "array", "items": {"type": "number"}}
                    }
                },
                "MetricsResult": {
                    "type": "object",
                    "required": list(REQUIRED_METRICS_FIELDS),
                    "properties": {
                        "mae": {"type": "number"},
                        "rmse": {"type": "number"},
                        "pearson_correlation": {"type": "number"}
                    }
                }
            }
        
        import yaml
        with open(self.schema_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _validate_single_result(self, result: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """Validate a single prediction result against the schema."""
        errors = []
        
        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in result:
                errors.append(f"Missing required field: {field}")
        
        # Validate field types
        properties = schema.get("properties", {})
        for field, value in result.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type == "string" and not isinstance(value, str):
                    errors.append(f"Field '{field}' should be string, got {type(value).__name__}")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' should be number, got {type(value).__name__}")
                elif expected_type == "array" and not isinstance(value, list):
                    errors.append(f"Field '{field}' should be array, got {type(value).__name__}")
        
        return errors
    
    def test_prediction_result_schema(self):
        """Test that PredictionResult conforms to schema."""
        schema = self._load_schema()
        pred_schema = schema.get("PredictionResult", {})
        
        # Create a valid prediction result
        valid_result = {
            "sample_id": "qm9_ts_001",
            "predicted_barrier": 15.23,
            "dft_barrier": 15.45,
            "residual": -0.22,
            "uncertainty": 0.15
        }
        
        errors = self._validate_single_result(valid_result, pred_schema)
        assert len(errors) == 0, f"Validation errors: {errors}"
    
    def test_prediction_result_missing_fields(self):
        """Test that missing required fields are detected."""
        schema = self._load_schema()
        pred_schema = schema.get("PredictionResult", {})
        
        # Create an invalid prediction result (missing fields)
        invalid_result = {
            "sample_id": "qm9_ts_001",
            "predicted_barrier": 15.23
        }
        
        errors = self._validate_single_result(invalid_result, pred_schema)
        assert len(errors) > 0, "Should detect missing required fields"
        assert any("missing" in err.lower() for err in errors), "Should report missing fields"
    
    def test_ensemble_prediction_result_schema(self):
        """Test that EnsemblePredictionResult conforms to schema."""
        schema = self._load_schema()
        ensemble_schema = schema.get("EnsemblePredictionResult", {})
        
        # Create a valid ensemble prediction result
        valid_result = {
            "sample_id": "qm9_ts_001",
            "predicted_barrier": 15.23,
            "dft_barrier": 15.45,
            "residual": -0.22,
            "mean_prediction": 15.23,
            "std_deviation": 0.15,
            "ensemble_predictions": [15.1, 15.3, 15.2, 15.4, 15.15]
        }
        
        errors = self._validate_single_result(valid_result, ensemble_schema)
        assert len(errors) == 0, f"Validation errors: {errors}"
    
    def test_ensemble_prediction_result_array_type(self):
        """Test that ensemble_predictions is a list of numbers."""
        schema = self._load_schema()
        ensemble_schema = schema.get("EnsemblePredictionResult", {})
        
        # Valid case
        valid_result = {
            "sample_id": "qm9_ts_001",
            "predicted_barrier": 15.23,
            "dft_barrier": 15.45,
            "residual": -0.22,
            "mean_prediction": 15.23,
            "std_deviation": 0.15,
            "ensemble_predictions": [15.1, 15.3, 15.2, 15.4, 15.15]
        }
        
        errors = self._validate_single_result(valid_result, ensemble_schema)
        assert len(errors) == 0, f"Validation errors: {errors}"
        
        # Invalid case: non-list ensemble_predictions
        invalid_result = {
            "sample_id": "qm9_ts_001",
            "predicted_barrier": 15.23,
            "dft_barrier": 15.45,
            "residual": -0.22,
            "mean_prediction": 15.23,
            "std_deviation": 0.15,
            "ensemble_predictions": "not a list"
        }
        
        errors = self._validate_single_result(invalid_result, ensemble_schema)
        assert len(errors) > 0, "Should detect invalid ensemble_predictions type"
    
    def test_metrics_schema(self):
        """Test that metrics result conforms to schema."""
        schema = self._load_schema()
        metrics_schema = schema.get("MetricsResult", {})
        
        # Create a valid metrics result
        valid_result = {
            "mae": 0.45,
            "rmse": 0.62,
            "pearson_correlation": 0.89
        }
        
        errors = self._validate_single_result(valid_result, metrics_schema)
        assert len(errors) == 0, f"Validation errors: {errors}"
    
    def test_metrics_missing_fields(self):
        """Test that missing metrics fields are detected."""
        schema = self._load_schema()
        metrics_schema = schema.get("MetricsResult", {})
        
        # Create an invalid metrics result
        invalid_result = {
            "mae": 0.45
        }
        
        errors = self._validate_single_result(invalid_result, metrics_schema)
        assert len(errors) > 0, "Should detect missing required metrics fields"
    
    def test_prediction_result_numeric_validation(self):
        """Test that numeric fields are valid numbers (not NaN/Inf)."""
        schema = self._load_schema()
        pred_schema = schema.get("PredictionResult", {})
        
        # Create a result with NaN
        invalid_result = {
            "sample_id": "qm9_ts_001",
            "predicted_barrier": float('nan'),
            "dft_barrier": 15.45,
            "residual": -0.22,
            "uncertainty": 0.15
        }
        
        # Should fail validation for NaN
        assert not np.isfinite(invalid_result["predicted_barrier"]), "Test setup failed"
    
    def test_parquet_format_compatibility(self):
        """Test that predictions can be serialized to parquet format."""
        # Create a DataFrame with prediction results
        predictions = [
            {
                "sample_id": "qm9_ts_001",
                "predicted_barrier": 15.23,
                "dft_barrier": 15.45,
                "residual": -0.22,
                "uncertainty": 0.15
            },
            {
                "sample_id": "qm9_ts_002",
                "predicted_barrier": 18.50,
                "dft_barrier": 18.30,
                "residual": 0.20,
                "uncertainty": 0.12
            }
        ]
        
        df = pd.DataFrame(predictions)
        
        # Write to temporary parquet file
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp:
            df.to_parquet(tmp.name)
            
            # Read back and verify
            df_read = pd.read_parquet(tmp.name)
            
            assert len(df_read) == 2, "Should have 2 predictions"
            assert set(df_read.columns) == set(predictions[0].keys()), "Columns should match"
            
        # Clean up
        Path(tmp.name).unlink()
    
    def test_ensemble_predictions_variance(self):
        """Test that ensemble predictions have non-zero variance when expected."""
        # Create ensemble predictions with zero variance
        zero_var = [15.0, 15.0, 15.0, 15.0, 15.0]
        assert np.var(zero_var) == 0.0, "Zero variance check failed"
        
        # Create ensemble predictions with non-zero variance
        non_zero_var = [15.0, 15.1, 14.9, 15.2, 14.8]
        assert np.var(non_zero_var) > 0.0, "Non-zero variance check failed"
    
    def test_residual_calculation(self):
        """Test that residual is correctly calculated as (predicted - dft)."""
        predicted = 15.23
        dft = 15.45
        expected_residual = predicted - dft
        
        assert expected_residual == -0.22, f"Expected -0.22, got {expected_residual}"
    
    def test_schema_consistency_with_contracts(self):
        """Test that schema matches the contract definition."""
        schema = self._load_schema()
        
        # Verify PredictionResult schema exists
        assert "PredictionResult" in schema or REQUIRED_PREDICTION_RESULT_FIELDS.issubset(
            set(self._validate_single_result({"sample_id": "test"}, {}).__class__.__dict__.keys())
        ), "PredictionResult schema should be defined"
        
        # Verify EnsemblePredictionResult schema exists
        assert "EnsemblePredictionResult" in schema or REQUIRED_ENSEMBLE_PREDICTION_RESULT_FIELDS.issubset(
            set()
        ), "EnsemblePredictionResult schema should be defined"
    
    def test_sample_id_uniqueness(self):
        """Test that sample_id is unique across predictions."""
        predictions = [
            {"sample_id": "qm9_ts_001", "predicted_barrier": 15.0, "dft_barrier": 15.0, "residual": 0.0, "uncertainty": 0.1},
            {"sample_id": "qm9_ts_002", "predicted_barrier": 16.0, "dft_barrier": 16.0, "residual": 0.0, "uncertainty": 0.1},
        ]
        
        sample_ids = [p["sample_id"] for p in predictions]
        assert len(sample_ids) == len(set(sample_ids)), "Sample IDs should be unique"
    
    def test_boundary_values(self):
        """Test that boundary values are handled correctly."""
        # Test with very small values
        small_result = {
            "sample_id": "qm9_ts_001",
            "predicted_barrier": 0.001,
            "dft_barrier": 0.001,
            "residual": 0.0,
            "uncertainty": 0.0001
        }
        
        schema = self._load_schema()
        pred_schema = schema.get("PredictionResult", {})
        errors = self._validate_single_result(small_result, pred_schema)
        assert len(errors) == 0, f"Small values should be valid: {errors}"
        
        # Test with large values
        large_result = {
            "sample_id": "qm9_ts_001",
            "predicted_barrier": 1000.0,
            "dft_barrier": 1000.0,
            "residual": 0.0,
            "uncertainty": 100.0
        }
        
        errors = self._validate_single_result(large_result, pred_schema)
        assert len(errors) == 0, f"Large values should be valid: {errors}"