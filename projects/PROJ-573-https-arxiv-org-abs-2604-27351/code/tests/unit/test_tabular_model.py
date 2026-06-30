"""
Unit tests for TabularModel (src/models/tabular_model.py).
Tests TabPFN-based tabular model wrapper functionality.
"""
import os
import tempfile
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.models.tabular_model import TabularModel


class TestTabularModel:
    """Test suite for TabularModel class."""

    def test_init_default(self):
        """Test default initialization."""
        model = TabularModel()
        assert model.model is None
        assert model.model_id is None
        assert model.logger is not None

    def test_load_model_mock(self):
        """Test load_model with mocked TabPFN model."""
        mock_model = MagicMock()
        mock_model.device = "cpu"

        with patch('src.models.tabular_model.TabPFNClassifier') as mock_cls:
            mock_cls.return_value = mock_model
            
            model = TabularModel()
            model.load_model("tabpfn-base")
            
            assert model.model is not None
            assert model.model_id == "tabpfn-base"
            mock_cls.assert_called_once()

    def test_predict_binary_classification(self):
        """Test prediction for binary classification."""
        model = TabularModel()
        model.model = MagicMock()
        model.model_id = "test-tabpfn"
        
        # Mock model predict_proba
        model.model.predict_proba.return_value = np.array([
            [0.1, 0.9],
            [0.8, 0.2]
        ])

        # Input: (n_samples, n_features)
        X = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0]
        ])

        result = model.predict(X)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (2, 1)
        assert result[0, 0] == 1  # Class with higher probability
        assert result[1, 0] == 0

    def test_predict_multiclass(self):
        """Test prediction for multi-class classification."""
        model = TabularModel()
        model.model = MagicMock()
        
        # 3-class probabilities
        model.model.predict_proba.return_value = np.array([
            [0.1, 0.1, 0.8],
            [0.7, 0.2, 0.1]
        ])

        X = np.array([
            [1.0, 2.0],
            [3.0, 4.0]
        ])

        result = model.predict(X)
        
        assert result.shape == (2, 1)
        assert result[0, 0] == 2  # Class 2
        assert result[1, 0] == 0   # Class 0

    def test_get_embedding(self):
        """Test embedding generation."""
        model = TabularModel()
        model.model = MagicMock()
        
        # Mock embedding output
        mock_embeddings = np.random.randn(2, 128).astype(np.float32)
        model.model.get_embeddings.return_value = mock_embeddings

        X = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0]
        ])

        embeddings = model.get_embedding(X)
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (2, 128)

    def test_predict_invalid_input(self):
        """Test prediction with invalid input shape."""
        model = TabularModel()
        model.model = MagicMock()
        
        # 1D input instead of 2D
        invalid_input = np.array([1.0, 2.0, 3.0])
        
        with pytest.raises(ValueError, match="Input must be 2D"):
            model.predict(invalid_input)

    def test_predict_empty_array(self):
        """Test prediction with empty input."""
        model = TabularModel()
        model.model = MagicMock()
        
        empty_input = np.array([]).reshape(0, 5)
        
        with pytest.raises(ValueError, match="Input array is empty"):
            model.predict(empty_input)

    def test_cpu_only_mode(self):
        """Test that model forces CPU execution."""
        mock_model = MagicMock()
        
        with patch('src.models.tabular_model.TabPFNClassifier') as mock_cls:
            mock_cls.return_value = mock_model
            
            model = TabularModel()
            model.load_model("cpu-tabpfn")
            
            # Verify model is moved to CPU
            mock_model.to.assert_called_with("cpu")


class TestTabularModelIntegration:
    """Integration tests for TabularModel with actual numpy operations."""

    def test_full_classification_flow(self):
        """Test complete classification flow."""
        model = TabularModel()
        model.model = MagicMock()
        
        # Simulate realistic tabular data
        n_samples = 100
        n_features = 20
        n_classes = 3
        
        X = np.random.randn(n_samples, n_features).astype(np.float32)
        
        # Mock probabilities
        probs = np.random.rand(n_samples, n_classes).astype(np.float32)
        probs = probs / probs.sum(axis=1, keepdims=True)  # Normalize
        model.model.predict_proba.return_value = probs

        predictions = model.predict(X)
        
        assert predictions.shape == (n_samples, 1)
        assert np.all(predictions >= 0)
        assert np.all(predictions < n_classes)

    def test_embedding_consistency(self):
        """Test that embeddings are deterministic for same input."""
        model = TabularModel()
        model.model = MagicMock()
        
        X = np.random.randn(5, 10).astype(np.float32)
        
        mock_embeddings = np.random.randn(5, 128).astype(np.float32)
        model.model.get_embeddings.return_value = mock_embeddings

        emb1 = model.get_embedding(X)
        emb2 = model.get_embedding(X)
        
        np.testing.assert_array_equal(emb1, emb2)

    def test_large_batch_handling(self):
        """Test with large batch size."""
        model = TabularModel()
        model.model = MagicMock()
        
        n_samples = 1000
        n_features = 50
        
        X = np.random.randn(n_samples, n_features).astype(np.float32)
        
        probs = np.random.rand(n_samples, 2).astype(np.float32)
        probs = probs / probs.sum(axis=1, keepdims=True)
        model.model.predict_proba.return_value = probs

        result = model.predict(X)
        
        assert result.shape == (n_samples, 1)