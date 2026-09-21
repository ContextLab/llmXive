"""
Unit tests for data validation utilities in src/utils/validators.py.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.validators import (
    ValidationError,
    validate_composition_sum,
    normalize_compositions,
    validate_sample_count,
    validate_data_integrity,
    run_validations
)

class TestValidateCompositionSum:
    def test_valid_sum(self):
        row = {"Fe": 0.2, "Co": 0.2, "Ni": 0.2, "Cr": 0.2, "Mn": 0.2}
        cols = ["Fe", "Co", "Ni", "Cr", "Mn"]
        assert validate_composition_sum(row, cols) is True

    def test_invalid_sum(self):
        row = {"Fe": 0.3, "Co": 0.3, "Ni": 0.3}
        cols = ["Fe", "Co", "Ni"]
        with pytest.raises(ValidationError):
            validate_composition_sum(row, cols, tolerance=1e-6)

    def test_within_tolerance(self):
        row = {"Fe": 0.333333, "Co": 0.333333, "Ni": 0.333334}
        cols = ["Fe", "Co", "Ni"]
        assert validate_composition_sum(row, cols, tolerance=1e-5) is True

    def test_empty_columns(self):
        row = {}
        cols = []
        with pytest.raises(ValidationError):
            validate_composition_sum(row, cols)

class TestNormalizeCompositions:
    def test_already_normalized(self):
        df = pd.DataFrame({
            "Fe": [0.2, 0.25],
            "Co": [0.2, 0.25],
            "Ni": [0.2, 0.25],
            "Cr": [0.2, 0.25],
            "Mn": [0.2, 0.25]
        })
        cols = ["Fe", "Co", "Ni", "Cr", "Mn"]
        result = normalize_compositions(df, cols)
        # Sums should be exactly 1.0
        sums = result[cols].sum(axis=1)
        assert np.allclose(sums, 1.0)

    def test_requires_normalization(self):
        df = pd.DataFrame({
            "Fe": [0.5, 0.3],
            "Co": [0.5, 0.3],
            "Ni": [0.5, 0.3]
        })
        cols = ["Fe", "Co", "Ni"]
        result = normalize_compositions(df, cols)
        sums = result[cols].sum(axis=1)
        assert np.allclose(sums, 1.0)

    def test_nan_values_raises_error(self):
        df = pd.DataFrame({
            "Fe": [0.2, np.nan],
            "Co": [0.2, 0.2],
            "Ni": [0.2, 0.2],
            "Cr": [0.2, 0.2],
            "Mn": [0.2, 0.2]
        })
        cols = ["Fe", "Co", "Ni", "Cr", "Mn"]
        with pytest.raises(ValidationError):
            normalize_compositions(df, cols)

    def test_negative_values_raises_error(self):
        df = pd.DataFrame({
            "Fe": [-0.1, 0.2],
            "Co": [0.2, 0.2],
            "Ni": [0.2, 0.2],
            "Cr": [0.2, 0.2],
            "Mn": [0.2, 0.2]
        })
        cols = ["Fe", "Co", "Ni", "Cr", "Mn"]
        with pytest.raises(ValidationError):
            normalize_compositions(df, cols)

class TestValidateSampleCount:
    def test_sufficient_samples(self):
        result = validate_sample_count(1500, min_threshold=500, warning_threshold=1000)
        assert result["is_valid"] is True
        assert result["is_reduced_power"] is False

    def test_reduced_power_warning(self):
        result = validate_sample_count(800, min_threshold=500, warning_threshold=1000)
        assert result["is_valid"] is True
        assert result["is_reduced_power"] is True
        assert "WARNING" in result["message"]

    def test_insufficient_samples(self):
        result = validate_sample_count(400, min_threshold=500, warning_threshold=1000)
        assert result["is_valid"] is False
        assert result["is_reduced_power"] is True
        assert "CRITICAL" in result["message"]

class TestValidateDataIntegrity:
    def test_valid_data(self):
        df = pd.DataFrame({
            "composition_Fe": [0.2, 0.2],
            "composition_Co": [0.2, 0.2],
            "composition_Ni": [0.2, 0.2],
            "composition_Cr": [0.2, 0.2],
            "composition_Mn": [0.2, 0.2],
            "Bulk_Modulus_Residual": [10.0, 15.0]
        })
        cols = [c for c in df.columns if c.startswith("composition_")]
        is_valid, errors = validate_data_integrity(
            df, cols, target_col="Bulk_Modulus_Residual", min_samples=1
        )
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_target(self):
        df = pd.DataFrame({
            "composition_Fe": [0.2],
            "Bulk_Modulus_Residual": [10.0]
        })
        cols = ["composition_Fe"]
        is_valid, errors = validate_data_integrity(
            df, cols, target_col="Missing_Target", min_samples=1
        )
        assert is_valid is False
        assert any("not found" in e for e in errors)

    def test_nan_in_target(self):
        df = pd.DataFrame({
            "composition_Fe": [0.2, 0.2],
            "composition_Co": [0.2, 0.2],
            "composition_Ni": [0.2, 0.2],
            "composition_Cr": [0.2, 0.2],
            "composition_Mn": [0.2, 0.2],
            "Bulk_Modulus_Residual": [10.0, np.nan]
        })
        cols = [c for c in df.columns if c.startswith("composition_")]
        is_valid, errors = validate_data_integrity(
            df, cols, target_col="Bulk_Modulus_Residual", min_samples=1
        )
        assert is_valid is False
        assert any("NaN" in e for e in errors)

class TestRunValidations:
    def test_full_validation_success(self):
        df = pd.DataFrame({
            "composition_Fe": [0.2] * 100,
            "composition_Co": [0.2] * 100,
            "composition_Ni": [0.2] * 100,
            "composition_Cr": [0.2] * 100,
            "composition_Mn": [0.2] * 100,
            "Bulk_Modulus_Residual": [10.0] * 100
        })
        cols = [c for c in df.columns if c.startswith("composition_")]
        report = run_validations(df, cols, target_col="Bulk_Modulus_Residual", min_samples=10)
        
        assert report["is_valid"] is True
        assert report["total_samples"] == 100
        assert len(report["errors"]) == 0

    def test_full_validation_failure(self):
        df = pd.DataFrame({
            "composition_Fe": [0.1] * 10,
            "composition_Co": [0.1] * 10,
            "composition_Ni": [0.1] * 10,
            "composition_Cr": [0.1] * 10,
            "composition_Mn": [0.1] * 10,
            "Bulk_Modulus_Residual": [10.0] * 10
        })
        cols = [c for c in df.columns if c.startswith("composition_")]
        
        # Should fail because sum is 0.5, not 1.0
        report = run_validations(df, cols, target_col="Bulk_Modulus_Residual", min_samples=1, raise_on_error=False)
        
        assert report["is_valid"] is False
        assert len(report["errors"]) > 0
        
        # Should raise if raise_on_error=True
        with pytest.raises(ValidationError):
            run_validations(df, cols, target_col="Bulk_Modulus_Residual", min_samples=1, raise_on_error=True)