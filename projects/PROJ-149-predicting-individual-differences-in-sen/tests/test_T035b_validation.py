"""
Unit tests for T035b: Schema validation of model_results.json and correlations.csv.
"""
import os
import sys
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code_06_validate_model_results import (
    MODEL_RESULTS_REQUIRED_KEYS,
    CORRELATIONS_REQUIRED_COLUMNS,
    CORRELATIONS_VALID_BANDS,
    validate_model_results_json,
    validate_correlations_csv
)

class TestModelResultsValidation:
    """Tests for validate_model_results_json function."""

    def test_valid_model_results(self, tmp_path):
        """Test validation passes for valid model_results.json."""
        valid_data = {
            "adjusted_r2": 0.45,
            "rmse": 12.5,
            "n_samples": 100,
            "n_features": 6,
            "optimal_lambda": 0.01,
            "permutation_pvalue": 0.02,
            "bonferroni_flag": True,
            "model_type": "LASSO",
            "cv_folds": 5,
            "timestamp": "2024-01-01T00:00:00"
        }
        
        file_path = tmp_path / "model_results.json"
        with open(file_path, 'w') as f:
            json.dump(valid_data, f)
        
        errors = validate_model_results_json(file_path)
        assert len(errors) == 0

    def test_missing_required_keys(self, tmp_path):
        """Test validation fails when required keys are missing."""
        incomplete_data = {
            "adjusted_r2": 0.45,
            "rmse": 12.5
        }
        
        file_path = tmp_path / "model_results.json"
        with open(file_path, 'w') as f:
            json.dump(incomplete_data, f)
        
        errors = validate_model_results_json(file_path)
        assert len(errors) > 0
        assert any("Missing required keys" in err for err in errors)

    def test_invalid_pvalue_range(self, tmp_path):
        """Test validation fails when p-value is out of range."""
        invalid_data = {
            "adjusted_r2": 0.45,
            "rmse": 12.5,
            "n_samples": 100,
            "n_features": 6,
            "optimal_lambda": 0.01,
            "permutation_pvalue": 1.5,  # Invalid: > 1
            "bonferroni_flag": True,
            "model_type": "LASSO",
            "cv_folds": 5,
            "timestamp": "2024-01-01T00:00:00"
        }
        
        file_path = tmp_path / "model_results.json"
        with open(file_path, 'w') as f:
            json.dump(invalid_data, f)
        
        errors = validate_model_results_json(file_path)
        assert len(errors) > 0
        assert any("permutation_pvalue" in err for err in errors)

    def test_file_not_found(self, tmp_path):
        """Test validation handles missing file gracefully."""
        errors = validate_model_results_json(tmp_path / "nonexistent.json")
        assert len(errors) == 1
        assert "does not exist" in errors[0]

    def test_invalid_json(self, tmp_path):
        """Test validation handles invalid JSON."""
        file_path = tmp_path / "invalid.json"
        with open(file_path, 'w') as f:
            f.write("{ invalid json }")
        
        errors = validate_model_results_json(file_path)
        assert len(errors) == 1
        assert "Invalid JSON" in errors[0]

class TestCorrelationsValidation:
    """Tests for validate_correlations_csv function."""

    def test_valid_correlations(self, tmp_path):
        """Test validation passes for valid correlations.csv."""
        df = pd.DataFrame({
            "band": ["delta", "theta", "alpha", "low_beta", "high_beta", "gamma"],
            "correlation": [0.1, 0.2, 0.3, -0.1, -0.2, 0.05],
            "p_value": [0.1, 0.05, 0.01, 0.2, 0.15, 0.3],
            "bonferroni_flag": [False, False, True, False, False, False],
            "participant_count": [100, 100, 100, 100, 100, 100]
        })
        
        file_path = tmp_path / "correlations.csv"
        df.to_csv(file_path, index=False)
        
        errors = validate_correlations_csv(file_path)
        assert len(errors) == 0

    def test_missing_required_columns(self, tmp_path):
        """Test validation fails when required columns are missing."""
        df = pd.DataFrame({
            "band": ["delta", "theta"],
            "correlation": [0.1, 0.2]
        })
        
        file_path = tmp_path / "correlations.csv"
        df.to_csv(file_path, index=False)
        
        errors = validate_correlations_csv(file_path)
        assert len(errors) > 0
        assert any("Missing required columns" in err for err in errors)

    def test_invalid_band_values(self, tmp_path):
        """Test validation fails when band values are invalid."""
        df = pd.DataFrame({
            "band": ["delta", "invalid_band", "alpha"],
            "correlation": [0.1, 0.2, 0.3],
            "p_value": [0.1, 0.05, 0.01],
            "bonferroni_flag": [False, False, True],
            "participant_count": [100, 100, 100]
        })
        
        file_path = tmp_path / "correlations.csv"
        df.to_csv(file_path, index=False)
        
        errors = validate_correlations_csv(file_path)
        assert len(errors) > 0
        assert any("Invalid band values" in err for err in errors)

    def test_null_values_in_critical_columns(self, tmp_path):
        """Test validation fails when critical columns have nulls."""
        df = pd.DataFrame({
            "band": ["delta", None, "alpha"],
            "correlation": [0.1, 0.2, 0.3],
            "p_value": [0.1, 0.05, 0.01],
            "bonferroni_flag": [False, False, True],
            "participant_count": [100, 100, 100]
        })
        
        file_path = tmp_path / "correlations.csv"
        df.to_csv(file_path, index=False)
        
        errors = validate_correlations_csv(file_path)
        assert len(errors) > 0
        assert any("contains null values" in err for err in errors)

    def test_file_not_found(self, tmp_path):
        """Test validation handles missing file gracefully."""
        errors = validate_correlations_csv(tmp_path / "nonexistent.csv")
        assert len(errors) == 1
        assert "does not exist" in errors[0]

    def test_empty_file(self, tmp_path):
        """Test validation handles empty file."""
        file_path = tmp_path / "empty.csv"
        file_path.touch()
        
        errors = validate_correlations_csv(file_path)
        assert len(errors) == 1
        assert "empty" in errors[0].lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])