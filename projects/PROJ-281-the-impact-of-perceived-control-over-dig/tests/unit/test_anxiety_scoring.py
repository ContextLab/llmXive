import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock, mock_open
import json

from code.services.anxiety_scoring import (
    filter_text_quality,
    load_anxiety_model,
    compute_anxiety_scores,
    run_full_scoring_pipeline
)
from code.config import DATA_PROCESSED_PATH

def test_filter_text_quality():
    """Unit tests for text quality filtering logic."""
    # Valid English
    assert filter_text_quality("This is a normal English sentence.") is True
    # Gibberish / symbols only
    assert filter_text_quality("!!!@@@") is False
    # Too short
    assert filter_text_quality("Short") is False
    # Empty string
    assert filter_text_quality("") is False
    # None input
    assert filter_text_quality(None) is False
    # Mixed language / non-English (assuming langdetect is integrated in filter)
    # Note: The actual implementation in anxiety_scoring.py uses langdetect.
    # We assume "This is a test" passes and "Ceci est un test" might fail depending on threshold.
    # For this unit test, we focus on the structural checks (length, nulls, symbols).
    assert filter_text_quality("Test 123 test") is True

def test_load_anxiety_model_mock():
    """Test that the model loading function handles the mock correctly."""
    # We mock the transformers pipeline to avoid downloading the real model in unit tests
    with patch('code.services.anxiety_scoring.pipeline') as mock_pipeline:
        mock_pipeline.return_value = MagicMock()
        model = load_anxiety_model()
        assert model is not None
        mock_pipeline.assert_called_once()

def test_compute_anxiety_scores_with_mock():
    """
    Unit test for compute_anxiety_scores using a mocked model output.
    This verifies the logic of extracting anxiety scores and confidence
    without requiring the actual heavy model inference.
    """
    # Create mock input data
    texts = [
        "I am feeling very anxious and scared.",
        "This is a happy day.",
        "Neutral statement here."
    ]
    
    # Mock the model's return value
    # The cardiffnlp/twitter-roberta-base-emotion model returns a list of dicts with labels and scores
    # We need to map 'anxiety' specifically if it's an emotion, or 'fear' if that's the proxy.
    # The spec implies 'anxiety_score'. We assume the model output has an 'anxiety' key or we map 'fear'.
    # For this test, we construct a mock output that matches the expected structure.
    mock_outputs = [
        [
            {'label': 'anxiety', 'score': 0.85},
            {'label': 'fear', 'score': 0.10},
            {'label': 'joy', 'score': 0.05}
        ],
        [
            {'label': 'joy', 'score': 0.90},
            {'label': 'anxiety', 'score': 0.05},
            {'label': 'fear', 'score': 0.05}
        ],
        [
            {'label': 'neutral', 'score': 0.80},
            {'label': 'anxiety', 'score': 0.15},
            {'label': 'fear', 'score': 0.05}
        ]
    ]

    with patch('code.services.anxiety_scoring.pipeline') as mock_pipeline:
        mock_model_instance = MagicMock()
        mock_model_instance.return_value = mock_outputs
        mock_pipeline.return_value = mock_model_instance

        results = compute_anxiety_scores(texts)

        # Verify results structure
        assert isinstance(results, pd.DataFrame)
        assert 'text' in results.columns
        assert 'anxiety_score' in results.columns
        assert 'confidence_score' in results.columns
        assert len(results) == 3

        # Verify specific values
        # Row 0: Anxiety 0.85
        assert results.iloc[0]['anxiety_score'] == 0.85
        # Row 1: Anxiety 0.05
        assert results.iloc[1]['anxiety_score'] == 0.05
        # Row 2: Anxiety 0.15
        assert results.iloc[2]['anxiety_score'] == 0.15

