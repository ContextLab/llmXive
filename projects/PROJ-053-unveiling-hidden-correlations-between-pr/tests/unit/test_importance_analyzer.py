import pytest
import numpy as np
import os
import json
from unittest.mock import patch, MagicMock

from code.utils.importance_analyzer import (
    calculate_correlation_coefficient,
    get_hardcoded_baseline_ranking,
    rank_list_to_feature_list
)

def test_correlation_perfect_match():
    """Test correlation when both rankings are identical."""
    r1 = ["A", "B", "C"]
    r2 = ["A", "B", "C"]
    corr = calculate_correlation_coefficient(r1, r2)
    assert abs(corr - 1.0) < 1e-6

def test_correlation_perfect_reverse():
    """Test correlation when rankings are perfectly reversed."""
    r1 = ["A", "B", "C"]
    r2 = ["C", "B", "A"]
    corr = calculate_correlation_coefficient(r1, r2)
    # Spearman for n=3, reverse: 1 - (6*(1+1+1))/(3*8) = 1 - 18/24 = 1 - 0.75 = 0.25?
    # Wait, for n=3:
    # A(0), B(1), C(2) vs C(0), B(1), A(2)
    # d = [0-2, 1-1, 2-0] = [-2, 0, 2]
    # d^2 = [4, 0, 4] sum=8
    # 1 - (6*8)/(3*8) = 1 - 48/24 = 1 - 2 = -1.0
    assert abs(corr - (-1.0)) < 1e-6

def test_correlation_partial_overlap():
    """Test correlation with partial overlap."""
    r1 = ["A", "B", "C"]
    r2 = ["B", "A", "D"] # D is ignored
    # Common: A, B
    # r1: A=0, B=1
    # r2: A=1, B=0
    # d = [-1, 1] -> d^2 = 2
    # n=2 -> 1 - (6*2)/(2*3) = 1 - 12/6 = -1.0
    corr = calculate_correlation_coefficient(r1, r2)
    assert abs(corr - (-1.0)) < 1e-6

def test_hardcoded_baseline_ranking():
    """Test that hardcoded baseline returns a list."""
    ranking = get_hardcoded_baseline_ranking()
    assert isinstance(ranking, list)
    assert len(ranking) > 0
    assert "laser_power" in ranking

def test_rank_list_to_feature_list():
    """Test extraction of feature names."""
    data = [("A", 0.5), ("B", 0.2), ("C", 0.1)]
    result = rank_list_to_feature_list(data)
    assert result == ["A", "B", "C"]
    assert isinstance(result, list)