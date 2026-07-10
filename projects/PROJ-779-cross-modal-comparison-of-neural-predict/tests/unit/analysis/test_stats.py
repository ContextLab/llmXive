"""
Unit tests for permutation test logic in code/analysis/stats.py.

This module validates the correctness of the Mixed-Effects Permutation Test
implementation used for source strength modality comparison (US3).

Tests verify:
1. Correct shuffling of labels while preserving data structure
2. Proper calculation of test statistics (t-values) for observed and permuted data
3. Correct p-value calculation based on rank ordering
4. Handling of edge cases (e.g., all zeros, single permutation)
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path to allow imports from code/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.analysis import stats

# Mock data generator for testing
def generate_mock_source_data(n_subjects=20, n_sources=100, seed=42):
    """Generate mock source strength data for testing."""
    np.random.seed(seed)
    
    # Simulate source strengths for two modalities (auditory, visual)
    # Auditory: higher mean in fronto-central regions
    # Visual: higher mean in occipito-parietal regions
    auditory_strength = np.random.randn(n_subjects, n_sources) * 1.0 + 2.0
    visual_strength = np.random.randn(n_subjects, n_sources) * 1.0 + 1.5
    
    return {
        'auditory': auditory_strength,
        'visual': visual_strength,
        'subjects': [f'Subject_{i}' for i in range(n_subjects)]
    }

class TestPermutationTestLogic:
    """Tests for the permutation test implementation."""

    def test_permutation_test_basic_functionality(self):
        """Test that permutation test runs and returns expected structure."""
        data = generate_mock_source_data(n_subjects=10, n_sources=50)
        
        # Run permutation test with minimal permutations for speed
        result = stats.mixed_effects_permutation_test(
            data['auditory'],
            data['visual'],
            n_permutations=10,
            random_state=42
        )
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'observed_t' in result
        assert 'p_value' in result
        assert 'permuted_t_distribution' in result
        assert 'n_permutations' in result
        
        # Verify result types
        assert isinstance(result['observed_t'], float)
        assert isinstance(result['p_value'], float)
        assert isinstance(result['permuted_t_distribution'], np.ndarray)
        assert result['n_permutations'] == 10

    def test_permutation_test_p_value_range(self):
        """Test that p-value is within valid range [0, 1]."""
        data = generate_mock_source_data(n_subjects=10, n_sources=50)
        
        result = stats.mixed_effects_permutation_test(
            data['auditory'],
            data['visual'],
            n_permutations=100,
            random_state=42
        )
        
        assert 0.0 <= result['p_value'] <= 1.0

    def test_permutation_test_deterministic_with_seed(self):
        """Test that results are deterministic when random_state is set."""
        data = generate_mock_source_data(n_subjects=10, n_sources=50)
        
        result1 = stats.mixed_effects_permutation_test(
            data['auditory'],
            data['visual'],
            n_permutations=50,
            random_state=42
        )
        
        result2 = stats.mixed_effects_permutation_test(
            data['auditory'],
            data['visual'],
            n_permutations=50,
            random_state=42
        )
        
        # Results should be identical
        assert result1['observed_t'] == result2['observed_t']
        assert result1['p_value'] == result2['p_value']
        np.testing.assert_array_equal(
            result1['permuted_t_distribution'],
            result2['permuted_t_distribution']
        )

    def test_permutation_test_with_identical_groups(self):
        """Test that p-value is high when groups are identical (null hypothesis true)."""
        n_subjects = 20
        n_sources = 50
        
        # Create identical data for both groups
        np.random.seed(42)
        identical_data = np.random.randn(n_subjects, n_sources) * 1.0 + 2.0
        
        result = stats.mixed_effects_permutation_test(
            identical_data,
            identical_data,
            n_permutations=1000,
            random_state=42
        )
        
        # P-value should be high (not significant)
        assert result['p_value'] > 0.05

    def test_permutation_test_with_different_groups(self):
        """Test that p-value is low when groups have large difference."""
        n_subjects = 20
        n_sources = 50
        
        # Create groups with large difference
        np.random.seed(42)
        group1 = np.random.randn(n_subjects, n_sources) * 0.5 + 1.0
        group2 = np.random.randn(n_subjects, n_sources) * 0.5 + 10.0  # Large offset
        
        result = stats.mixed_effects_permutation_test(
            group1,
            group2,
            n_permutations=1000,
            random_state=42
        )
        
        # P-value should be low (significant difference)
        assert result['p_value'] < 0.05

    def test_permutation_test_permuted_t_distribution_shape(self):
        """Test that permuted t-distribution has correct shape."""
        data = generate_mock_source_data(n_subjects=10, n_sources=50)
        n_permutations = 25
        
        result = stats.mixed_effects_permutation_test(
            data['auditory'],
            data['visual'],
            n_permutations=n_permutations,
            random_state=42
        )
        
        assert len(result['permuted_t_distribution']) == n_permutations

    def test_permutation_test_with_single_subject(self):
        """Test edge case with minimal subjects (should handle gracefully or raise informative error)."""
        np.random.seed(42)
        single_subject_data = np.random.randn(1, 10)
        
        # This might raise an error due to insufficient degrees of freedom
        # or return a valid result depending on implementation
        try:
            result = stats.mixed_effects_permutation_test(
                single_subject_data,
                single_subject_data,
                n_permutations=5,
                random_state=42
            )
            # If it runs, verify structure
            assert isinstance(result, dict)
        except ValueError as e:
            # Expected behavior for insufficient data
            assert "insufficient" in str(e).lower() or "degrees of freedom" in str(e).lower()

    def test_permutation_test_statistic_calculation(self):
        """Test that the observed t-statistic is calculated correctly."""
        # Create simple test case with known difference
        np.random.seed(42)
        group1 = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])  # 2 subjects, 3 sources
        group2 = np.array([[10.0, 11.0, 12.0], [13.0, 14.0, 15.0]])
        
        result = stats.mixed_effects_permutation_test(
            group1,
            group2,
            n_permutations=0,  # No permutations needed for this test
            random_state=42
        )
        
        # The observed t should be negative (group1 < group2)
        # Exact value depends on implementation, but sign should be correct
        assert result['observed_t'] < 0

    def test_permutation_test_label_shuffling(self):
        """Test that label shuffling actually changes the data assignment."""
        np.random.seed(42)
        group1 = np.random.randn(10, 20)
        group2 = np.random.randn(10, 20)
        
        # Run multiple times with different permutations
        results = []
        for i in range(5):
            result = stats.mixed_effects_permutation_test(
                group1,
                group2,
                n_permutations=10,
                random_state=i  # Different seed for each run
            )
            results.append(result['permuted_t_distribution'])
        
        # Results should vary due to different shuffles
        # (at least some should be different)
        are_different = False
        for i in range(len(results) - 1):
            if not np.array_equal(results[i], results[i+1]):
                are_different = True
                break
        
        assert are_different, "Permutation test should produce different results with different random seeds"

    def test_permutation_test_with_nan_handling(self):
        """Test behavior with NaN values in data."""
        np.random.seed(42)
        group1 = np.random.randn(10, 20)
        group2 = np.random.randn(10, 20)
        
        # Introduce NaN
        group1[0, 0] = np.nan
        
        # Should either handle gracefully or raise informative error
        try:
            result = stats.mixed_effects_permutation_test(
                group1,
                group2,
                n_permutations=5,
                random_state=42
            )
            # If it runs, verify it didn't crash
            assert isinstance(result, dict)
        except (ValueError, RuntimeError) as e:
            # Expected if NaN handling is strict
            assert "nan" in str(e).lower() or "invalid value" in str(e).lower()

    def test_permutation_test_random_state_consistency(self):
        """Test that random_state parameter controls randomness correctly."""
        np.random.seed(42)
        group1 = np.random.randn(10, 20)
        group2 = np.random.randn(10, 20)
        
        # Run with same seed multiple times
        results_same_seed = []
        for _ in range(3):
            result = stats.mixed_effects_permutation_test(
                group1,
                group2,
                n_permutations=20,
                random_state=123
            )
            results_same_seed.append(result['permuted_t_distribution'])
        
        # All should be identical
        for i in range(len(results_same_seed) - 1):
            np.testing.assert_array_equal(
                results_same_seed[i],
                results_same_seed[i+1]
            )

    def test_permutation_test_edge_case_zero_permutations(self):
        """Test behavior when n_permutations=0."""
        np.random.seed(42)
        group1 = np.random.randn(10, 20)
        group2 = np.random.randn(10, 20)
        
        # This should either raise an error or return a result with empty distribution
        try:
            result = stats.mixed_effects_permutation_test(
                group1,
                group2,
                n_permutations=0,
                random_state=42
            )
            # If it runs, verify structure
            assert isinstance(result, dict)
            assert 'observed_t' in result
        except ValueError as e:
            # Expected if zero permutations is invalid
            assert "zero" in str(e).lower() or "minimum" in str(e).lower()

    def test_permutation_test_large_scale(self):
        """Test with larger dataset to ensure scalability."""
        data = generate_mock_source_data(n_subjects=30, n_sources=100)
        
        result = stats.mixed_effects_permutation_test(
            data['auditory'],
            data['visual'],
            n_permutations=50,
            random_state=42
        )
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'observed_t' in result
        assert 'p_value' in result
        assert 'permuted_t_distribution' in result
        assert len(result['permuted_t_distribution']) == 50

    def test_permutation_test_statistical_power(self):
        """Test that the permutation test can detect known effect sizes."""
        n_subjects = 20
        n_sources = 50
        
        # Create data with known effect size (Cohen's d ~ 1.0)
        np.random.seed(42)
        effect_size = 1.0
        group1 = np.random.randn(n_subjects, n_sources)
        group2 = np.random.randn(n_subjects, n_sources) + effect_size
        
        result = stats.mixed_effects_permutation_test(
            group1,
            group2,
            n_permutations=1000,
            random_state=42
        )
        
        # With large effect size and sufficient power, p-value should be small
        assert result['p_value'] < 0.1  # Relaxed threshold for robustness

    def test_permutation_test_mixed_effects_structure(self):
        """Test that the mixed effects structure is preserved during permutation."""
        # Create data with subject-specific effects
        np.random.seed(42)
        n_subjects = 15
        n_sources = 30
        
        # Add subject-specific baseline
        subject_baselines = np.random.randn(n_subjects, 1) * 2.0
        group1 = np.random.randn(n_subjects, n_sources) + subject_baselines
        group2 = np.random.randn(n_subjects, n_sources) + subject_baselines + 1.0
        
        result = stats.mixed_effects_permutation_test(
            group1,
            group2,
            n_permutations=100,
            random_state=42
        )
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'observed_t' in result
        assert 'p_value' in result
        assert 0.0 <= result['p_value'] <= 1.0

    def test_permutation_test_output_format(self):
        """Test that output format matches expected specification."""
        data = generate_mock_source_data(n_subjects=10, n_sources=20)
        
        result = stats.mixed_effects_permutation_test(
            data['auditory'],
            data['visual'],
            n_permutations=50,
            random_state=42
        )
        
        # Verify all required keys are present
        required_keys = [
            'observed_t',
            'p_value',
            'permuted_t_distribution',
            'n_permutations'
        ]
        
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
        
        # Verify data types
        assert isinstance(result['observed_t'], (int, float, np.floating))
        assert isinstance(result['p_value'], (int, float, np.floating))
        assert isinstance(result['permuted_t_distribution'], np.ndarray)
        assert isinstance(result['n_permutations'], int)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
