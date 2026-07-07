"""
Unit tests for the Sentiment Analyzer module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.extraction.sentiment_analyzer import calculate_valence_score, extract_sentiment_features


class TestCalculateValenceScore:
    """Tests for the calculate_valence_score function."""

    def test_positive_sentiment(self):
        """Test that positive text yields a positive score."""
        text = "This is amazing and wonderful!"
        score = calculate_valence_score(text)
        assert score > 0.5, f"Expected positive score, got {score}"

    def test_negative_sentiment(self):
        """Test that negative text yields a negative score."""
        text = "This is terrible and awful."
        score = calculate_valence_score(text)
        assert score < -0.5, f"Expected negative score, got {score}"

    def test_neutral_sentiment(self):
        """Test that neutral text yields a score near zero."""
        text = "The box is on the table."
        score = calculate_valence_score(text)
        # Neutral text usually results in a score close to 0
        assert abs(score) < 0.5, f"Expected near-zero score for neutral text, got {score}"

    def test_empty_string(self):
        """Test that empty strings return 0.0."""
        score = calculate_valence_score("")
        assert score == 0.0

    def test_whitespace_only(self):
        """Test that whitespace-only strings return 0.0."""
        score = calculate_valence_score("   ")
        assert score == 0.0

    def test_none_input(self):
        """Test that None input returns 0.0."""
        score = calculate_valence_score(None)
        assert score == 0.0

    def test_mixed_sentiment(self):
        """Test text with mixed sentiment."""
        text = "I love the product but hate the shipping."
        score = calculate_valence_score(text)
        # Should be a valid float between -1 and 1
        assert -1.0 <= score <= 1.0


class TestExtractSentimentFeatures:
    """Tests for the extract_sentiment_features function."""

    def test_basic_extraction(self):
        """Test basic feature extraction on a DataFrame."""
        data = {
            "conversation_id": [1, 2, 3],
            "text": [
                "This is great!",
                "This is terrible.",
                "It is okay."
            ]
        }
        df = pd.DataFrame(data)
        result = extract_sentiment_features(df, text_column="text")

        assert "valence_score" in result.columns
        assert len(result) == 3
        assert result["valence_score"].iloc[0] > 0  # Great -> positive
        assert result["valence_score"].iloc[1] < 0  # Terrible -> negative

    def test_missing_text_column(self):
        """Test that an error is raised if the text column is missing."""
        df = pd.DataFrame({"id": [1], "content": ["Hello"]})
        with pytest.raises(ValueError, match="Column 'text' not found"):
            extract_sentiment_features(df, text_column="text")

    def test_custom_output_column(self):
        """Test specifying a custom output column name."""
        df = pd.DataFrame({"text": ["Happy"]})
        result = extract_sentiment_features(df, output_column="my_sentiment")
        assert "my_sentiment" in result.columns
        assert "valence_score" not in result.columns

    def test_empty_dataframe(self):
        """Test extraction on an empty DataFrame."""
        df = pd.DataFrame(columns=["conversation_id", "text"])
        result = extract_sentiment_features(df)
        assert len(result) == 0
        assert "valence_score" in result.columns

    def test_original_dataframe_unchanged(self):
        """Test that the original DataFrame is not modified."""
        original_data = {"text": ["Happy"]}
        df = pd.DataFrame(original_data)
        _ = extract_sentiment_features(df)
        assert "valence_score" not in df.columns