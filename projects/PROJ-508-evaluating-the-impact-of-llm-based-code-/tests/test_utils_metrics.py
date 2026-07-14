"""
Unit tests for code/utils/metrics.py
"""
import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.metrics import (
    calculate_iteration_count,
    calculate_avg_comment_length,
    calculate_review_thread_depth,
    calculate_revert_frequency,
    calculate_diff_complexity_score,
    is_ai_noise_flag,
    calculate_domain_complexity
)

def test_calculate_iteration_count():
    """Test iteration count logic (total push events)."""
    # Mock data: 3 push events
    push_events = [
        {"sha": "abc123", "message": "Initial commit"},
        {"sha": "def456", "message": "Fix bug"},
        {"sha": "ghi789", "message": "Update docs"}
    ]
    count = calculate_iteration_count(push_events)
    assert count == 3, f"Expected 3 iterations, got {count}"

def test_calculate_diff_complexity_score():
    """Test diff complexity score calculation."""
    # Scenario 1: Normal case
    metrics = {
        "lines_added": 10,
        "lines_deleted": 5,
        "total_lines": 100
    }
    score = calculate_diff_complexity_score(metrics)
    expected = (10 + 5) / 100
    assert score == expected, f"Expected {expected}, got {score}"

    # Scenario 2: No deletions (should be 0)
    metrics_no_del = {
        "lines_added": 10,
        "lines_deleted": 0,
        "total_lines": 100
    }
    score_no_del = calculate_diff_complexity_score(metrics_no_del)
    assert score_no_del == 0, f"Expected 0 when no deletions, got {score_no_del}"

def test_is_ai_noise_flag():
    """Test AI Noise flag logic."""
    # Scenario 1: High complexity + fix keyword
    metrics = {
        "diff_complexity_score": 0.5,
        "commit_message": "fix: urgent patch"
    }
    assert is_ai_noise_flag(metrics) is True

    # Scenario 2: Low complexity
    metrics_low = {
        "diff_complexity_score": 0.1,
        "commit_message": "fix: urgent patch"
    }
    assert is_ai_noise_flag(metrics_low) is False

    # Scenario 3: High complexity but no fix keyword
    metrics_no_fix = {
        "diff_complexity_score": 0.5,
        "commit_message": "feat: new feature"
    }
    assert is_ai_noise_flag(metrics_no_fix) is False

def test_calculate_domain_complexity():
    """Test domain complexity calculation."""
    data = {
        "languages": ["Python", "JavaScript"],
        "dependencies_count": 5
    }
    complexity = calculate_domain_complexity(data)
    # Logic: unique languages + dependencies
    expected = 2 + 5
    assert complexity == expected, f"Expected {expected}, got {complexity}"
