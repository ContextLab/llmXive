"""
Unit tests for semantic feature extraction (T024).
"""
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
import os
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from features import extract_semantic_features, EMBEDDING_DIM

class TestSemanticFeatureExtraction:
    def test_empty_input(self):
        """Test handling of empty input list."""
        result = extract_semantic_features([])
        assert result.shape == (0, EMBEDDING_DIM)
        assert result.dtype == np.float32

    def test_invalid_input(self):
        """Test handling of None and invalid texts."""
        texts = [None, "", "   ", "Valid text"]
        with patch('features.SentenceTransformer') as mock_model:
            # Mock the model to return dummy embeddings
            mock_instance = MagicMock()
            mock_instance.encode.return_value = np.random.rand(1, EMBEDDING_DIM).astype(np.float32)
            mock_model.return_value = mock_instance
            
            result = extract_semantic_features(texts)
            assert result.shape == (4, EMBEDDING_DIM)
            assert result.dtype == np.float32
            # First three should be zeros (invalid texts)
            assert np.allclose(result[0], 0)
            assert np.allclose(result[1], 0)
            assert np.allclose(result[2], 0)
            # Last one should be non-zero (valid text)
            assert not np.allclose(result[3], 0)

    def test_single_valid_text(self):
        """Test handling of a single valid text."""
        texts = ["This is a test sentence."]
        with patch('features.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            expected_embedding = np.random.rand(EMBEDDING_DIM).astype(np.float32)
            mock_instance.encode.return_value = expected_embedding.reshape(1, -1)
            mock_model.return_value = mock_instance
            
            result = extract_semantic_features(texts)
            assert result.shape == (1, EMBEDDING_DIM)
            assert result.dtype == np.float32
            assert np.allclose(result[0], expected_embedding)

    def test_multiple_valid_texts(self):
        """Test handling of multiple valid texts."""
        texts = [
            "First sentence.",
            "Second sentence.",
            "Third sentence."
        ]
        with patch('features.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            expected_embeddings = np.random.rand(3, EMBEDDING_DIM).astype(np.float32)
            mock_instance.encode.return_value = expected_embeddings
            mock_model.return_value = mock_instance
            
            result = extract_semantic_features(texts)
            assert result.shape == (3, EMBEDDING_DIM)
            assert result.dtype == np.float32
            assert np.allclose(result, expected_embeddings)

    def test_output_dtype(self):
        """Ensure output is always float32."""
        texts = ["Test"]
        with patch('features.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            # Return float64 to test conversion
            mock_instance.encode.return_value = np.random.rand(1, EMBEDDING_DIM).astype(np.float64)
            mock_model.return_value = mock_instance
            
            result = extract_semantic_features(texts)
            assert result.dtype == np.float32

    def test_embedding_dimensions(self):
        """Ensure embeddings have correct dimensionality (384)."""
        texts = ["Test"]
        with patch('features.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            mock_instance.encode.return_value = np.random.rand(1, 384).astype(np.float32)
            mock_model.return_value = mock_instance
            
            result = extract_semantic_features(texts)
            assert result.shape[1] == 384