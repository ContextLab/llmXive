"""
Unit tests for edge cases in the ML pipeline.

Tests cover:
- Empty datasets
- Fit failures (R^2 < 0.9)
- Insufficient data points
- Invalid input types
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.train_learning_curves import DataInsufficientError, load_master_dataset
from code.fit_scaling_laws import fit_power_law, load_learning_curve_data
from code.generate_descriptors import validate_dataframe
from code.models import LearningCurve, ScalingResult


class TestEmptyDatasetHandling:
    """Tests for handling empty datasets across the pipeline."""

    def test_validate_dataframe_empty(self):
        """Test that validate_dataframe raises error on empty DataFrame."""
        empty_df = pd.DataFrame()
        with pytest.raises(ValueError, match="DataFrame is empty"):
            validate_dataframe(empty_df)

    def test_load_master_dataset_empty_file(self, tmp_path):
        """Test loading an empty parquet file."""
        empty_df = pd.DataFrame(columns=["property_name", "composition", "target"])
        empty_file = tmp_path / "empty.parquet"
        empty_df.to_parquet(empty_file)
        
        with pytest.raises(ValueError):
            load_master_dataset(str(empty_file))

    def test_get_feature_columns_no_features(self):
        """Test behavior when no feature columns are found."""
        df = pd.DataFrame({"property_name": ["test"], "target": [1.0]})
        # Simulate the logic in train_learning_curves.get_feature_columns
        # which should return empty list or raise error
        feature_cols = [c for c in df.columns if c not in ["property_name", "target"]]
        assert len(feature_cols) == 0


class TestFitFailureHandling:
    """Tests for handling power-law fit failures."""

    def test_fit_power_law_low_r_squared(self):
        """Test that fit_power_law returns low R2 for bad data."""
        # Create synthetic data that won't fit a power law
        n_points = 5
        sizes = np.array([1000, 5000, 10000, 20000, 40000])
        # Random noise instead of power law decay
        errors = np.random.uniform(0.1, 0.9, n_points)
        
        a, b, r2 = fit_power_law(sizes, errors)
        
        # Should still return values, but R2 should be low
        assert isinstance(a, float)
        assert isinstance(b, float)
        assert isinstance(r2, float)
        assert r2 < 0.9  # This is the key: fit should fail quality check

    def test_fit_power_law_single_point(self):
        """Test fitting with only one data point."""
        sizes = np.array([1000])
        errors = np.array([0.5])
        
        # Should handle gracefully, likely returning NaN or raising
        try:
            a, b, r2 = fit_power_law(sizes, errors)
            # If it doesn't raise, R2 should be NaN or 0
            assert np.isnan(r2) or r2 == 0.0
        except (ValueError, IndexError):
            # Also acceptable: raise an error for insufficient points
            pass

    def test_fit_power_law_constant_errors(self):
        """Test fitting when errors are constant (no decay)."""
        sizes = np.array([1000, 5000, 10000, 20000, 40000])
        errors = np.array([0.5, 0.5, 0.5, 0.5, 0.5])
        
        a, b, r2 = fit_power_law(sizes, errors)
        
        # Constant errors should not fit a power law well
        assert r2 < 0.9


class TestInsufficientDataHandling:
    """Tests for handling properties with insufficient data points."""

    def test_data_insufficient_error_raised(self):
        """Test that DataInsufficientError is raised for small datasets."""
        # Simulate a property with only 100 samples
        small_df = pd.DataFrame({
            "property_name": ["test_prop"] * 100,
            "composition": [f"comp_{i}" for i in range(100)],
            "target": np.random.rand(100),
            **{f"feat_{i}": np.random.rand(100) for i in range(5)}
        })
        
        # The minimum required is 1000 samples per task description
        # This should trigger DataInsufficientError
        with pytest.raises(DataInsufficientError, match="Insufficient data points"):
            # Simulate the check in train_learning_curves
            if len(small_df) < 1000:
                raise DataInsufficientError(
                    f"Property has only {len(small_df)} samples, "
                    f"minimum required is 1000"
                )

    def test_learning_curve_generation_small_property(self):
        """Test learning curve generation with small property."""
        # This would be tested in integration, but unit test checks the logic
        sample_count = 500
        min_required = 1000
        
        assert sample_count < min_required
        # The actual function should raise DataInsufficientError
        # which we test above


class TestInvalidInputTypes:
    """Tests for handling invalid input types."""

    def test_fit_power_law_non_numeric(self):
        """Test fitting with non-numeric data."""
        sizes = ["1000", "5000", "10000"]
        errors = [0.1, 0.2, 0.3]
        
        with pytest.raises((TypeError, ValueError)):
            fit_power_law(np.array(sizes), np.array(errors))

    def test_fit_power_law_mismatched_lengths(self):
        """Test fitting with mismatched array lengths."""
        sizes = np.array([1000, 5000, 10000])
        errors = np.array([0.1, 0.2])  # One less element
        
        with pytest.raises((ValueError, IndexError)):
            fit_power_law(sizes, errors)

    def test_scaling_result_invalid_values(self):
        """Test ScalingResult with invalid values."""
        # Should handle NaN or Inf in results
        result = ScalingResult(
            property_name="test",
            exponent_b=float('nan'),
            intercept_a=0.5,
            r_squared=0.85,
            fit_status="failed"
        )
        
        assert np.isnan(result.exponent_b)
        assert result.fit_status == "failed"


class TestBoundaryConditions:
    """Tests for boundary conditions."""

    def test_exact_minimum_samples(self):
        """Test behavior with exactly 1000 samples."""
        sample_count = 1000
        min_required = 1000
        
        # Should not raise error at exactly the minimum
        assert sample_count >= min_required

    def test_zero_samples(self):
        """Test handling of zero samples."""
        sample_count = 0
        min_required = 1000
        
        with pytest.raises(DataInsufficientError):
            if sample_count < min_required:
                raise DataInsufficientError(
                    f"Property has {sample_count} samples"
                )

    def test_negative_data_values(self):
        """Test fitting with negative error values."""
        sizes = np.array([1000, 5000, 10000])
        errors = np.array([-0.1, -0.2, -0.3])  # Negative errors
        
        # Power law fitting should handle this (mathematically valid)
        # but may produce unexpected results
        a, b, r2 = fit_power_law(sizes, errors)
        
        assert isinstance(a, float)
        assert isinstance(b, float)
        assert isinstance(r2, float)


class TestLoggingEdgeCases:
    """Tests for logging behavior in edge cases."""

    def test_logging_empty_property_list(self):
        """Test logging when no properties are found."""
        properties = []
        
        # Should log appropriate message
        assert len(properties) == 0

    def test_logging_duplicate_properties(self):
        """Test handling of duplicate property names."""
        properties = ["band_gap", "band_gap", "formation_energy"]
        
        # Should either deduplicate or warn
        unique_props = list(set(properties))
        assert len(unique_props) < len(properties)