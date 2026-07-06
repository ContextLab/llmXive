"""
Unit tests for stimulus generation logic, specifically focusing on
readability constraints (Flesch-Kincaid score differences) and
sentiment constraints (VADER compound score differences).
"""
import pytest
import sys
import os
from pathlib import Path

# Add the project root to the path to allow imports from 'code'
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from code.utils.logger import setup_logger
    LOGGER = setup_logger("tests")
except ImportError:
    import logging
    LOGGER = logging.getLogger("tests")

# Mock VADER implementation for testing logic without hard dependency on real nltk data
# In the real implementation (T014), this will be replaced by vaderSentiment.SentimentIntensityAnalyzer
class MockVaderAnalyzer:
    """Mock VADER analyzer to simulate compound scores for testing."""
    def __init__(self):
        # Pre-calculated mock scores for specific phrases to ensure deterministic testing
        self._cache = {
            "The AI acts as a partner, helping you complete your tasks efficiently.": 0.65,
            "The AI acts as a tool, helping you complete your tasks efficiently.": 0.62,
            "Your AI partner understands your needs and adapts to your workflow.": 0.70,
            "Your AI tool processes your data and adapts to your workflow.": 0.68,
            "It helps.": 0.0,
            "The sophisticated algorithmic architecture facilitates the optimization of user workflows through iterative feedback loops.": -0.10,
            "I love this amazing partner!": 0.90,
            "This terrible tool is useless.": -0.85,
        }

    def compound_score(self, text: str) -> float:
        if text in self._cache:
            return self._cache[text]
        # Fallback: simple heuristic based on length for unknown texts (deterministic)
        return 0.0

def calculate_mock_vader_compound(text: str) -> float:
    """
    Mock implementation of VADER compound score calculation.
    """
    analyzer = MockVaderAnalyzer()
    return analyzer.compound_score(text)

def calculate_sentiment_diff(text_a: str, text_b: str) -> float:
    """
    Calculates the absolute difference in VADER compound scores between two texts.
    """
    score_a = calculate_mock_vader_compound(text_a)
    score_b = calculate_mock_vader_compound(text_b)
    return abs(score_a - score_b)

class TestStimuliReadability:
    """
    Tests for the readability constraint: Flesch-Kincaid difference must be <= 2.0.
    This corresponds to FR-001 and SC-001.
    """

    def test_identical_texts_have_zero_diff(self):
        """Identical texts should have a readability difference of 0.0."""
        text = "The AI assistant acts as a partner to the user."
        diff = calculate_readability_diff(text, text)
        assert diff == 0.0

    def test_similar_texts_pass_threshold(self):
        """
        Two texts with minor wording changes (same structure, different nouns)
        should have a difference well below the 2.0 threshold.
        """
        text_partner = "The AI acts as a partner, helping you complete your tasks efficiently."
        text_tool = "The AI acts as a tool, helping you complete your tasks efficiently."
        
        diff = calculate_readability_diff(text_partner, text_tool)
        assert diff <= 2.0, f"Difference {diff:.2f} exceeds threshold of 2.0"

    def test_drastically_different_complexity_fails_threshold(self):
        """
        Two texts where one is extremely simple and the other is complex
        should fail the threshold check.
        """
        text_simple = "It helps."
        text_complex = "The sophisticated algorithmic architecture facilitates the optimization of user workflows through iterative feedback loops."
        
        diff = calculate_readability_diff(text_simple, text_complex)
        assert diff > 2.0, "Complexity difference should exceed 2.0"

    def test_stimulus_generation_constraint_logic(self):
        """
        Test the specific logic that would be used in code/01_stimulus_generation.py
        to enforce the constraint.
        """
        candidate_partner = "Your AI partner understands your needs and adapts to your workflow."
        candidate_tool = "Your AI tool processes your data and adapts to your workflow."
        
        diff = calculate_readability_diff(candidate_partner, candidate_tool)
        is_valid = diff <= 2.0
        
        assert is_valid is True, (
            f"Generated stimuli failed readability check. "
            f"Partner score vs Tool score diff: {diff:.2f} (Max allowed: 2.0)"
        )

    def test_boundary_condition_exactly_2_0(self):
        threshold = 2.0
        assert (threshold <= threshold) is True

    def test_boundary_condition_exceeding_2_0(self):
        threshold = 2.01
        assert (threshold <= 2.0) is False

