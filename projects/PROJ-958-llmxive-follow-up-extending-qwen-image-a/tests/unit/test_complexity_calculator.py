"""
Unit tests for the Complexity Calculator module (T013b).

These tests verify that the normalization logic correctly clamps
raw scores to the [0.0, 1.0] range as specified in Task T013b.
"""

import pytest
import logging
from src.scoring.complexity_calculator import (
    calculate_raw_score,
    normalize_score,
    compute_complexity_score
)

# Configure logging to capture warnings during clamping
logging.basicConfig(level=logging.WARNING)


class TestNormalizeScore:
    """Tests for the normalization logic."""

    def test_clamp_below_zero(self):
        """Test that negative raw scores are clamped to 0.0."""
        assert normalize_score(-0.5) == 0.0
        assert normalize_score(-100.0) == 0.0
        assert normalize_score(-0.0001) == 0.0

    def test_clamp_above_one(self):
        """Test that scores > 1.0 are clamped to 1.0."""
        assert normalize_score(1.5) == 1.0
        assert normalize_score(10.0) == 1.0
        assert normalize_score(1.0001) == 1.0

    def test_within_bounds(self):
        """Test that valid scores remain unchanged."""
        assert normalize_score(0.0) == 0.0
        assert normalize_score(1.0) == 1.0
        assert normalize_score(0.5) == 0.5
        assert normalize_score(0.734) == 0.734

    def test_type_preservation(self):
        """Test that the return type is float."""
        result = normalize_score(0.5)
        assert isinstance(result, float)


class TestCalculateRawScore:
    """Tests for the raw score calculation."""

    def test_equal_weights(self):
        """Test default equal weighting."""
        # (1 + 1 + 1) / 3 = 1.0
        score = calculate_raw_score(1.0, 1.0, 1.0)
        assert score == 1.0

        # (0 + 0 + 0) / 3 = 0.0
        score = calculate_raw_score(0.0, 0.0, 0.0)
        assert score == 0.0

    def test_custom_weights(self):
        """Test custom weighting logic."""
        # Weights: depth=2, clause=1, mtld=1. Total=4.
        # (2*2 + 1*1 + 1*1) / 4 = 6/4 = 1.5
        weights = {"parse_depth": 2.0, "clause_count": 1.0, "mtld": 1.0}
        score = calculate_raw_score(2.0, 1.0, 1.0, weights)
        assert score == 1.5

    def test_zero_weights(self):
        """Test handling of zero total weight."""
        weights = {"parse_depth": 0.0, "clause_count": 0.0, "mtld": 0.0}
        score = calculate_raw_score(10.0, 10.0, 10.0, weights)
        assert score == 0.0


class TestComputeComplexityScore:
    """Integration tests for the full pipeline."""

    def test_pipeline_normalization(self):
        """Test that the full pipeline clamps high raw scores."""
        # Inputs that produce a raw score > 1.0
        # Assume raw calculation results in 1.5
        score = compute_complexity_score(10.0, 10.0, 10.0)
        assert score == 1.0

    def test_pipeline_negative_normalization(self):
        """Test that the full pipeline clamps negative raw scores."""
        # Inputs that produce a raw score < 0.0 (if metrics allowed negative)
        # For this test, we pass negative metrics directly if the logic allows,
        # or rely on the internal calculation.
        # Since metrics are usually positive, we test the boundary directly via normalize
        # but here we test the function wrapper.
        # If we pass 0.0 for all, result is 0.0.
        # If we pass negative values (hypothetically):
        score = compute_complexity_score(-5.0, -5.0, -5.0)
        assert score == 0.0

    def test_pipeline_mid_range(self):
        """Test a mid-range score passes through."""
        # Construct inputs that yield exactly 0.5
        # If weights are equal, (x+x+x)/3 = 0.5 => x=0.5
        score = compute_complexity_score(0.5, 0.5, 0.5)
        assert score == 0.5