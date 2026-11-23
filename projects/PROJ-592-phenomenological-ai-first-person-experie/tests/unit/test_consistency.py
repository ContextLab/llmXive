"""Unit tests for consistency analysis module."""
import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import tempfile
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from code.analysis.consistency import (
    ConsistencyError,
    load_nli_model,
    split_into_sentences,
    compute_pairwise_contradictions,
    compute_consistency_metric,
    run_consistency_analysis
)


class TestSplitIntoSentences:
    """Tests for sentence splitting logic."""

    def test_simple_sentences(self):
        """Test splitting on standard punctuation."""
        text = "This is a sentence. This is another! Is this a question?"
        sentences = split_into_sentences(text)
        assert len(sentences) == 3
        assert sentences[0] == "This is a sentence."
        assert sentences[1] == "This is another!"
        assert sentences[2] == "Is this a question?"

    def test_short_fragments_filtered(self):
        """Test that very short fragments are filtered out."""
        text = "Hi. OK. This is a real sentence. X."
        sentences = split_into_sentences(text)
        # "Hi." and "OK." and "X." might be filtered if < 10 chars
        # "This is a real sentence." should remain
        assert len(sentences) >= 1
        assert "This is a real sentence." in sentences

    def test_empty_string(self):
        """Test empty input."""
        assert split_into_sentences("") == []

    def test_no_punctuation(self):
        """Test text without sentence-ending punctuation."""
        text = "This is one long fragment without punctuation"
        sentences = split_into_sentences(text)
        # Should return one sentence if > 10 chars
        assert len(sentences) == 1


class TestComputePairwiseContradictions:
    """Tests for pairwise contradiction counting."""

    def test_no_sentences(self):
        """Test with empty or single sentence."""
        mock_model = Mock()
        assert compute_pairwise_contradictions(mock_model, []) == 0
        assert compute_pairwise_contradictions(mock_model, ["One sentence"]) == 0

    def test_contradiction_detection(self):
        """Test that low scores are counted as contradictions."""
        mock_model = Mock()
        # Mock predict to return scores: [0.9, 0.4, 0.8] -> 1 contradiction
        mock_model.predict.return_value = [0.9, 0.4, 0.8]

        sentences = ["Sentence A", "Sentence B", "Sentence C"]
        result = compute_pairwise_contradictions(mock_model, sentences)

        # Pairs: (A,B), (A,C), (B,C) -> 3 pairs
        # Scores: 0.9 (no), 0.4 (yes), 0.8 (no) -> 1 contradiction
        assert result == 1
        mock_model.predict.assert_called_once()

    def test_no_contradictions(self):
        """Test with all high scores."""
        mock_model = Mock()
        mock_model.predict.return_value = [0.9, 0.9, 0.9]

        sentences = ["A", "B", "C"]
        result = compute_pairwise_contradictions(mock_model, sentences)
        assert result == 0

    def test_exception_handling(self):
        """Test that exceptions return 0 and log warning."""
        mock_model = Mock()
        mock_model.predict.side_effect = Exception("Model error")

        sentences = ["A", "B", "C"]
        # Should not raise, return 0
        result = compute_pairwise_contradictions(mock_model, sentences)
        assert result == 0


class TestComputeConsistencyMetric:
    """Tests for the main consistency metric."""

    def test_short_text(self):
        """Test text with fewer than 2 sentences."""
        mock_model = Mock()
        # Single sentence
        assert compute_consistency_metric("Just one sentence.", mock_model) == 1.0
        # Empty
        assert compute_consistency_metric("", mock_model) == 1.0

    def test_perfect_consistency(self):
        """Test text with no contradictions."""
        mock_model = Mock()
        mock_model.predict.return_value = [0.9, 0.9]

        text = "Sentence one. Sentence two. Sentence three."
        score = compute_consistency_metric(text, mock_model)
        # 3 sentences -> 3 pairs. All scores > 0.5 -> 0 contradictions.
        # Score = 1 - (0/3) = 1.0
        assert score == 1.0

    def test_half_contradictions(self):
        """Test text with 50% contradictions."""
        mock_model = Mock()
        # 3 sentences -> 3 pairs. 1.5 contradictions? No, integer count.
        # Let's say 2 out of 3 are contradictions.
        mock_model.predict.return_value = [0.3, 0.3, 0.9]

        text = "A. B. C."
        score = compute_consistency_metric(text, mock_model)
        # 2 contradictions / 3 pairs = 0.666...
        # Score = 1 - 0.666 = 0.333...
        expected = 1.0 - (2.0 / 3.0)
        assert abs(score - expected) < 0.001


class TestRunConsistencyAnalysis:
    """Integration tests for the full analysis pipeline."""

    def test_missing_input_file(self):
        """Test behavior when input file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.csv")
            config = {
                "input_path": "/nonexistent/path.csv",
                "output_path": output_path,
                "model_name": "cross-encoder/stsb-distilroberta-base"
            }

            # Should not raise, should create empty file
            run_consistency_analysis(config)
            assert os.path.exists(output_path)
            df = pd.read_csv(output_path)
            assert df.empty

    def test_full_pipeline_with_mock_model(self):
        """Test full pipeline with mocked model to avoid real download."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.csv")
            output_path = os.path.join(tmpdir, "output.csv")

            # Create input data
            data = {
                "id": ["1", "2"],
                "text": ["Sentence one. Sentence two.", "A. B. C. D."]
            }
            pd.DataFrame(data).to_csv(input_path, index=False)

            # Mock the model loading and prediction
            with patch('code.analysis.consistency.load_nli_model') as mock_load:
                mock_model = Mock()
                mock_model.predict.return_value = [0.9, 0.9, 0.9, 0.9, 0.9, 0.9] # All consistent
                mock_load.return_value = mock_model

                config = {
                    "input_path": input_path,
                    "output_path": output_path,
                    "model_name": "test-model"
                }

                run_consistency_analysis(config)

                assert os.path.exists(output_path)
                df = pd.read_csv(output_path)
                assert len(df) == 2
                assert "id" in df.columns
                assert "consistency_score" in df.columns
                # All scores should be 1.0 (no contradictions)
                assert all(df["consistency_score"] == 1.0)

    def test_run_consistency_analysis_with_config_dict(self):
        """Test that run_consistency_analysis accepts a config dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.csv")
            output_path = os.path.join(tmpdir, "output.csv")

            data = {"id": ["1"], "text": ["Just one sentence."]}
            pd.DataFrame(data).to_csv(input_path, index=False)

            with patch('code.analysis.consistency.load_nli_model') as mock_load:
                mock_model = Mock()
                mock_load.return_value = mock_model

                config = {
                    "input_path": input_path,
                    "output_path": output_path,
                    "model_name": "test"
                }
                # Should not raise
                run_consistency_analysis(config)
                assert os.path.exists(output_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])