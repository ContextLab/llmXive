"""
Unit tests for correlation analysis with census data handling.

Per FR-006 and Constitution Principle VII: Tests verify that p-values
are NOT reported for census data and are marked as 'not applicable for census data'.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.regression import (
    calculate_pearson_correlation,
    calculate_spearman_correlation,
    calculate_cohen_d,
    interpret_cohen_d,
    calculate_correlation_effect_size,
    run_regression_analysis,
    CorrelationResult,
    EffectSizeResult
)


class TestPearsonCorrelation:
    """Tests for Pearson correlation calculation."""
    
    def test_pearson_correlation_basic(self):
        """Test basic Pearson correlation calculation."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        corr, p_value = calculate_pearson_correlation(x, y, is_census_data=True)
        
        assert abs(corr - 1.0) < 1e-10, "Perfect positive correlation should be 1.0"
        assert p_value == "not applicable for census data", \
            "p-value should be marked as N/A for census data per FR-006"
    
    def test_pearson_correlation_negative(self):
        """Test negative Pearson correlation."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 8, 6, 4, 2])
        
        corr, p_value = calculate_pearson_correlation(x, y, is_census_data=True)
        
        assert abs(corr - (-1.0)) < 1e-10, "Perfect negative correlation should be -1.0"
        assert p_value == "not applicable for census data", \
            "p-value should be marked as N/A for census data per FR-006"
    
    def test_pearson_correlation_no_correlation(self):
        """Test zero correlation."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)
        
        corr, p_value = calculate_pearson_correlation(x, y, is_census_data=True)
        
        assert abs(corr) < 0.2, "Random data should have near-zero correlation"
        assert p_value == "not applicable for census data", \
            "p-value should be marked as N/A for census data per FR-006"
    
    def test_pearson_correlation_handles_nan(self):
        """Test that NaN values are handled correctly."""
        x = np.array([1, 2, np.nan, 4, 5])
        y = np.array([2, 4, 6, np.nan, 10])
        
        corr, p_value = calculate_pearson_correlation(x, y, is_census_data=True)
        
        # Should still calculate with remaining valid pairs
        assert not np.isnan(corr), "Correlation should not be NaN"
        assert p_value == "not applicable for census data", \
            "p-value should be marked as N/A for census data per FR-006"
    
    def test_pearson_correlation_census_data_exception(self):
        """
        CRITICAL TEST: Verify p-values are NOT reported for census data.
        
        Per FR-006 and Constitution Principle VII:
        "p-values are NOT reported for census data and marked as 'not applicable for census data'"
        """
        x = np.array([3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13])
        y = np.array([1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4])
        
        # Test with census data (is_census_data=True)
        corr_census, p_census = calculate_pearson_correlation(x, y, is_census_data=True)
        
        assert p_census == "not applicable for census data", \
            "FAIL: p-value MUST be 'not applicable for census data' for census data per FR-006"
        
        # Test with non-census data (is_census_data=False) - should calculate p-value
        corr_non_census, p_non_census = calculate_pearson_correlation(x, y, is_census_data=False)
        
        assert p_non_census != "not applicable for census data", \
            "p-value should be calculated for non-census data"
        assert isinstance(p_non_census, str), "p-value should be a string representation"
        # Should be a valid probability
        assert 0 <= float(p_non_census) <= 1, "p-value should be between 0 and 1"
    
    def test_pearson_correlation_error_on_mismatched_length(self):
        """Test error handling for mismatched array lengths."""
        x = np.array([1, 2, 3])
        y = np.array([1, 2])
        
        with pytest.raises(ValueError, match="same length"):
            calculate_pearson_correlation(x, y)
    
    def test_pearson_correlation_error_on_insufficient_data(self):
        """Test error handling for insufficient data points."""
        x = np.array([1])
        y = np.array([2])
        
        with pytest.raises(ValueError, match="at least 2"):
            calculate_pearson_correlation(x, y)


