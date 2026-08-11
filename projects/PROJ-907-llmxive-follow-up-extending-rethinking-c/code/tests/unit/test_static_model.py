"""
Unit tests for the StaticRoutingSiT model.
"""

import json
import tempfile
import torch
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.static_model import StaticRoutingSiT, load_static_model


class MockBaseModel(torch.nn.Module):
    """Mock base model for testing purposes."""
    
    def __init__(self):
        super().__init__()
        self.mock_param = torch.nn.Parameter(torch.randn(10))
    
    def forward(self, *args, **kwargs):
        # Return a dummy output
        return torch.randn(1, 10)


@pytest.fixture
def mock_canonical_map():
    """Create a mock canonical map for testing."""
    return {
        "routing_weights": [
            {"block_id": "0", "weight_vector": [0.1, 0.2, 0.3, 0.4, 0.5]},
            {"block_id": "1", "weight_vector": [0.5, 0.4, 0.3, 0.2, 0.1]},
            {"block_id": "global", "weight_vector": [0.25, 0.25, 0.25, 0.25, 0.25]}
        ]
    }


@pytest.fixture
def temp_canonical_map_file(mock_canonical_map):
    """Create a temporary file with the canonical map."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_canonical_map, f)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    temp_path.unlink()


def test_static_model_instantiation(mock_canonical_map):
    """Test that StaticRoutingSiT can be instantiated with a valid canonical map."""
    base_model = MockBaseModel()
    static_model = StaticRoutingSiT(base_model, mock_canonical_map)
    
    assert static_model is not None
    assert len(static_model.routing_weights) == 3
    assert "0" in static_model.routing_weights
    assert "1" in static_model.routing_weights
    assert "global" in static_model.routing_weights


def test_missing_canonical_map():
    """Test that load_static_model raises an error when the canonical map is missing."""
    with pytest.raises(FileNotFoundError):
        load_static_model(canonical_map_path=Path("/nonexistent/path/canonical_map.json"))


def test_static_weight_broadcasting(mock_canonical_map):
    """Test that static weights are correctly retrieved for different blocks."""
    base_model = MockBaseModel()
    static_model = StaticRoutingSiT(base_model, mock_canonical_map)
    
    # Test block-specific weights
    weight_0 = static_model.get_static_routing_weight(0, 0)
    assert weight_0.shape == (5,)
    assert torch.allclose(weight_0, torch.tensor([0.1, 0.2, 0.3, 0.4, 0.5]))
    
    weight_1 = static_model.get_static_routing_weight(1, 0)
    assert weight_1.shape == (5,)
    assert torch.allclose(weight_1, torch.tensor([0.5, 0.4, 0.3, 0.2, 0.1]))
    
    # Test global fallback
    weight_2 = static_model.get_static_routing_weight(99, 0)  # Non-existent block
    assert weight_2.shape == (5,)
    assert torch.allclose(weight_2, torch.tensor([0.25, 0.25, 0.25, 0.25, 0.25]))


def test_load_static_model_integration(temp_canonical_map_file):
    """Test the full integration of loading a static model from a file."""
    with patch('src.static_model.load_sit_xl_model') as mock_load:
        # Mock the base model loading
        mock_base = MockBaseModel()
        mock_load.return_value = mock_base
        
        # Load the static model
        model, canonical_map = load_static_model(canonical_map_path=temp_canonical_map_file)
        
        # Verify the model is the correct type
        assert isinstance(model, StaticRoutingSiT)
        
        # Verify the canonical map was loaded correctly
        assert canonical_map == {
            "routing_weights": [
                {"block_id": "0", "weight_vector": [0.1, 0.2, 0.3, 0.4, 0.5]},
                {"block_id": "1", "weight_vector": [0.5, 0.4, 0.3, 0.2, 0.1]},
                {"block_id": "global", "weight_vector": [0.25, 0.25, 0.25, 0.25, 0.25]}
            ]
        }
        
        # Verify the model has the correct routing weights
        assert len(model.routing_weights) == 3
        assert "0" in model.routing_weights
        assert "1" in model.routing_weights
        assert "global" in model.routing_weights


def test_invalid_canonical_map_format():
    """Test that load_static_model raises an error for invalid canonical map format."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"invalid": "format"}, f)
        temp_path = Path(f.name)
    
    try:
        with patch('src.static_model.load_sit_xl_model'):
            with pytest.raises(ValueError, match="Invalid canonical map format"):
                load_static_model(canonical_map_path=temp_path)
    finally:
        temp_path.unlink()