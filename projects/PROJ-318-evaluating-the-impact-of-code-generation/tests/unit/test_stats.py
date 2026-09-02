"""
Unit tests for statistical analysis utilities in code/utils/stats.py.

This file extends the existing test suite to include tests for the 
Wilcoxon signed-rank test implementation, specifically focusing on 
small dataset warnings and edge cases.
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import logging

# Ensure the project root is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.stats import run_wilcoxon_test, StatsException, SampleSizeException
from scipy import stats

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestWilcoxonTest:
    """Test suite for the Wilcoxon signed-rank test implementation."""
    
    def test_wilcoxon_standard_case(self):
        """Test Wilcoxon test with a standard dataset (n >= 30)."""
        # Generate two correlated samples (paired data)
        np.random.seed(42)
        n = 50
        human_scores = np.random.normal(loc=0.6, scale=0.1, size=n)
        llm_scores = np.random.normal(loc=0.55, scale=0.1, size=n)
        
        # Ensure no zeros in differences to avoid scipy warnings
        human_scores = np.clip(human_scores, 0.01, 0.99)
        llm_scores = np.clip(llm_scores, 0.01, 0.99)
        
        result = run_wilcoxon_test(human_scores, llm_scores)
        
        assert result is not None
        assert 'statistic' in result
        assert 'pvalue' in result
        assert isinstance(result['statistic'], (int, float))
        assert isinstance(result['pvalue'], (int, float))
        assert result['sample_size'] == n
        assert result['warning'] is None
        
        # Verify the values match scipy directly
        scipy_stat, scipy_p = stats.wilcoxon(human_scores, llm_scores)
        assert np.isclose(result['statistic'], scipy_stat)
        assert np.isclose(result['pvalue'], scipy_p)
        
        logger.info(f"Standard test passed: statistic={result['statistic']:.4f}, p-value={result['pvalue']:.4f}")
    
    def test_wilcoxon_small_dataset_warning(self):
        """Test that a warning is raised for small datasets (n < 30)."""
        # Generate a small dataset
        np.random.seed(123)
        n = 15
        human_scores = np.random.normal(loc=0.6, scale=0.1, size=n)
        llm_scores = np.random.normal(loc=0.55, scale=0.1, size=n)
        
        # Ensure no zeros in differences
        human_scores = np.clip(human_scores, 0.01, 0.99)
        llm_scores = np.clip(llm_scores, 0.01, 0.99)
        
        result = run_wilcoxon_test(human_scores, llm_scores)
        
        assert result is not None
        assert result['sample_size'] == n
        assert result['warning'] is not None
        assert "small sample size" in result['warning'].lower()
        assert n < 30 in result['warning']
        
        # The test should still run and return valid statistics
        assert 'statistic' in result
        assert 'pvalue' in result
        
        logger.info(f"Small dataset test passed with warning: {result['warning']}")
    
    def test_wilcoxon_very_small_dataset(self):
        """Test with a very small dataset (n < 5) where Wilcoxon might fail."""
        # Wilcoxon requires at least 2 pairs, but results are unreliable for very small n
        np.random.seed(456)
        n = 3
        human_scores = np.array([0.5, 0.6, 0.7])
        llm_scores = np.array([0.4, 0.55, 0.65])
        
        result = run_wilcoxon_test(human_scores, llm_scores)
        
        assert result is not None
        assert result['sample_size'] == n
        assert result['warning'] is not None
        assert "small sample size" in result['warning'].lower()
        
        # Should still return results
        assert 'statistic' in result
        assert 'pvalue' in result
        
        logger.info(f"Very small dataset test passed: n={n}")
    
    def test_wilcoxon_identical_scores(self):
        """Test when all differences are zero (identical scores)."""
        human_scores = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        llm_scores = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        
        # This case is tricky: scipy.wilcoxon returns (0.0, 1.0) for identical arrays
        result = run_wilcoxon_test(human_scores, llm_scores)
        
        assert result is not None
        assert result['statistic'] == 0.0
        assert result['pvalue'] == 1.0
        assert result['sample_size'] == len(human_scores)
        
        logger.info("Identical scores test passed: statistic=0.0, p-value=1.0")
    
    def test_wilcoxon_single_pair(self):
        """Test with a single pair of values (edge case)."""
        human_scores = np.array([0.6])
        llm_scores = np.array([0.55])
        
        # Wilcoxon cannot run with n=1, should raise an error or handle gracefully
        with pytest.raises(Exception):
            run_wilcoxon_test(human_scores, llm_scores)
        
        logger.info("Single pair test correctly raised exception")
    
    def test_wilcoxon_mismatched_lengths(self):
        """Test when input arrays have different lengths."""
        human_scores = np.array([0.5, 0.6, 0.7])
        llm_scores = np.array([0.4, 0.55])
        
        with pytest.raises(ValueError):
            run_wilcoxon_test(human_scores, llm_scores)
        
        logger.info("Mismatched lengths test correctly raised ValueError")
    
    def test_wilcoxon_with_zeros_in_differences(self):
        """Test handling of zero differences (ties)."""
        # Create data with some identical pairs
        human_scores = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        llm_scores = np.array([0.5, 0.65, 0.7, 0.85, 0.9])
        # Pairs 0 and 2 have zero difference
        
        result = run_wilcoxon_test(human_scores, llm_scores)
        
        assert result is not None
        assert 'statistic' in result
        assert 'pvalue' in result
        assert result['sample_size'] == len(human_scores)
        
        # scipy handles zeros by excluding them from the ranking
        logger.info(f"Zeros in differences test passed: statistic={result['statistic']:.4f}")
    
    def test_wilcoxon_large_effect_size(self):
        """Test with a large effect size (clear difference between groups)."""
        np.random.seed(789)
        n = 100
        human_scores = np.random.normal(loc=0.7, scale=0.05, size=n)
        llm_scores = np.random.normal(loc=0.3, scale=0.05, size=n)
        
        result = run_wilcoxon_test(human_scores, llm_scores)
        
        assert result is not None
        assert result['pvalue'] < 0.05  # Should be statistically significant
        assert result['statistic'] > 0
        
        logger.info(f"Large effect size test passed: p-value={result['pvalue']:.6f} (significant)")
    
    def test_wilcoxon_input_types(self):
        """Test that the function accepts various input types (list, numpy array)."""
        human_list = [0.5, 0.6, 0.7, 0.8, 0.9]
        llm_array = np.array([0.4, 0.55, 0.65, 0.75, 0.85])
        
        result = run_wilcoxon_test(human_list, llm_array)
        
        assert result is not None
        assert result['sample_size'] == 5
        
        logger.info("Input types test passed: list and array accepted")
    
    def test_wilcoxon_return_structure(self):
        """Test that the return dictionary has all expected keys."""
        human_scores = np.random.normal(loc=0.6, scale=0.1, size=30)
        llm_scores = np.random.normal(loc=0.55, scale=0.1, size=30)
        
        result = run_wilcoxon_test(human_scores, llm_scores)
        
        expected_keys = {'statistic', 'pvalue', 'sample_size', 'warning'}
        assert set(result.keys()) == expected_keys
        
        logger.info("Return structure test passed: all expected keys present")

class TestStatsExceptionHandling:
    """Test exception handling in statistical functions."""
    
    def test_stats_exception_raised_for_invalid_input(self):
        """Test that StatsException is raised for completely invalid inputs."""
        # Passing None should raise an exception
        with pytest.raises(Exception):
            run_wilcoxon_test(None, None)
        
        logger.info("Invalid input exception test passed")
    
    def test_stats_exception_raised_for_non_numeric(self):
        """Test that exception is raised for non-numeric inputs."""
        human_scores = ["a", "b", "c"]
        llm_scores = [1, 2, 3]
        
        with pytest.raises(Exception):
            run_wilcoxon_test(human_scores, llm_scores)
        
        logger.info("Non-numeric input exception test passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])