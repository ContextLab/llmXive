"""
Integration tests for User Story 3 (Statistical Analysis and Correlation).

Specifically targets T035: Multiple-comparison correction (Bonferroni/BH).

This test verifies that the analysis module correctly applies multiple-comparison
corrections to p-values when testing multiple hypotheses (e.g., correlation between
different defect types and conductivity).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pytest
from scipy import stats

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis import (
    perform_linear_regression,
    apply_multiple_comparison_correction,
    run_statistical_analysis,
)
from models import AnalysisResult

# Constants for testing
TEST_DATA_FILE = "data/processed/test_analysis_data.json"
EXPECTED_CORRECTIONS = ["bonferroni", "benjamini-hochberg"]


def generate_synthetic_analysis_data(n_samples: int = 50) -> Dict[str, Any]:
    """
    Generate synthetic data for testing statistical analysis.
    
    This creates a realistic dataset with defect energies, defect densities,
    and ionic conductivity values.
    
    Args:
        n_samples: Number of samples to generate
        
    Returns:
        Dictionary containing the synthetic dataset
    """
    np.random.seed(42)  # Reproducibility
    
    # Generate defect formation energies (Ef) - typically 0.5 to 3.0 eV
    defect_formation_energy = np.random.uniform(0.5, 3.0, n_samples)
    
    # Generate migration barriers (Em) - typically 0.2 to 0.8 eV
    migration_barrier = np.random.uniform(0.2, 0.8, n_samples)
    
    # Calculate total activation energy
    total_activation_energy = defect_formation_energy + migration_barrier
    
    # Generate defect densities (defects/volume) - typically 1e18 to 1e21 cm^-3
    defect_density = np.random.uniform(1e18, 1e21, n_samples)
    
    # Generate ionic conductivity (log scale, typically 1e-8 to 1e-3 S/cm)
    # Create a negative correlation with activation energy (higher Ea = lower conductivity)
    base_conductivity = 1e-3
    conductivity = base_conductivity * np.exp(-total_activation_energy * 2)
    # Add some noise
    conductivity *= np.random.lognormal(0, 0.1, n_samples)
    
    # Generate multiple defect type energies for multiple hypothesis testing
    vacancy_energy = defect_formation_energy + np.random.normal(0, 0.1, n_samples)
    interstitial_energy = defect_formation_energy + np.random.normal(0, 0.1, n_samples)
    antisite_energy = defect_formation_energy + np.random.normal(0, 0.1, n_samples)
    
    data = {
        "samples": n_samples,
        "variables": {
            "total_activation_energy": total_activation_energy.tolist(),
            "defect_formation_energy": defect_formation_energy.tolist(),
            "migration_barrier": migration_barrier.tolist(),
            "defect_density": defect_density.tolist(),
            "ionic_conductivity": conductivity.tolist(),
            "vacancy_energy": vacancy_energy.tolist(),
            "interstitial_energy": interstitial_energy.tolist(),
            "antisite_energy": antisite_energy.tolist(),
        },
        "metadata": {
            "source": "synthetic_test_data",
            "generated_at": "2026-06-28T12:00:00Z",
            "test_purpose": "multiple_comparison_correction"
        }
    }
    
    return data


def save_test_data(data: Dict[str, Any], filepath: Path) -> None:
    """Save synthetic data to a JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


