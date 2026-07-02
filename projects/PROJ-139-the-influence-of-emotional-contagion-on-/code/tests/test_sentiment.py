"""
Unit tests for sentiment analysis module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd

from code.data.sentiment import (
    apply_vader_sentiment,
    compute_sentiment_scores,
    run_sentiment_analysis,
    load_extracted_data
)


class TestVaderSentiment:
    """Tests for VADER sentiment scoring logic."""

    def test_positive_text(self):
        """Test that clearly positive text yields a positive compound score."""
        text = "This is the best thing ever! I love it so much."
        scores = apply_vader_sentiment(text)
        assert scores['compound'] > 0.5
        assert scores['pos'] > scores['neg']

    def test_negative_text(self):
        """Test that clearly negative text yields a negative compound score."""
        text = "This is terrible. I hate it. Worst experience ever."
        scores = apply_vader_sentiment(text)
        assert scores['compound'] < -0.5
        assert scores['neg'] > scores['pos']

    def test_neutral_text(self):
        """Test that neutral text yields a near-zero compound score."""
        text = "The sky is blue. The grass is green."
        scores = apply_vader_sentiment(text)
        # VADER might not be perfectly zero, but should be close
        assert -0.2 < scores['compound'] < 0.2

    def test_empty_text(self):
        """Test that empty text returns neutral scores."""
        text = ""
        scores = apply_vader_sentiment(text)
        assert scores['compound'] == 0.0
        assert scores['neu'] == 1.0

    def test_none_text(self):
        """Test that None text returns neutral scores."""
        text = None
        scores = apply_vader_sentiment(text)
        assert scores['compound'] == 0.0
        assert scores['neu'] == 1.0


class TestSentimentIntegration:
    """Integration tests for the sentiment pipeline."""

    @pytest.fixture
    def sample_data(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            'id': [1, 2, 3, 4],
            'text': [
                "I am very happy today!",
                "This is absolutely awful.",
                "It is okay, nothing special.",
                "Mixed feelings: happy but also sad."
            ]
        })

    @pytest.fixture
    def temp_input_file(self, sample_data):
        """Create a temporary JSON file with sample data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            sample_data.to_json(f.name, orient='records')
            return f.name

    @pytest.fixture
    def temp_output_file(self):
        """Create a temporary file path for output."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        return path

    def test_compute_sentiment_scores(self, sample_data):
        """Test that compute_sentiment_scores adds the correct columns."""
        result_df = compute_sentiment_scores(sample_data)

        expected_cols = ['vader_neg', 'vader_neu', 'vader_pos', 'vader_compound']
        for col in expected_cols:
            assert col in result_df.columns

        # Check that the first row (positive) has a positive compound score
        assert result_df.iloc[0]['vader_compound'] > 0
        # Check that the second row (negative) has a negative compound score
        assert result_df.iloc[1]['vader_compound'] < 0

    def test_run_sentiment_analysis(self, temp_input_file, temp_output_file):
        """Test the full run_sentiment_analysis pipeline."""
        # Run the analysis
        output_path = run_sentiment_analysis(temp_input_file, temp_output_file)

        # Verify output file exists
        assert os.path.exists(output_path)

        # Load and verify content
        result_df = pd.read_json(output_path)

        # Check columns
        assert 'vader_compound' in result_df.columns
        assert len(result_df) == 4

        # Cleanup
        os.remove(temp_input_file)
        os.remove(output_path)

    def test_run_sentiment_analysis_jsonl(self, sample_data):
        """Test saving to JSONL format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as in_f:
            sample_data.to_json(in_f.name, orient='records', lines=True)
            input_path = in_f.name

        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as out_f:
            output_path = out_f.name

        try:
            run_sentiment_analysis(input_path, output_path)

            assert os.path.exists(output_path)
            result_df = pd.read_json(output_path, lines=True)
            assert 'vader_compound' in result_df.columns
        finally:
            os.remove(input_path)
            os.remove(output_path)

    def test_missing_input_file(self):
        """Test that run_sentiment_analysis raises error for missing input."""
        with pytest.raises(FileNotFoundError):
            run_sentiment_analysis("non_existent_file.json", "output.json")

    def test_missing_text_column(self):
        """Test that run_sentiment_analysis raises error if 'text' column is missing."""
        df = pd.DataFrame({'id': [1, 2]})
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            df.to_json(f.name, orient='records')
            input_path = f.name

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            with pytest.raises(ValueError):
                run_sentiment_analysis(input_path, output_path)
        finally:
            os.remove(input_path)
            os.remove(output_path)