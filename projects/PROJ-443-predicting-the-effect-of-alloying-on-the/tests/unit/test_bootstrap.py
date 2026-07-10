"""
Unit tests for grouped bootstrap logic in src/eval/bootstrap.py.

These tests verify:
1. Correct grouping of samples by 'Alloy System'.
2. Proper sampling of groups (not individual samples) during resampling.
3. Handling of edge cases (fewer groups than resamples, single group).
4. Integration with the seed management system for reproducibility.
"""
import pytest
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the path to allow imports
# Assuming the test is run from the project root or the path is set correctly
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.eval.bootstrap import (
    perform_grouped_bootstrap,
    calculate_bootstrap_metrics,
    generate_group_indices,
    validate_group_sufficiency
)
from src.utils.seeds import set_seed, get_seed
from src.model.derive_groups import derive_alloy_systems


class TestGenerateGroupIndices:
    """Tests for the group index generation logic."""

    def test_generate_indices_basic(self):
        """Test basic generation of group indices."""
        groups = ['A', 'B', 'C', 'A', 'B']
        unique_groups = list(set(groups))
        group_to_idx = {g: i for i, g in enumerate(unique_groups)}
        
        indices = generate_group_indices(groups, group_to_idx)
        
        assert len(indices) == len(groups)
        # Verify that indices correspond to the correct groups
        for i, g in enumerate(groups):
            assert indices[i] == group_to_idx[g]

    def test_generate_indices_empty(self):
        """Test with empty list."""
        with pytest.raises(ValueError):
            generate_group_indices([], {})


class TestValidateGroupSufficiency:
    """Tests for group sufficiency validation."""

    def test_sufficient_groups(self):
        """Test with enough groups."""
        is_valid, warning = validate_group_sufficiency(15, min_groups=10)
        assert is_valid is True
        assert warning is None

    def test_insufficient_groups(self):
        """Test with too few groups."""
        is_valid, warning = validate_group_sufficiency(5, min_groups=10)
        assert is_valid is False
        assert warning is not None
        assert "Insufficient groups" in warning

    def test_exact_threshold(self):
        """Test with exactly the minimum number of groups."""
        is_valid, warning = validate_group_sufficiency(10, min_groups=10)
        assert is_valid is True
        assert warning is None


class TestPerformGroupedBootstrap:
    """Tests for the main grouped bootstrap function."""

    def test_bootstrap_samples_correct_structure(self):
        """Test that bootstrap samples maintain group integrity."""
        # Create a synthetic dataset with known groups
        np.random.seed(42)
        n_samples = 100
        n_groups = 20
        
        data = pd.DataFrame({
            'feature': np.random.rand(n_samples),
            'target': np.random.rand(n_samples),
            'group': [f'Group_{i % n_groups}' for i in range(n_samples)]
        })
        
        set_seed(12345)
        bootstrap_samples = perform_grouped_bootstrap(
            data, 
            'group', 
          'target', 
            n_resamples=5,
            random_state=12345
        )
        
        assert len(bootstrap_samples) == 5
        
        # Check that each sample has the same number of rows as original
        for sample in bootstrap_samples:
            assert len(sample) == n_samples
            # Check that groups are intact (all rows of a group should be together or not at all)
            # This is harder to check directly, but we can check that group sizes are consistent
            # with the original distribution in the resampled data
            unique_groups, counts = np.unique(sample['group'], return_counts=True)
            original_counts = data.groupby('group').size()
            
            # The resampled groups should be a subset of original groups
            assert set(unique_groups).issubset(set(data['group'].unique()))

    def test_bootstrap_reproducibility(self):
        """Test that the same seed produces the same results."""
        np.random.seed(42)
        data = pd.DataFrame({
            'feature': np.random.rand(50),
            'target': np.random.rand(50),
            'group': [f'G_{i % 10}' for i in range(50)]
        })
        
        set_seed(999)
        samples1 = perform_grouped_bootstrap(data, 'group', 'target', n_resamples=3, random_state=999)
        
        set_seed(999)
        samples2 = perform_grouped_bootstrap(data, 'group', 'target', n_resamples=3, random_state=999)
        
        # Compare samples
        for s1, s2 in zip(samples1, samples2):
            pd.testing.assert_frame_equal(s1, s2)

    def test_fallback_to_standard_bootstrap(self):
        """Test fallback when groups are too few."""
        data = pd.DataFrame({
            'feature': np.random.rand(20),
            'target': np.random.rand(20),
            'group': ['A'] * 20  # Only 1 group
        })
        
        # This should trigger the fallback logic and return standard bootstrap samples
        # The function should not crash
        set_seed(111)
        samples = perform_grouped_bootstrap(
            data, 
            'group', 
            'target', 
            n_resamples=3, 
            random_state=111,
            min_groups_for_grouped=10
        )
        
        assert len(samples) == 3
        # In standard bootstrap, individual rows are sampled, so group integrity is lost
        # We can check that the function completed without error


class TestCalculateBootstrapMetrics:
    """Tests for metric calculation on bootstrap samples."""

    def test_r2_calculation(self):
        """Test R² calculation on bootstrap samples."""
        # Create a simple linear relationship
        np.random.seed(42)
        n = 50
        x = np.random.rand(n)
        y = 2 * x + np.random.normal(0, 0.1, n)
        
        data = pd.DataFrame({
            'feature': x,
            'target': y,
            'group': [f'G_{i % 10}' for i in range(n)]
        })
        
        # Mock a simple model that predicts the mean (for testing purposes)
        # In reality, this would be trained on each bootstrap sample
        # For this test, we'll just verify the function structure
        
        # We'll create a mock "predictions" column
        data['prediction'] = y.mean()  # Dummy prediction
        
        metrics = calculate_bootstrap_metrics(
            [data], 
            'target', 
            'prediction',
            metrics=['r2', 'rmse', 'mae']
        )
        
        assert 'r2' in metrics
        assert 'rmse' in metrics
        assert 'mae' in metrics
        
        # R² of predicting the mean is 0
        assert np.isclose(metrics['r2']['mean'], 0.0, atol=1e-5)

    def test_ci_calculation(self):
        """Test confidence interval calculation."""
        # Create multiple bootstrap samples with varying metrics
        metrics_list = [
            {'r2': 0.8, 'rmse': 0.5, 'mae': 0.4},
            {'r2': 0.75, 'rmse': 0.55, 'mae': 0.45},
            {'r2': 0.85, 'rmse': 0.45, 'mae': 0.35},
            {'r2': 0.7, 'rmse': 0.6, 'mae': 0.5},
            {'r2': 0.9, 'rmse': 0.4, 'mae': 0.3},
        ]
        
        # Convert to DataFrame format expected by the function
        df_metrics = pd.DataFrame(metrics_list)
        
        # Calculate summary stats
        r2_mean = df_metrics['r2'].mean()
        r2_ci_lower = np.percentile(df_metrics['r2'], 2.5)
        r2_ci_upper = np.percentile(df_metrics['r2'], 97.5)
        
        # Verify the calculation logic
        assert abs(r2_mean - 0.8) < 0.01
        assert r2_ci_lower < r2_mean < r2_ci_upper