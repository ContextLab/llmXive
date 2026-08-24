"""
Unit tests for T040: Statistical significance analysis.

Tests that significance.py correctly performs ANOVA and Bonferroni correction.
"""
import pytest
import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
from scipy import stats

# Add code/src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.stats.significance import (
    perform_anova,
    bonferroni_correction,
    check_sample_sizes,
    has_low_sample_count,
    analyze_significance
)


class TestANOVA:
    """Tests for ANOVA computation."""

    def test_perform_anova_with_significant_difference(self):
        """Test ANOVA when there is a significant difference between groups."""
        # Create groups with different means
        group1 = np.random.normal(loc=0.1, scale=0.02, size=50)
        group2 = np.random.normal(loc=0.3, scale=0.02, size=50)
        group3 = np.random.normal(loc=0.5, scale=0.02, size=50)
        
        f_stat, p_value = perform_anova([group1, group2, group3])
        
        assert isinstance(f_stat, float)
        assert isinstance(p_value, float)
        assert f_stat > 0
        assert 0 <= p_value <= 1
        # With such different means, p-value should be very small
        assert p_value < 0.05

    def test_perform_anova_with_no_difference(self):
        """Test ANOVA when groups are similar."""
        # Create groups with similar means
        group1 = np.random.normal(loc=0.3, scale=0.05, size=50)
        group2 = np.random.normal(loc=0.31, scale=0.05, size=50)
        group3 = np.random.normal(loc=0.29, scale=0.05, size=50)
        
        f_stat, p_value = perform_anova([group1, group2, group3])
        
        assert isinstance(f_stat, float)
        assert isinstance(p_value, float)
        # With similar means, p-value should be larger (though random)
        # We just check it's a valid p-value
        assert 0 <= p_value <= 1

    def test_perform_anova_with_insufficient_samples(self):
        """Test ANOVA with very small sample sizes."""
        group1 = np.array([0.1, 0.2])
        group2 = np.array([0.3, 0.4])
        group3 = np.array([0.5, 0.6])
        
        # Should still compute but may have issues
        f_stat, p_value = perform_anova([group1, group2, group3])
        
        assert isinstance(f_stat, float)
        assert isinstance(p_value, float)


class TestBonferroniCorrection:
    """Tests for Bonferroni correction."""

    def test_bonferroni_correction_reduces_alpha(self):
        """Test that Bonferroni correction reduces the alpha threshold."""
        original_alpha = 0.05
        num_tests = 3
        
        corrected_alpha = bonferroni_correction(original_alpha, num_tests)
        
        assert corrected_alpha == original_alpha / num_tests
        assert corrected_alpha < original_alpha

    def test_bonferroni_correction_with_many_tests(self):
        """Test correction with many hypothesis tests."""
        original_alpha = 0.05
        num_tests = 100
        
        corrected_alpha = bonferroni_correction(original_alpha, num_tests)
        
        assert corrected_alpha == 0.0005

    def test_bonferroni_correction_edge_cases(self):
        """Test correction with edge case values."""
        # Single test
        assert bonferroni_correction(0.05, 1) == 0.05
        
        # Very small alpha
        assert bonferroni_correction(0.001, 10) == 0.0001


class TestSampleSizeChecks:
    """Tests for sample size validation."""

    def test_check_sample_sizes_returns_true_for_adequate(self):
        """Test check when sample sizes are adequate."""
        sample_sizes = [50, 60, 55]
        
        result = check_sample_sizes(sample_sizes, min_size=30)
        
        assert result is True

    def test_check_sample_sizes_returns_false_for_insufficient(self):
        """Test check when sample sizes are insufficient."""
        sample_sizes = [20, 60, 55]
        
        result = check_sample_sizes(sample_sizes, min_size=30)
        
        assert result is False

    def test_has_low_sample_count_detects_low_samples(self):
        """Test detection of low sample counts."""
        # Single class with low samples
        result = has_low_sample_count([10], min_size=30)
        assert result is True

    def test_has_low_sample_count_all_classes_adequate(self):
        """Test when all classes have adequate samples."""
        result = has_low_sample_count([50, 60, 55], min_size=30)
        assert result is False


class TestSignificanceAnalysis:
    """Tests for the full significance analysis pipeline."""

    def test_analyze_significance_returns_expected_structure(self):
        """Test that analysis returns the expected dictionary structure."""
        # Mock data
        scores_by_class = {
            'color': [0.1, 0.12, 0.11, 0.13, 0.1],
            'pattern': [0.2, 0.22, 0.21, 0.23, 0.2],
            'texture': [0.3, 0.32, 0.31, 0.33, 0.3]
        }
        
        result = analyze_significance(scores_by_class, alpha=0.05)
        
        assert isinstance(result, dict)
        assert 'anova_f_stat' in result
        assert 'anova_p_value' in result
        assert 'bonferroni_corrected_alpha' in result
        assert 'is_significant' in result
        assert 'low_sample_warning' in result
