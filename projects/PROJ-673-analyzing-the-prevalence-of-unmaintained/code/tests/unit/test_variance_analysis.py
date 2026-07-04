"""
Unit tests for variance analysis functionality.
"""
import pytest
import numpy as np
from src.analysis.variance_analysis import (
    calculate_variance_and_comparisons,
    run_variance_analysis
)


class TestCalculateVarianceAndComparisons:
    """Tests for the calculate_variance_and_comparisons function."""
    
    def test_empty_stratified_results(self):
        """Test handling of empty stratified results."""
        result = calculate_variance_and_comparisons({}, 0.5)
        assert "error" in result
        assert result["error"] == "No stratified results provided"
    
    def test_single_category_no_variance(self):
        """Test that variance cannot be calculated with only one category."""
        stratified = {
            "category_a": {"rho": 0.7, "p_value": 0.01, "n_samples": 100}
        }
        result = calculate_variance_and_comparisons(stratified, 0.6)
        
        assert result["variance"] is None
        assert result["std_dev"] is None
        assert "Insufficient categories" in result.get("note", "")
    
    def test_two_categories_variance_calculation(self):
        """Test variance calculation with two categories."""
        stratified = {
            "category_a": {"rho": 0.7, "p_value": 0.01, "n_samples": 100},
            "category_b": {"rho": 0.9, "p_value": 0.001, "n_samples": 150}
        }
        overall = 0.8
        
        result = calculate_variance_and_comparisons(stratified, overall)
        
        # Manual calculation: variance of [0.7, 0.9] with ddof=1
        expected_variance = np.var([0.7, 0.9], ddof=1)
        expected_std = np.std([0.7, 0.9], ddof=1)
        
        assert abs(result["variance"] - expected_variance) < 1e-10
        assert abs(result["std_dev"] - expected_std) < 1e-10
        assert result["mean_category_rho"] == 0.8
        assert result["overall_correlation"] == overall
        assert result["n_categories"] == 2
    
    def test_comparisons_z_score_calculation(self):
        """Test that z-scores are calculated correctly for comparisons."""
        stratified = {
            "category_a": {"rho": 0.5, "p_value": 0.05, "n_samples": 50},
            "category_b": {"rho": 0.9, "p_value": 0.01, "n_samples": 100},
            "category_c": {"rho": 0.7, "p_value": 0.02, "n_samples": 75}
        }
        overall = 0.7
        
        result = calculate_variance_and_comparisons(stratified, overall)
        
        assert len(result["comparisons"]) == 3
        
        # Check that z-scores are present and calculated
        for comp in result["comparisons"]:
            assert "z_score" in comp
            assert "difference" in comp
            assert comp["category_rho"] - overall == comp["difference"]
    
    def test_significantly_different_flag(self):
        """Test that significantly_different is set based on z-score threshold."""
        stratified = {
            "category_a": {"rho": 0.2, "p_value": 0.01, "n_samples": 100},
            "category_b": {"rho": 0.8, "p_value": 0.01, "n_samples": 100}
        }
        overall = 0.5
        
        result = calculate_variance_and_comparisons(stratified, overall)
        
        # With only 2 categories, the variance will be large, so z-scores might not be extreme
        # but the logic should still be tested
        for comp in result["comparisons"]:
            if comp["z_score"] is not None:
                expected_significant = abs(comp["z_score"]) > 1.96
                assert comp["significantly_different"] == expected_significant


class TestRunVarianceAnalysis:
    """Tests for the run_variance_analysis function."""
    
    def test_missing_input_file(self, tmp_path):
        """Test handling of missing input file."""
        output_file = tmp_path / "results.json"
        result = run_variance_analysis(
            input_csv_path="nonexistent.csv",
            output_json_path=str(output_file)
        )
        assert "error" in result or "No data loaded" in str(result)
    
    def test_invalid_correlation_values(self):
        """Test handling of invalid correlation values in stratified results."""
        stratified = {
            "category_a": {"rho": None, "p_value": 0.01, "n_samples": 100},
            "category_b": {"rho": 0.5, "p_value": 0.02, "n_samples": 100}
        }
        result = calculate_variance_and_comparisons(stratified, 0.4)
        
        # Should only include categories with valid rho values
        assert result["n_categories"] == 1
        assert len(result["comparisons"]) == 1
        assert result["comparisons"][0]["category"] == "category_b"