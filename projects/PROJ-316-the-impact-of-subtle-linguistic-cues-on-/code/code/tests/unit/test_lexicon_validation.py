"""
Unit tests for T001d: lexicon validation.
"""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from code.lexicon_validation import (
    find_lexicon_matches,
    sample_turns,
    validate_lexicon_precision,
    tokenize_text,
    HEDGE_LEXICON
)

@pytest.fixture
def sample_conversations():
    """Create sample conversations data."""
    data = [
        {"conversation_id": "1", "text_content": "I think this is a good idea."},
        {"conversation_id": "2", "text_content": "This is definitely the best option."},
        {"conversation_id": "3", "text_content": "Perhaps we should consider other alternatives."},
        {"conversation_id": "4", "text_content": "I believe this will work."},
        {"conversation_id": "5", "text_content": "The results are clear and unambiguous."}
    ]
    return pd.DataFrame(data)

@pytest.fixture
def sample_ratings():
    """Create sample ratings data."""
    data = [
        {"conversation_id": "1", "authenticity_score": 4.0, "rater_id": "r1"},
        {"conversation_id": "2", "authenticity_score": 3.5, "rater_id": "r1"},
        {"conversation_id": "3", "authenticity_score": 4.5, "rater_id": "r2"},
        {"conversation_id": "4", "authenticity_score": 4.0, "rater_id": "r2"},
        {"conversation_id": "5", "authenticity_score": 3.0, "rater_id": "r1"}
    ]
    return pd.DataFrame(data)

def test_tokenize_text():
    """Test basic tokenization."""
    text = "I think this is a test"
    tokens = tokenize_text(text)
    assert tokens == ["i", "think", "this", "is", "a", "test"]

def test_find_lexicon_matches_basic():
    """Test finding hedge matches in text."""
    text = "I think this might be possible"
    matches = find_lexicon_matches(text)
    # Should find "I think" and "might" and "possibly" (if in lexicon)
    assert "I think" in matches or "think" in matches
    assert "might" in matches

def test_find_lexicon_matches_no_hedges():
    """Test text with no hedges."""
    text = "This is definitely the answer"
    matches = find_lexicon_matches(text)
    # "definitely" is not in our lexicon
    assert len(matches) == 0

def test_sample_turns(sample_conversations, sample_ratings):
    """Test sampling turns."""
    sample = sample_turns(sample_conversations, sample_ratings, sample_size=3, seed=42)
    assert len(sample) == 3
    assert "conversation_id" in sample.columns
    assert "text_content" in sample.columns

def test_sample_turns_smaller_than_requested(sample_conversations, sample_ratings):
    """Test sampling when requested size is larger than available."""
    sample = sample_turns(sample_conversations, sample_ratings, sample_size=10, seed=42)
    assert len(sample) == 5  # All available

def test_validate_lexicon_precision(sample_conversations, sample_ratings):
    """Test precision calculation."""
    sample_df = sample_turns(sample_conversations, sample_ratings, sample_size=3, seed=42)
    precision, results = validate_lexicon_precision(sample_df)
    
    assert 0.0 <= precision <= 1.0
    assert "total_lexicon_matches" in results
    assert "total_human_matches" in results
    assert "precision" in results
    assert results["precision"] == precision

def test_hedge_lexicon_content():
    """Test that the hedge lexicon contains expected words."""
    expected_hedges = {"perhaps", "maybe", "possibly", "I think", "I believe"}
    for hedge in expected_hedges:
        assert hedge in HEDGE_LEXICON, f"Expected hedge '{hedge}' not in lexicon"
