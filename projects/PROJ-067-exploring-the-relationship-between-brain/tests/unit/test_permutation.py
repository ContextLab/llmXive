"""
Unit tests for the permutation test implementation.

Tests verify:
- Correct calculation of observed correlation
- Proper generation of null distribution
- Accurate p-value calculation
- Handling of edge cases
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.permutation_test import (
    calculate_correlation,
    run_permutation_test,
    run_permutation_tests_for_all_metrics
)

class TestCalculateCorrelation:
    """Tests for the calculate_correlation function."""

    def test_perfect_positive_correlation(self):
        """Test with perfectly correlated data."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        rho = calculate_correlation(x, y)
        assert np.isclose(rho, 1.0, atol=0.01)

    def test_perfect_negative_correlation(self):
        """Test with perfectly anti-correlated data."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 8, 6, 4, 2])
        rho = calculate_correlation(x, y)
        assert np.isclose(rho, -1.0, atol=0.01)

    def test_no_correlation(self):
        """Test with uncorrelated data."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)
        rho = calculate_correlation(x, y)
        # With random data, correlation should be close to 0
        assert np.abs(rho) < 0.3

    def test_constant_array(self):
        """Test with a constant array (edge case)."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 5, 5, 5, 5])
        rho = calculate_correlation(x, y)
        assert rho == 0.0

    def test_mismatched_lengths(self):
        """Test with mismatched array lengths."""
        x = np.array([1, 2, 3])
        y = np.array([1, 2, 3, 4])
        with pytest.raises(ValueError):
            calculate_correlation(x, y)

class TestRunPermutationTest:
    """Tests for the run_permutation_test function."""

    def test_deterministic_with_seed(self):
        """Test that results are deterministic with a fixed seed."""
        np.random.seed(42)
        x = np.random.randn(50)
        y = x * 0.5 + np.random.randn(50) * 0.5
        
        rho1, dist1, p1 = run_permutation_test(x, y, n_iterations=100, seed=123)
        rho2, dist2, p2 = run_permutation_test(x, y, n_iterations=100, seed=123)
        
        assert np.isclose(rho1, rho2)
        assert np.array_equal(dist1, dist2)
        assert np.isclose(p1, p2)

    def test_null_distribution_centered_near_zero(self):
        """Test that null distribution is centered near zero for uncorrelated data."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)
        
        rho, null_dist, p = run_permutation_test(x, y, n_iterations=500, seed=42)
        
        # Null distribution should be centered near 0
        assert np.abs(np.mean(null_dist)) < 0.2
        # Standard deviation should be reasonable
        assert 0.05 < np.std(null_dist) < 0.3

    def test_p_value_calculation(self):
        """Test that p-value is calculated correctly."""
        # Create data with known strong correlation
        x = np.array(range(100))
        y = x * 2 + np.random.normal(0, 1, 100)
        
        rho, null_dist, p = run_permutation_test(x, y, n_iterations=1000, seed=42)
        
        # With strong correlation, p-value should be small
        assert p < 0.05

    def test_insufficient_samples(self):
        """Test that insufficient samples raise an error."""
        x = np.array([1, 2, 3])
        y = np.array([4, 5, 6])
        
        with pytest.raises(ValueError, match="Insufficient samples"):
            run_permutation_test(x, y, n_iterations=100)

    def test_mismatched_lengths(self):
        """Test that mismatched lengths raise an error."""
        x = np.array([1, 2, 3, 4])
        y = np.array([1, 2, 3])
        
        with pytest.raises(ValueError, match="Input arrays must have the same length"):
            run_permutation_test(x, y)

    def test_correct_iteration_count(self):
        """Test that the null distribution has the correct number of iterations."""
        np.random.seed(42)
        x = np.random.randn(50)
        y = np.random.randn(50)
        
        n_iters = 1000
        rho, null_dist, p = run_permutation_test(x, y, n_iterations=n_iters, seed=42)
        
        assert len(null_dist) == n_iters

