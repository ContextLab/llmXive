"""
Unit tests for the matching logic in utils/matching.py
"""
import pytest
from utils.matching import (
    normalize_title,
    normalize_author,
    calculate_title_similarity,
    calculate_author_similarity,
    combine_similarity_scores
)

def test_normalize_title_lowercase():
    """Test that titles are normalized to lowercase."""
    title = "A Study on Statistical Bias"
    normalized = normalize_title(title)
    assert normalized == "a study on statistical bias"

def test_normalize_title_remove_punctuation():
    """Test that punctuation is removed from titles."""
    title = "A Study: Statistical Bias!"
    normalized = normalize_title(title)
    assert ":" not in normalized
    assert "!" not in normalized

def test_normalize_author_remove_initials():
    """Test that author names are normalized."""
    author = "John A. Smith"
    normalized = normalize_author(author)
    # Should remove middle initial and lowercase
    assert "a." not in normalized.lower()
    assert "john" in normalized.lower()
    assert "smith" in normalized.lower()

def test_calculate_title_similarity_high():
    """Test high similarity for identical titles."""
    title1 = "Statistical Bias in Pre-Prints"
    title2 = "Statistical Bias in Pre-Prints"
    score = calculate_title_similarity(title1, title2)
    assert score == 100.0  # Exact match

def test_calculate_title_similarity_low():
    """Test low similarity for very different titles."""
    title1 = "Quantum Mechanics"
    title2 = "Baking Bread"
    score = calculate_title_similarity(title1, title2)
    assert score < 50.0  # Should be low similarity

def test_combine_similarities_weighted():
    """Test that combined score weights title higher than author."""
    title_score = 100.0
    author_score = 50.0
    
    # Default weights: title=0.7, author=0.3
    combined = combine_similarity_scores(title_score, author_score)
    
    expected = (0.7 * title_score) + (0.3 * author_score)
    assert combined == expected
