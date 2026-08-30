import pytest
from rapidfuzz import fuzz
import sys
import os

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.matching import (
    normalize_title, 
    normalize_author, 
    calculate_title_similarity, 
    calculate_author_similarity, 
    combine_similarity_scores
)

def test_normalize_title_lowercase():
    """Test that titles are normalized to lowercase."""
    title = "The Great Gatsby"
    result = normalize_title(title)
    assert result == "the great gatsby"

def test_normalize_title_remove_punctuation():
    """Test that punctuation is removed from titles."""
    title = "Hello, World!"
    result = normalize_title(title)
    assert result == "hello world"

def test_normalize_author_format():
    """Test author name normalization (removing middle initials, lowercasing)."""
    author = "John Q. Doe"
    result = normalize_author(author)
    assert "john" in result
    assert "doe" in result
    assert "q" not in result # Middle initial removed

def test_calculate_title_similarity_exact_match():
    """Test fuzzy matching for exact matches."""
    title1 = "Statistical Analysis of Pre-prints"
    title2 = "statistical analysis of pre-prints"
    score = calculate_title_similarity(title1, title2)
    assert score == 100.0

def test_calculate_title_similarity_partial_match():
    """Test fuzzy matching for partial matches."""
    title1 = "Analysis of Pre-prints"
    title2 = "Statistical Analysis of Pre-prints"
    score = calculate_title_similarity(title1, title2)
    # Should be high but not 100
    assert 80.0 <= score < 100.0

def test_calculate_author_similarity():
    """Test author similarity calculation."""
    author1 = "John Doe"
    author2 = "John Doe"
    score = calculate_author_similarity(author1, author2)
    assert score == 100.0

def test_combine_similarity_scores_weighted():
    """Test that combined score weights title higher than author."""
    title_score = 100.0
    author_score = 0.0
    combined = combine_similarity_scores(title_score, author_score)
    # Default weights: title=0.7, author=0.3
    expected = (100.0 * 0.7) + (0.0 * 0.3)
    assert combined == expected

    title_score = 0.0
    author_score = 100.0
    combined = combine_similarity_scores(title_score, author_score)
    expected = (0.0 * 0.7) + (100.0 * 0.3)
    assert combined == expected
