"""
Unit tests for the Static Model implementation (T018).
"""

import pytest
import json
import tempfile
import torch
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.static_model import StaticRoutingSiT, load_static_model


class MockBaseModel(torch.nn.Module):
    """Mock base model for testing."""
    def __init__(self):
        super().__init__()
        self.routing_mode = None
        self.static_weights = None

    def set_routing_mode(self, mode, weights):
        self.routing_mode = mode
        self.static_weights = weights

    def forward(self, x):
        return x

    def generate(self, x, num_inference_steps=10):
        return x


def test_static_model_instantiation():
    """Test that the StaticRoutingSiT can be instantiated with a mock model."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock canonical map
        canonical_map = [
            {"block_id": 0, "weight_vector": [0.1, 0.2, 0.3]},
            {"block_id": 1, "weight_vector": [0.4, 0.5, 0.6]}
        ]
        map_path = Path(tmpdir) / "canonical_map.json"
        with open(map_path, 'w') as f:
            json.dump(canonical_map, f)

        mock_base = MockBaseModel()
        static_model = StaticRoutingSiT(mock_base, str(map_path))

        assert static_model.is_static_mode is True
        assert len(static_model.static_weights) == 2
        assert 0 in static_model.static_weights
        assert 1 in static_model.static_weights
        assert torch.allclose(static_model.static_weights[0], torch.tensor([0.1, 0.2, 0.3]))
        assert mock_base.routing_mode == 'static'


def test_missing_canonical_map():
    """Test that an error is raised if the canonical map is missing."""
    mock_base = MockBaseModel()
    with pytest.raises(FileNotFoundError):
        StaticRoutingSiT(mock_base, "/nonexistent/path/map.json")


def test_static_weight_broadcasting():
    """Test that static weights are correctly expanded for timesteps."""
    with tempfile.TemporaryDirectory() as tmpdir:
        canonical_map = [
            {"block_id": 0, "weight_vector": [1.0, 2.0]}
        ]
        map_path = Path(tmpdir) / "canonical_map.json"
        with open(map_path, 'w') as f:
            json.dump(canonical_map, f)

        mock_base = MockBaseModel()
        static_model = StaticRoutingSiT(mock_base, str(map_path))

        # Get weights for 5 timesteps
        weights = static_model._get_static_routing_weights(0, 5)
        
        # Expected shape: [5, 2]
        assert weights.shape == (5, 2)
        # Check values are broadcasted correctly
        assert torch.allclose(weights[0], torch.tensor([1.0, 2.0]))
        assert torch.allclose(weights[4], torch.tensor([1.0, 2.0]))


def test_load_static_model_integration():
    """Test the load_static_model function with mocking."""
    with patch('src.static_model.load_sit_xl_model') as mock_loader, \
         patch('src.static_model.get_routing_cache_path') as mock_get_path, \
         tempfile.TemporaryDirectory() as tmpdir:
        
        # Setup mocks
        mock_base = MockBaseModel()
        mock_loader.return_value = mock_base
        mock_get_path.return_value = tmpdir
        
        # Create canonical map in temp dir
        canonical_map = [{"block_id": 0, "weight_vector": [0.5]}]
        map_path = Path(tmpdir) / "canonical_map.json"
        with open(map_path, 'w') as f:
            json.dump(canonical_map, f)

        # Load the model
        model = load_static_model(model_name="test-model", device="cpu")

        assert isinstance(model, StaticRoutingSiT)
        assert model.is_static_mode is True
        mock_loader.assert_called_once_with("test-model", device="cpu", precision="float32")
