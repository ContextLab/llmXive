"""
Unit tests for code/metrics/extract.py functions.
Tests compute_entropy, compute_repetition, and compute_variance.
"""
import pytest
import math
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List

# Import the functions under test
# Note: The API surface lists them as calculate_sequence_entropy, etc.
# The task description asks for tests for compute_entropy, etc.
# We assume the implementation in extract.py exposes these functions
# or the test should import from utils.metrics_extract which has the correct names.
# Based on the API surface, code/utils/metrics_extract.py has the pure functions.
# We will import from there to ensure we test the pure logic.
from code.utils.metrics_extract import (
    calculate_sequence_entropy,
    calculate_tool_repetition_frequency,
    calculate_argument_variance
)
from code.metrics.extract import MetricExtractionError


class TestCalculateSequenceEntropy:
    """Tests for calculate_sequence_entropy."""

    def test_empty_sequence_raises_error(self):
        """Test that an empty sequence raises ValueError."""
        with pytest.raises(ValueError):
            calculate_sequence_entropy([])

    def test_single_element_sequence(self):
        """Test entropy for a single element (should be 0)."""
        sequence = ["tool_A"]
        entropy = calculate_sequence_entropy(sequence)
        assert entropy == 0.0

    def test_uniform_distribution(self):
        """Test entropy for a uniform distribution."""
        # Two tools, equal frequency
        sequence = ["tool_A", "tool_B", "tool_A", "tool_B"]
        entropy = calculate_sequence_entropy(sequence)
        # Entropy = - (0.5 * log2(0.5) + 0.5 * log2(0.5)) = 1.0
        assert math.isclose(entropy, 1.0, rel_tol=1e-6)

    def test_skewed_distribution(self):
        """Test entropy for a skewed distribution."""
        # One tool dominates
        sequence = ["tool_A", "tool_A", "tool_A", "tool_B"]
        entropy = calculate_sequence_entropy(sequence)
        # p(A) = 0.75, p(B) = 0.25
        # H = - (0.75 * log2(0.75) + 0.25 * log2(0.25))
        expected = - (0.75 * math.log2(0.75) + 0.25 * math.log2(0.25))
        assert math.isclose(entropy, expected, rel_tol=1e-6)

    def test_all_unique_elements(self):
        """Test entropy when all elements are unique."""
        sequence = ["tool_A", "tool_B", "tool_C", "tool_D"]
        entropy = calculate_sequence_entropy(sequence)
        # p(x) = 0.25 for all x, H = log2(4) = 2.0
        assert math.isclose(entropy, 2.0, rel_tol=1e-6)


class TestCalculateToolRepetitionFrequency:
    """Tests for calculate_tool_repetition_frequency."""

    def test_empty_sequence_raises_error(self):
        """Test that an empty sequence raises ValueError."""
        with pytest.raises(ValueError):
            calculate_tool_repetition_frequency([])

    def test_no_repetitions(self):
        """Test frequency when no tools repeat."""
        sequence = ["tool_A", "tool_B", "tool_C"]
        freq = calculate_tool_repetition_frequency(sequence)
        # Repetitions = 0
        assert freq == 0.0

    def test_all_same_tool(self):
        """Test frequency when all tools are the same."""
        sequence = ["tool_A", "tool_A", "tool_A", "tool_A"]
        freq = calculate_tool_repetition_frequency(sequence)
        # Total = 4, Unique = 1, Repetitions = 3
        # Freq = 3 / 4 = 0.75
        assert freq == 0.75

    def test_partial_repetition(self):
        """Test frequency with partial repetition."""
        sequence = ["tool_A", "tool_A", "tool_B", "tool_C", "tool_B"]
        # Total = 5, Unique = 3 (A, B, C)
        # Repetitions = 5 - 3 = 2
        # Freq = 2 / 5 = 0.4
        freq = calculate_tool_repetition_frequency(sequence)
        assert freq == 0.4

    def test_single_element_no_repetition(self):
        """Test frequency for a single element."""
        sequence = ["tool_A"]
        freq = calculate_tool_repetition_frequency(sequence)
        # Total = 1, Unique = 1, Repetitions = 0
        assert freq == 0.0


class TestCalculateArgumentVariance:
    """Tests for calculate_argument_variance."""

    def test_empty_list_raises_error(self):
        """Test that an empty list raises ValueError."""
        with pytest.raises(ValueError):
            calculate_argument_variance([])

    def test_single_value_variance(self):
        """Test variance for a single value (should be 0)."""
        values = [5.0]
        variance = calculate_argument_variance(values)
        assert variance == 0.0

    def test_identical_values_variance(self):
        """Test variance for identical values (should be 0)."""
        values = [3.5, 3.5, 3.5, 3.5]
        variance = calculate_argument_variance(values)
        assert variance == 0.0

    def test_simple_variance_calculation(self):
        """Test variance calculation for a simple set."""
        # Values: [1, 2, 3, 4, 5]
        # Mean = 3
        # Variance (population) = ((1-3)^2 + (2-3)^2 + (3-3)^2 + (4-3)^2 + (5-3)^2) / 5
        # = (4 + 1 + 0 + 1 + 4) / 5 = 10 / 5 = 2.0
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        variance = calculate_argument_variance(values)
        assert math.isclose(variance, 2.0, rel_tol=1e-6)

    def test_float_values(self):
        """Test variance with float values."""
        values = [1.1, 2.2, 3.3]
        mean = sum(values) / len(values)
        expected = sum((x - mean) ** 2 for x in values) / len(values)
        variance = calculate_argument_variance(values)
        assert math.isclose(variance, expected, rel_tol=1e-6)

    def test_negative_values(self):
        """Test variance with negative values."""
        values = [-1.0, -2.0, -3.0]
        mean = sum(values) / len(values)
        expected = sum((x - mean) ** 2 for x in values) / len(values)
        variance = calculate_argument_variance(values)
        assert math.isclose(variance, expected, rel_tol=1e-6)


class TestMetricExtractionEdgeCases:
    """Tests for edge cases in metric extraction."""

    def test_very_long_sequence(self):
        """Test entropy calculation with a very long sequence."""
        # Create a sequence with 1000 elements
        sequence = ["tool_A"] * 500 + ["tool_B"] * 500
        entropy = calculate_sequence_entropy(sequence)
        # Should be close to 1.0
        assert math.isclose(entropy, 1.0, rel_tol=1e-3)

    def test_very_large_variance_values(self):
        """Test variance with very large numbers."""
        values = [1e10, 2e10, 3e10]
        variance = calculate_argument_variance(values)
        # Mean = 2e10
        # Variance = ((1e10)^2 + 0 + (1e10)^2) / 3 = 2e20 / 3
        expected = 2e20 / 3
        assert math.isclose(variance, expected, rel_tol=1e-6)

    def test_very_small_variance_values(self):
        """Test variance with very small numbers."""
        values = [1e-10, 2e-10, 3e-10]
        variance = calculate_argument_variance(values)
        # Mean = 2e-10
        # Variance = ((1e-10)^2 + 0 + (1e-10)^2) / 3 = 2e-20 / 3
        expected = 2e-20 / 3
        assert math.isclose(variance, expected, rel_tol=1e-6)

    def test_mixed_sign_arguments(self):
        """Test variance with mixed positive and negative values."""
        values = [-5.0, 0.0, 5.0]
        mean = 0.0
        expected = (25 + 0 + 25) / 3
        variance = calculate_argument_variance(values)
        assert math.isclose(variance, expected, rel_tol=1e-6)