class TestSpearmanCorrelation:
    """Tests for Spearman correlation calculation."""
    
    def test_spearman_correlation_basic(self):
        """Test basic Spearman correlation calculation."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        corr, p_value = calculate_spearman_correlation(x, y, is_census_data=True)
        
        assert abs(corr - 1.0) < 1e-10, "Perfect positive correlation should be 1.0"
        assert p_value == "not applicable for census data", \
            "p-value should be marked as N/A for census data per FR-006"
    
    def test_spearman_correlation_census_data_exception(self):
        """
        CRITICAL TEST: Verify p-values are NOT reported for census data.
        
        Per FR-006 and Constitution Principle VII:
        "p-values are NOT reported for census data and marked as 'not applicable for census data'"
        """
        x = np.array([3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13])
        y = np.array([1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4])
        
        # Test with census data (is_census_data=True)
        corr_census, p_census = calculate_spearman_correlation(x, y, is_census_data=True)
        
        assert p_census == "not applicable for census data", \
            "FAIL: p-value MUST be 'not applicable for census data' for census data per FR-006"
    
    def test_spearman_correlation_handles_nan(self):
        """Test that NaN values are handled correctly."""
        x = np.array([1, 2, np.nan, 4, 5])
        y = np.array([2, 4, 6, np.nan, 10])
        
        corr, p_value = calculate_spearman_correlation(x, y, is_census_data=True)
        
        assert not np.isnan(corr), "Correlation should not be NaN"
        assert p_value == "not applicable for census data", \
            "p-value should be marked as N/A for census data per FR-006"
    
    def test_spearman_correlation_error_on_mismatched_length(self):
        """Test error handling for mismatched array lengths."""
        x = np.array([1, 2, 3])
        y = np.array([1, 2])
        
        with pytest.raises(ValueError, match="same length"):
            calculate_spearman_correlation(x, y)


class TestCohenD:
    """Tests for Cohen's d effect size calculation."""
    
    def test_cohen_d_positive_effect(self):
        """Test Cohen's d with positive effect."""
        group1 = np.array([5, 6, 7, 8, 9])
        group2 = np.array([2, 3, 4, 5, 6])
        
        d, interpretation = calculate_cohen_d(group1, group2)
        
        assert d > 0, "Cohen's d should be positive when group1 > group2"
        assert "effect" in interpretation.lower(), "Should have effect interpretation"
    
    def test_cohen_d_negative_effect(self):
        """Test Cohen's d with negative effect."""
        group1 = np.array([2, 3, 4, 5, 6])
        group2 = np.array([5, 6, 7, 8, 9])
        
        d, interpretation = calculate_cohen_d(group1, group2)
        
        assert d < 0, "Cohen's d should be negative when group1 < group2"
    
    def test_cohen_d_interpretation_negligible(self):
        """Test negligible effect size interpretation."""
        assert interpret_cohen_d(0.1) == "negligible effect"
    
    def test_cohen_d_interpretation_small(self):
        """Test small effect size interpretation."""
        assert interpret_cohen_d(0.3) == "small effect"
    
    def test_cohen_d_interpretation_medium(self):
        """Test medium effect size interpretation."""
        assert interpret_cohen_d(0.6) == "medium effect"
    
    def test_cohen_d_interpretation_large(self):
        """Test large effect size interpretation."""
        assert interpret_cohen_d(1.0) == "large effect"
    
    def test_cohen_d_handles_nan(self):
        """Test that NaN values are handled correctly."""
        group1 = np.array([5, 6, np.nan, 8, 9])
        group2 = np.array([2, 3, 4, 5, np.nan])
        
        d, interpretation = calculate_cohen_d(group1, group2)
        
        assert not np.isnan(d), "Cohen's d should not be NaN"
    
    def test_cohen_d_error_on_insufficient_data(self):
        """Test error handling for insufficient data."""
        group1 = np.array([1])
        group2 = np.array([2])
        
        with pytest.raises(ValueError, match="at least 2"):
            calculate_cohen_d(group1, group2)

