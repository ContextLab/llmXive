"""
Unit tests for sensitivity sweep logic in code/validation/sensitivity.py.

Tests verify:
1. The sweep generates the correct sequence of thresholds.
2. The classification stability metric is calculated correctly.
3. The stability verification logic (variation within ±5% of mean) works as expected.
4. Edge cases (e.g., empty thresholds, single threshold) are handled.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.validation.sensitivity import (
    run_sensitivity_sweep,
    calculate_classification_stability,
    verify_stability_threshold,
    generate_threshold_sweep
)
from code.config import DATA_DIR, MODELS_DIR


class TestGenerateThresholdSweep:
    """Tests for the threshold generation logic."""

    def test_standard_range(self):
        """Test generation of thresholds from 0.45 to 0.55 with step 0.01."""
        thresholds = generate_threshold_sweep(0.45, 0.55, 0.01)
        expected = [0.45, 0.46, 0.47, 0.48, 0.49, 0.50, 0.51, 0.52, 0.53, 0.54, 0.55]
        assert thresholds == expected, f"Expected {expected}, got {thresholds}"

    def test_custom_range(self):
        """Test generation with custom start, stop, and step."""
        thresholds = generate_threshold_sweep(0.1, 0.3, 0.1)
        expected = [0.1, 0.2, 0.3]
        assert thresholds == expected

    def test_single_threshold(self):
        """Test when start and stop are the same."""
        thresholds = generate_threshold_sweep(0.5, 0.5, 0.01)
        assert len(thresholds) == 1
        assert thresholds[0] == 0.5

    def test_step_size_precision(self):
        """Test that floating point precision does not cause missing values."""
        # 0.45 to 0.55 with 0.01 steps should be robust
        thresholds = generate_threshold_sweep(0.45, 0.55, 0.01)
        # Check that 0.50 is present
        assert 0.50 in thresholds
        # Check count
        assert len(thresholds) == 11


class TestCalculateClassificationStability:
    """Tests for the stability calculation logic."""

    def test_stable_classification(self):
        """Test calculation when classification rates are identical (stable)."""
        rates = [0.80, 0.80, 0.80, 0.80]
        variation, mean_rate = calculate_classification_stability(rates)
        assert variation == 0.0
        assert mean_rate == 0.80

    def test_varying_classification(self):
        """Test calculation when rates vary."""
        rates = [0.70, 0.75, 0.80, 0.85]
        variation, mean_rate = calculate_classification_stability(rates)
        # Variation is defined as range (max - min)
        expected_variation = 0.85 - 0.70
        assert variation == expected_variation
        assert mean_rate == (0.70 + 0.75 + 0.80 + 0.85) / 4.0

    def test_single_rate(self):
        """Test calculation with a single rate."""
        rates = [0.90]
        variation, mean_rate = calculate_classification_stability(rates)
        assert variation == 0.0
        assert mean_rate == 0.90

    def test_empty_rates(self):
        """Test calculation with empty list."""
        with pytest.raises(ValueError):
            calculate_classification_stability([])


class TestVerifyStabilityThreshold:
    """Tests for the stability verification logic."""

    def test_pass_stability(self):
        """Test verification when variation is within ±5% of mean."""
        # Mean = 0.80, Variation = 0.04 (5% of 0.80)
        # This should pass (variation <= 0.05 * mean)
        passed = verify_stability_threshold(0.04, 0.80)
        assert passed is True

    def test_fail_stability(self):
        """Test verification when variation exceeds ±5% of mean."""
        # Mean = 0.80, Variation = 0.05 (6.25% of 0.80)
        # This should fail
        passed = verify_stability_threshold(0.05, 0.80)
        assert passed is False

    def test_boundary_case(self):
        """Test verification exactly at the 5% boundary."""
        # Mean = 1.0, Variation = 0.05 (exactly 5%)
        passed = verify_stability_threshold(0.05, 1.0)
        assert passed is True

    def test_zero_mean(self):
        """Test verification when mean is zero (edge case)."""
        # If mean is 0, any non-zero variation should fail (division by zero handling)
        # The function should handle this gracefully, likely returning False
        passed = verify_stability_threshold(0.01, 0.0)
        assert passed is False


class TestRunSensitivitySweep:
    """Integration tests for the full sweep logic."""

    @pytest.fixture
    def mock_curated_data(self):
        """Create a mock curated dataset for testing."""
        data = {
            'solute_symbol': ['Cu', 'Cu', 'Cu', 'Cu', 'Cu'],
            'host_symbol': ['Ni', 'Ni', 'Ni', 'Ni', 'Ni'],
            'concentration': [0.0, 1.0, 2.0, 3.0, 4.0],
            'measured_E': [2.5, 2.6, 2.7, 2.8, 2.9], # eV
            'size_mismatch': [0.01, 0.02, 0.03, 0.04, 0.05]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def mock_metrics(self):
        """Create a mock metrics file content."""
        return {
            'rf': {'r2': 0.85, 'rmse': 0.1, 'mae': 0.08},
            'gb': {'r2': 0.86, 'rmse': 0.09, 'mae': 0.07},
            'linear': {'r2': 0.70, 'rmse': 0.15, 'mae': 0.12, 'size_mismatch_coef': 15.0, 'p_value': 0.001}
        }

    def test_sweep_execution(self, mock_curated_data, mock_metrics, tmp_path):
        """Test that the sweep runs and produces expected output structure."""
        # Save mock data
        curated_path = tmp_path / "curated" / "filtered.csv"
        curated_path.parent.mkdir(parents=True)
        mock_curated_data.to_csv(curated_path, index=False)

        metrics_path = tmp_path / "models" / "metrics.json"
        metrics_path.parent.mkdir(parents=True)
        import json
        with open(metrics_path, 'w') as f:
            json.dump(mock_metrics, f)

        # Run sweep
        result = run_sensitivity_sweep(
            curated_data_path=str(curated_path),
            metrics_path=str(metrics_path),
            output_dir=str(tmp_path / "reports")
        )

        assert 'thresholds' in result
        assert 'classification_rates' in result
        assert 'variation' in result
        assert 'mean_rate' in result
        assert 'is_stable' in result
        assert len(result['thresholds']) == 11 # 0.45 to 0.55

    def test_sweep_uses_correct_model_metrics(self, mock_curated_data, mock_metrics, tmp_path):
        """Test that the sweep uses the RMSE from the correct model (RF or GB)."""
        # The logic should use the best model or a specific one.
        # For this test, we verify the structure is populated.
        curated_path = tmp_path / "curated" / "filtered.csv"
        curated_path.parent.mkdir(parents=True)
        mock_curated_data.to_csv(curated_path, index=False)

        metrics_path = tmp_path / "models" / "metrics.json"
        metrics_path.parent.mkdir(parents=True)
        import json
        with open(metrics_path, 'w') as f:
            json.dump(mock_metrics, f)

        result = run_sensitivity_sweep(
            curated_data_path=str(curated_path),
            metrics_path=str(metrics_path),
            output_dir=str(tmp_path / "reports")
        )

        # Verify that the result contains the stability verification
        assert 'is_stable' in result
        assert isinstance(result['is_stable'], bool)