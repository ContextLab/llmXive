"""
Unit tests for ``code/model_metrics.py`` – specifically the detection of NaN
and infinite perplexity values, as well as the edge‑case where model loading
in 8‑bit quantization fails.  In addition, tests for the newly added semantic
distance calculation are provided.
"""

import math

import pytest

# Import the functions/classes from the module under test
from model_metrics import (
    detect_invalid_perplexity,
    compute_perplexity_batch,
    ModelLoadingError,
    compute_semantic_distance_batch,
)


@pytest.mark.parametrize(
    "perplexities,expected_invalid",
    [
        # No invalid values
        ([10.0, 20.5, 30.2], []),
        # Single NaN
        ([float("nan"), 15.0, 25.0], [0]),
        # Single positive infinity
        ([12.0, float("inf"), 22.0], [1]),
        # Single negative infinity
        ([12.0, -float("inf"), 22.0], [1]),
        # Mixed invalid values
        (
            [5.0, float("nan"), float("inf"), -float("inf"), 9.0],
            [1, 2, 3],
        ),
    ],
)
def test_detect_invalid_perplexity(perplexities, expected_invalid):
    """
    Verify that ``detect_invalid_perplexity`` returns the correct indices
    for NaN and infinite values.
    """
    result = detect_invalid_perplexity(perplexities)
    assert result == expected_invalid


def test_detect_invalid_perplexity_all_invalid():
    """
    Edge case where every entry is invalid – the function should return
    a list covering the entire range.
    """
    perplexities = [float("nan"), float("inf"), -float("inf")]
    assert detect_invalid_perplexity(perplexities) == [0, 1, 2]


def test_detect_invalid_perplexity_type_error():
    """
    The helper expects a list of floats.  Passing a non‑iterable should raise
    a ``TypeError`` because the function will attempt to iterate over it.
    """
    with pytest.raises(TypeError):
        # type: ignore[arg-type] – intentionally passing wrong type
        detect_invalid_perplexity(42)  # pyright: ignore[reportGeneralTypeIssues]


def test_compute_perplexity_batch_model_loading_failure():
    """
    Edge‑case test for model‑loading failure in 8‑bit quantization.

    In the CI environment ``bitsandbytes`` is not installed.  The function
    should therefore raise ``ModelLoadingError`` when it attempts to load
    the model.
    """
    # Provide a minimal, valid input list.
    inputs = ["def foo():\n    return 42"]
    with pytest.raises(ModelLoadingError):
        compute_perplexity_batch(inputs)


# ----------------------------------------------------------------------
# Semantic distance tests (new for T053)
# ----------------------------------------------------------------------
def test_compute_semantic_distance_batch_identical_inputs():
    """
    Two identical code snippets should have a semantic distance of (approximately) 0.
    """
    inputs = [
        "def add(a, b):\n    return a + b",
        "def add(a, b):\n    return a + b",
    ]
    distances = compute_semantic_distance_batch(inputs)
    # Both distances should be near zero
    assert distances[0] == pytest.approx(0.0, abs=1e-3)
    assert distances[1] == pytest.approx(0.0, abs=1e-3)


def test_compute_semantic_distance_batch_different_inputs():
    """
    Dissimilar snippets should yield a distance greater than zero.
    """
    inputs = [
        "def add(a, b):\n    return a + b",
        "def multiply(x, y):\n    return x * y",
        "def hello():\n    print('Hello world')",
    ]
    distances = compute_semantic_distance_batch(inputs)
    # At least one distance should be noticeably > 0
    assert any(d > 0.1 for d in distances)


def test_compute_semantic_distance_batch_single_input():
    """
    A single element batch should return a distance of 0.0.
    """
    inputs = ["def foo():\n    pass"]
    distances = compute_semantic_distance_batch(inputs)
    assert distances == [0.0]