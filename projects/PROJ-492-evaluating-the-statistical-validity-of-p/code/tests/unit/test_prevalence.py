"""
Unit tests for prevalence analysis module.
Tests binomial test, Wilson CI, and sensitivity analysis.
"""
import pytest
import json
from pathlib import Path
from code.src.audit.prevalence import (
    binomial_test,
    wilson_ci,
    compute_prevalence,
    sensitivity_analysis,
    apply_dynamic_bonferroni,
    run_prevalence_analysis
)

class TestBinomialTest:
    def test_binomial_test_exact_match(self):
        """Test binomial test with known values."""
        # 5 successes out of 10 trials, p=0.5
        p_value = binomial_test(5, 10, 0.5)
        # Should be 1.0 for exactly half successes
        assert p_value == 1.0
    
    def test_binomial_test_significant(self):
        """Test binomial test detects significant deviation."""
        # 1 success out of 10 trials, p=0.5 should be significant
        p_value = binomial_test(1, 10, 0.5)
        assert p_value < 0.05
    
    def test_binomial_test_empty(self):
        """Test binomial test with zero trials."""
        p_value = binomial_test(0, 0)
        assert p_value == 1.0

class TestWilsonCI:
    def test_wilson_ci_symmetric(self):
        """Test Wilson CI with 50% success rate."""
        lower, upper = wilson_ci(5, 10, 0.95)
        # Should be roughly symmetric around 0.5
        assert 0.2 < lower < 0.5
        assert 0.5 < upper < 0.8
    
    def test_wilson_ci_empty(self):
        """Test Wilson CI with zero trials."""
        lower, upper = wilson_ci(0, 0)
        assert lower == 0.0
        assert upper == 0.0
    
    def test_wilson_ci_bounds(self):
        """Test Wilson CI stays within [0, 1]."""
        lower, upper = wilson_ci(10, 10, 0.95)
        assert 0.0 <= lower <= 1.0
        assert 0.0 <= upper <= 1.0
        assert lower <= upper

class TestComputePrevalence:
    def test_compute_prevalence_basic(self):
        """Test basic prevalence computation."""
        records = [
            {'is_inconsistent': True},
            {'is_inconsistent': False},
            {'is_inconsistent': True}
        ]
        result = compute_prevalence(records)
        
        assert result['total_summaries'] == 3
        assert result['inconsistent_count'] == 2
        assert abs(result['inconsistent_rate'] - 2/3) < 0.0001
        assert 'wilson_ci_lower' in result
        assert 'wilson_ci_upper' in result
        assert 'binomial_p_value' in result
    
    def test_compute_prevalence_empty(self):
        """Test prevalence computation with empty records."""
        result = compute_prevalence([])
        
        assert result['total_summaries'] == 0
        assert result['inconsistent_count'] == 0
        assert result['inconsistent_rate'] == 0.0

class TestSensitivityAnalysis:
    def test_sensitivity_analysis_basic(self):
        """Test basic sensitivity analysis."""
        records = [
            {'is_inconsistent': True},
            {'is_inconsistent': False},
            {'is_inconsistent': True}
        ]
        result = sensitivity_analysis(records, num_points=5)
        
        assert 'baseline_range' in result
        assert 'num_points' in result
        assert 'rate_variance' in result
        assert 'max_deviation' in result
        assert 'results' in result
        assert len(result['results']) == 5
    
    def test_sensitivity_analysis_empty(self):
        """Test sensitivity analysis with empty records."""
        result = sensitivity_analysis([], num_points=5)
        
        assert result['rate_variance'] == 0.0
        assert result['max_deviation'] == 0.0
        assert len(result['results']) == 5

class TestDynamicBonferroni:
    def test_bonferroni_single_test(self):
        """Test Bonferroni with single test."""
        result = apply_dynamic_bonferroni([0.03], alpha=0.05)
        
        assert result['n_subgroups'] == 1
        assert result['adjusted_alpha'] == 0.05
        assert result['corrected_p_values'] == [0.03]
        assert result['significant_flags'] == [False]  # 0.03 > 0.05/1 is False? No, 0.03 < 0.05
        # Actually 0.03 < 0.05, so it should be True
        # Let me recalculate: corrected_p = 0.03 * 1 = 0.03
        # significant = 0.03 < 0.05/1 = 0.05 -> True
        assert result['significant_flags'] == [True]
    
    def test_bonferroni_multiple_tests(self):
        """Test Bonferroni with multiple tests."""
        p_values = [0.01, 0.04, 0.06]
        result = apply_dynamic_bonferroni(p_values, alpha=0.05)
        
        assert result['n_subgroups'] == 3
        assert abs(result['adjusted_alpha'] - 0.05/3) < 0.0001
        assert len(result['corrected_p_values']) == 3
        assert len(result['significant_flags']) == 3
    
    def test_bonferroni_empty(self):
        """Test Bonferroni with no tests."""
        result = apply_dynamic_bonferroni([], alpha=0.05)
        
        assert result['n_subgroups'] == 0
        assert result['adjusted_alpha'] == 0.05
        assert result['corrected_p_values'] == []
        assert result['significant_flags'] == []

class TestPrevalenceIntegration:
    def test_full_prevalence_analysis(self, tmp_path):
        """Test full prevalence analysis pipeline."""
        # Create test audit report
        audit_data = {
            'records': [
                {'is_inconsistent': True, 'domain': 'tech'},
                {'is_inconsistent': False, 'domain': 'tech'},
                {'is_inconsistent': True, 'domain': 'health'},
                {'is_inconsistent': False, 'domain': 'finance'},
                {'is_inconsistent': True, 'domain': 'tech'}
            ]
        }
        
        input_path = tmp_path / 'audit_report.json'
        output_path = tmp_path / 'prevalence.json'
        
        with open(input_path, 'w') as f:
            json.dump(audit_data, f)
        
        # Run analysis
        result = run_prevalence_analysis(input_path, output_path)
        
        # Verify output file exists
        assert output_path.exists()
        
        # Verify result structure
        assert 'timestamp' in result
        assert 'prevalence' in result
        assert 'sensitivity_analysis' in result
        
        # Verify prevalence stats
        assert result['prevalence']['total_summaries'] == 5
        assert result['prevalence']['inconsistent_count'] == 3
        assert abs(result['prevalence']['inconsistent_rate'] - 0.6) < 0.0001
        
        # Verify sensitivity analysis
        assert result['sensitivity_analysis']['max_deviation'] >= 0.0
        
        # Verify output file can be loaded
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['prevalence']['total_summaries'] == 5

if __name__ == '__main__':
    pytest.main([__file__, '-v'])