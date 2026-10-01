"""
Unit tests for T014: Pytest configuration and sampling utilities.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from tests.conftest import _stratified_sample, STRATIFIED_COLUMN, SAMPLE_FRACTION, RANDOM_SEED


def test_stratified_sampling_preserves_proportions():
    """
    Verify that stratified sampling maintains the relative distribution 
    of the stratification column.
    """
    # Create a synthetic dataset with known proportions
    data = {
        "value": range(100),
        "country": ["A"] * 50 + ["B"] * 30 + ["C"] * 20
    }
    df = pd.DataFrame(data)
    
    fraction = 0.5
    sampled_df = _stratified_sample(df, fraction, "country", seed=RANDOM_SEED)
    
    # Check that the sampled counts are roughly half (allowing for randomness)
    original_counts = df["country"].value_counts()
    sampled_counts = sampled_df["country"].value_counts()
    
    # Since we use a fixed seed, the counts should be deterministic
    # A: 25, B: 15, C: 10
    assert sampled_counts["A"] == 25
    assert sampled_counts["B"] == 15
    assert sampled_counts["C"] == 10


def test_stratified_sampling_missing_column():
    """
    Verify behavior when stratification column is missing.
    """
    data = {
        "value": range(10),
        "other_col": ["X"] * 10
    }
    df = pd.DataFrame(data)
    
    # Should fall back to random sampling without raising
    sampled_df = _stratified_sample(df, 0.5, "missing_col", seed=RANDOM_SEED)
    
    assert len(sampled_df) == 5  # 50% of 10
    assert "value" in sampled_df.columns


def test_determinism_with_seed():
    """
    Verify that using the same seed produces identical results.
    """
    data = {
        "value": range(20),
        "country": ["A"] * 10 + ["B"] * 10
    }
    df = pd.DataFrame(data)
    
    result1 = _stratified_sample(df, 0.5, "country", seed=RANDOM_SEED)
    result2 = _stratified_sample(df, 0.5, "country", seed=RANDOM_SEED)
    
    pd.testing.assert_frame_equal(result1.sort_index(), result2.sort_index())