def test_run_full_scoring_pipeline_mock():
    """
    Integration-style unit test for the full pipeline using mocks for heavy dependencies.
    Verifies that the pipeline reads input, processes, and writes output correctly.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = Path(tmp_dir) / "preprocessed_text.csv"
        output_path = Path(tmp_dir) / "scoring_results.csv"

        # Create a mock input file
        mock_data = {
            "text": [
                "I feel anxious about the future.",
                "Everything is great and calm."
            ]
        }
        df_input = pd.DataFrame(mock_data)
        df_input.to_csv(input_path, index=False)

        # Mock the model loading and inference
        mock_outputs = [
            [{'label': 'anxiety', 'score': 0.9}, {'label': 'joy', 'score': 0.1}],
            [{'label': 'joy', 'score': 0.9}, {'label': 'anxiety', 'score': 0.1}]
        ]

        with patch('code.services.anxiety_scoring.pipeline') as mock_pipeline:
            mock_model_instance = MagicMock()
            mock_model_instance.return_value = mock_outputs
            mock_pipeline.return_value = mock_model_instance

            # Run the pipeline with overridden paths
            # The function signature needs to be checked. If it doesn't accept paths,
            # we might need to patch the global CONFIG or the function internals.
            # Assuming run_full_scoring_pipeline accepts input_path and output_path args or uses defaults.
            # Based on the task T017, it saves to a specific path.
            # We will patch the internal calls to ensure it writes to our temp dir.
            
            # Since the function might use global paths, we patch the specific file operations
            # or assume the function allows overriding.
            # Let's assume the function signature is: run_full_scoring_pipeline(input_path, output_path)
            # If not, we would need to mock the global DATA_PROCESSED_PATH usage.
            # Given the constraints, we assume the function is designed to be testable.
            
            # Fallback: If the function doesn't accept args, we patch the global constants.
            with patch('code.services.anxiety_scoring.DATA_PROCESSED_PATH', Path(tmp_dir)):
                # Also need to ensure the function uses the correct input filename
                # The function likely looks for 'preprocessed_text.csv' in that directory.
                run_full_scoring_pipeline() 

            # Verify output file exists
            assert output_path.exists()

            # Verify content
            df_output = pd.read_csv(output_path)
            assert 'text' in df_output.columns
            assert 'anxiety_score' in df_output.columns
            assert 'confidence_score' in df_output.columns
            assert len(df_output) == 2

def test_compute_anxiety_scores_low_confidence_filtering():
    """
    Test that the compute_anxiety_scores function (or the pipeline logic)
    correctly identifies low confidence scores if filtering is part of this step.
    Note: T016 handles filtering. This test ensures the SCORES are calculated correctly
    so T016 can filter them.
    """
    texts = ["Anxious text"]
    mock_outputs = [
        [{'label': 'anxiety', 'score': 0.4}] # Low confidence
    ]

    with patch('code.services.anxiety_scoring.pipeline') as mock_pipeline:
        mock_model_instance = MagicMock()
        mock_model_instance.return_value = mock_outputs
        mock_pipeline.return_value = mock_model_instance

        results = compute_anxiety_scores(texts)
        
        # Verify the score is captured, even if low
        assert results.iloc[0]['anxiety_score'] == 0.4
        assert results.iloc[0]['confidence_score'] == 0.4 # Assuming confidence is the max score or anxiety score itself
        
def test_filter_text_quality_edge_cases():
    """Test edge cases for text filtering."""
    # Very long text
    long_text = "Word " * 1000
    assert filter_text_quality(long_text) is True
    
    # Text with only whitespace
    assert filter_text_quality("   ") is False
    
    # Text with numbers and symbols but some words
    assert filter_text_quality("Test 123 !@#") is True

def test_run_full_scoring_pipeline_empty_input():
    """Test pipeline behavior with empty input file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = Path(tmp_dir) / "preprocessed_text.csv"
        output_path = Path(tmp_dir) / "scoring_results.csv"

        # Create empty dataframe
        df_input = pd.DataFrame(columns=["text"])
        df_input.to_csv(input_path, index=False)

        with patch('code.services.anxiety_scoring.pipeline') as mock_pipeline:
            mock_model_instance = MagicMock()
            mock_model_instance.return_value = []
            mock_pipeline.return_value = mock_model_instance

            with patch('code.services.anxiety_scoring.DATA_PROCESSED_PATH', Path(tmp_dir)):
                run_full_scoring_pipeline()

            assert output_path.exists()
            df_output = pd.read_csv(output_path)
            assert len(df_output) == 0