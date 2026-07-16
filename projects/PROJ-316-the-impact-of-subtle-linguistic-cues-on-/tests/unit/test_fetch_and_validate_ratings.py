import pytest
import pandas as pd
import json
import tempfile
from pathlib import Path
import os
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fetch_and_validate_ratings import (
    simulate_rater_score,
    calculate_reliability,
    execute_annotation
)

def test_simulate_rater_score_deterministic():
    """Test that the score is deterministic for the same text and rater."""
    text = "This is a test conversation."
    rater = "rater_001"
    seed = 42
    
    score1 = simulate_rater_score(text, rater, seed)
    score2 = simulate_rater_score(text, rater, seed)
    
    assert score1 == score2
    assert 1 <= score1 <= 5

def test_simulate_rater_score_different_raters():
    """Test that different raters might give different scores."""
    text = "This is a test conversation with perhaps some hedges."
    seed = 42
    
    score1 = simulate_rater_score(text, "rater_001", seed)
    score2 = simulate_rater_score(text, "rater_002", seed)
    
    # They might be the same by chance, but usually different due to bias logic
    # We just check they are valid scores
    assert 1 <= score1 <= 5
    assert 1 <= score2 <= 5

def test_execute_annotation():
    """Test the annotation execution function."""
    data = [
        {"conversation_id": "1", "text_content": "Hello world"},
        {"conversation_id": "2", "text_content": "Perhaps this is a test."}
    ]
    df = pd.DataFrame(data)
    
    ratings = execute_annotation(df, ["rater_001", "rater_002"], seed=42)
    
    assert len(ratings) == 4 # 2 conversations * 2 raters
    assert "conversation_id" in ratings.columns
    assert "authenticity_score" in ratings.columns
    assert "rater_id" in ratings.columns
    assert "timestamp" in ratings.columns

def test_calculate_reliability():
    """Test Cohen's Kappa calculation."""
    # Create a DataFrame with perfect agreement
    data = [
        {"conversation_id": "1", "authenticity_score": 3, "rater_id": "rater_001"},
        {"conversation_id": "1", "authenticity_score": 3, "rater_id": "rater_002"},
        {"conversation_id": "2", "authenticity_score": 4, "rater_id": "rater_001"},
        {"conversation_id": "2", "authenticity_score": 4, "rater_id": "rater_002"},
    ]
    df = pd.DataFrame(data)
    
    metrics = calculate_reliability(df)
    
    assert metrics["kappa_value"] == 1.0
    assert metrics["status"] == "passed"
    assert metrics["sample_size"] == 2

def test_calculate_reliability_low_agreement():
    """Test Cohen's Kappa calculation with low agreement."""
    # Create a DataFrame with low agreement
    data = [
        {"conversation_id": "1", "authenticity_score": 1, "rater_id": "rater_001"},
        {"conversation_id": "1", "authenticity_score": 5, "rater_id": "rater_002"},
        {"conversation_id": "2", "authenticity_score": 5, "rater_id": "rater_001"},
        {"conversation_id": "2", "authenticity_score": 1, "rater_id": "rater_002"},
    ]
    df = pd.DataFrame(data)
    
    metrics = calculate_reliability(df)
    
    # Kappa should be low or negative
    assert metrics["kappa_value"] < 0.6
    assert metrics["status"] == "failed"

def test_calculate_reliability_missing_rater():
    """Test that calculate_reliability raises error for missing rater."""
    data = [
        {"conversation_id": "1", "authenticity_score": 3, "rater_id": "rater_001"},
        {"conversation_id": "1", "authenticity_score": 3, "rater_id": "rater_001"}, # Only one rater
    ]
    df = pd.DataFrame(data)
    
    with pytest.raises(ValueError, match="Cohen's Kappa requires exactly 2 raters"):
        calculate_reliability(df)