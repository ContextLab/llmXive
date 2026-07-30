import pytest
import json
import os
import sys
import numpy as np
from unittest.mock import patch, mock_open

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.validation import (
    apply_bonferroni_correction,
    bootstrap_correlation,
    verify_ci_precision,
    perform_hypothesis_tests,
    check_sales_data_availability,
    load_hypothesis_tests
)

class TestBonferroniCorrection:
    """Tests for Bonferroni correction functionality (T024)."""
    
    def test_bonferroni_basic_calculation(self):
        """Test basic Bonferroni correction calculation."""
        hypothesis_results = {
            "birthday_test": {"p_value": 0.03},
            "consecutive_test": {"p_value": 0.07}
        }
        
        result = apply_bonferroni_correction(hypothesis_results, alpha=0.05)
        
        # Should have 2 tests
        assert result["number_of_tests"] == 2
        
        # Corrected alpha should be 0.05 / 2 = 0.025
        assert abs(result["corrected_alpha"] - 0.025) < 1e-10
        
        # Adjusted p-values should be p * 2, capped at 1.0
        assert abs(result["adjusted_p_values"]["birthday"] - 0.06) < 1e-10
        assert abs(result["adjusted_p_values"]["consecutive"] - 0.14) < 1e-10
        
        # Neither should be significant at corrected alpha
        assert result["significance_results"]["birthday"]["is_significant"] is False
        assert result["significance_results"]["consecutive"]["is_significant"] is False
    
    def test_bonferroni_significant_result(self):
        """Test Bonferroni correction with a significant result."""
        hypothesis_results = {
            "birthday_test": {"p_value": 0.01},
            "consecutive_test": {"p_value": 0.15}
        }
        
        result = apply_bonferroni_correction(hypothesis_results, alpha=0.05)
        
        # Adjusted birthday p-value: 0.01 * 2 = 0.02
        # Corrected alpha: 0.025
        # 0.02 < 0.025, so significant
        assert result["significance_results"]["birthday"]["is_significant"] is True
        assert abs(result["adjusted_p_values"]["birthday"] - 0.02) < 1e-10
        
        # Consecutive: 0.15 * 2 = 0.30 > 0.025, not significant
        assert result["significance_results"]["consecutive"]["is_significant"] is False
    
    def test_bonferroni_p_value_capping(self):
        """Test that p-values are capped at 1.0."""
        hypothesis_results = {
            "birthday_test": {"p_value": 0.6},
            "consecutive_test": {"p_value": 0.8}
        }
        
        result = apply_bonferroni_correction(hypothesis_results, alpha=0.05)
        
        # 0.6 * 2 = 1.2 -> capped at 1.0
        assert result["adjusted_p_values"]["birthday"] == 1.0
        # 0.8 * 2 = 1.6 -> capped at 1.0
        assert result["adjusted_p_values"]["consecutive"] == 1.0
    
    def test_bonferroni_custom_alpha(self):
        """Test Bonferroni correction with custom alpha."""
        hypothesis_results = {
            "birthday_test": {"p_value": 0.04},
            "consecutive_test": {"p_value": 0.06}
        }
        
        result = apply_bonferroni_correction(hypothesis_results, alpha=0.10)
        
        # Corrected alpha: 0.10 / 2 = 0.05
        assert abs(result["corrected_alpha"] - 0.05) < 1e-10
        
        # Adjusted p-values
        assert abs(result["adjusted_p_values"]["birthday"] - 0.08) < 1e-10
        assert abs(result["adjusted_p_values"]["consecutive"] - 0.12) < 1e-10
    
    def test_bonferroni_single_test(self):
        """Test Bonferroni correction with hypothetical single test scenario."""
        # In our case, we always have 2 tests, but test the logic
        hypothesis_results = {
            "birthday_test": {"p_value": 0.03},
            "consecutive_test": {"p_value": 0.03}
        }
        
        result = apply_bonferroni_correction(hypothesis_results, alpha=0.05)
        
        # Both have same p-value, both adjusted to 0.06
        assert result["adjusted_p_values"]["birthday"] == result["adjusted_p_values"]["consecutive"]
    
    def test_bonferroni_output_structure(self):
        """Test that output structure matches expected schema."""
        hypothesis_results = {
            "birthday_test": {"p_value": 0.05},
            "consecutive_test": {"p_value": 0.10}
        }
        
        result = apply_bonferroni_correction(hypothesis_results)
        
        # Check required keys
        assert "original_alpha" in result
        assert "number_of_tests" in result
        assert "corrected_alpha" in result
        assert "adjusted_p_values" in result
        assert "significance_results" in result
        assert "method" in result
        
        # Check nested structure
        assert "birthday" in result["significance_results"]
        assert "consecutive" in result["significance_results"]
        assert "adjusted_p_value" in result["significance_results"]["birthday"]
        assert "is_significant" in result["significance_results"]["birthday"]
        assert "original_p_value" in result["significance_results"]["birthday"]

