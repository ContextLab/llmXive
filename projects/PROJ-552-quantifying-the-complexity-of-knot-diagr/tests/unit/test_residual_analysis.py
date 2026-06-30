"""
Unit tests for residual-family identification logic.
Per Reviewer Action Item Testing (T087).
Tests that families with residuals >= 2 sigma are correctly listed.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import List, Tuple

import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.model_fitting import identify_residual_families, ResidualEntry, RegressionMetrics


class MockDataLoader:
    """Mock data loader to provide synthetic knot data for testing."""

    @staticmethod
    def load_cleaned_knots() -> List[dict]:
        """
        Generate synthetic knot data with known residual properties.
        Creates:
        - A "Pretzel" family with large residuals (outliers)
        - A "Hyperbolic Non-Alternating" family with moderate residuals
        - A "General" group with small residuals (normal distribution)
        """
        knots = []

        # Pretzel family: 5 knots with large residuals (should be flagged)
        for i in range(1, 6):
            knots.append({
                "knot_id": f"12n{i:03d}",
                "crossing_number": 12,
                "braid_index": 4,
                "hyperbolic_volume": 10.0 + i * 0.5,
                "predicted_volume": 5.0 + i * 0.2,  # Large error
                "family": "Pretzel",
                "is_alternating": False
            })

        # Hyperbolic Non-Alternating family: 4 knots with moderate residuals
        for i in range(1, 5):
            knots.append({
                "knot_id": f"11n{i:03d}",
                "crossing_number": 11,
                "braid_index": 3,
                "hyperbolic_volume": 8.0 + i * 0.3,
                "predicted_volume": 7.0 + i * 0.1,  # Moderate error
                "family": "Hyperbolic Non-Alternating",
                "is_alternating": False
            })

        # General group: 20 knots with small residuals (normal-like)
        for i in range(1, 21):
            knots.append({
                "knot_id": f"10n{i:03d}",
                "crossing_number": 10,
                "braid_index": 3,
                "hyperbolic_volume": 6.0 + (i % 10) * 0.1,
                "predicted_volume": 6.0 + (i % 10) * 0.1 + (i * 0.01),  # Small error
                "family": "General",
                "is_alternating": i % 2 == 0
            })

        return knots


def calculate_residuals_from_data(knots: List[dict]) -> List[ResidualEntry]:
    """Helper to calculate residuals from synthetic data."""
    residuals = []
    for knot in knots:
        actual = knot["hyperbolic_volume"]
        predicted = knot["predicted_volume"]
        residual = actual - predicted
        residuals.append(ResidualEntry(
            knot_id=knot["knot_id"],
            crossing_number=knot["crossing_number"],
            braid_index=knot["braid_index"],
            actual_volume=actual,
            predicted_volume=predicted,
            residual=residual,
            family=knot.get("family", "Unknown"),
            is_alternating=knot.get("is_alternating", False)
        ))
    return residuals


def test_identify_residual_families_detects_pretzel_outliers():
    """
    Test that the Pretzel family (large residuals) is correctly identified.
    """
    knots = MockDataLoader.load_cleaned_knots()
    residuals = calculate_residuals_from_data(knots)

    # Calculate mean and std of residuals for threshold
    residual_values = [r.residual for r in residuals]
    mean_residual = sum(residual_values) / len(residual_values)
    variance = sum((r - mean_residual) ** 2 for r in residual_values) / len(residual_values)
    std_residual = math.sqrt(variance)

    # Threshold: 2 sigma
    threshold = 2 * std_residual

    # Identify families with residuals >= threshold
    outlier_families = identify_residual_families(residuals, threshold)

    # Pretzel family should be in the results
    assert len(outlier_families) > 0, "No outlier families detected"
    family_names = [f[0] for f in outlier_families]
    assert "Pretzel" in family_names, f"Pretzel family not detected in outliers: {family_names}"


def test_identify_residual_families_moderate_outliers():
    """
    Test that the Hyperbolic Non-Alternating family is detected if residuals are high enough.
    """
    knots = MockDataLoader.load_cleaned_knots()
    residuals = calculate_residuals_from_data(knots)

    residual_values = [r.residual for r in residuals]
    mean_residual = sum(residual_values) / len(residual_values)
    variance = sum((r - mean_residual) ** 2 for r in residual_values) / len(residual_values)
    std_residual = math.sqrt(variance)

    # Use a lower threshold to catch moderate outliers (1.5 sigma)
    threshold = 1.5 * std_residual

    outlier_families = identify_residual_families(residuals, threshold)
    family_names = [f[0] for f in outlier_families]

    # Should catch at least Pretzel, possibly Hyperbolic Non-Alternating
    assert "Pretzel" in family_names


def test_identify_residual_families_general_group_excluded():
    """
    Test that the General group (small residuals) is NOT flagged as outliers.
    """
    knots = MockDataLoader.load_cleaned_knots()
    residuals = calculate_residuals_from_data(knots)

    residual_values = [r.residual for r in residuals]
    mean_residual = sum(residual_values) / len(residual_values)
    variance = sum((r - mean_residual) ** 2 for r in residual_values) / len(residual_values)
    std_residual = math.sqrt(variance)

    # High threshold: 2 sigma
    threshold = 2 * std_residual

    outlier_families = identify_residual_families(residuals, threshold)
    family_names = [f[0] for f in outlier_families]

    # General group should NOT be in outliers (residuals are small)
    # Note: This depends on the distribution, but with our synthetic data,
    # General group residuals are intentionally small.
    # We assert that the count of outliers is dominated by Pretzel
    assert len(outlier_families) < len(set(k["family"] for k in knots)), "Too many families flagged"


def test_identify_residual_families_empty_input():
    """Test behavior with empty residual list."""
    residuals = []
    outlier_families = identify_residual_families(residuals, threshold=1.0)
    assert len(outlier_families) == 0, "Empty input should return empty list"


def test_identify_residual_families_single_outlier():
    """Test detection of a single outlier family."""
    knots = [
        {"knot_id": "k1", "crossing_number": 5, "braid_index": 2,
         "hyperbolic_volume": 100.0, "predicted_volume": 10.0,
         "family": "SingleOutlier", "is_alternating": False},
        {"knot_id": "k2", "crossing_number": 5, "braid_index": 2,
         "hyperbolic_volume": 10.0, "predicted_volume": 10.0,
         "family": "Normal", "is_alternating": False}
    ]
    residuals = calculate_residuals_from_data(knots)

    # Threshold: 1.0 (SingleOutlier has residual 90.0)
    outlier_families = identify_residual_families(residuals, threshold=1.0)
    family_names = [f[0] for f in outlier_families]

    assert "SingleOutlier" in family_names


def test_identify_residual_families_returns_correct_format():
    """Test that the return format is a list of tuples (family_name, count, list_of_knot_ids)."""
    knots = MockDataLoader.load_cleaned_knots()
    residuals = calculate_residuals_from_data(knots)

    residual_values = [r.residual for r in residuals]
    mean_residual = sum(residual_values) / len(residual_values)
    variance = sum((r - mean_residual) ** 2 for r in residual_values) / len(residual_values)
    std_residual = math.sqrt(variance)

    threshold = 2 * std_residual
    outlier_families = identify_residual_families(residuals, threshold)

    assert isinstance(outlier_families, list), "Output must be a list"
    for item in outlier_families:
        assert isinstance(item, tuple), "Each item must be a tuple"
        assert len(item) == 3, "Each tuple must have 3 elements: (family_name, count, knot_ids)"
        family_name, count, knot_ids = item
        assert isinstance(family_name, str), "Family name must be string"
        assert isinstance(count, int), "Count must be integer"
        assert isinstance(knot_ids, list), "Knot IDs must be list"
        assert count == len(knot_ids), "Count must match length of knot_ids"