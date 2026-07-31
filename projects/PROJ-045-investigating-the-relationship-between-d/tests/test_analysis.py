"""
Contract tests for User Story 3 (Statistical Analysis and Correlation).

These tests verify that the analysis module produces the required statistical
outputs (R², p-values) with correct types and valid ranges, assuming the
input data meets the quality constraints (BVS validation, defect density inclusion).

Run with: pytest tests/test_analysis.py -v
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis import (
    load_processed_data,
    perform_regression_with_density,
    apply_multiple_comparison_correction,
    calculate_statistical_power,
    run_full_analysis,
    validate_data_quality
)
from models import AnalysisResult

# Constants for test data generation
N_SAMPLES = 50
N_FEATURES = 3  # vacancy_energy, interstitial_energy, defect_density

def generate_synthetic_regression_data(
    n_samples: int = N_SAMPLES,
    n_features: int = N_FEATURES,
    noise_scale: float = 0.1
) -> Dict[str, np.ndarray]:
    """
    Generate synthetic data for regression testing.
    
    Creates a dataset where:
    - Features (X) are random values
    - Target (y) has a linear relationship with the first feature + noise
    - This ensures R² > 0 and p-value < 0.05 for the first feature.
    
    Returns:
        Dictionary with keys: 'X' (features), 'y' (target), 'feature_names'
    """
    rng = np.random.default_rng(42)  # Fixed seed for reproducibility
    
    # Generate features
    X = rng.standard_normal((n_samples, n_features))
    feature_names = ['vacancy_energy', 'interstitial_energy', 'defect_density']
    
    # Generate target with known relationship: y = 2 * X[:,0] + 0.5 * X[:,2] + noise
    # This ensures vacancy_energy and defect_density are significant predictors
    true_coefs = [2.0, 0.0, 0.5]  # Second feature is irrelevant
    y = X @ np.array(true_coefs) + rng.normal(0, noise_scale, n_samples)
    
    return {
        'X': X,
        'y': y,
        'feature_names': feature_names
    }

def create_temp_processed_data_file(data: Dict[str, Any]) -> str:
    """
    Create a temporary JSON file containing processed analysis data.
    
    Args:
        data: Dictionary containing 'X', 'y', 'feature_names', and 'composition_ids'
    
    Returns:
        Path to the temporary JSON file
    """
    fd, path = tempfile.mkstemp(suffix='.json')
    try:
        with os.fdopen(fd, 'w') as tmp:
            json.dump(data, tmp)
    except Exception as e:
        os.remove(path)
        raise e
    return path

class TestRegressionOutputs:
    """Contract tests for regression output validity."""

    def test_perform_regression_returns_required_metrics(self):
        """
        Contract test: perform_regression_with_density must return a dictionary
        containing 'r_squared', 'p_values', 'coefficients', and 'model'.
        """
        data = generate_synthetic_regression_data()
        
        result = perform_regression_with_density(
            X=data['X'],
            y=data['y'],
            feature_names=data['feature_names']
        )
        
        # Assert required keys exist
        assert 'r_squared' in result, "Missing 'r_squared' in regression result"
        assert 'p_values' in result, "Missing 'p_values' in regression result"
        assert 'coefficients' in result, "Missing 'coefficients' in regression result"
        assert 'model' in result, "Missing 'model' in regression result"
        assert 'intercept' in result, "Missing 'intercept' in regression result"

    def test_r_squared_is_valid_range(self):
        """
        Contract test: R² must be between 0 and 1 (inclusive) for OLS regression.
        """
        data = generate_synthetic_regression_data()
        
        result = perform_regression_with_density(
            X=data['X'],
            y=data['y'],
            feature_names=data['feature_names']
        )
        
        r_sq = result['r_squared']
        assert 0.0 <= r_sq <= 1.0, f"R² ({r_sq}) must be in range [0, 1]"

    def test_p_values_are_valid_range(self):
        """
        Contract test: P-values must be between 0 and 1 (inclusive).
        """
        data = generate_synthetic_regression_data()
        
        result = perform_regression_with_density(
            X=data['X'],
            y=data['y'],
            feature_names=data['feature_names']
        )
        
        p_vals = result['p_values']
        assert isinstance(p_vals, (list, np.ndarray)), "p_values must be a list or array"
        assert len(p_vals) == len(data['feature_names']), "p_values length mismatch"
        
        for p in p_vals:
            assert 0.0 <= p <= 1.0, f"P-value ({p}) must be in range [0, 1]"

    def test_regression_significant_for_known_signal(self):
        """
        Contract test: With synthetic data designed to have a signal,
        the first feature (vacancy_energy) should have a significant p-value (< 0.05).
        """
        # Use low noise to ensure signal is detectable
        data = generate_synthetic_regression_data(noise_scale=0.05)
        
        result = perform_regression_with_density(
            X=data['X'],
            y=data['y'],
            feature_names=data['feature_names']
        )
        
        # The first feature was designed to be significant
        p_val_first = result['p_values'][0]
        assert p_val_first < 0.05, (
            f"Expected p-value < 0.05 for first feature, got {p_val_first}. "
            "The regression model is not detecting the known signal."
        )

class TestMultipleComparisonCorrection:
    """Contract tests for multiple comparison correction."""

    def test_bonferroni_returns_corrected_pvalues(self):
        """
        Contract test: apply_multiple_comparison_correction must return
        corrected p-values that are >= original p-values.
        """
        original_p_values = [0.01, 0.04, 0.08, 0.50]
        
        corrected = apply_multiple_comparison_correction(original_p_values, method='bonferroni')
        
        assert len(corrected) == len(original_p_values), "Length mismatch in corrected p-values"
        for orig, corr in zip(original_p_values, corrected):
            assert corr >= orig, f"Corrected p-value ({corr}) should be >= original ({orig})"
            assert corr <= 1.0, f"Corrected p-value ({corr}) must be <= 1.0"

    def test_bh_correction_returns_corrected_pvalues(self):
        """
        Contract test: Benjamini-Hochberg correction returns valid values.
        """
        original_p_values = [0.01, 0.04, 0.08, 0.50]
        
        corrected = apply_multiple_comparison_correction(original_p_values, method='fdr_bh')
        
        assert len(corrected) == len(original_p_values), "Length mismatch in corrected p-values"
        for corr in corrected:
            assert 0.0 <= corr <= 1.0, f"Corrected p-value ({corr}) must be in [0, 1]"

class TestStatisticalPower:
    """Contract tests for power analysis."""

    def test_calculate_statistical_power_returns_valid_result(self):
        """
        Contract test: calculate_statistical_power must return a dictionary
        with 'power', 'effect_size', 'sample_size', and 'alpha'.
        """
        # Typical parameters for power analysis
        effect_size = 0.5
        sample_size = 50
        alpha = 0.05
        
        result = calculate_statistical_power(
            effect_size=effect_size,
            sample_size=sample_size,
            alpha=alpha
        )
        
        assert 'power' in result, "Missing 'power' in result"
        assert 'effect_size' in result, "Missing 'effect_size' in result"
        assert 'sample_size' in result, "Missing 'sample_size' in result"
        assert 'alpha' in result, "Missing 'alpha' in result"
        
        # Power should be between 0 and 1
        assert 0.0 <= result['power'] <= 1.0, f"Power ({result['power']}) must be in [0, 1]"

class TestFullAnalysisIntegration:
    """Integration tests for the full analysis pipeline."""

    def test_run_full_analysis_produces_output_structure(self):
        """
        Contract test: run_full_analysis must return a dictionary with
        'regression_results', 'power_analysis', 'vif_scores', and 'summary'.
        """
        data = generate_synthetic_regression_data()
        
        # Mock composition IDs for the test
        composition_ids = [f"comp_{i}" for i in range(len(data['y']))]
        
        result = run_full_analysis(
            X=data['X'],
            y=data['y'],
            feature_names=data['feature_names'],
            composition_ids=composition_ids
        )
        
        assert 'regression_results' in result, "Missing 'regression_results'"
        assert 'power_analysis' in result, "Missing 'power_analysis'"
        assert 'vif_scores' in result, "Missing 'vif_scores'"
        assert 'summary' in result, "Missing 'summary'"
        
        # Verify regression results structure
        reg_res = result['regression_results']
        assert 'r_squared' in reg_res
        assert 'p_values' in reg_res

class TestDataValidation:
    """Tests for data validation before analysis."""

    def test_validate_data_quality_rejects_invalid_input(self):
        """
        Contract test: validate_data_quality must raise ValueError for
        mismatched dimensions or NaN inputs.
        """
        # Test 1: Mismatched dimensions
        X_bad = np.random.rand(10, 3)
        y_bad = np.random.rand(5)  # Mismatched length
        
        with pytest.raises(ValueError, match="dimension mismatch"):
            validate_data_quality(X_bad, y_bad, ['f1', 'f2', 'f3'])

        # Test 2: NaN in X
        X_nan = np.random.rand(10, 3)
        X_nan[0, 0] = np.nan
        y_clean = np.random.rand(10)
        
        with pytest.raises(ValueError, match="NaN"):
            validate_data_quality(X_nan, y_clean, ['f1', 'f2', 'f3'])

        # Test 3: NaN in y
        X_clean = np.random.rand(10, 3)
        y_nan = np.random.rand(10)
        y_nan[2] = np.nan
        
        with pytest.raises(ValueError, match="NaN"):
            validate_data_quality(X_clean, y_nan, ['f1', 'f2', 'f3'])

    def test_validate_data_quality_accepts_valid_input(self):
        """
        Contract test: validate_data_quality returns True for clean,
        correctly shaped data.
        """
        X = np.random.rand(20, 3)
        y = np.random.rand(20)
        names = ['f1', 'f2', 'f3']
        
        assert validate_data_quality(X, y, names) is True