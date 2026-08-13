"""
Unit Tests for StaticRoutingSiT (T018)

Tests verify:
1. Model instantiation with valid map.
2. Error handling for missing map.
3. Correct weight retrieval.
4. Integration with load_static_model.
"""

import json
import tempfile
import torch
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys
import os

# Add code to path if not already
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.static_model import StaticRoutingSiT, load_static_model
from src.config import get_routing_cache_path


class MockBaseModel(torch.nn.Module):
    """Mock base model for testing without loading the full SiT-XL."""
    def __init__(self):
        super().__init__()
        self.dummy_param = torch.nn.Parameter(torch.randn(10))

    def forward(self, x):
        return x


@pytest.fixture
def mock_canonical_map():
    """Fixture providing a valid canonical map dictionary."""
    return {
        "0": [0.1, 0.2, 0.3, 0.4, 0.5],
        "1": [0.5, 0.4, 0.3, 0.2, 0.1],
        "2": [0.0, 1.0, 0.0, 0.0, 0.0]
    }


@pytest.fixture
def temp_canonical_map_file(mock_canonical_map):
    """Creates a temporary JSON file with the canonical map."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_canonical_map, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


def test_static_model_instantiation(mock_canonical_map):
    """Test that StaticRoutingSiT can be instantiated with a valid map."""
    base_model = MockBaseModel()
    device = "cpu"

    model = StaticRoutingSiT(base_model, mock_canonical_map, device=device)

    assert model.num_blocks == 3
    assert model.history_dim == 5
    assert model.device == "cpu"

    # Check that weights are converted to tensors
    assert isinstance(model.static_routing_map["0"], torch.Tensor)
    assert model.static_routing_map["0"].dtype == torch.float32


def test_missing_canonical_map():
    """Test that load_static_model raises FileNotFoundError if map is missing."""
    with pytest.raises(FileNotFoundError):
        # Use a non-existent path
        load_static_model(canonical_map_path="/non/existent/path.json")


def test_static_weight_broadcasting(mock_canonical_map):
    """Test that get_static_routing_weight returns the correct tensor."""
    base_model = MockBaseModel()
    model = StaticRoutingSiT(base_model, mock_canonical_map, device="cpu")

    # Test block 0
    w0 = model.get_static_routing_weight(0, 0)
    expected = torch.tensor([0.1, 0.2, 0.3, 0.4, 0.5])
    assert torch.allclose(w0, expected)

    # Test block 1
    w1 = model.get_static_routing_weight(1, 50) # timestep should be ignored
    expected = torch.tensor([0.5, 0.4, 0.3, 0.2, 0.1])
    assert torch.allclose(w1, expected)

    # Test invalid block
    with pytest.raises(ValueError):
        model.get_static_routing_weight(99, 0)


def test_load_static_model_integration(temp_canonical_map_file):
    """Test the full load_static_model function with a temp file."""
    # Mock the load_sit_xl_model to return our MockBaseModel
    with patch('src.static_model.load_sit_xl_model', return_value=MockBaseModel()):
        model, routing_map = load_static_model(canonical_map_path=temp_canonical_map_file)

        assert isinstance(model, StaticRoutingSiT)
        assert routing_map == {
            "0": [0.1, 0.2, 0.3, 0.4, 0.5],
            "1": [0.5, 0.4, 0.3, 0.2, 0.1],
            "2": [0.0, 1.0, 0.0, 0.0, 0.0]
        }
        assert model.num_blocks == 3


def test_invalid_canonical_map_format(temp_canonical_map_file):
    """Test error handling for invalid map formats."""
    # Create a file with invalid content (not a dict)
    with open(temp_canonical_map_file, 'w') as f:
        json.dump(["invalid", "list"], f)

    with patch('src.static_model.load_sit_xl_model', return_value=MockBaseModel()):
        with pytest.raises(ValueError, match="Canonical map must be a dictionary"):
            load_static_model(canonical_map_path=temp_canonical_map_file)

    # Create a file with non-numeric weights
    with open(temp_canonical_map_file, 'w') as f:
        json.dump({"0": ["a", "b"]}, f)

    with patch('src.static_model.load_sit_xl_model', return_value=MockBaseModel()):
        with pytest.raises(ValueError, match="contains non-numeric values"):
            load_static_model(canonical_map_path=temp_canonical_map_file)