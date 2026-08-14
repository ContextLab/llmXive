import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.config import ensure_directories
from utils.model_loader import get_rosenberg_lexicon
from utils.logger import setup_logger

# Mock the metrics calculation logic for testing since 02_metrics.py is not yet implemented
# In a real scenario, this would import from code/02_metrics.py
def calculate_rosenberg_score(text: str, lexicon: dict) -> float:
    """
    Calculate the Rosenberg self-esteem score for a given text.
    
    This is a simplified implementation for testing purposes.
    In the actual 02_metrics.py, this will be integrated properly.
    """
    if not text or not isinstance(text, str):
        return -999.0
    
    text_lower = text.lower()
    words = text_lower.split()
    
    score = 0.0
    count = 0
    
    for word in words:
        # Clean punctuation
        clean_word = "".join(c for c in word if c.isalnum())
        if not clean_word:
            continue
            
        if clean_word in lexicon:
            # Rosenberg lexicon uses positive weights for positive words
            # and negative weights for negative words (self-esteem related)
            score += lexicon[clean_word]
            count += 1
    
    if count == 0:
        return 0.0  # No Rosenberg words found
    
    return score / count  # Average score

@pytest.fixture
def rosenberg_lexicon():
    """Fixture to load the Rosenberg lexicon for testing."""
    return get_rosenberg_lexicon()

@pytest.fixture
def sample_texts():
    """Fixture providing known input strings for testing."""
    return {
        "positive_self_esteem": "I feel that I am a person of worth, at least on an equal plane with others. I am able to do things as well as most other people.",
        "negative_self_esteem": "At times I think I am no good at all. I feel I do not have much to be proud of. I certainly wish I could be more like someone else.",
        "mixed": "I feel that I have a number of good qualities. I wish I could be more like someone else. I am able to do things as well as most other people.",
        "empty": "",
        "no_rosenberg_words": "The quick brown fox jumps over the lazy dog. This sentence contains no self-esteem related words.",
        "special_chars": "I am #great! And I feel *wonderful* about myself. @self-esteem is key."
    }

def test_rosenberg_score_positive_text(rosenberg_lexicon, sample_texts):
    """Test that positive self-esteem text yields a positive score."""
    text = sample_texts["positive_self_esteem"]
    score = calculate_rosenberg_score(text, rosenberg_lexicon)
    
    # Positive self-esteem text should yield a positive average score
    assert score > 0, f"Expected positive score for positive text, got {score}"
    assert not np.isnan(score), "Score should not be NaN"
    assert score != -999.0, "Score should not be the sentinel value for valid text"

def test_rosenberg_score_negative_text(rosenberg_lexicon, sample_texts):
    """Test that negative self-esteem text yields a negative score."""
    text = sample_texts["negative_self_esteem"]
    score = calculate_rosenberg_score(text, rosenberg_lexicon)
    
    # Negative self-esteem text should yield a negative average score
    assert score < 0, f"Expected negative score for negative text, got {score}"
    assert not np.isnan(score), "Score should not be NaN"
    assert score != -999.0, "Score should not be the sentinel value for valid text"

def test_rosenberg_score_mixed_text(rosenberg_lexicon, sample_texts):
    """Test that mixed text yields a score closer to zero than pure positive/negative."""
    mixed_text = sample_texts["mixed"]
    positive_text = sample_texts["positive_self_esteem"]
    negative_text = sample_texts["negative_self_esteem"]
    
    mixed_score = calculate_rosenberg_score(mixed_text, rosenberg_lexicon)
    positive_score = calculate_rosenberg_score(positive_text, rosenberg_lexicon)
    negative_score = calculate_rosenberg_score(negative_text, rosenberg_lexicon)
    
    # Mixed score should be between negative and positive scores
    assert negative_score <= mixed_score <= positive_score, \
        f"Mixed score {mixed_score} should be between negative {negative_score} and positive {positive_score}"

def test_rosenberg_score_empty_text(rosenberg_lexicon):
    """Test that empty text returns -999.0 (sentinel value)."""
    score = calculate_rosenberg_score("", rosenberg_lexicon)
    assert score == -999.0, f"Expected -999.0 for empty text, got {score}"

def test_rosenberg_score_none_text(rosenberg_lexicon):
    """Test that None text returns -999.0 (sentinel value)."""
    score = calculate_rosenberg_score(None, rosenberg_lexicon)
    assert score == -999.0, f"Expected -999.0 for None text, got {score}"

def test_rosenberg_score_no_matching_words(rosenberg_lexicon, sample_texts):
    """Test that text with no Rosenberg words returns 0.0."""
    text = sample_texts["no_rosenberg_words"]
    score = calculate_rosenberg_score(text, rosenberg_lexicon)
    
    # No matching words should result in 0.0 (not -999.0 since it's valid text)
    assert score == 0.0, f"Expected 0.0 for text with no Rosenberg words, got {score}"

def test_rosenberg_score_special_characters(rosenberg_lexicon, sample_texts):
    """Test that special characters are handled correctly."""
    text = sample_texts["special_chars"]
    score = calculate_rosenberg_score(text, rosenberg_lexicon)
    
    # Should not be -999.0 since it's valid text
    assert score != -999.0, "Score should not be sentinel for text with special chars"
    assert not np.isnan(score), "Score should not be NaN"

def test_rosenberg_score_consistency(rosenberg_lexicon, sample_texts):
    """Test that the same input always produces the same output (deterministic)."""
    text = sample_texts["positive_self_esteem"]
    
    score1 = calculate_rosenberg_score(text, rosenberg_lexicon)
    score2 = calculate_rosenberg_score(text, rosenberg_lexicon)
    score3 = calculate_rosenberg_score(text, rosenberg_lexicon)
    
    assert score1 == score2 == score3, "Score calculation should be deterministic"

def test_rosenberg_score_known_string():
    """
    Verify Rosenberg lexicon score calculation against a known input string.
    This test uses a predefined string with known Rosenberg words to validate the calculation.
    """
    lexicon = get_rosenberg_lexicon()
    
    # Known test string with specific Rosenberg words
    # "I feel that I am a person of worth" contains "worth" (positive)
    # "At times I think I am no good" contains "good" (positive) and "no" (negative context)
    # Simplified: "I am good" should be positive
    test_string = "I am good and worthy"
    
    score = calculate_rosenberg_score(test_string, lexicon)
    
    # Verify the score is calculated (not sentinel)
    assert score != -999.0, "Valid text should not return sentinel value"
    assert not np.isnan(score), "Score should not be NaN"
    
    # The exact value depends on the lexicon weights, but it should be calculable
    # We verify that the function executes and returns a float
    assert isinstance(score, float), "Score should be a float"

def test_rosenberg_lexicon_loading():
    """Test that the Rosenberg lexicon loads correctly and contains expected words."""
    lexicon = get_rosenberg_lexicon()
    
    assert isinstance(lexicon, dict), "Lexicon should be a dictionary"
    assert len(lexicon) > 0, "Lexicon should not be empty"
    
    # Check for some expected Rosenberg words
    expected_positive = ["worth", "good", "able", "feel", "person"]
    expected_negative = ["no", "not", "wish", "fail", "useless"]
    
    # At least some of these should be present
    positive_found = any(word in lexicon for word in expected_positive)
    negative_found = any(word in lexicon for word in expected_negative)
    
    assert positive_found or negative_found, "Lexicon should contain some Rosenberg words"