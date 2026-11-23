"""
Unit tests for the reduce_sample_size module.

Tests cover:
- Basic reduction functionality
- Target size enforcement
- Stratified sampling
- Power limitation error handling
- Edge cases
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.tasks.reduce_sample_size import (
    reduce_sample_size,
    PowerLimitationError,
    MIN_SAMPLE_SIZE,
    get_current_memory_usage_mb
)


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    np.random.seed(42)
    n_samples = 100000

    df = pd.DataFrame({
        'timestamp': np.random.randint(0, 1000000, n_samples),
        'semantic_feature': np.random.randn(n_samples),
        'prosodic_feature': np.random.randn(n_samples),
        'latent_delta_magnitude': np.random.randn(n_samples),
        'turn_label': np.random.choice(['speaker_a', 'speaker_b', 'interrupt', 'pause'], n_samples)
    })

    return df


@pytest.fixture
def small_dataframe():
    """Create a small DataFrame for edge case testing."""
    np.random.seed(42)
    n_samples = 5000

    df = pd.DataFrame({
        'timestamp': np.random.randint(0, 100000, n_samples),
        'value': np.random.randn(n_samples),
        'category': np.random.choice(['A', 'B', 'C'], n_samples)
    })

    return df


def test_basic_reduction(sample_dataframe):
    """Test basic sample size reduction."""
    target_size = 50000
    reduced_df, metadata = reduce_sample_size(
        sample_dataframe,
        target_size=target_size,
        seed=42
    )

    assert len(reduced_df) == target_size
    assert metadata['original_size'] == 100000
    assert metadata['reduced_size'] == target_size
    assert metadata['reduction_ratio'] == 0.5
    assert metadata['reason'] == 'power_limit_reduction'


def test_target_size(sample_dataframe):
    """Test that target size is correctly enforced."""
    target_size = 75000
    reduced_df, metadata = reduce_sample_size(
        sample_dataframe,
        target_size=target_size,
        seed=42
    )

    assert len(reduced_df) == target_size
    assert metadata['target_size'] == target_size


def test_stratified_sampling(sample_dataframe):
    """Test stratified sampling preserves distribution."""
    original_distribution = sample_dataframe['turn_label'].value_counts(normalize=True)

    reduced_df, metadata = reduce_sample_size(
        sample_dataframe,
        target_size=50000,
        stratify_column='turn_label',
        seed=42
    )

    reduced_distribution = reduced_df['turn_label'].value_counts(normalize=True)

    # Check that distribution is approximately preserved (within 5% tolerance)
    for label in original_distribution.index:
        orig_prop = original_distribution.get(label, 0)
        red_prop = reduced_distribution.get(label, 0)
        assert abs(orig_prop - red_prop) < 0.05, \
            f"Distribution mismatch for {label}: {orig_prop:.3f} vs {red_prop:.3f}"


def test_power_limitation_error_small_target(sample_dataframe):
    """Test that PowerLimitationError is raised when target is too small."""
    target_size = MIN_SAMPLE_SIZE - 1000

    with pytest.raises(PowerLimitationError) as exc_info:
        reduce_sample_size(
            sample_dataframe,
            target_size=target_size,
            min_sample_size=MIN_SAMPLE_SIZE
        )

    assert "Power Limitation" in str(exc_info.value)
    assert str(MIN_SAMPLE_SIZE) in str(exc_info.value)


def test_power_limitation_error_already_small(sample_dataframe):
    """Test error when dataset is already below minimum."""
    # Create a dataset smaller than minimum
    small_df = sample_dataframe.head(MIN_SAMPLE_SIZE - 1000)

    with pytest.raises(PowerLimitationError) as exc_info:
        reduce_sample_size(
            small_df,
            target_size=MIN_SAMPLE_SIZE - 2000,
            min_sample_size=MIN_SAMPLE_SIZE
        )

    assert "Power Limitation" in str(exc_info.value)


def test_no_reduction_needed(sample_dataframe):
    """Test behavior when no reduction is needed."""
    target_size = 150000  # Larger than dataset

    reduced_df, metadata = reduce_sample_size(
        sample_dataframe,
        target_size=target_size,
        seed=42
    )

    assert len(reduced_df) == len(sample_dataframe)
    assert metadata['reason'] == 'no_reduction_needed'
    assert metadata['reduction_ratio'] == 1.0


def test_reproducibility(sample_dataframe):
    """Test that same seed produces same results."""
    target_size = 50000

    reduced_df1, _ = reduce_sample_size(
        sample_dataframe,
        target_size=target_size,
        seed=123
    )

    reduced_df2, _ = reduce_sample_size(
        sample_dataframe,
        target_size=target_size,
        seed=123
    )

    # Check that results are identical
    pd.testing.assert_frame_equal(reduced_df1.reset_index(drop=True),
                                 reduced_df2.reset_index(drop=True))


def test_invalid_input():
    """Test handling of empty DataFrame."""
    empty_df = pd.DataFrame()

    with pytest.raises(ValueError) as exc_info:
        reduce_sample_size(empty_df, target_size=1000)

    assert "empty" in str(exc_info.value).lower()


def test_memory_usage_function():
    """Test that memory usage function returns a valid number."""
    memory_mb = get_current_memory_usage_mb()
    assert isinstance(memory_mb, float)
    assert memory_mb >= 0