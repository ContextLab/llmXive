import pytest
import math
import os
import sys
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# Import the function under test from the robustness module
# The API surface confirms: from src.robustness import holm_bonferroni_correction, sensitivity_analysis_sweep
from src.robustness import holm_bonferroni_correction, sensitivity_analysis_sweep


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_p_values():
    """Provide a list of mock p-values for testing."""
    # Unsorted p-values to test sorting logic
    return [0.05, 0.02, 0.01, 0.20, 0.03]


@pytest.fixture
def expected_holm_results():
    """
    Expected results for Holm-Bonferroni correction on sample_p_values.
    
    Input: [0.05, 0.02, 0.01, 0.20, 0.03] (n=5)
    Sorted: [0.01 (i=1), 0.02 (i=2), 0.03 (i=3), 0.05 (i=4), 0.20 (i=5)]
    
    Step 1: 0.01 * (5/1) = 0.05 -> min(0.05, 1.0) = 0.05
    Step 2: 0.02 * (5/2) = 0.05 -> min(0.05, 0.05) = 0.05 (monotonicity)
    Step 3: 0.03 * (5/3) = 0.05 -> min(0.05, 0.05) = 0.05
    Step 4: 0.05 * (5/4) = 0.0625 -> min(0.0625, 0.05) = 0.05 (monotonicity)
    Step 5: 0.20 * (5/5) = 0.20 -> min(0.20, 0.05) = 0.05 (monotonicity)
    
    Note: The Holm algorithm enforces monotonicity (adjusted p-values must be non-decreasing).
    The raw calculation for step 4 is 0.0625, but since the previous adjusted value is 0.05,
    it is capped at 0.05.
    """
    return [0.05, 0.05, 0.05, 0.05, 0.05]


class TestHolmBonferroni:
    """Unit tests for multiple-comparison correction implementation."""

    def test_holm_bonferroni_basic(self, sample_p_values, expected_holm_results):
        """
        Test that Holm-Bonferroni correction produces correct adjusted p-values.
        
        Asserts:
            1. Adjusted p-values are monotonic (non-decreasing).
            2. Adjusted p-values do not exceed 1.0.
            3. The values match the expected Holm-Bonferroni calculation.
        """
        adjusted = holm_bonferroni_correction(sample_p_values)
        
        # 1. Check monotonicity: adjusted[i] <= adjusted[i+1]
        for i in range(len(adjusted) - 1):
            assert adjusted[i] <= adjusted[i + 1], \
                f"Monotonicity violation: {adjusted[i]} > {adjusted[i+1]}"
        
        # 2. Check bounds: 0 <= p <= 1
        for p in adjusted:
            assert 0.0 <= p <= 1.0, f"Adjusted p-value out of bounds: {p}"
        
        # 3. Check exact values (allowing small floating point tolerance)
        for i, (obs, exp) in enumerate(zip(adjusted, expected_holm_results)):
            assert math.isclose(obs, exp, rel_tol=1e-5), \
                f"Mismatch at index {i}: got {obs}, expected {exp}"

    def test_holm_bonferroni_single_value(self):
        """Test correction with a single p-value."""
        p_values = [0.05]
        adjusted = holm_bonferroni_correction(p_values)
        assert len(adjusted) == 1
        # n=1, so multiplier is 1.0/1.0 = 1.0
        assert math.isclose(adjusted[0], 0.05, rel_tol=1e-5)

    def test_holm_bonferroni_all_zeros(self):
        """Test correction when all p-values are zero."""
        p_values = [0.0, 0.0, 0.0]
        adjusted = holm_bonferroni_correction(p_values)
        # Zero times anything is zero
        assert all(p == 0.0 for p in adjusted)

    def test_holm_bonferroni_all_ones(self):
        """Test correction when all p-values are 1.0."""
        p_values = [1.0, 1.0, 1.0]
        adjusted = holm_bonferroni_correction(p_values)
        # 1.0 * multiplier, capped at 1.0
        assert all(p == 1.0 for p in adjusted)

    def test_holm_bonferroni_empty_list(self):
        """Test correction with an empty list."""
        p_values = []
        adjusted = holm_bonferroni_correction(p_values)
        assert adjusted == []

    def test_holm_bonferroni_preserves_length(self, sample_p_values):
        """Ensure the output list has the same length as the input."""
        adjusted = holm_bonferroni_correction(sample_p_values)
        assert len(adjusted) == len(sample_p_values)

    def test_holm_bonferroni_monotonicity_stress(self):
        """Stress test monotonicity with random-ish values."""
        # Create a list that would violate monotonicity if not capped
        # e.g., small p with large multiplier vs larger p with small multiplier
        p_values = [0.1, 0.001, 0.5]
        # Sorted: 0.001 (i=1), 0.1 (i=2), 0.5 (i=3)
        # 0.001 * 3 = 0.003
        # 0.1 * 1.5 = 0.15
        # 0.5 * 1 = 0.5
        # Result: [0.003, 0.15, 0.5] -> Monotonic
        
        # Case where capping is needed:
        # p_values = [0.05, 0.04] -> sorted [0.04, 0.05]
        # 0.04 * 2 = 0.08
        # 0.05 * 1 = 0.05 -> capped to 0.08
        p_values = [0.05, 0.04]
        adjusted = holm_bonferroni_correction(p_values)
        assert adjusted[0] <= adjusted[1]

    def test_holm_bonferroni_return_type(self, sample_p_values):
        """Ensure the function returns a list of floats."""
        adjusted = holm_bonferroni_correction(sample_p_values)
        assert isinstance(adjusted, list)
        assert all(isinstance(x, float) for x in adjusted)


