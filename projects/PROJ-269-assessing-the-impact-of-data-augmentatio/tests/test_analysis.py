"""
Integration test for comparative analysis logic (User Story 3).

This test verifies that the comparative analysis logic in `code/analyze.py`
correctly calculates differences in Type I/II error rates between baseline
and augmented groups, and identifies unsafe thresholds (Type I > 0.10).
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np

# Import the functions to be tested from the project code
from code.analyze import (
    load_simulation_results,
    calculate_error_rates,
    calculate_bootstrap_ci,
    analyze_baseline_results
)
from code.simulation import save_results


# Fixtures
@pytest.fixture
def temp_results_dir():
    """Create a temporary directory for test results."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_baseline_data(temp_results_dir):
    """Create mock baseline simulation results."""
    # Simulate Type I error results (Null condition)
    # We create a scenario where the empirical error rate is ~0.05
    null_p_values = np.random.uniform(0.0, 1.0, 1000)
    # Force a specific proportion to be < 0.05 to simulate ~5% error
    null_p_values[:50] = np.random.uniform(0.0, 0.05, 50)
    
    baseline_null = {
        "metadata": {
            "dataset": "test_dataset",
            "size": 25,
            "condition": "null",
            "method": "baseline",
            "iterations": 1000,
            "seed": 42
        },
        "p_values": null_p_values.tolist(),
        "error_rate": 0.05,
        "ci_lower": 0.035,
        "ci_upper": 0.065
    }

    # Simulate Type II error results (Alt condition)
    # We create a scenario where the empirical error rate is ~0.30 (Power = 0.70)
    alt_p_values = np.random.uniform(0.0, 1.0, 1000)
    # Force a higher proportion to be > 0.05 to simulate Type II error
    alt_p_values[700:] = np.random.uniform(0.05, 1.0, 300)
    
    baseline_alt = {
        "metadata": {
            "dataset": "test_dataset",
            "size": 25,
            "condition": "alt",
            "method": "baseline",
            "iterations": 1000,
            "seed": 42
        },
        "p_values": alt_p_values.tolist(),
        "error_rate": 0.30,
        "ci_lower": 0.27,
        "ci_upper": 0.33
    }

    # Save to files
    null_path = temp_results_dir / "test_dataset_25_baseline_null.json"
    alt_path = temp_results_dir / "test_dataset_25_baseline_alt.json"
    
    with open(null_path, 'w') as f:
        json.dump(baseline_null, f)
    with open(alt_path, 'w') as f:
        json.dump(baseline_alt, f)

    return temp_results_dir, "test_dataset", 25, "baseline"


@pytest.fixture
def mock_augmented_data(temp_results_dir):
    """Create mock augmented simulation results (e.g., SMOTE)."""
    # Simulate a scenario where augmentation inflates Type I error to ~0.15 (Unsafe)
    null_p_values = np.random.uniform(0.0, 1.0, 1000)
    # Force 15% to be < 0.05
    null_p_values[:150] = np.random.uniform(0.0, 0.05, 150)
    
    aug_null = {
        "metadata": {
            "dataset": "test_dataset",
            "size": 25,
            "condition": "null",
            "method": "smote",
            "iterations": 1000,
            "seed": 42
        },
        "p_values": null_p_values.tolist(),
        "error_rate": 0.15,
        "ci_lower": 0.13,
        "ci_upper": 0.17
    }

    # Simulate Type II error (Power improvement)
    alt_p_values = np.random.uniform(0.0, 1.0, 1000)
    # Force 20% to be > 0.05 (Type II error = 0.20, Power = 0.80)
    alt_p_values[800:] = np.random.uniform(0.05, 1.0, 200)
    
    aug_alt = {
        "metadata": {
            "dataset": "test_dataset",
            "size": 25,
            "condition": "alt",
            "method": "smote",
            "iterations": 1000,
            "seed": 42
        },
        "p_values": alt_p_values.tolist(),
        "error_rate": 0.20,
        "ci_lower": 0.17,
        "ci_upper": 0.23
    }

    # Save to files
    null_path = temp_results_dir / "test_dataset_25_smote_null.json"
    alt_path = temp_results_dir / "test_dataset_25_smote_alt.json"
    
    with open(null_path, 'w') as f:
        json.dump(aug_null, f)
    with open(alt_path, 'w') as f:
        json.dump(aug_alt, f)

    return temp_results_dir, "test_dataset", 25, "smote"


