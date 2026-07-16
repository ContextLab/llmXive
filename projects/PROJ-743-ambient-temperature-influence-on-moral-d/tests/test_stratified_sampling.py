"""
Tests for stratified sampling functionality.

These tests verify that the stratified sampling logic works correctly
for CPU-only execution scenarios with memory constraints.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from tests.conftest import stratified_sample


class TestStratifiedSampling:
    """Test suite for stratified sampling functionality."""

    def test_stratified_sample_by_fraction(self):
        """Test stratified sampling with a fraction parameter."""
        # Create a simple dataset with known distribution
        data = {
            'group': ['A'] * 100 + ['B'] * 100 + ['C'] * 100,
            'value': list(range(300))
        }
        df = pd.DataFrame(data)

        # Sample 50% of each group
        sampled = stratified_sample(df, stratify_col='group', fraction=0.5, random_state=42)

        # Verify that each group has approximately 50 samples
        assert len(sampled) == 150, f"Expected 150 samples, got {len(sampled)}"
        assert sampled['group'].value_counts()['A'] == 50
        assert sampled['group'].value_counts()['B'] == 50
        assert sampled['group'].value_counts()['C'] == 50

    def test_stratified_sample_by_count(self):
        """Test stratified sampling with a sample_size parameter."""
        data = {
            'group': ['A'] * 100 + ['B'] * 100 + ['C'] * 100,
            'value': list(range(300))
        }
        df = pd.DataFrame(data)

        # Sample 30 from each group (total 90)
        sampled = stratified_sample(df, stratify_col='group', sample_size=90, random_state=42)

        # Verify total count and distribution
        assert len(sampled) == 90
        assert sampled['group'].value_counts()['A'] == 30
        assert sampled['group'].value_counts()['B'] == 30
        assert sampled['group'].value_counts()['C'] == 30

    def test_stratified_sample_reproducibility(self):
        """Test that stratified sampling is reproducible with the same seed."""
        data = {
            'group': ['A'] * 50 + ['B'] * 50,
            'value': list(range(100))
        }
        df = pd.DataFrame(data)

        # Run twice with same seed
        sampled1 = stratified_sample(df, stratify_col='group', fraction=0.2, random_state=123)
        sampled2 = stratified_sample(df, stratify_col='group', fraction=0.2, random_state=123)

        # Results should be identical
        pd.testing.assert_frame_equal(sampled1.sort_values('value').reset_index(drop=True),
                                    sampled2.sort_values('value').reset_index(drop=True))

    def test_stratified_sample_error_no_parameter(self):
        """Test that an error is raised when neither sample_size nor fraction is provided."""
        data = {'group': ['A'] * 10, 'value': list(range(10))}
        df = pd.DataFrame(data)

        with pytest.raises(ValueError, match="Either sample_size or fraction must be provided"):
            stratified_sample(df, stratify_col='group')

    def test_stratified_sample_error_both_parameters(self):
        """Test that an error is raised when both sample_size and fraction are provided."""
        data = {'group': ['A'] * 10, 'value': list(range(10))}
        df = pd.DataFrame(data)

        with pytest.raises(ValueError, match="Only one of sample_size or fraction should be provided"):
            stratified_sample(df, stratify_col='group', sample_size=5, fraction=0.5)

    def test_stratified_sample_preserves_groups(self):
        """Test that stratified sampling preserves all groups in the original data."""
        data = {
            'group': ['A'] * 20 + ['B'] * 20 + ['C'] * 20 + ['D'] * 20,
            'value': list(range(80))
        }
        df = pd.DataFrame(data)

        # Sample 25%
        sampled = stratified_sample(df, stratify_col='group', fraction=0.25, random_state=42)

        # All groups should still be present
        assert set(sampled['group'].unique()) == {'A', 'B', 'C', 'D'}

    def test_stratified_sample_with_moral_machine_structure(self, sample_moral_machine_data):
        """Test stratified sampling on data with Moral Machine structure."""
        # This tests the fixture data structure
        assert 'country' in sample_moral_machine_data.columns
        assert 'dilemma_type' in sample_moral_machine_data.columns
        assert len(sample_moral_machine_data) > 0

        # Perform stratified sampling by dilemma_type
        sampled = stratified_sample(
            sample_moral_machine_data,
            stratify_col='dilemma_type',
            fraction=0.5,
            random_state=42
        )

        # Verify all dilemma types are still represented
        assert set(sampled['dilemma_type'].unique()) == set(sample_moral_machine_data['dilemma_type'].unique())