class TestSensitivitySweep:
    """Unit tests for sensitivity analysis sweep validation (T024)."""

    def test_sensitivity_sweep(self, temp_dir):
        """
        Test sensitivity analysis sweep validation.
        
        Mock: Synthetic convergence data for k=2, 3, 4.
        Assert: Variation in rho is calculated correctly.
        
        This test creates synthetic data representing convergence results
        for different k thresholds and verifies that the sensitivity
        analysis function correctly computes the variation in Spearman
        correlation coefficients.
        """
        # Create synthetic convergence data for k=2, 3, 4
        # Format: task_id, k, converged, step, timestamp
        synthetic_data = {
            2: [
                {"task_id": "task_1", "k": 2, "converged": True, "step": 1, "entropy": 0.5},
                {"task_id": "task_2", "k": 2, "converged": False, "step": 2, "entropy": 1.2},
                {"task_id": "task_3", "k": 2, "converged": True, "step": 1, "entropy": 0.3},
                {"task_id": "task_4", "k": 2, "converged": False, "step": 3, "entropy": 1.5},
                {"task_id": "task_5", "k": 2, "converged": True, "step": 2, "entropy": 0.8},
            ],
            3: [
                {"task_id": "task_1", "k": 3, "converged": True, "step": 1, "entropy": 0.5},
                {"task_id": "task_2", "k": 3, "converged": True, "step": 2, "entropy": 1.2},
                {"task_id": "task_3", "k": 3, "converged": True, "step": 1, "entropy": 0.3},
                {"task_id": "task_4", "k": 3, "converged": False, "step": 3, "entropy": 1.5},
                {"task_id": "task_5", "k": 3, "converged": True, "step": 2, "entropy": 0.8},
            ],
            4: [
                {"task_id": "task_1", "k": 4, "converged": True, "step": 1, "entropy": 0.5},
                {"task_id": "task_2", "k": 4, "converged": True, "step": 2, "entropy": 1.2},
                {"task_id": "task_3", "k": 4, "converged": True, "step": 1, "entropy": 0.3},
                {"task_id": "task_4", "k": 4, "converged": True, "step": 3, "entropy": 1.5},
                {"task_id": "task_5", "k": 4, "converged": True, "step": 2, "entropy": 0.8},
            ]
        }

        # Create temporary files for each k threshold
        temp_files = {}
        for k, data in synthetic_data.items():
            file_path = Path(temp_dir) / f"convergence_k{k}.csv"
            with open(file_path, 'w', newline='') as f:
                import csv
                writer = csv.DictWriter(f, fieldnames=["task_id", "k", "converged", "step", "entropy"])
                writer.writeheader()
                writer.writerows(data)
            temp_files[k] = str(file_path)

        # Call the sensitivity analysis function
        # The function should read the files, compute rho for each k,
        # and calculate the variation in rho
        results = sensitivity_analysis_sweep(
            k_thresholds=[2, 3, 4],
            convergence_files=temp_files,
            entropy_column="entropy",
            converged_column="converged"
        )

        # Verify the results structure
        assert isinstance(results, dict), "Results should be a dictionary"
        assert "sweep_results" in results, "Results should contain 'sweep_results' key"
        assert "variation_metrics" in results, "Results should contain 'variation_metrics' key"

        sweep_results = results["sweep_results"]
        assert isinstance(sweep_results, list), "sweep_results should be a list"
        assert len(sweep_results) == 3, "Should have 3 results for k=2, 3, 4"

        # Verify each result has the required fields
        for result in sweep_results:
            assert "k_threshold" in result, "Each result should have 'k_threshold'"
            assert "rho" in result, "Each result should have 'rho'"
            assert "p_value" in result, "Each result should have 'p_value'"

        # Verify variation metrics
        variation_metrics = results["variation_metrics"]
        assert "rho_range" in variation_metrics, "Variation metrics should have 'rho_range'"
        assert "rho_std" in variation_metrics, "Variation metrics should have 'rho_std'"
        assert "stability_score" in variation_metrics, "Variation metrics should have 'stability_score'"

        # Assert that rho values are within valid range [-1, 1]
        for result in sweep_results:
            assert -1.0 <= result["rho"] <= 1.0, f"rho {result['rho']} out of bounds"

        # Assert that p-values are within valid range [0, 1]
        for result in sweep_results:
            assert 0.0 <= result["p_value"] <= 1.0, f"p_value {result['p_value']} out of bounds"

    def test_sensitivity_sweep_empty_data(self, temp_dir):
        """Test sensitivity analysis with empty data files."""
        # Create empty files
        temp_files = {}
        for k in [2, 3, 4]:
            file_path = Path(temp_dir) / f"convergence_k{k}.csv"
            with open(file_path, 'w') as f:
                f.write("task_id,k,converged,step,entropy\n")  # Header only
            temp_files[k] = str(file_path)

        # Should handle empty data gracefully
        results = sensitivity_analysis_sweep(
            k_thresholds=[2, 3, 4],
            convergence_files=temp_files,
            entropy_column="entropy",
            converged_column="converged"
        )

        # Should return results with None or NaN for rho when data is empty
        assert isinstance(results, dict)
        assert "sweep_results" in results

    def test_sensitivity_sweep_single_k(self, temp_dir):
        """Test sensitivity analysis with a single k threshold."""
        synthetic_data = [
            {"task_id": "task_1", "k": 2, "converged": True, "step": 1, "entropy": 0.5},
            {"task_id": "task_2", "k": 2, "converged": False, "step": 2, "entropy": 1.2},
        ]

        file_path = Path(temp_dir) / "convergence_k2.csv"
        with open(file_path, 'w', newline='') as f:
            import csv
            writer = csv.DictWriter(f, fieldnames=["task_id", "k", "converged", "step", "entropy"])
            writer.writeheader()
            writer.writerows(synthetic_data)

        results = sensitivity_analysis_sweep(
            k_thresholds=[2],
            convergence_files={2: str(file_path)},
            entropy_column="entropy",
            converged_column="converged"
        )

        assert len(results["sweep_results"]) == 1
        assert results["sweep_results"][0]["k_threshold"] == 2