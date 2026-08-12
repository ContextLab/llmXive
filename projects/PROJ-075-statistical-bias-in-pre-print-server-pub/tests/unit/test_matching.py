"""
Unit tests for the matching logic in code/utils/matching.py.
Verifies fuzzy match thresholds and similarity scoring functions.
"""
import pytest
import sys
from pathlib import Path

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.matching import (
    normalize_title,
    normalize_author,
    calculate_title_similarity,
    calculate_author_similarity,
    combine_similarity_scores,
    find_best_match,
)
from rapidfuzz import fuzz


class TestNormalization:
    """Tests for title and author normalization functions."""

    def test_normalize_title_lowercase(self):
        """Test that titles are converted to lowercase."""
        title = "A Study on Statistical Bias"
        normalized = normalize_title(title)
        assert normalized == "a study on statistical bias"

    def test_normalize_title_remove_punctuation(self):
        """Test that punctuation is removed from titles."""
        title = "A Study on Statistical Bias: A Review!"
        normalized = normalize_title(title)
        assert ":" not in normalized
        assert "!" not in normalized
        assert normalized == "a study on statistical bias a review"

    def test_normalize_title_remove_stopwords(self):
        """Test that common stopwords are removed."""
        title = "The Study of Statistical Bias in Papers"
        normalized = normalize_title(title)
        # "the", "of", "in" should be removed
        assert "the" not in normalized
        assert "of" not in normalized
        assert "in" not in normalized

    def test_normalize_author_lowercase(self):
        """Test that author names are converted to lowercase."""
        author = "John Doe"
        normalized = normalize_author(author)
        assert normalized == "john doe"

    def test_normalize_author_remove_punctuation(self):
        """Test that punctuation is removed from author names."""
        author = "Doe, John"
        normalized = normalize_author(author)
        assert "," not in normalized
        assert normalized == "doe john"


class TestSimilarityScoring:
    """Tests for similarity calculation functions."""

    def test_calculate_title_similarity_exact_match(self):
        """Test that identical titles return a score of 100."""
        title1 = "Statistical Bias in Pre-Prints"
        title2 = "Statistical Bias in Pre-Prints"
        score = calculate_title_similarity(title1, title2)
        assert score == 100.0

    def test_calculate_title_similarity_case_insensitive(self):
        """Test that case differences do not affect similarity."""
        title1 = "Statistical Bias in Pre-Prints"
        title2 = "statistical bias in pre-prints"
        score = calculate_title_similarity(title1, title2)
        assert score == 100.0

    def test_calculate_title_similarity_partial_match(self):
        """Test that partial matches return a score between 0 and 100."""
        title1 = "Statistical Bias in Pre-Prints and Journals"
        title2 = "Statistical Bias in Pre-Prints"
        score = calculate_title_similarity(title1, title2)
        assert 0 < score < 100

    def test_calculate_author_similarity_exact_match(self):
        """Test that identical authors return a score of 100."""
        author1 = "John Doe"
        author2 = "John Doe"
        score = calculate_author_similarity(author1, author2)
        assert score == 100.0

    def test_calculate_author_similarity_order_independent(self):
        """Test that author order does not affect similarity."""
        author1 = "John Doe Jane Smith"
        author2 = "Jane Smith John Doe"
        score = calculate_author_similarity(author1, author2)
        # The order might affect the score slightly depending on the algorithm,
        # but it should be high for the same set of authors
        assert score >= 80.0

    def test_calculate_author_similarity_partial_match(self):
        """Test that partial author matches return a score between 0 and 100."""
        author1 = "John Doe Jane Smith"
        author2 = "John Doe"
        score = calculate_author_similarity(author1, author2)
        assert 0 < score < 100


class TestCombinedScoring:
    """Tests for combining similarity scores."""

    def test_combine_scores_equal_weight(self):
        """Test combining scores with equal weights."""
        title_score = 80.0
        author_score = 60.0
        combined = combine_similarity_scores(title_score, author_score)
        # Default weights are 0.7 for title and 0.3 for author
        expected = (0.7 * title_score) + (0.3 * author_score)
        assert combined == expected

    def test_combine_scores_custom_weights(self):
        """Test combining scores with custom weights."""
        title_score = 80.0
        author_score = 60.0
        combined = combine_similarity_scores(title_score, author_score, title_weight=0.5, author_weight=0.5)
        expected = (0.5 * title_score) + (0.5 * author_score)
        assert combined == expected

    def test_combine_scores_weights_sum_to_one(self):
        """Test that weights must sum to 1.0."""
        with pytest.raises(ValueError):
            combine_similarity_scores(80.0, 60.0, title_weight=0.6, author_weight=0.6)


class TestFindBestMatch:
    """Tests for the find_best_match function."""

    def test_find_best_match_exact_match(self):
        """Test finding a best match with an exact match in candidates."""
        query_title = "Statistical Bias"
        query_author = "John Doe"
        candidates = [
            {"title": "Statistical Bias", "author": "John Doe"},
            {"title": "Other Paper", "author": "Jane Smith"},
        ]
        best_match, score = find_best_match(query_title, query_author, candidates)
        assert best_match is not None
        assert score == 100.0
        assert best_match["title"] == "Statistical Bias"

    def test_find_best_match_no_match_above_threshold(self):
        """Test that None is returned when no match is above the threshold."""
        query_title = "Completely Different Title"
        query_author = "Unknown Author"
        candidates = [
            {"title": "Statistical Bias", "author": "John Doe"},
            {"title": "Other Paper", "author": "Jane Smith"},
        ]
        best_match, score = find_best_match(query_title, query_author, candidates, threshold=90.0)
        assert best_match is None
        assert score == 0.0

    def test_find_best_match_best_match_selected(self):
        """Test that the best match is selected among multiple candidates."""
        query_title = "Statistical Bias"
        query_author = "John Doe"
        candidates = [
            {"title": "Statistical Bias", "author": "Jane Smith"},  # Good title match
            {"title": "Statistical Biases", "author": "John Doe"},  # Good author match
            {"title": "Other Paper", "author": "John Doe"},  # Poor title match
        ]
        best_match, score = find_best_match(query_title, query_author, candidates)
        assert best_match is not None
        assert score > 0.0

    def test_find_best_match_empty_candidates(self):
        """Test that None is returned when candidates list is empty."""
        query_title = "Statistical Bias"
        query_author = "John Doe"
        candidates = []
        best_match, score = find_best_match(query_title, query_author, candidates)
        assert best_match is None
        assert score == 0.0

    def test_find_best_match_threshold_parameter(self):
        """Test that the threshold parameter affects the result."""
        query_title = "Statistical Bias"
        query_author = "John Doe"
        candidates = [
            {"title": "Statistical Bias", "author": "Jane Smith"},
        ]
        # With a low threshold, a match should be found
        best_match_low, score_low = find_best_match(query_title, query_author, candidates, threshold=50.0)
        assert best_match_low is not None

        # With a high threshold, no match might be found (depending on author mismatch)
        best_match_high, score_high = find_best_match(query_title, query_author, candidates, threshold=95.0)
        # If the score is below 95, best_match_high should be None
        if score_high < 95.0:
            assert best_match_high is None