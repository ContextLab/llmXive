"""
Unit tests for stratified sampling functionality.
Verifies that sampling preserves distribution across strata.
"""
import pytest
import pandas as pd
import numpy as np

def test_stratified_sampling_basic(stratified_sampler):
    """
    Test basic stratified sampling on a simple DataFrame.
    """
    # Create a synthetic dataset with known strata distribution
    data = {
        'value': range(100),
        'group': ['A'] * 40 + ['B'] * 30 + ['C'] * 30
    }
    df = pd.DataFrame(data)

    # Sample 20 items
    sample = stratified_sampler(df, 'group', sample_size=20, random_state=42)

    # Check total size
    assert len(sample) == 20

    # Check that strata are represented
    counts = sample['group'].value_counts()
    assert 'A' in counts.index
    assert 'B' in counts.index
    assert 'C' in counts.index

    # Check approximate proportions (allowing for rounding)
    # Original: A=40%, B=30%, C=30%
    # Expected: A=8, B=6, C=6
    assert counts['A'] == 8
    assert counts['B'] == 6
    assert counts['C'] == 6

def test_stratified_sampling_small_strata(stratified_sampler):
    """
    Test stratified sampling when a stratum is smaller than the requested sample size.
    """
    data = {
        'value': range(20),
        'group': ['A'] * 15 + ['B'] * 5
    }
    df = pd.DataFrame(data)

    # Request 10 samples, but 'B' only has 5
    sample = stratified_sampler(df, 'group', sample_size=10, random_state=42)

    # Should take all of 'B'
    assert sample[sample['group'] == 'B'].shape[0] == 5

    # Total should be 10
    assert len(sample) == 10

def test_stratified_sampling_missing_column(stratified_sampler):
    """
    Test that sampling raises an error if the strata column is missing.
    """
    df = pd.DataFrame({'value': [1, 2, 3]})

    with pytest.raises(ValueError, match="Strata column 'nonexistent' not found"):
        stratified_sampler(df, 'nonexistent', sample_size=2)

def test_cpu_only_enforcement():
    """
    Test that CPU-only environment is enforced.
    """
    import os
    # This test relies on the conftest.py hook setting CUDA_VISIBLE_DEVICES
    # We verify it is set to empty string
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "", "CPU-only enforcement failed."
