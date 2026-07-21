"""
Tests for the metrics calculation module (code/utils/metrics.py).
"""
import pytest

from utils.metrics import (
    calculate_diff_complexity_score,
    is_ai_noise_flag,
    calculate_iteration_count,
)


def test_diff_complexity_score_normal():
    """Test diff complexity calculation for normal case."""
    lines_added = 10
    lines_deleted = 5
    total_lines = 100

    score = calculate_diff_complexity_score(lines_added, lines_deleted, total_lines)
    expected = (10 + 5) / 100
    assert abs(score - expected) < 1e-6


def test_diff_complexity_score_no_deletion():
    """Test diff complexity when lines_deleted is 0."""
    score = calculate_diff_complexity_score(10, 0, 100)
    assert score == 0


def test_ai_noise_flag_true():
    """Test AI noise flag when conditions are met."""
    # Score > 0.3 and message contains 'fix'
    score = 0.4
    message = "fix: resolve critical bug"
    assert is_ai_noise_flag(score, message) is True


def test_ai_noise_flag_false_score():
    """Test AI noise flag when score is low."""
    score = 0.1
    message = "fix: resolve critical bug"
    assert is_ai_noise_flag(score, message) is False


def test_ai_noise_flag_false_message():
    """Test AI noise flag when message doesn't match keywords."""
    score = 0.4
    message = "feat: add new feature"
    assert is_ai_noise_flag(score, message) is False


def test_iteration_count_simple():
    """Test iteration count calculation."""
    # Mock PR data with 3 push events
    pr_data = {
        "events": [
            {"type": "push", "timestamp": "2023-01-01"},
            {"type": "push", "timestamp": "2023-01-02"},
            {"type": "push", "timestamp": "2023-01-03"},
        ]
    }
    count = calculate_iteration_count(pr_data)
    assert count == 3