class TestBootstrapCorrelation:
    """Tests for bootstrap correlation functionality."""
    
    def test_bootstrap_basic(self):
        """Test basic bootstrap correlation calculation."""
        data = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        result = bootstrap_correlation(data, iterations=100)
        
        assert "mean" in result
        assert "std" in result
        assert "ci_95_lower" in result
        assert "ci_95_upper" in result
        assert "iterations" in result
        
        # Mean should be close to 0.3
        assert 0.25 < result["mean"] < 0.35
        
        # CI lower should be less than CI upper
        assert result["ci_95_lower"] < result["ci_95_upper"]
    
    def test_bootstrap_insufficient_data(self):
        """Test bootstrap with insufficient data points."""
        with pytest.raises(ValueError, match="Need at least 2 data points"):
            bootstrap_correlation([0.1], iterations=100)

class TestVerifyCIPrecision:
    """Tests for CI precision verification."""
    
    def test_precision_within_threshold(self):
        """Test when CI width is within precision threshold."""
        result = verify_ci_precision(ci_width=0.05, effect_size=0.5)
        
        assert result["is_precise"] is True
        assert result["warning"] is None
        
        # Precision threshold should be 0.2 * 0.5 = 0.1
        assert abs(result["precision_threshold"] - 0.1) < 1e-10
    
    def test_precision_exceeds_threshold(self):
        """Test when CI width exceeds precision threshold."""
        result = verify_ci_precision(ci_width=0.2, effect_size=0.5)
        
        assert result["is_precise"] is False
        assert result["warning"] == "CI width exceeds precision threshold"
    
    def test_precision_zero_effect_size(self):
        """Test precision check with zero effect size."""
        result = verify_ci_precision(ci_width=0.05, effect_size=0.0)
        
        # When effect_size is 0, precision_threshold defaults to 0.1
        assert abs(result["precision_threshold"] - 0.1) < 1e-10

class TestHypothesisTests:
    """Tests for hypothesis test functionality."""
    
    def test_hypothesis_tests_structure(self):
        """Test that hypothesis tests return expected structure."""
        dataframe = {
            "birthday_cluster_ratios": [0.3, 0.4, 0.5],
            "consecutive_pattern_counts": [1, 2, 3]
        }
        
        result = perform_hypothesis_tests(dataframe)
        
        assert "birthday_test" in result
        assert "consecutive_test" in result
        assert "p_value" in result["birthday_test"]
        assert "p_value" in result["consecutive_test"]
        assert "test_statistic" in result["birthday_test"]
        assert "alternative_hypothesis" in result["birthday_test"]

class TestSalesDataAvailability:
    """Tests for sales data availability check."""
    
    def test_sales_data_sufficient(self):
        """Test when sales data is sufficient."""
        dataframe = {
            "draws": [
                {"total_sales": 1000},
                {"total_sales": 2000},
                {"total_sales": 1500}
            ]
        }
        
        result = check_sales_data_availability(dataframe)
        
        assert result["is_sufficient"] is True
        assert result["missing_percentage"] == 0.0
        assert result["warning"] is None
    
    def test_sales_data_insufficient(self):
        """Test when sales data is insufficient."""
        dataframe = {
            "draws": [
                {"total_sales": 1000},
                {"total_sales": None},
                {"total_sales": None},
                {"total_sales": None},
                {"total_sales": None}
            ]
        }
        
        result = check_sales_data_availability(dataframe)
        
        # 4 out of 5 missing = 80%
        assert result["missing_percentage"] == 80.0
        assert result["is_sufficient"] is False
        assert result["warning"] == "Sales data insufficient for sales sensitivity analysis"
    
    def test_sales_data_empty(self):
        """Test with empty draws list."""
        dataframe = {"draws": []}
        
        result = check_sales_data_availability(dataframe)
        
        assert result["total_draws"] == 0
        assert result["missing_percentage"] == 100.0
        assert result["is_sufficient"] is False

class TestLoadHypothesisTests:
    """Tests for loading hypothesis tests from file."""
    
    def test_load_hypothesis_tests_success(self):
        """Test successful loading of hypothesis tests."""
        test_data = {
            "birthday_test": {"p_value": 0.05},
            "consecutive_test": {"p_value": 0.08}
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
            with patch('os.path.exists', return_value=True):
                result = load_hypothesis_tests("test_path.json")
                
                assert result == test_data
    
    def test_load_hypothesis_tests_file_not_found(self):
        """Test loading when file doesn't exist."""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError, match="Hypothesis tests file not found"):
                load_hypothesis_tests("nonexistent.json")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