class TestCorrelationEffectSize:
    """Tests for correlation-based effect size calculation."""
    
    def test_effect_size_negligible(self):
        """Test negligible correlation effect size."""
        result = calculate_correlation_effect_size(0.05, 100)
        
        assert result.effect_size_type == "correlation_r"
        assert result.interpretation == "negligible effect"
    
    def test_effect_size_small(self):
        """Test small correlation effect size."""
        result = calculate_correlation_effect_size(0.2, 100)
        
        assert result.effect_size_type == "correlation_r"
        assert result.interpretation == "small effect"
    
    def test_effect_size_medium(self):
        """Test medium correlation effect size."""
        result = calculate_correlation_effect_size(0.4, 100)
        
        assert result.effect_size_type == "correlation_r"
        assert result.interpretation == "medium effect"
    
    def test_effect_size_large(self):
        """Test large correlation effect size."""
        result = calculate_correlation_effect_size(0.7, 100)
        
        assert result.effect_size_type == "correlation_r"
        assert result.interpretation == "large effect"

class TestRegressionAnalysis:
    """Tests for full regression analysis."""
    
    def test_run_regression_analysis_census_data(self):
        """
        CRITICAL TEST: Verify full regression analysis handles census data correctly.
        
        Per FR-006 and Constitution Principle VII:
        p-values in all output artifacts must be marked as 'not applicable for census data'
        """
        # Create sample data
        np.random.seed(42)
        n = 50
        x = np.random.uniform(3, 13, n)
        y = 0.5 * x + np.random.normal(0, 0.5, n)
        
        df = pd.DataFrame({"crossing_number": x, "braid_index": y})
        
        # Run analysis
        report = run_regression_analysis(df, "crossing_number", "braid_index", is_census_data=True)
        
        # Verify census data note is present
        assert "census" in report.census_data_note.lower(), \
            "Report must document census data handling per FR-006"
        
        # Verify all correlation results have N/A p-values
        for corr_result in report.correlation_results:
            assert corr_result.p_value == "not applicable for census data", \
                f"FAIL: {corr_result.correlation_type} p-value MUST be 'not applicable for census data' per FR-006"
        
        # Verify effect sizes are calculated
        assert len(report.effect_size_results) > 0, "Effect sizes should be calculated"
    
    def test_run_regression_analysis_non_census_data(self):
        """Test that p-values ARE calculated for non-census data."""
        np.random.seed(42)
        n = 50
        x = np.random.uniform(3, 13, n)
        y = 0.5 * x + np.random.normal(0, 0.5, n)
        
        df = pd.DataFrame({"crossing_number": x, "braid_index": y})
        
        # Run analysis with non-census data
        report = run_regression_analysis(df, "crossing_number", "braid_index", is_census_data=False)
        
        # Verify p-values are calculated (not N/A)
        for corr_result in report.correlation_results:
            assert corr_result.p_value != "not applicable for census data", \
                "p-value should be calculated for non-census data"
    
    def test_run_regression_analysis_handles_nan(self):
        """Test that NaN values are handled correctly."""
        np.random.seed(42)
        n = 50
        x = np.random.uniform(3, 13, n)
        y = 0.5 * x + np.random.normal(0, 0.5, n)
        
        # Add some NaN values
        x[5] = np.nan
        y[10] = np.nan
        
        df = pd.DataFrame({"crossing_number": x, "braid_index": y})
        
        # Should not raise error
        report = run_regression_analysis(df, "crossing_number", "braid_index", is_census_data=True)
        
        # Sample size should be reduced
        assert report.sample_size < n, "NaN values should be excluded from analysis"
        assert report.sample_size > 0, "Should still have valid data points"

