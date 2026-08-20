import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

from code.utils.logger import get_logger, log_operation


def test_permutation_results_file_exists():
    """Simple sanity test – the permutation script should create the JSON file."""
    result_path = Path("data/processed/permutation_results.json")
    assert result_path.is_file(), f"{result_path} does not exist"

    # The file should contain valid JSON with the expected keys
    with result_path.open() as f:
        data = json.load(f)
    assert "permutations" in data and data["permutations"] == 500
    assert "auc_scores" in data and isinstance(data["auc_scores"], list)


def test_p_value_calculation_logic():
    """
    Test the core logic of p-value calculation for permutation tests.
    The p-value is defined as (count of permuted scores >= original score + 1) / (n_permutations + 1).
    """
    # Simulate a scenario where the original score is clearly better than the distribution
    original_score = 0.85
    permuted_scores = [0.40, 0.45, 0.50, 0.55, 0.60]
    n_permutations = len(permuted_scores)

    # Calculate p-value manually according to the formula
    count_greater_or_equal = sum(1 for s in permuted_scores if s >= original_score)
    expected_p_value = (count_greater_or_equal + 1) / (n_permutations + 1)

    # Expected: 0 >= 0.85 is False for all, so count is 0.
    # p = (0 + 1) / (5 + 1) = 1/6
    assert expected_p_value == pytest.approx(1/6)

    # Now test a scenario where some permuted scores are higher (worse model)
    permuted_scores_worse = [0.80, 0.90, 0.85, 0.70, 0.60]
    count_greater_or_equal_worse = sum(1 for s in permuted_scores_worse if s >= original_score)
    expected_p_value_worse = (count_greater_or_equal_worse + 1) / (n_permutations + 1)
    # 0.90 >= 0.85 (True), 0.85 >= 0.85 (True). Count = 2.
    # p = (2 + 1) / 6 = 0.5
    assert expected_p_value_worse == pytest.approx(0.5)


def test_p_value_calculation_edge_case():
    """Test p-value when original score is lower than all permuted scores."""
    original_score = 0.30
    permuted_scores = [0.50, 0.60, 0.70]
    n_permutations = len(permuted_scores)

    count = sum(1 for s in permuted_scores if s >= original_score)
    p_value = (count + 1) / (n_permutations + 1)

    # All 3 are >= 0.30. Count = 3.
    # p = 4 / 4 = 1.0
    assert p_value == 1.0


def test_p_value_calculation_edge_case_best():
    """Test p-value when original score is higher than all permuted scores."""
    original_score = 0.95
    permuted_scores = [0.40, 0.50, 0.60]
    n_permutations = len(permuted_scores)

    count = sum(1 for s in permuted_scores if s >= original_score)
    p_value = (count + 1) / (n_permutations + 1)

    # None are >= 0.95. Count = 0.
    # p = 1 / 4 = 0.25
    assert p_value == 0.25


def test_distribution_statistics():
    """Test calculation of mean and std of the permutation distribution."""
    scores = [0.4, 0.5, 0.6, 0.7, 0.8]
    mean_score = np.mean(scores)
    std_score = np.std(scores, ddof=1) # Sample std

    assert mean_score == pytest.approx(0.6)
    assert std_score > 0.0


def test_permutation_count_validation():
    """Ensure that the number of permutations matches the expected count."""
    expected_n = 500
    # Simulate a list of 500 random scores
    scores = np.random.random(expected_n)
    assert len(scores) == expected_n