class TestRunPermutationTestsForAllMetrics:
    """Tests for the run_permutation_tests_for_all_metrics function."""

    def test_basic_execution(self):
        """Test basic execution with mock data."""
        metrics = {
            'DMN': [
                {'subject_id': 'sub-01', 'DMN_flexibility': 0.5, 'dream_recall_frequency': 5.0},
                {'subject_id': 'sub-02', 'DMN_flexibility': 0.6, 'dream_recall_frequency': 6.0},
                {'subject_id': 'sub-03', 'DMN_flexibility': 0.4, 'dream_recall_frequency': 4.0},
                {'subject_id': 'sub-04', 'DMN_flexibility': 0.7, 'dream_recall_frequency': 7.0},
                {'subject_id': 'sub-05', 'DMN_flexibility': 0.8, 'dream_recall_frequency': 8.0},
                {'subject_id': 'sub-06', 'DMN_flexibility': 0.55, 'dream_recall_frequency': 5.5},
                {'subject_id': 'sub-07', 'DMN_flexibility': 0.65, 'dream_recall_frequency': 6.5},
                {'subject_id': 'sub-08', 'DMN_flexibility': 0.45, 'dream_recall_frequency': 4.5},
                {'subject_id': 'sub-09', 'DMN_flexibility': 0.75, 'dream_recall_frequency': 7.5},
                {'subject_id': 'sub-10', 'DMN_flexibility': 0.85, 'dream_recall_frequency': 8.5},
                {'subject_id': 'sub-11', 'DMN_flexibility': 0.52, 'dream_recall_frequency': 5.2},
                {'subject_id': 'sub-12', 'DMN_flexibility': 0.68, 'dream_recall_frequency': 6.8},
                {'subject_id': 'sub-13', 'DMN_flexibility': 0.48, 'dream_recall_frequency': 4.8},
                {'subject_id': 'sub-14', 'DMN_flexibility': 0.72, 'dream_recall_frequency': 7.2},
                {'subject_id': 'sub-15', 'DMN_flexibility': 0.82, 'dream_recall_frequency': 8.2},
                {'subject_id': 'sub-16', 'DMN_flexibility': 0.58, 'dream_recall_frequency': 5.8},
                {'subject_id': 'sub-17', 'DMN_flexibility': 0.62, 'dream_recall_frequency': 6.2},
                {'subject_id': 'sub-18', 'DMN_flexibility': 0.51, 'dream_recall_frequency': 5.1},
                {'subject_id': 'sub-19', 'DMN_flexibility': 0.69, 'dream_recall_frequency': 6.9},
                {'subject_id': 'sub-20', 'DMN_flexibility': 0.49, 'dream_recall_frequency': 4.9},
                {'subject_id': 'sub-21', 'DMN_flexibility': 0.71, 'dream_recall_frequency': 7.1},
                {'subject_id': 'sub-22', 'DMN_flexibility': 0.81, 'dream_recall_frequency': 8.1},
                {'subject_id': 'sub-23', 'DMN_flexibility': 0.53, 'dream_recall_frequency': 5.3},
                {'subject_id': 'sub-24', 'DMN_flexibility': 0.67, 'dream_recall_frequency': 6.7},
                {'subject_id': 'sub-25', 'DMN_flexibility': 0.47, 'dream_recall_frequency': 4.7},
                {'subject_id': 'sub-26', 'DMN_flexibility': 0.73, 'dream_recall_frequency': 7.3},
                {'subject_id': 'sub-27', 'DMN_flexibility': 0.83, 'dream_recall_frequency': 8.3},
                {'subject_id': 'sub-28', 'DMN_flexibility': 0.56, 'dream_recall_frequency': 5.6},
                {'subject_id': 'sub-29', 'DMN_flexibility': 0.64, 'dream_recall_frequency': 6.4},
                {'subject_id': 'sub-30', 'DMN_flexibility': 0.54, 'dream_recall_frequency': 5.4},
                {'subject_id': 'sub-31', 'DMN_flexibility': 0.66, 'dream_recall_frequency': 6.6},
                {'subject_id': 'sub-32', 'DMN_flexibility': 0.46, 'dream_recall_frequency': 4.6},
                {'subject_id': 'sub-33', 'DMN_flexibility': 0.74, 'dream_recall_frequency': 7.4},
                {'subject_id': 'sub-34', 'DMN_flexibility': 0.84, 'dream_recall_frequency': 8.4},
                {'subject_id': 'sub-35', 'DMN_flexibility': 0.57, 'dream_recall_frequency': 5.7},
                {'subject_id': 'sub-36', 'DMN_flexibility': 0.63, 'dream_recall_frequency': 6.3},
                {'subject_id': 'sub-37', 'DMN_flexibility': 0.59, 'dream_recall_frequency': 5.9},
                {'subject_id': 'sub-38', 'DMN_flexibility': 0.76, 'dream_recall_frequency': 7.6},
                {'subject_id': 'sub-39', 'DMN_flexibility': 0.44, 'dream_recall_frequency': 4.4},
                {'subject_id': 'sub-40', 'DMN_flexibility': 0.78, 'dream_recall_frequency': 7.8},
                {'subject_id': 'sub-41', 'DMN_flexibility': 0.86, 'dream_recall_frequency': 8.6},
                {'subject_id': 'sub-42', 'DMN_flexibility': 0.52, 'dream_recall_frequency': 5.2},
                {'subject_id': 'sub-43', 'DMN_flexibility': 0.68, 'dream_recall_frequency': 6.8},
                {'subject_id': 'sub-44', 'DMN_flexibility': 0.48, 'dream_recall_frequency': 4.8},
                {'subject_id': 'sub-45', 'DMN_flexibility': 0.72, 'dream_recall_frequency': 7.2},
                {'subject_id': 'sub-46', 'DMN_flexibility': 0.82, 'dream_recall_frequency': 8.2},
                {'subject_id': 'sub-47', 'DMN_flexibility': 0.55, 'dream_recall_frequency': 5.5},
                {'subject_id': 'sub-48', 'DMN_flexibility': 0.65, 'dream_recall_frequency': 6.5},
                {'subject_id': 'sub-49', 'DMN_flexibility': 0.45, 'dream_recall_frequency': 4.5},
                {'subject_id': 'sub-50', 'DMN_flexibility': 0.75, 'dream_recall_frequency': 7.5},
            ]
        }
        
        dream_recall = {
            'sub-01': 5.0, 'sub-02': 6.0, 'sub-03': 4.0, 'sub-04': 7.0, 'sub-05': 8.0,
            'sub-06': 5.5, 'sub-07': 6.5, 'sub-08': 4.5, 'sub-09': 7.5, 'sub-10': 8.5,
            'sub-11': 5.2, 'sub-12': 6.8, 'sub-13': 4.8, 'sub-14': 7.2, 'sub-15': 8.2,
            'sub-16': 5.8, 'sub-17': 6.2, 'sub-18': 5.1, 'sub-19': 6.9, 'sub-20': 4.9,
            'sub-21': 7.1, 'sub-22': 8.1, 'sub-23': 5.3, 'sub-24': 6.7, 'sub-25': 4.7,
            'sub-26': 7.3, 'sub-27': 8.3, 'sub-28': 5.6, 'sub-29': 6.4, 'sub-30': 5.4,
            'sub-31': 6.6, 'sub-32': 4.6, 'sub-33': 7.4, 'sub-34': 8.4, 'sub-35': 5.7,
            'sub-36': 6.3, 'sub-37': 5.9, 'sub-38': 7.6, 'sub-39': 4.4, 'sub-40': 7.8,
            'sub-41': 8.6, 'sub-42': 5.2, 'sub-43': 6.8, 'sub-44': 4.8, 'sub-45': 7.2,
            'sub-46': 8.2, 'sub-47': 5.5, 'sub-48': 6.5, 'sub-49': 4.5, 'sub-50': 7.5,
        }
        
        results = run_permutation_tests_for_all_metrics(metrics, dream_recall)
        
        assert 'DMN_flexibility' in results
        assert results['DMN_flexibility']['observed_rho'] is not None
        assert results['DMN_flexibility']['permutation_p_value'] is not None
        assert results['DMN_flexibility']['n_iterations'] == 1000
        assert results['DMN_flexibility']['n_subjects'] == 50

    def test_insufficient_subjects(self):
        """Test handling of insufficient subjects."""
        metrics = {
            'DMN': [
                {'subject_id': 'sub-01', 'DMN_flexibility': 0.5, 'dream_recall_frequency': 5.0},
                {'subject_id': 'sub-02', 'DMN_flexibility': 0.6, 'dream_recall_frequency': 6.0},
            ]
        }
        
        dream_recall = {'sub-01': 5.0, 'sub-02': 6.0}
        
        results = run_permutation_tests_for_all_metrics(metrics, dream_recall)
        
        assert 'DMN_flexibility' in results
        assert results['DMN_flexibility']['error'] == 'Insufficient subjects'