class TestCensusDataCompliance:
    """
    Compliance tests specifically for FR-006 and Constitution Principle VII.
    
    These tests ensure that p-values are NEVER reported for census data.
    """
    
    def test_no_p_values_in_census_correlation_results(self):
        """
        Verify correlation results contain no numeric p-values for census data.
        
        This is the primary verification requirement from FR-006:
        "explicitly verify p-values are NOT reported for census data and marked as 
        'not applicable for census data' in all output artifacts"
        """
        np.random.seed(42)
        x = np.random.uniform(3, 13, 100)
        y = 0.5 * x + np.random.normal(0, 0.5, 100)
        
        df = pd.DataFrame({"crossing_number": x, "braid_index": y})
        
        report = run_regression_analysis(df, "crossing_number", "braid_index", is_census_data=True)
        
        # Check all correlation results
        for corr_result in report.correlation_results:
            # Verify p_value is exactly the expected string
            assert corr_result.p_value == "not applicable for census data", \
                f"FAIL: p-value for {corr_result.correlation_type} must be exactly " \
                f"'not applicable for census data' per FR-006, got: {corr_result.p_value}"
            
            # Verify p_value is not a numeric string
            try:
                float(corr_result.p_value)
                assert False, "p-value should not be a numeric value for census data"
            except ValueError:
                pass  # Expected - it's the N/A string
    
    def test_census_data_note_present(self):
        """Verify census data explanation is documented in report."""
        np.random.seed(42)
        x = np.random.uniform(3, 13, 100)
        y = 0.5 * x + np.random.normal(0, 0.5, 100)
        
        df = pd.DataFrame({"crossing_number": x, "braid_index": y})
        
        report = run_regression_analysis(df, "crossing_number", "braid_index", is_census_data=True)
        
        # Verify census data note exists and is meaningful
        assert len(report.census_data_note) > 0, "Census data note must be present"
        assert "FR-006" in report.census_data_note or "Principle" in report.census_data_note, \
            "Note should reference FR-006 or Constitution Principle"
    
    def test_effect_sizes_always_calculated(self):
        """Verify effect sizes are always calculated regardless of census status."""
        np.random.seed(42)
        x = np.random.uniform(3, 13, 100)
        y = 0.5 * x + np.random.normal(0, 0.5, 100)
        
        df = pd.DataFrame({"crossing_number": x, "braid_index": y})
        
        # Test with census data
        report_census = run_regression_analysis(df, "crossing_number", "braid_index", is_census_data=True)
        
        # Test with non-census data
        report_non_census = run_regression_analysis(df, "crossing_number", "braid_index", is_census_data=False)
        
        # Both should have effect sizes
        assert len(report_census.effect_size_results) > 0, "Effect sizes required for census data"
        assert len(report_non_census.effect_size_results) > 0, "Effect sizes required for non-census data"
    
    def test_constitution_principle_vii_compliance(self):
        """
        Test compliance with Constitution Principle VII (census-data exception).
        
        Per Constitution Principle VII: Statistical inference (p-values) is not applicable
        for complete census data where the entire population is observed.
        """
        # Create census-like data (all prime knots with crossing number ≤13)
        np.random.seed(42)
        crossing_numbers = np.repeat(np.arange(3, 14), [1, 1, 2, 3, 4, 7, 9, 18, 41, 49, 165])
        braid_indices = np.clip(crossing_numbers * 0.5 + np.random.normal(0, 0.3, len(crossing_numbers)), 1, None)
        
        df = pd.DataFrame({"crossing_number": crossing_numbers, "braid_index": braid_indices})
        
        report = run_regression_analysis(df, "crossing_number", "braid_index", is_census_data=True)
        
        # Verify Principle VII compliance
        for corr_result in report.correlation_results:
            assert corr_result.p_value == "not applicable for census data", \
                "Constitution Principle VII violation: p-values must not be reported for census data"
            
            # Verify effect sizes ARE reported (they are descriptive, not inferential)
            assert corr_result.effect_size_r is not None, \
                "Effect sizes must still be reported (descriptive statistics)"
    
    def test_verification_statement_in_outputs(self):
        """
        Verify that verification statements about census data handling are present.
        
        This ensures traceability for auditors reviewing the census data exception.
        """
        np.random.seed(42)
        x = np.random.uniform(3, 13, 100)
        y = 0.5 * x + np.random.normal(0, 0.5, 100)
        
        df = pd.DataFrame({"crossing_number": x, "braid_index": y})
        
        report = run_regression_analysis(df, "crossing_number", "braid_index", is_census_data=True)
        
        # Verify explicit mention of the census data exception
        assert "census" in report.census_data_note.lower(), \
            "Must explicitly mention census data in report"
        assert "not applicable" in report.census_data_note.lower(), \
            "Must state p-values are not applicable"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])