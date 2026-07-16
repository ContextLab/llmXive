import pytest
import numpy as np
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock
from code.data.preprocess import (
    HumanRatingResult,
    process_human_ratings,
    compute_clip_scores,
    normalize_and_calculate_deviation,
    compute_deviation_batch,
)
from code.utils.logging import setup_logging
import logging

# Setup logging for tests
setup_logging()
logger = logging.getLogger(__name__)


class TestMissingRatingHandling:
    """Tests for missing rating handling in preprocessing (T027)."""

    def test_excludes_missing_human_ratings(self):
        """Verify rows with missing human ratings are excluded."""
        records = [
            {"caption": "A cat", "clip_score": 0.8, "human_rating": 0.9},
            {"caption": "A dog", "clip_score": 0.7, "human_rating": None},
            {"caption": "A bird", "clip_score": 0.6, "human_rating": 0.5},
        ]

        # Mock the internal functions to isolate the exclusion logic
        with patch(
            "code.data.preprocess.normalize_and_calculate_deviation"
        ) as mock_norm:
            mock_norm.return_value = [0.1, 0.2]  # Return values for valid rows only

            result = compute_deviation_batch(records)

            # Should only have 2 rows (the ones with valid human ratings)
            assert len(result) == 2
            assert "human_rating" in result.columns
            # Verify no None values in the result
            assert result["human_rating"].isna().sum() == 0


class TestZeroVarianceDetection:
    """Tests for zero variance detection in target variable (T028)."""

    def test_raises_error_on_zero_variance(self):
        """Verify 'Target not learnable' error is raised when deviation has zero variance."""
        # Create records where all deviations would be identical (zero variance)
        # e.g., all CLIP scores and Human ratings are identical
        records = [
            {"caption": "A cat", "clip_score": 0.5, "human_rating": 0.5},
            {"caption": "A dog", "clip_score": 0.5, "human_rating": 0.5},
            {"caption": "A bird", "clip_score": 0.5, "human_rating": 0.5},
        ]

        # Mock normalize_and_calculate_deviation to return identical values
        with patch(
            "code.data.preprocess.normalize_and_calculate_deviation"
        ) as mock_norm:
            # Return a list of identical deviations (0.0 in this case)
            mock_norm.return_value = [0.0, 0.0, 0.0]

            with pytest.raises(ValueError) as exc_info:
                compute_deviation_batch(records)

            assert "Target not learnable" in str(exc_info.value)

    def test_no_error_on_nonzero_variance(self):
        """Verify no error is raised when deviation has non-zero variance."""
        records = [
            {"caption": "A cat", "clip_score": 0.8, "human_rating": 0.9},
            {"caption": "A dog", "clip_score": 0.7, "human_rating": 0.5},
            {"caption": "A bird", "clip_score": 0.6, "human_rating": 0.8},
        ]

        with patch(
            "code.data.preprocess.normalize_and_calculate_deviation"
        ) as mock_norm:
            # Return deviations with non-zero variance
            mock_norm.return_value = [0.1, 0.3, 0.2]

            # Should not raise an error
            result = compute_deviation_batch(records)
            assert len(result) == 3
            assert "deviation" in result.columns

    def test_raises_error_on_constant_nonzero_deviation(self):
        """Verify error is raised even if constant deviation is non-zero."""
        records = [
            {"caption": "A cat", "clip_score": 0.9, "human_rating": 0.7},
            {"caption": "A dog", "clip_score": 0.8, "human_rating": 0.6},
            {"caption": "A bird", "clip_score": 0.7, "human_rating": 0.5},
        ]

        with patch(
            "code.data.preprocess.normalize_and_calculate_deviation"
        ) as mock_norm:
            # Return constant non-zero deviations (e.g., all 0.2)
            mock_norm.return_value = [0.2, 0.2, 0.2]

            with pytest.raises(ValueError) as exc_info:
                compute_deviation_batch(records)

            assert "Target not learnable" in str(exc_info.value)