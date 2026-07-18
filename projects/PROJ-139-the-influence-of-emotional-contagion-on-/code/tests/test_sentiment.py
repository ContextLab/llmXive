"""
Tests for the Sentiment Analysis Module (T013).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from code.data.sentiment import apply_vader_sentiment, load_valid_dataset


class TestVaderSentiment:
    """Tests for VADER sentiment application."""

    def test_apply_vader_sentiment_positive(self):
        """Test that positive text yields a positive score."""
        data = {
            'text': ["I love this! It is amazing and wonderful.", "Great job everyone!"]
        }
        df = pd.DataFrame(data)
        result = apply_vader_sentiment(df)

        assert 'sentiment_score' in result.columns
        # VADER compound scores for very positive text should be > 0.5
        assert all(result['sentiment_score'] > 0.5), f"Expected positive scores, got {result['sentiment_score']}"

    def test_apply_vader_sentiment_negative(self):
        """Test that negative text yields a negative score."""
        data = {
            'text': ["This is terrible and awful.", "I hate this so much."]
        }
        df = pd.DataFrame(data)
        result = apply_vader_sentiment(df)

        assert 'sentiment_score' in result.columns
        # VADER compound scores for very negative text should be < -0.5
        assert all(result['sentiment_score'] < -0.5), f"Expected negative scores, got {result['sentiment_score']}"

    def test_apply_vader_sentiment_neutral(self):
        """Test that neutral text yields a score near zero."""
        data = {
            'text': ["The sky is blue.", "It is Tuesday."]
        }
        df = pd.DataFrame(data)
        result = apply_vader_sentiment(df)

        assert 'sentiment_score' in result.columns
        # Neutral text should be close to 0, typically within [-0.1, 0.1]
        # We allow a slightly wider range for robustness
        assert all(abs(score) < 0.2 for score in result['sentiment_score']), f"Expected near-zero scores, got {result['sentiment_score']}"

    def test_apply_vader_sentiment_bounds(self):
        """Test that scores are strictly bounded within [-1.0, 1.0]."""
        data = {
            'text': [
                "This is the best thing ever!!!",
                "This is the worst thing ever!!!",
                "Mixed feelings but mostly good."
            ]
        }
        df = pd.DataFrame(data)
        result = apply_vader_sentiment(df)

        assert result['sentiment_score'].min() >= -1.0
        assert result['sentiment_score'].max() <= 1.0

    def test_apply_vader_sentiment_empty_text(self):
        """Test handling of empty or NaN text."""
        data = {
            'text': ["", "   ", None, np.nan]
        }
        df = pd.DataFrame(data)
        result = apply_vader_sentiment(df)

        assert 'sentiment_score' in result.columns
        # Empty text should result in 0.0
        assert all(result['sentiment_score'] == 0.0)


class TestSentimentIntegration:
    """Integration tests for the sentiment pipeline."""

    def test_load_valid_dataset_success(self):
        """Test loading a valid CSV file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            csv_path = tmp_path / "valid_threads.csv"

            # Create a mock valid dataset
            data = {
                'thread_id': [1, 2],
                'post_id': [10, 20],
                'text': ["Test text 1", "Test text 2"],
                'timestamp': [100, 200],
                'author_id': [1, 2],
                'sentiment_score': [0.1, 0.2]
            }
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False)

            loaded_df = load_valid_dataset(csv_path)
            assert len(loaded_df) == 2
            assert 'text' in loaded_df.columns

    def test_load_valid_dataset_missing_file(self):
        """Test loading a non-existent file raises error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            csv_path = tmp_path / "non_existent.csv"

            with pytest.raises(FileNotFoundError):
                load_valid_dataset(csv_path)

    def test_load_valid_dataset_missing_columns(self):
        """Test loading a file with missing required columns raises error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            csv_path = tmp_path / "invalid.csv"

            # Missing 'text' column
            data = {
                'thread_id': [1],
                'post_id': [10]
            }
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False)

            with pytest.raises(ValueError):
                load_valid_dataset(csv_path)