class TestMultipleComparisonCorrection:
    """
    Integration tests for multiple-comparison correction methods.
    
    These tests verify that:
    1. Bonferroni correction is correctly applied
    2. Benjamini-Hochberg (BH) procedure is correctly applied
    3. Corrected p-values maintain proper ordering and bounds
    4. The analysis pipeline integrates correction correctly
    """
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmp_path):
        """Setup test environment and clean up after tests."""
        self.tmp_path = tmp_path
        self.test_data_path = self.tmp_path / "test_analysis_data.json"
        
        # Generate and save synthetic test data
        test_data = generate_synthetic_analysis_data(n_samples=50)
        save_test_data(test_data, self.test_data_path)
        
        yield
        
        # Cleanup (tmp_path is automatically cleaned by pytest)
        pass
    
    def test_bonferroni_correction_applied(self):
        """
        Test that Bonferroni correction is correctly applied to p-values.
        
        Bonferroni correction: p_corrected = min(p * m, 1.0)
        where m is the number of hypotheses tested.
        """
        # Load test data
        with open(self.test_data_path, 'r') as f:
            data = json.load(f)
        
        # Extract variables for multiple hypothesis testing
        # We'll test correlation of 3 defect types with conductivity
        y = np.array(data["variables"]["ionic_conductivity"])
        X_vacancy = np.array(data["variables"]["vacancy_energy"])
        X_interstitial = np.array(data["variables"]["interstitial_energy"])
        X_antisite = np.array(data["variables"]["antisite_energy"])
        
        # Perform individual regressions and collect p-values
        p_values = []
        X_list = [X_vacancy, X_interstitial, X_antisite]
        
        for X in X_list:
            # Simple linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)
            p_values.append(p_value)
        
        p_values = np.array(p_values)
        m = len(p_values)  # Number of hypotheses
        
        # Apply Bonferroni correction using the analysis module
        corrected_pvalues_bonf = apply_multiple_comparison_correction(
            p_values, method="bonferroni"
        )
        
        # Verify Bonferroni correction logic
        expected_bonf = np.minimum(p_values * m, 1.0)
        
        # Check that corrected values are close to expected
        np.testing.assert_array_almost_equal(
            corrected_pvalues_bonf, 
            expected_bonf,
            decimal=10,
            err_msg="Bonferroni correction formula incorrect"
        )
        
        # Verify that all corrected p-values are <= 1.0
        assert np.all(corrected_pvalues_bonf <= 1.0), \
            "Bonferroni corrected p-values exceed 1.0"
        
        # Verify that corrected p-values are >= original p-values
        assert np.all(corrected_pvalues_bonf >= p_values), \
            "Bonferroni correction should not decrease p-values"
        
        print(f"✓ Bonferroni correction verified for {m} hypotheses")
        print(f"  Original p-values: {p_values}")
        print(f"  Corrected p-values: {corrected_pvalues_bonf}")
    
    def test_benjamini_hochberg_correction_applied(self):
        """
        Test that Benjamini-Hochberg (BH) correction is correctly applied.
        
        BH procedure controls the False Discovery Rate (FDR).
        Steps:
        1. Sort p-values: p(1) <= p(2) <= ... <= p(m)
        2. Find largest k such that p(k) <= (k/m) * alpha
        3. Reject all hypotheses for i <= k
        
        The corrected p-value for hypothesis i is:
        p_bh(i) = min( (m/i) * p(i), p_bh(i+1) ) for i from m down to 1
        """
        # Load test data
        with open(self.test_data_path, 'r') as f:
            data = json.load(f)
        
        # Extract variables
        y = np.array(data["variables"]["ionic_conductivity"])
        X_vacancy = np.array(data["variables"]["vacancy_energy"])
        X_interstitial = np.array(data["variables"]["interstitial_energy"])
        X_antisite = np.array(data["variables"]["antisite_energy"])
        
        # Perform individual regressions
        p_values = []
        X_list = [X_vacancy, X_interstitial, X_antisite]
        
        for X in X_list:
            slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)
            p_values.append(p_value)
        
        p_values = np.array(p_values)
        m = len(p_values)
        
        # Apply BH correction using the analysis module
        corrected_pvalues_bh = apply_multiple_comparison_correction(
            p_values, method="benjamini-hochberg"
        )
        
        # Verify BH correction logic manually
        # Sort p-values and keep track of original indices
        sorted_indices = np.argsort(p_values)
        sorted_pvalues = p_values[sorted_indices]
        
        # Calculate BH corrected p-values
        bh_corrected = np.zeros(m)
        for i in range(m):
            rank = i + 1  # 1-indexed rank
            bh_corrected[i] = (m / rank) * sorted_pvalues[i]
        
        # Ensure monotonicity (cumulative min from the end)
        for i in range(m - 2, -1, -1):
            bh_corrected[i] = min(bh_corrected[i], bh_corrected[i + 1])
        
        # Clip to [0, 1]
        bh_corrected = np.clip(bh_corrected, 0, 1)
        
        # Reorder back to original indices
        expected_bh = np.zeros(m)
        expected_bh[sorted_indices] = bh_corrected
        
        # Check that corrected values are close to expected
        np.testing.assert_array_almost_equal(
            corrected_pvalues_bh,
            expected_bh,
            decimal=10,
            err_msg="Benjamini-Hochberg correction formula incorrect"
        )
        
        # Verify monotonicity in sorted order
        sorted_corrected = corrected_pvalues_bh[np.argsort(p_values)]
        assert np.all(np.diff(sorted_corrected) >= -1e-10), \
            "BH corrected p-values should be monotonically non-decreasing"
        
        # Verify all corrected p-values are <= 1.0
        assert np.all(corrected_pvalues_bh <= 1.0), \
            "BH corrected p-values exceed 1.0"
        
        # Verify that corrected p-values are >= original p-values
        assert np.all(corrected_pvalues_bh >= p_values), \
            "BH correction should not decrease p-values"
        
        print(f"✓ Benjamini-Hochberg correction verified for {m} hypotheses")
        print(f"  Original p-values: {p_values}")
        print(f"  Corrected p-values: {corrected_pvalues_bh}")
    
    def test_correction_method_selection(self):
        """Test that the correct method is selected and applied."""
        p_values = np.array([0.01, 0.03, 0.05, 0.10, 0.20])
        
        # Test Bonferroni
        bonf_result = apply_multiple_comparison_correction(p_values, method="bonferroni")
        assert bonf_result is not None
        assert len(bonf_result) == len(p_values)
        
        # Test Benjamini-Hochberg
        bh_result = apply_multiple_comparison_correction(p_values, method="benjamini-hochberg")
        assert bh_result is not None
        assert len(bh_result) == len(p_values)
        
        # Test invalid method (should raise ValueError)
        with pytest.raises(ValueError, match="Unknown correction method"):
            apply_multiple_comparison_correction(p_values, method="invalid_method")
        
        print("✓ Method selection and error handling verified")
    
    def test_integration_with_analysis_pipeline(self):
        """
        Test that multiple-comparison correction is integrated into the full analysis pipeline.
        
        This verifies that run_statistical_analysis correctly calls the correction
        function and includes corrected p-values in the results.
        """
        # Run the full analysis pipeline
        results = run_statistical_analysis(
            input_path=str(self.test_data_path),
            output_path=str(self.tmp_path / "analysis_results.json"),
            correction_method="bonferroni"
        )
        
        # Verify results structure
        assert isinstance(results, AnalysisResult)
        assert results.correction_method == "bonferroni"
        assert results.correction_applied is True
        
        # Verify that multiple hypothesis tests were performed
        assert len(results.regression_results) > 0
        
        # Verify that corrected p-values are present
        for reg_result in results.regression_results:
            assert hasattr(reg_result, 'p_value_corrected')
            assert reg_result.p_value_corrected is not None
            assert 0 <= reg_result.p_value_corrected <= 1.0
        
        # Verify output file was created
        output_file = Path(self.tmp_path) / "analysis_results.json"
        assert output_file.exists(), "Analysis results file was not created"
        
        # Verify JSON structure
        with open(output_file, 'r') as f:
            json_data = json.load(f)
        
        assert "correction_method" in json_data
        assert json_data["correction_method"] == "bonferroni"
        assert "correction_applied" in json_data
        assert json_data["correction_applied"] is True
        
        print("✓ Full analysis pipeline integration verified")
        print(f"  Correction method: {results.correction_method}")
        print(f"  Number of hypotheses tested: {len(results.regression_results)}")
    
    def test_statistical_power_with_correction(self):
        """
        Test that statistical power calculations are consistent with corrected p-values.
        
        This ensures that the multiple-comparison correction doesn't invalidate
        the power analysis (T043).
        """
        # Load test data
        with open(self.test_data_path, 'r') as f:
            data = json.load(f)
        
        y = np.array(data["variables"]["ionic_conductivity"])
        X = np.array(data["variables"]["total_activation_energy"])
        
        # Perform regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)
        
        # Calculate effect size (Cohen's f^2)
        r_squared = r_value ** 2
        effect_size = r_squared / (1 - r_squared) if r_squared < 1 else 10.0
        
        # Apply Bonferroni correction
        corrected_p = apply_multiple_comparison_correction(np.array([p_value]), method="bonferroni")[0]
        
        # Verify that corrected p-value is more conservative
        assert corrected_p >= p_value, "Corrected p-value should be >= original p-value"
        
        # For a single hypothesis, Bonferroni should just multiply by 1 (no change)
        # But if we pretend there are multiple tests, it should increase
        m = 5  # Assume 5 tests
        expected_corrected = min(p_value * m, 1.0)
        assert abs(corrected_p - expected_corrected) < 1e-10, \
            f"Bonferroni correction mismatch: {corrected_p} vs {expected_corrected}"
        
        print("✓ Statistical power consistency verified")
        print(f"  Original p-value: {p_value:.4f}")
        print(f"  Corrected p-value (m=5): {corrected_p:.4f}")
        print(f"  Effect size (f^2): {effect_size:.4f}")
    
    def test_edge_cases(self):
        """Test edge cases in multiple-comparison correction."""
        
        # Empty array
        with pytest.raises((ValueError, IndexError)):
            apply_multiple_comparison_correction(np.array([]), method="bonferroni")
        
        # Single p-value
        single_p = np.array([0.05])
        bonf_single = apply_multiple_comparison_correction(single_p, method="bonferroni")
        assert np.isclose(bonf_single[0], 0.05), "Single p-value should not change with Bonferroni"
        
        bh_single = apply_multiple_comparison_correction(single_p, method="benjamini-hochberg")
        assert np.isclose(bh_single[0], 0.05), "Single p-value should not change with BH"
        
        # All p-values = 1.0
        all_ones = np.array([1.0, 1.0, 1.0])
        bonf_ones = apply_multiple_comparison_correction(all_ones, method="bonferroni")
        assert np.all(bonf_ones == 1.0), "P-values of 1.0 should remain 1.0"
        
        # Very small p-values
        tiny_p = np.array([1e-10, 1e-9, 1e-8])
        bonf_tiny = apply_multiple_comparison_correction(tiny_p, method="bonferroni")
        assert np.all(bonf_tiny <= 1.0), "Tiny p-values should be correctly capped"
        
        print("✓ Edge cases handled correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
