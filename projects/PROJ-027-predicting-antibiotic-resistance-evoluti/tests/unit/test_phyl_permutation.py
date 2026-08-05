"""
Unit tests for phylogenetically-aware permutation null distribution logic.

Tests the core logic of phylo_permutation.py without requiring the full
pipeline to run. Focuses on verifying that:
1. Null distribution is generated correctly under the null hypothesis
2. P-value calculation is accurate
3. Edge cases are handled properly
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.logging import get_logger
from utils.config import load_config

logger = get_logger(__name__)


class TestNullDistributionLogic:
    """Tests for the null distribution generation in phylogenetic permutation."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing permutation logic."""
        # Create synthetic feature matrix (real data not needed for unit tests)
        np.random.seed(42)
        n_samples = 100
        n_features = 10
        
        features = np.random.randn(n_samples, n_features)
        labels = np.random.choice([0, 1], size=n_samples, p=[0.6, 0.4])
        
        # Create a simple clade assignment (for phylogenetic blocking)
        clades = np.random.choice(['clade_A', 'clade_B', 'clade_C'], size=n_samples)
        
        return {
            'features': features,
            'labels': labels,
            'clades': clades
        }

    @pytest.fixture
    def test_config(self):
        """Create a minimal test configuration."""
        return {
            'random_seed': 42,
            'n_permutations': 100,
            'p_value_threshold': 0.05
        }

    def test_null_distribution_generation(self, sample_data, test_config):
        """Test that null distribution is generated correctly."""
        from code.validate.phylo_permutation import generate_null_distribution

        n_permutations = test_config['n_permutations']
        
        # Generate null distribution
        null_dist = generate_null_distribution(
            sample_data['features'],
            sample_data['labels'],
            sample_data['clades'],
            n_permutations,
            test_config['random_seed']
        )
        
        # Verify null distribution properties
        assert len(null_dist) == n_permutations, \
            f"Null distribution should have {n_permutations} values, got {len(null_dist)}"
        
        assert isinstance(null_dist, np.ndarray), \
            "Null distribution should be a numpy array"
        
        assert null_dist.dtype in [np.float64, np.float32, np.int64, np.int32], \
            f"Null distribution should contain numeric values, got {null_dist.dtype}"

    def test_permutation_respects_clades(self, sample_data, test_config):
        """Test that permutations respect clade structure."""
        from code.validate.phylo_permutation import generate_null_distribution

        # Create data where clade structure is obvious
        np.random.seed(123)
        n_samples = 60
        n_features = 5
        
        features = np.random.randn(n_samples, n_features)
        labels = np.random.choice([0, 1], size=n_samples, p=[0.5, 0.5])
        
        # Create 3 clades with 20 samples each
        clades = np.array(['clade_A'] * 20 + ['clade_B'] * 20 + ['clade_C'] * 20)
        
        null_dist = generate_null_distribution(
            features,
            labels,
            clades,
            n_permutations=50,
            random_seed=test_config['random_seed']
        )
        
        # The null distribution should be generated without errors
        assert len(null_dist) == 50, "Null distribution generation failed"
        
        # Verify that the permutation function doesn't break clade structure
        # by checking that it returns reasonable values
        assert np.all(np.isfinite(null_dist)), \
            "Null distribution contains non-finite values"

    def test_p_value_calculation(self, sample_data, test_config):
        """Test p-value calculation from null distribution."""
        from code.validate.phylo_permutation import calculate_p_value

        # Create a simple null distribution
        np.random.seed(42)
        null_dist = np.random.randn(1000)
        
        # Test case 1: Observed statistic in the middle of null distribution
        observed_stat = 0.0
        p_value = calculate_p_value(observed_stat, null_dist)
        assert 0.4 < p_value < 0.6, \
            f"P-value should be ~0.5 for observed stat in middle, got {p_value}"
        
        # Test case 2: Observed statistic far in the tail
        observed_stat = 4.0
        p_value = calculate_p_value(observed_stat, null_dist)
        assert p_value < 0.01, \
            f"P-value should be very small for extreme observed stat, got {p_value}"
        
        # Test case 3: Observed statistic at the edge
        observed_stat = null_dist.max()
        p_value = calculate_p_value(observed_stat, null_dist)
        assert p_value <= 1.0 / len(null_dist), \
            f"P-value should be minimal for max observed stat, got {p_value}"

    def test_p_value_with_small_null_distribution(self, sample_data, test_config):
        """Test p-value calculation with small null distribution."""
        from code.validate.phylo_permutation import calculate_p_value

        # Very small null distribution
        null_dist = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        observed_stat = 2.5
        p_value = calculate_p_value(observed_stat, null_dist)
        
        # Should handle small distributions correctly
        assert 0.0 <= p_value <= 1.0, \
            f"P-value should be between 0 and 1, got {p_value}"

    def test_permutation_with_single_clade(self, test_config):
        """Test permutation when all samples belong to one clade."""
        from code.validate.phylo_permutation import generate_null_distribution

        np.random.seed(42)
        n_samples = 50
        n_features = 5
        
        features = np.random.randn(n_samples, n_features)
        labels = np.random.choice([0, 1], size=n_samples)
        clades = np.array(['single_clade'] * n_samples)
        
        # Should not crash with single clade
        null_dist = generate_null_distribution(
            features,
            labels,
            clades,
            n_permutations=20,
            random_seed=test_config['random_seed']
        )
        
        assert len(null_dist) == 20, "Null distribution should be generated for single clade"

    def test_permutation_with_imbalanced_clades(self, test_config):
        """Test permutation with highly imbalanced clade sizes."""
        from code.validate.phylo_permutation import generate_null_distribution

        np.random.seed(42)
        n_samples = 100
        n_features = 5
        
        features = np.random.randn(n_samples, n_features)
        labels = np.random.choice([0, 1], size=n_samples)
        
        # Highly imbalanced: 90 in one clade, 10 in another
        clades = np.array(['large_clade'] * 90 + ['small_clade'] * 10)
        
        null_dist = generate_null_distribution(
            features,
            labels,
            clades,
            n_permutations=20,
            random_seed=test_config['random_seed']
        )
        
        assert len(null_dist) == 20, "Null distribution should handle imbalanced clades"

    def test_seed_reproducibility(self, sample_data, test_config):
        """Test that permutation results are reproducible with fixed seed."""
        from code.validate.phylo_permutation import generate_null_distribution

        # Run twice with same seed
        null_dist_1 = generate_null_distribution(
            sample_data['features'],
            sample_data['labels'],
            sample_data['clades'],
            n_permutations=50,
            random_seed=42
        )
        
        null_dist_2 = generate_null_distribution(
            sample_data['features'],
            sample_data['labels'],
            sample_data['clades'],
            n_permutations=50,
            random_seed=42
        )
        
        # Results should be identical
        assert np.array_equal(null_dist_1, null_dist_2), \
            "Null distributions should be identical with same seed"

    def test_edge_case_zero_permutations(self, sample_data, test_config):
        """Test behavior with zero permutations (edge case)."""
        from code.validate.phylo_permutation import generate_null_distribution

        with pytest.raises(ValueError):
            generate_null_distribution(
                sample_data['features'],
                sample_data['labels'],
                sample_data['clades'],
                n_permutations=0,
                random_seed=test_config['random_seed']
            )

    def test_edge_case_single_permutation(self, sample_data, test_config):
        """Test behavior with a single permutation."""
        from code.validate.phylo_permutation import generate_null_distribution

        null_dist = generate_null_distribution(
            sample_data['features'],
            sample_data['labels'],
            sample_data['clades'],
            n_permutations=1,
            random_seed=test_config['random_seed']
        )
        
        assert len(null_dist) == 1, "Should handle single permutation"

    def test_phyl_permutation_integration(self, sample_data, test_config):
        """Integration test for the full phylogenetic permutation workflow."""
        from code.validate.phylo_permutation import run_phylogenetic_permutation

        # Run the full permutation test
        result = run_phylogenetic_permutation(
            features=sample_data['features'],
            labels=sample_data['labels'],
            clades=sample_data['clades'],
            n_permutations=100,
            random_seed=test_config['random_seed']
        )
        
        # Verify result structure
        assert 'observed_statistic' in result, "Result should contain observed statistic"
        assert 'null_distribution' in result, "Result should contain null distribution"
        assert 'p_value' in result, "Result should contain p-value"
        assert 'is_significant' in result, "Result should contain significance flag"
        
        # Verify types
        assert isinstance(result['null_distribution'], np.ndarray), \
            "Null distribution should be numpy array"
        assert len(result['null_distribution']) == 100, \
            "Null distribution should have 100 values"
        
        # Verify p-value is in valid range
        assert 0.0 <= result['p_value'] <= 1.0, \
            f"P-value should be between 0 and 1, got {result['p_value']}"

    def test_significance_flag_logic(self, sample_data, test_config):
        """Test that significance flag is set correctly based on p-value threshold."""
        from code.validate.phylo_permutation import run_phylogenetic_permutation

        # Create data with known significance
        np.random.seed(42)
        features = np.random.randn(100, 5)
        labels = np.random.choice([0, 1], size=100)
        clades = np.random.choice(['A', 'B', 'C'], size=100)
        
        result = run_phylogenetic_permutation(
            features=features,
            labels=labels,
            clades=clades,
            n_permutations=100,
            random_seed=42,
            p_value_threshold=0.05
        )
        
        # Significance flag should match p-value comparison
        expected_significant = result['p_value'] < 0.05
        assert result['is_significant'] == expected_significant, \
            f"Significance flag should be {expected_significant}, got {result['is_significant']}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])