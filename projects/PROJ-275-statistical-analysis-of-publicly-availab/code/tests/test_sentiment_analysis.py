"""
Unit tests for sentiment_analysis.py
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sentiment_analysis import compute_vader_sentiment, process_reviews_for_timeseries

class TestComputeVaderSentiment:
    """Tests for the compute_vader_sentiment function."""

    def test_positive_text(self):
        """Test that positive text yields a positive compound score."""
        text = "This movie was absolutely fantastic and I loved it!"
        scores = compute_vader_sentiment(text)
        assert scores['compound'] > 0
        assert scores['pos'] > scores['neg']

    def test_negative_text(self):
        """Test that negative text yields a negative compound score."""
        text = "This movie was terrible and a waste of time."
        scores = compute_vader_sentiment(text)
        assert scores['compound'] < 0
        assert scores['neg'] > scores['pos']

    def test_neutral_text(self):
        """Test that neutral text yields a near-zero compound score."""
        text = "The movie was okay, nothing special."
        scores = compute_vader_sentiment(text)
        # VADER might not be perfectly 0, but should be close
        assert abs(scores['compound']) < 0.5

    def test_empty_text(self):
        """Test that empty text returns neutral scores."""
        text = ""
        scores = compute_vader_sentiment(text)
        assert scores['compound'] == 0.0
        assert scores['neu'] == 1.0

    def test_none_text(self):
        """Test that None text returns neutral scores."""
        text = None
        scores = compute_vader_sentiment(text)
        assert scores['compound'] == 0.0
        assert scores['neu'] == 1.0

class TestProcessReviewsForTimeseries:
    """Tests for the process_reviews_for_timeseries function."""

    def test_basic_processing(self):
        """Test basic sentiment processing on a DataFrame."""
        df = pd.DataFrame({
            'review_text': [
                "I loved this movie!",
                "Terrible experience.",
                "It was okay."
            ],
            'movie_id': [1, 2, 3]
        })
        result = process_reviews_for_timeseries(df, text_column='review_text', score_column='sentiment_score')
        
        assert 'sentiment_score' in result.columns
        assert len(result) == 3
        assert result['sentiment_score'].iloc[0] > 0  # Positive
        assert result['sentiment_score'].iloc[1] < 0  # Negative
        assert abs(result['sentiment_score'].iloc[2]) < 0.5  # Neutral

    def test_empty_dataframe(self):
        """Test processing an empty DataFrame."""
        df = pd.DataFrame(columns=['review_text', 'movie_id'])
        result = process_reviews_for_timeseries(df)
        assert result.empty

    def test_mixed_valid_invalid(self):
        """Test processing with some invalid text entries."""
        df = pd.DataFrame({
            'review_text': [
                "Great movie!",
                None,
                "",
                "Bad movie."
            ],
            'movie_id': [1, 2, 3, 4]
        })
        result = process_reviews_for_timeseries(df)
        
        assert result['sentiment_score'].iloc[0] > 0
        assert result['sentiment_score'].iloc[1] == 0.0  # None -> 0
        assert result['sentiment_score'].iloc[2] == 0.0  # Empty -> 0
        assert result['sentiment_score'].iloc[3] < 0