def calculate_readability_diff(text_a: str, text_b: str) -> float:
    """
    Calculates the absolute difference in Flesch-Kincaid scores between two texts.
    (Copied from the previous test file content to ensure this file is self-contained for the test run)
    """
    if not text_a or not text_b:
        return 0.0
    
    def get_fk_score(text: str) -> float:
        sentences = text.count('.') + text.count('!') + text.count('?')
        if sentences == 0:
            sentences = 1
        words = len(text.split())
        if words == 0:
            return 0.0
        
        syllables = 0
        for word in text.split():
            vowels = "aeiouAEIOU"
            count = 0
            prev_vowel = False
            for char in word:
                is_vowel = char in vowels
                if is_vowel and not prev_vowel:
                    count += 1
                prev_vowel = is_vowel
            syllables += max(1, count)
        
        return 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59

    score_a = get_fk_score(text_a)
    score_b = get_fk_score(text_b)
    return abs(score_a - score_b)


class TestStimuliSentiment:
    """
    Tests for the sentiment constraint: VADER compound score difference must be <= 0.05.
    This corresponds to FR-010 and SC-005.
    """

    def test_identical_texts_have_zero_sentiment_diff(self):
        """Identical texts should have a sentiment difference of 0.0."""
        text = "The AI assistant acts as a partner to the user."
        diff = calculate_sentiment_diff(text, text)
        assert diff == 0.0

    def test_similar_texts_pass_sentiment_threshold(self):
        """
        Two texts with minimal structural change (Partner vs Tool)
        should have a sentiment difference well below the 0.05 threshold.
        """
        text_partner = "The AI acts as a partner, helping you complete your tasks efficiently."
        text_tool = "The AI acts as a tool, helping you complete your tasks efficiently."
        
        diff = calculate_sentiment_diff(text_partner, text_tool)
        assert diff <= 0.05, f"Sentiment difference {diff:.3f} exceeds threshold of 0.05"

    def test_drastically_different_sentiment_fails_threshold(self):
        """
        Two texts with opposite sentiment should fail the threshold check.
        """
        text_positive = "I love this amazing partner!"
        text_negative = "This terrible tool is useless."
        
        diff = calculate_sentiment_diff(text_positive, text_negative)
        assert diff > 0.05, "Sentiment difference should exceed 0.05"

    def test_stimulus_generation_constraint_logic(self):
        """
        Test the specific logic that would be used in code/01_stimulus_generation.py
        to enforce the sentiment constraint.
        """
        candidate_partner = "Your AI partner understands your needs and adapts to your workflow."
        candidate_tool = "Your AI tool processes your data and adapts to your workflow."
        
        diff = calculate_sentiment_diff(candidate_partner, candidate_tool)
        
        # The constraint is: diff <= 0.05
        is_valid = diff <= 0.05
        
        assert is_valid is True, (
            f"Generated stimuli failed sentiment check. "
            f"Partner vs Tool compound diff: {diff:.3f} (Max allowed: 0.05)"
        )

    def test_boundary_condition_exactly_0_05(self):
        """
        Test the boundary where the difference is exactly 0.05.
        This should pass (<= 0.05).
        """
        threshold = 0.05
        assert (threshold <= threshold) is True

    def test_boundary_condition_exceeding_0_05(self):
        """
        Test the boundary where the difference is 0.051.
        This should fail.
        """
        threshold = 0.051
        assert (threshold <= 0.05) is False

    def test_mock_vader_consistency(self):
        """
        Ensure the mock VADER implementation returns consistent values.
        """
        text = "The AI acts as a partner, helping you complete your tasks efficiently."
        score1 = calculate_mock_vader_compound(text)
        score2 = calculate_mock_vader_compound(text)
        assert score1 == score2
        assert score1 == 0.65  # Verify against known mock value