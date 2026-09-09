import pytest
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, mock_open

# Add code to path if not already
code_root = Path(__file__).parent.parent.parent.parent / "code"
sys.path.insert(0, str(code_root))

from data_generation.expert_system_validator import (
    calculate_expert_score, 
    review_trajectories, 
    EXPERT_SCORE_THRESHOLD,
    MIN_TRAJECTORIES_TO_REVIEW
)

@pytest.fixture
def valid_trajectory():
    return {
        "trajectory_id": "test-001",
        "actions": [
            {"description": "Open Settings", "step": 1},
            {"description": "Click WiFi", "step": 2},
            {"description": "Connect to Network", "step": 3},
            {"description": "Verify Connection", "step": 4}
        ],
        "state": "connected"
    }

@pytest.fixture
def short_trajectory():
    return {
        "trajectory_id": "test-002",
        "actions": [
            {"description": "Open App", "step": 1}
        ]
    }

@pytest.fixture
def error_trajectory():
    return {
        "trajectory_id": "test-003",
        "actions": [
            {"description": "Open App", "step": 1},
            {"description": "Click Button", "step": 2},
            {"description": "Error: Timeout occurred", "step": 3},
            {"description": "Retry", "step": 4}
        ]
    }

def test_calculate_score_high_quality(valid_trajectory):
    score, reasons = calculate_expert_score(valid_trajectory)
    assert score >= EXPERT_SCORE_THRESHOLD
    assert len(reasons) == 0

def test_calculate_score_short_trajectory(short_trajectory):
    score, reasons = calculate_expert_score(short_trajectory)
    assert score < EXPERT_SCORE_THRESHOLD
    assert any("too short" in r for r in reasons)

def test_calculate_score_negative_keywords(error_trajectory):
    score, reasons = calculate_expert_score(error_trajectory)
    # Should be penalized for 'error' keyword
    assert any("Negative keyword" in r for r in reasons)
    assert score < 1.0

def test_review_trajectories_subset_size(valid_trajectory):
    # Create a list of exactly MIN_TRAJECTORIES_TO_REVIEW valid trajectories
    trajectories = [valid_trajectory] * MIN_TRAJECTORIES_TO_REVIEW
    
    reviewed, human_review, avg_score = review_trajectories(trajectories)
    
    assert len(reviewed) == MIN_TRAJECTORIES_TO_REVIEW
    assert len(human_review) == 0
    assert avg_score >= EXPERT_SCORE_THRESHOLD

def test_review_trajectories_mixed_quality(valid_trajectory, error_trajectory):
    # Mix good and bad
    trajectories = [valid_trajectory] * 5 + [error_trajectory] * 5
    
    reviewed, human_review, avg_score = review_trajectories(trajectories)
    
    assert len(reviewed) == 10
    assert len(human_review) == 5
    # Average should be lower due to 50% failures
    assert avg_score < 1.0
    # Depending on penalty weights, it might be below threshold
    # We just assert the logic ran correctly
    assert isinstance(avg_score, float)

def test_review_trajectories_insufficient_count(valid_trajectory):
    with pytest.raises(ValueError) as exc_info:
        review_trajectories([valid_trajectory], count=5)
    
    assert "Insufficient trajectories" in str(exc_info.value)
