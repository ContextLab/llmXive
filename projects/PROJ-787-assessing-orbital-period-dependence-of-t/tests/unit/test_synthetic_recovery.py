"""
Unit tests for synthetic recovery validation (T026)
"""
import os
import sys
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from validation.synthetic_recovery import (
    generate_synthetic_dataset,
    validate_recovery,
    GAP_LOCATION_TOLERANCE,
    SLOPE_TOLERANCE
)

class TestSyntheticDatasetGeneration:
    """Tests for synthetic dataset generation."""

    def test_generate_synthetic_dataset_creates_expected_columns(self):
        """Test that generated dataset has all required columns."""
        df = generate_synthetic_dataset(n_planets=100, seed=42)
        
        expected_columns = [
            'koid', 'period', 'radius', 'period_err', 'radius_err',
            'log_period', 'log_radius', 'true_gap_log_radius', 'group'
        ]
        
        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"

    def test_generate_synthetic_dataset_respects_seed(self):
        """Test that random seed produces reproducible results."""
        df1 = generate_synthetic_dataset(n_planets=100, seed=123)
        df2 = generate_synthetic_dataset(n_planets=100, seed=123)
        
        assert np.allclose(df1['period'].values, df2['period'].values)
        assert np.allclose(df1['radius'].values, df2['radius'].values)

    def test_generate_synthetic_dataset_period_range(self):
        """Test that periods are within expected range."""
        df = generate_synthetic_dataset(n_planets=100, seed=42)
        
        assert df['period'].min() >= 0.5
        assert df['period'].max() <= 100.0

    def test_generate_synthetic_dataset_uncertainty_constraints(self):
        """Test that uncertainties meet the <20% radius and <1% period criteria."""
        df = generate_synthetic_dataset(n_planets=100, seed=42)
        
        # Radius uncertainty should be <20%
        assert (df['radius_err'] / df['radius'] < 0.20).all()
        
        # Period uncertainty should be <1%
        assert (df['period_err'] / df['period'] < 0.01).all()

class TestValidationLogic:
    """Tests for validation logic."""

    def test_validate_recovery_passes_exact_match(self):
        """Test that exact match passes validation."""
        true_slope = -0.11
        recovered_slope = -0.11
        slope_err = 0.01
        
        true_gaps = np.array([2.0, 2.1, 2.2])
        recovered_gaps = np.array([2.0, 2.1, 2.2])
        
        results = validate_recovery(
            true_slope=true_slope,
            recovered_slope=recovered_slope,
            slope_err=slope_err,
            true_gap_locations=true_gaps,
            recovered_gap_locations=recovered_gaps
        )
        
        assert results['overall_pass'] is True
        assert results['slope_pass'] is True
        assert results['gap_locations_pass'] is True

    def test_validate_recovery_fails_large_slope_error(self):
        """Test that large slope error fails validation."""
        true_slope = -0.11
        recovered_slope = -0.20  # Large deviation
        slope_err = 0.01
        
        true_gaps = np.array([2.0, 2.1, 2.2])
        recovered_gaps = np.array([2.0, 2.1, 2.2])
        
        results = validate_recovery(
            true_slope=true_slope,
            recovered_slope=recovered_slope,
            slope_err=slope_err,
            true_gap_locations=true_gaps,
            recovered_gap_locations=recovered_gaps
        )
        
        assert results['slope_pass'] is False
        assert results['overall_pass'] is False

    def test_validate_recovery_fails_large_gap_error(self):
        """Test that large gap location error fails validation."""
        true_slope = -0.11
        recovered_slope = -0.11
        slope_err = 0.01
        
        true_gaps = np.array([2.0, 2.1, 2.2])
        recovered_gaps = np.array([2.5, 2.6, 2.7])  # Large deviation
        
        results = validate_recovery(
            true_slope=true_slope,
            recovered_slope=recovered_slope,
            slope_err=slope_err,
            true_gap_locations=true_gaps,
            recovered_gap_locations=recovered_gaps
        )
        
        assert results['gap_locations_pass'] is False
        assert results['overall_pass'] is False

    def test_validate_recovery_handles_nan_values(self):
        """Test that NaN values in recovered gaps are handled correctly."""
        true_slope = -0.11
        recovered_slope = -0.11
        slope_err = 0.01
        
        true_gaps = np.array([2.0, 2.1, 2.2])
        recovered_gaps = np.array([2.0, np.nan, 2.2])
        
        results = validate_recovery(
            true_slope=true_slope,
            recovered_slope=recovered_slope,
            slope_err=slope_err,
            true_gap_locations=true_gaps,
            recovered_gap_locations=recovered_gaps
        )
        
        # Should pass if remaining valid points are close enough
        assert 'mean_gap_error' in results['details']

class TestIntegration:
    """Integration tests for the synthetic recovery pipeline."""

    def test_full_pipeline_execution(self):
        """Test that the full pipeline can execute without errors."""
        # This is a basic smoke test - full validation is tested in the script itself
        from validation.synthetic_recovery import main
        
        # Create a temporary directory for test outputs
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override paths for testing
            import validation.synthetic_recovery as sr_module
            original_raw = sr_module.SYNTHETIC_RAW_PATH
            original_binned = sr_module.SYNTHETIC_BINNED_PATH
            original_gap = sr_module.SYNTHETIC_GAP_LOCATIONS_PATH
            original_results = sr_module.VALIDATION_RESULTS_PATH
            
            try:
                sr_module.SYNTHETIC_RAW_PATH = os.path.join(tmpdir, "synthetic_raw.csv")
                sr_module.SYNTHETIC_BINNED_PATH = os.path.join(tmpdir, "synthetic_binned.csv")
                sr_module.SYNTHETIC_GAP_LOCATIONS_PATH = os.path.join(tmpdir, "synthetic_gap.csv")
                sr_module.VALIDATION_RESULTS_PATH = os.path.join(tmpdir, "validation.json")
                
                # Run with small dataset for speed
                result = main()
                
                # Should complete successfully (return 0)
                assert result == 0
                
                # Check that output file was created
                assert os.path.exists(sr_module.VALIDATION_RESULTS_PATH)
                
                # Check that results are valid JSON
                with open(sr_module.VALIDATION_RESULTS_PATH, 'r') as f:
                    results = json.load(f)
                
                assert 'validation_status' in results
                assert 'overall_pass' in results['validation']
                
            finally:
                # Restore original paths
                sr_module.SYNTHETIC_RAW_PATH = original_raw
                sr_module.SYNTHETIC_BINNED_PATH = original_binned
                sr_module.SYNTHETIC_GAP_LOCATIONS_PATH = original_gap
                sr_module.VALIDATION_RESULTS_PATH = original_results