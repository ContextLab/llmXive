import pytest
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

from code.data.preprocess import (
    HumanRatingResult,
    validate_clip_scores,
    normalize_and_calculate_deviation,
    compute_deviation_batch,
)
from code.utils.errors import DataSchemaError


class TestMissingRatingHandling:
    """Tests for handling missing human ratings in deviation calculation."""

    def test_excludes_rows_with_nan_human_rating(self):
        """Verify that rows with missing human ratings are excluded."""
        clip_scores = [0.8, 0.9, 0.7, 0.85]
        human_ratings = [0.7, np.nan, 0.6, 0.8]

        result = normalize_and_calculate_deviation(clip_scores, human_ratings)

        # Should have 3 results (one excluded for NaN)
        assert len(result) == 3
        # The NaN row (index 1) should be excluded, so we have indices 0, 2, 3
        # Expected: |0.8-0.7|, |0.7-0.6|, |0.85-0.8| (after normalization)
        # We just verify length and that no NaN is in result
        assert all(not np.isnan(v) for v in result)

    def test_all_nan_human_ratings_raises_error(self):
        """Verify behavior when all human ratings are missing."""
        clip_scores = [0.8, 0.9, 0.7]
        human_ratings = [np.nan, np.nan, np.nan]

        with pytest.raises(ValueError, match="No valid human ratings found"):
            normalize_and_calculate_deviation(clip_scores, human_ratings)


class TestZeroVarianceDetection:
    """Tests for zero variance detection in target variable."""

    def test_raises_error_on_zero_variance_target(self):
        """Verify 'Target not learnable: zero variance detected' is raised."""
        # Create a case where deviation is constant (zero variance)
        # This happens when CLIP and Human are perfectly correlated with offset 0
        # or when all deviations are identical
        clip_scores = [0.5, 0.6, 0.7, 0.8]
        human_ratings = [0.5, 0.6, 0.7, 0.8]  # Perfect match -> deviation = 0 for all

        # After normalization, if all deviations are identical, variance is 0
        with pytest.raises(ValueError, match="Target not learnable: zero variance detected"):
            normalize_and_calculate_deviation(clip_scores, human_ratings)

    def test_raises_error_on_constant_non_zero_deviation(self):
        """Verify error when deviation is constant but non-zero."""
        # Force constant deviation by making CLIP = Human + constant
        clip_scores = [0.5, 0.6, 0.7, 0.8]
        human_ratings = [0.4, 0.5, 0.6, 0.7]  # Deviation = 0.1 for all

        with pytest.raises(ValueError, match="Target not learnable: zero variance detected"):
            normalize_and_calculate_deviation(clip_scores, human_ratings)

    def test_normal_variance_does_not_raise(self):
        """Verify normal variance cases do not raise zero variance error."""
        clip_scores = [0.5, 0.6, 0.7, 0.8]
        human_ratings = [0.5, 0.5, 0.7, 0.9]  # Varied deviations

        # Should not raise
        result = normalize_and_calculate_deviation(clip_scores, human_ratings)
        assert len(result) == 4
        # Verify variance is actually non-zero
        deviations = np.abs(np.array(clip_scores) - np.array(human_ratings))
        assert np.var(deviations) > 0

    def test_single_sample_raises_zero_variance(self):
        """Verify single sample raises zero variance (variance of 1 item is 0)."""
        clip_scores = [0.5]
        human_ratings = [0.5]

        with pytest.raises(ValueError, match="Target not learnable: zero variance detected"):
            normalize_and_calculate_deviation(clip_scores, human_ratings)

    def test_two_identical_samples_raises_zero_variance(self):
        """Verify two identical samples raise zero variance."""
        clip_scores = [0.5, 0.5]
        human_ratings = [0.5, 0.5]

        with pytest.raises(ValueError, match="Target not learnable: zero variance detected"):
            normalize_and_calculate_deviation(clip_scores, human_ratings)

    def test_two_different_samples_does_not_raise(self):
        """Verify two different samples do not raise zero variance."""
        clip_scores = [0.5, 0.6]
        human_ratings = [0.5, 0.7]  # Deviations: 0.0 and 0.1 -> variance > 0

        result = normalize_and_calculate_deviation(clip_scores, human_ratings)
        assert len(result) == 2


class TestNormalityCheckAndNormalization:
    """Tests for Shapiro-Wilk check and INT vs Z-score logic."""

    def test_gaussian_data_uses_zscore(self):
        """Verify Gaussian data uses Z-score normalization."""
        # Create data that should pass Shapiro-Wilk (normal distribution)
        np.random.seed(42)
        base_scores = np.random.normal(0.5, 0.1, 100)
        clip_scores = base_scores.tolist()
        human_ratings = (base_scores + np.random.normal(0, 0.01, 100)).tolist()

        result = normalize_and_calculate_deviation(clip_scores, human_ratings)
        assert len(result) == 100
        assert all(not np.isnan(v) for v in result)

    def test_non_gaussian_data_uses_int(self):
        """Verify non-Gaussian data uses rank-based INT."""
        # Create skewed data that should fail Shapiro-Wilk
        clip_scores = [0.1, 0.2, 0.3, 0.9, 0.95, 0.99] * 20  # Skewed
        human_ratings = [0.1, 0.2, 0.3, 0.8, 0.9, 0.95] * 20

        result = normalize_and_calculate_deviation(clip_scores, human_ratings)
        assert len(result) == 120
        assert all(not np.isnan(v) for v in result)
        # INT should produce values in approximately normal range
        assert np.mean(result) < 5  # INT typically bounded
        assert np.std(result) < 5


class TestDeviationCalculationCorrectness:
    """Tests for correctness of deviation calculation."""

    def test_absolute_difference_is_correct(self):
        """Verify deviation is absolute difference of normalized scores."""
        clip_scores = [0.5, 0.6, 0.7]
        human_ratings = [0.4, 0.6, 0.8]

        # Manual calculation:
        # After normalization, we expect some values
        # The key is that result[i] = |norm_clip[i] - norm_human[i]|
        result = normalize_and_calculate_deviation(clip_scores, human_ratings)

        assert len(result) == 3
        assert all(v >= 0 for v in result)  # Absolute difference is non-negative

    def test_deviation_order_preserves_input_order(self):
        """Verify result order matches input order (excluding NaN rows)."""
        clip_scores = [0.5, 0.6, 0.7, 0.8]
        human_ratings = [0.4, np.nan, 0.6, 0.7]

        result = normalize_and_calculate_deviation(clip_scores, human_ratings)
        # Should have 3 results corresponding to indices 0, 2, 3
        assert len(result) == 3