class TestComparativeAnalysis:
    """Integration tests for comparative analysis logic."""

    def test_load_baseline_results(self, mock_baseline_data):
        """Test loading baseline results from JSON files."""
        results_dir, dataset, size, method = mock_baseline_data
        
        null_path = results_dir / f"{dataset}_{size}_{method}_null.json"
        alt_path = results_dir / f"{dataset}_{size}_{method}_alt.json"
        
        null_data = load_simulation_results(null_path)
        alt_data = load_simulation_results(alt_path)
        
        assert null_data is not None
        assert alt_data is not None
        assert null_data["metadata"]["condition"] == "null"
        assert alt_data["metadata"]["condition"] == "alt"
        assert len(null_data["p_values"]) == 1000
        assert len(alt_data["p_values"]) == 1000

    def test_calculate_error_rates(self, mock_baseline_data):
        """Test error rate calculation from p-values."""
        results_dir, dataset, size, method = mock_baseline_data
        null_path = results_dir / f"{dataset}_{size}_{method}_null.json"
        
        data = load_simulation_results(null_path)
        p_values = data["p_values"]
        
        # Calculate error rate manually
        expected_error_rate = sum(1 for p in p_values if p < 0.05) / len(p_values)
        
        # Use the function
        calculated_rate = calculate_error_rates(p_values, threshold=0.05)
        
        assert abs(calculated_rate - expected_error_rate) < 1e-6

    def test_comparative_analysis_logic(self, mock_baseline_data, mock_augmented_data):
        """
        Test the core comparative analysis logic:
        1. Load baseline and augmented results.
        2. Calculate error rate differences.
        3. Verify unsafe threshold detection (Type I > 0.10).
        """
        base_dir, dataset, size, base_method = mock_baseline_data
        aug_dir, _, _, aug_method = mock_augmented_data
        
        # Load data
        base_null = load_simulation_results(base_dir / f"{dataset}_{size}_{base_method}_null.json")
        aug_null = load_simulation_results(aug_dir / f"{dataset}_{size}_{aug_method}_null.json")
        
        base_alt = load_simulation_results(base_dir / f"{dataset}_{size}_{base_method}_alt.json")
        aug_alt = load_simulation_results(aug_dir / f"{dataset}_{size}_{aug_method}_alt.json")
        
        # Calculate error rates
        base_type_i = calculate_error_rates(base_null["p_values"])
        aug_type_i = calculate_error_rates(aug_null["p_values"])
        
        base_type_ii = calculate_error_rates(base_alt["p_values"])
        aug_type_ii = calculate_error_rates(aug_alt["p_values"])
        
        # Calculate differences
        diff_type_i = aug_type_i - base_type_i
        diff_type_ii = aug_type_ii - base_type_ii
        
        # Assertions based on mock data:
        # Baseline Type I ~ 0.05, Augmented Type I ~ 0.15 -> Diff ~ 0.10
        # Baseline Type II ~ 0.30, Augmented Type II ~ 0.20 -> Diff ~ -0.10
        
        assert abs(diff_type_i - 0.10) < 0.02, f"Expected Type I diff ~0.10, got {diff_type_i}"
        assert abs(diff_type_ii - (-0.10)) < 0.02, f"Expected Type II diff ~-0.10, got {diff_type_ii}"
        
        # Test unsafe threshold detection (FR-005: Type I > 0.10)
        is_unsafe = aug_type_i > 0.10
        assert is_unsafe is True, "Augmented Type I error should be flagged as unsafe (> 0.10)"

    def test_bootstrap_ci_consistency(self, mock_baseline_data):
        """Test that bootstrap CI calculation is consistent with stored values."""
        results_dir, dataset, size, method = mock_baseline_data
        null_path = results_dir / f"{dataset}_{size}_{method}_null.json"
        
        data = load_simulation_results(null_path)
        p_values = data["p_values"]
        
        # Calculate CI using the function
        ci_lower, ci_upper = calculate_bootstrap_ci(p_values, n_bootstraps=1000, alpha=0.05)
        
        # Verify the calculated CI contains the point estimate
        error_rate = calculate_error_rates(p_values)
        assert ci_lower <= error_rate <= ci_upper, "CI should contain the point estimate"
        
        # Verify CI width is reasonable (not too narrow, not too wide)
        ci_width = ci_upper - ci_lower
        assert 0.01 < ci_width < 0.20, f"CI width {ci_width} seems unreasonable"

    def test_analyze_baseline_results_integration(self, mock_baseline_data):
        """Test the full analyze_baseline_results function."""
        results_dir, dataset, size, method = mock_baseline_data
        
        null_path = results_dir / f"{dataset}_{size}_{method}_null.json"
        alt_path = results_dir / f"{dataset}_{size}_{method}_alt.json"
        
        # Run the analysis function
        analysis_result = analyze_baseline_results(null_path, alt_path)
        
        # Verify structure
        assert "type_i_error" in analysis_result
        assert "type_ii_error" in analysis_result
        assert "power" in analysis_result
        assert "ci_type_i" in analysis_result
        assert "ci_type_ii" in analysis_result
        
        # Verify values
        assert 0.0 < analysis_result["type_i_error"] < 1.0
        assert 0.0 < analysis_result["type_ii_error"] < 1.0
        assert analysis_result["power"] == (1.0 - analysis_result["type_ii_error"])
        
        # Verify CI structure
        assert len(analysis_result["ci_type_i"]) == 2
        assert len(analysis_result["ci_type_ii"]) == 2

    def test_comparative_analysis_with_multiple_augmentations(self, mock_baseline_data, temp_results_dir):
        """
        Test comparative analysis when multiple augmentation methods are present.
        Simulates the scenario where we compare baseline vs SMOTE vs Random Oversampling.
        """
        # Create a second augmented dataset (Random Oversampling)
        # Simulate a scenario where Type I error is ~0.08 (Safe but inflated)
        null_p_values_ro = np.random.uniform(0.0, 1.0, 1000)
        null_p_values_ro[:80] = np.random.uniform(0.0, 0.05, 80)
        
        ro_null = {
            "metadata": {
                "dataset": "test_dataset",
                "size": 25,
                "condition": "null",
                "method": "random_oversampling",
                "iterations": 1000,
                "seed": 42
            },
            "p_values": null_p_values_ro.tolist(),
            "error_rate": 0.08,
            "ci_lower": 0.06,
            "ci_upper": 0.10
        }
        
        ro_path = temp_results_dir / "test_dataset_25_random_oversampling_null.json"
        with open(ro_path, 'w') as f:
            json.dump(ro_null, f)
        
        # Load baseline and both augmentations
        base_dir, dataset, size, _ = mock_baseline_data
        
        base_null = load_simulation_results(base_dir / f"{dataset}_{size}_baseline_null.json")
        smote_null = load_simulation_results(temp_results_dir.parent / f"{dataset}_{size}_smote_null.json")
        ro_null_data = load_simulation_results(ro_path)
        
        base_type_i = calculate_error_rates(base_null["p_values"])
        smote_type_i = calculate_error_rates(smote_null["p_values"])
        ro_type_i = calculate_error_rates(ro_null_data["p_values"])
        
        # Compare
        smote_diff = smote_type_i - base_type_i
        ro_diff = ro_type_i - base_type_i
        
        # SMOTE should have a larger increase in Type I error than RO
        # (Based on our mock data: SMOTE ~0.15, RO ~0.08, Base ~0.05)
        assert smote_diff > ro_diff, "SMOTE should show a larger Type I error increase than RO"
        
        # Verify unsafe detection for SMOTE only
        assert smote_type_i > 0.10, "SMOTE should be flagged as unsafe"
        assert ro_type_i <= 0.10, "RO should NOT be flagged as unsafe"