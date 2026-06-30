"""
Unit tests for TimeSeriesModel (src/models/timeseries_model.py).
Tests model loading, prediction, and embedding generation with mocked dependencies.
"""
import os
import tempfile
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the class being tested
from src.models.timeseries_model import TimeSeriesModel


class TestTimeSeriesModel:
    """Test suite for TimeSeriesModel class."""

    def test_init_default(self):
        """Test default initialization."""
        model = TimeSeriesModel()
        assert model.model is None
        assert model.model_id is None
        assert model.logger is not None

    def test_load_model_mock(self):
        """Test load_model with mocked HuggingFace model."""
        mock_model = MagicMock()
        mock_model.config = MagicMock()
        mock_model.config.hidden_size = 128

        with patch('src.models.timeseries_model.AutoModel') as mock_auto:
            mock_auto.from_pretrained.return_value = mock_model
            
            model = TimeSeriesModel()
            model.load_model("dummy-ts-model")
            
            assert model.model is not None
            assert model.model_id == "dummy-ts-model"
            mock_auto.from_pretrained.assert_called_once_with(
                "dummy-ts-model", 
                trust_remote_code=True
            )

    def test_predict_input_shape(self):
        """Test prediction with correct input shape."""
        model = TimeSeriesModel()
        model.model = MagicMock()
        model.model_id = "test-model"
        
        # Mock model output
        mock_output = MagicMock()
        mock_output.last_hidden_state = np.random.randn(1, 10, 128).astype(np.float32)
        model.model.return_value = mock_output
        model.model.config.hidden_size = 128

        # Input: (batch=1, time_steps=10, features=5)
        input_data = np.random.randn(1, 10, 5).astype(np.float32)
        
        result = model.predict(input_data)
        
        assert isinstance(result, np.ndarray)
        assert result.shape[0] == 1  # Batch size
        assert result.shape[1] == 1  # Single prediction per sample
        
    def test_predict_invalid_shape(self):
        """Test prediction with invalid input shape raises error."""
        model = TimeSeriesModel()
        model.model = MagicMock()
        
        # Input with wrong number of dimensions
        invalid_input = np.random.randn(10, 5).astype(np.float32)
        
        with pytest.raises(ValueError, match="Input must be 3D"):
            model.predict(invalid_input)

    def test_get_embedding_shape(self):
        """Test embedding generation returns correct shape."""
        model = TimeSeriesModel()
        model.model = MagicMock()
        
        # Mock model output
        mock_output = MagicMock()
        mock_output.last_hidden_state = np.random.randn(1, 10, 128).astype(np.float32)
        model.model.return_value = mock_output
        model.model.config.hidden_size = 128

        input_data = np.random.randn(1, 10, 5).astype(np.float32)
        
        embedding = model.get_embedding(input_data)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape[0] == 1
        assert embedding.shape[1] == 128  # Hidden size

    def test_predict_batch(self):
        """Test batch prediction."""
        model = TimeSeriesModel()
        model.model = MagicMock()
        
        mock_output = MagicMock()
        mock_output.last_hidden_state = np.random.randn(4, 10, 128).astype(np.float32)
        model.model.return_value = mock_output
        model.model.config.hidden_size = 128

        # Batch of 4 samples
        input_data = np.random.randn(4, 10, 5).astype(np.float32)
        
        result = model.predict(input_data)
        
        assert result.shape[0] == 4

    def test_cpu_only_mode(self):
        """Test that model forces CPU execution."""
        mock_model = MagicMock()
        mock_model.config = MagicMock()
        mock_model.config.hidden_size = 128

        with patch('src.models.timeseries_model.AutoModel') as mock_auto:
            with patch('torch.cuda.is_available', return_value=True):
                mock_auto.from_pretrained.return_value = mock_model
                
                model = TimeSeriesModel()
                model.load_model("cpu-only-model")
                
                # Verify model is moved to CPU
                mock_model.to.assert_called_with("cpu")


class TestTimeSeriesModelIntegration:
    """Integration tests for TimeSeriesModel with actual numpy operations."""

    def test_prediction_flow(self):
        """Test complete prediction flow with mock model."""
        model = TimeSeriesModel()
        model.model = MagicMock()
        
        # Simulate realistic time-series input
        batch_size = 2
        time_steps = 50
        features = 10
        
        input_data = np.random.randn(batch_size, time_steps, features).astype(np.float32)
        
        # Mock output
        hidden_size = 256
        mock_output = MagicMock()
        mock_output.last_hidden_state = np.random.randn(
            batch_size, time_steps, hidden_size
        ).astype(np.float32)
        model.model.return_value = mock_output
        model.model.config.hidden_size = hidden_size

        # Test prediction
        predictions = model.predict(input_data)
        assert predictions.shape == (batch_size, 1)
        
        # Test embedding
        embeddings = model.get_embedding(input_data)
        assert embeddings.shape == (batch_size, hidden_size)

    def test_edge_case_single_timestep(self):
        """Test with single timestep input."""
        model = TimeSeriesModel()
        model.model = MagicMock()
        
        input_data = np.random.randn(1, 1, 5).astype(np.float32)
        
        mock_output = MagicMock()
        mock_output.last_hidden_state = np.random.randn(1, 1, 128).astype(np.float32)
        model.model.return_value = mock_output
        model.model.config.hidden_size = 128

        result = model.predict(input_data)
        assert result.shape == (1, 1)

    def test_edge_case_many_features(self):
        """Test with many feature dimensions."""
        model = TimeSeriesModel()
        model.model = MagicMock()
        
        input_data = np.random.randn(1, 20, 100).astype(np.float32)
        
        mock_output = MagicMock()
        mock_output.last_hidden_state = np.random.randn(1, 20, 128).astype(np.float32)
        model.model.return_value = mock_output
        model.model.config.hidden_size = 128

        result = model.predict(input_data)
        assert result.shape == (1, 1)