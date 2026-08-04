"""
Unit tests for lexicon-based scoring logic (US3).

This module tests the robustness classifier implementation using textstat
and/or the politeness package as an alternative to the primary BERT model.

Tests verify:
1. Lexicon-based scoring produces numeric scores
2. Scores are within expected ranges for known inputs
3. Empty/invalid inputs are handled gracefully
4. Batch processing works correctly
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils.lexicon_scoring import (
    score_with_textstat,
    score_with_politeness_package,
    compute_lexicon_score,
    validate_lexicon_input
)

# Test fixtures
@pytest.fixture
def sample_utterances():
    """Sample utterances for testing lexicon scoring."""
    return [
        "Thank you so much for your help!",
        "I don't think you're being very polite.",
        "Could you please assist me with this?",
        "That's a terrible idea.",
        "I appreciate your time and effort.",
        "You're welcome.",
        "I'm sorry, but I disagree.",
        "Great job! Well done.",
        "",  # Empty string
        "This is a normal sentence with no strong sentiment.",
    ]

@pytest.fixture
def sample_dataframe():
    """Sample DataFrame with utterances for testing."""
    return pd.DataFrame({
        'utterance': [
            "Thank you so much!",
            "Please help me.",
            "You are rude.",
            "I love this!",
            "This is terrible."
        ],
        'dialogue_id': [1, 1, 2, 2, 3],
        'user_id': [101, 101, 102, 102, 103]
    })

class TestValidateLexiconInput:
    """Tests for input validation in lexicon scoring."""
    
    def test_valid_string_input(self):
        """Test that valid string input passes validation."""
        result = validate_lexicon_input("This is a test sentence.")
        assert result is True
    
    def test_empty_string_input(self):
        """Test that empty string input is handled correctly."""
        result = validate_lexicon_input("")
        assert result is False
    
    def test_none_input(self):
        """Test that None input is handled correctly."""
        result = validate_lexicon_input(None)
        assert result is False
    
    def test_whitespace_only_input(self):
        """Test that whitespace-only input is handled correctly."""
        result = validate_lexicon_input("   ")
        assert result is False
    
    def test_numeric_input(self):
        """Test that numeric input is handled correctly."""
        result = validate_lexicon_input(123)
        assert result is False

class TestScoreWithTextstat:
    """Tests for textstat-based scoring."""
    
    def test_politeness_score_positive(self, sample_utterances):
        """Test that polite utterances receive positive scores."""
        polite_utterance = "Thank you so much for your help!"
        score = score_with_textstat(polite_utterance, method='politeness')
        assert isinstance(score, (int, float, np.number))
        # Politeness scores can be negative or positive, but should be numeric
        assert not np.isnan(score)
    
    def test_sentiment_score_range(self, sample_utterances):
        """Test that sentiment scores are within expected ranges."""
        for utterance in sample_utterances:
            if utterance:  # Skip empty strings
                score = score_with_textstat(utterance, method='sentiment')
                assert isinstance(score, (int, float, np.number))
                assert not np.isnan(score)
    
    def test_readability_score_positive(self, sample_utterances):
        """Test that readability scores are non-negative."""
        for utterance in sample_utterances:
            if utterance:
                score = score_with_textstat(utterance, method='flesch_reading_ease')
                assert isinstance(score, (int, float, np.number))
                assert score >= 0  # Flesch Reading Ease is 0-100
                assert not np.isnan(score)
    
    def test_invalid_method(self):
        """Test that invalid method raises appropriate error."""
        with pytest.raises(ValueError):
            score_with_textstat("Test", method='invalid_method')
    
    def test_empty_utterance_handling(self):
        """Test that empty utterances return NaN or None."""
        result = score_with_textstat("", method='politeness')
        # Should handle gracefully, either return NaN or None
        assert result is None or (isinstance(result, float) and np.isnan(result))
    
    @patch('code.utils.lexicon_scoring.textstat')
    def test_exception_handling(self, mock_textstat):
        """Test that exceptions from textstat are handled gracefully."""
        mock_textstat.sentiment_analysis.side_effect = Exception("Test error")
        result = score_with_textstat("Test sentence", method='sentiment')
        assert result is None or (isinstance(result, float) and np.isnan(result))

class TestScoreWithPolitenessPackage:
    """Tests for politeness package-based scoring."""
    
    @patch('code.utils.lexicon_scoring.politeness')
    def test_politeness_detection_positive(self, mock_politeness):
        """Test that polite utterances are detected as polite."""
        mock_politeness.detect.return_value = True
        result = score_with_politeness_package("Thank you for your help!")
        assert result is True
    
    @patch('code.utils.lexicon_scoring.politeness')
    def test_politeness_detection_negative(self, mock_politeness):
        """Test that impolite utterances are detected as impolite."""
        mock_politeness.detect.return_value = False
        result = score_with_politeness_package("You're being rude.")
        assert result is False
    
    @patch('code.utils.lexicon_scoring.politeness')
    def test_empty_utterance_handling(self, mock_politeness):
        """Test that empty utterances are handled gracefully."""
        mock_politeness.detect.side_effect = ValueError("Empty input")
        result = score_with_politeness_package("")
        assert result is False
    
    @patch('code.utils.lexicon_scoring.politeness')
    def test_exception_handling(self, mock_politeness):
        """Test that exceptions are handled gracefully."""
        mock_politeness.detect.side_effect = Exception("Test error")
        result = score_with_politeness_package("Test sentence")
        assert result is False

class TestComputeLexiconScore:
    """Tests for the main lexicon scoring function."""
    
    def test_compute_score_with_valid_input(self, sample_utterances):
        """Test that compute_lexicon_score works with valid input."""
        scores = []
        for utterance in sample_utterances:
            score = compute_lexicon_score(utterance)
            scores.append(score)
        
        # Should have one score per utterance
        assert len(scores) == len(sample_utterances)
        
        # At least some scores should be non-None
        non_none_scores = [s for s in scores if s is not None]
        assert len(non_none_scores) > 0
    
    def test_compute_score_with_dataframe(self, sample_dataframe):
        """Test that compute_lexicon_score works with DataFrame."""
        scores = compute_lexicon_score(sample_dataframe['utterance'].tolist())
        
        assert isinstance(scores, list)
        assert len(scores) == len(sample_dataframe)
        
        # Check that we have numeric scores
        numeric_scores = [s for s in scores if isinstance(s, (int, float, np.number))]
        assert len(numeric_scores) > 0
    
    def test_compute_score_with_mixed_validity(self):
        """Test that compute_lexicon_score handles mixed valid/invalid inputs."""
        mixed_input = [
            "Valid sentence",
            "",
            "Another valid sentence",
            None,
            "   ",
            "Final valid sentence"
        ]
        
        scores = compute_lexicon_score(mixed_input)
        
        # Should have one score per input
        assert len(scores) == len(mixed_input)
        
        # Valid inputs should have scores, invalid should be None/NaN
        valid_indices = [0, 2, 5]
        invalid_indices = [1, 3, 4]
        
        for i in valid_indices:
            assert scores[i] is not None and not (isinstance(scores[i], float) and np.isnan(scores[i]))
        
        for i in invalid_indices:
            assert scores[i] is None or (isinstance(scores[i], float) and np.isnan(scores[i]))

class TestLexiconScoringIntegration:
    """Integration tests for lexicon scoring workflow."""
    
    def test_full_scoring_workflow(self, sample_dataframe):
        """Test the complete scoring workflow."""
        # Score all utterances
        scores = compute_lexicon_score(sample_dataframe['utterance'].tolist())
        
        # Add scores to DataFrame
        sample_dataframe['lexicon_score'] = scores
        
        # Verify DataFrame structure
        assert 'lexicon_score' in sample_dataframe.columns
        assert len(sample_dataframe) == 5
        
        # Check that we have at least some valid scores
        valid_scores = sample_dataframe['lexicon_score'].dropna()
        assert len(valid_scores) > 0
    
    def test_aggregate_scores_by_dialogue(self, sample_dataframe):
        """Test aggregating scores by dialogue."""
        scores = compute_lexicon_score(sample_dataframe['utterance'].tolist())
        sample_dataframe['lexicon_score'] = scores
        
        # Aggregate by dialogue_id
        aggregated = sample_dataframe.groupby('dialogue_id')['lexicon_score'].mean()
        
        # Should have aggregated scores for each dialogue
        assert len(aggregated) == 3  # We have 3 unique dialogue_ids
        assert all(aggregated.notna())
    
    def test_compare_lexicon_with_bert_scores(self):
        """Test that lexicon scores can be compared with BERT scores."""
        # This test verifies the interface compatibility
        lexicon_scores = [0.5, 0.7, 0.3, 0.8, 0.2]
        bert_scores = [0.6, 0.65, 0.35, 0.75, 0.25]
        
        # Should be able to compute correlation
        correlation = np.corrcoef(lexicon_scores, bert_scores)[0, 1]
        assert -1 <= correlation <= 1
        assert not np.isnan(correlation)

class TestEdgeCases:
    """Tests for edge cases in lexicon scoring."""
    
    def test_very_long_utterance(self):
        """Test handling of very long utterances."""
        long_text = "This is a very long sentence. " * 100
        score = score_with_textstat(long_text, method='politeness')
        assert score is not None
        assert not (isinstance(score, float) and np.isnan(score))
    
    def test_special_characters(self):
        """Test handling of special characters."""
        special_text = "Hello! @#$%^&*() How are you? 😊"
        score = score_with_textstat(special_text, method='sentiment')
        assert score is not None
        assert not (isinstance(score, float) and np.isnan(score))
    
    def test_multilingual_text(self):
        """Test handling of multilingual text (should not crash)."""
        multilingual = "Hello. Hola. Bonjour. Ciao."
        score = score_with_textstat(multilingual, method='sentiment')
        # May return NaN for non-English, but should not crash
        assert score is not None or (isinstance(score, float) and np.isnan(score))
    
    def test_numeric_content(self):
        """Test handling of numeric content."""
        numeric_text = "The price is $99.99 and the discount is 20%."
        score = score_with_textstat(numeric_text, method='sentiment')
        assert score is not None
        assert not (isinstance(score, float) and np.isnan(score))

if __name__ == '__main__':
    pytest.main([__file__, '-v'])