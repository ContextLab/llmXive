import json
import tempfile
import torch
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add the code directory to the path so we can import src modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.static_model import StaticRoutingSiT, load_static_model

class MockBaseModel(torch.nn.Module):
    """Mock base model for testing StaticRoutingSiT."""
    
    def __init__(self):
        super().__init__()
        self.linear = torch.nn.Linear(10, 10)
        self.static_routing_map = None
        
    def forward(self, x):
        return self.linear(x)
        
    def set_static_routing_map(self, mapping):
        self.static_routing_map = mapping

@pytest.fixture
def mock_canonical_map():
    """Fixture providing a valid mock canonical map."""
    return {
        "block_0": [0.1, 0.2, 0.3],
        "block_1": [0.4, 0.5, 0.6],
        "block_2": [0.7, 0.8, 0.9]
    }

@pytest.fixture
def temp_canonical_map_file(mock_canonical_map):
    """Fixture creating a temporary file with the mock canonical map."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_canonical_map, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_static_model_instantiation(mock_canonical_map):
    """Test that StaticRoutingSiT can be instantiated with a valid map."""
    base_model = MockBaseModel()
    static_model = StaticRoutingSiT(base_model, mock_canonical_map)
    
    assert static_model is not None
    assert static_model.static_map == mock_canonical_map
    # Verify the base model's attribute is set if the method exists
    # In our mock, set_static_routing_map is called during forward, 
    # but we can check the map was stored.
    # Actually, the map is stored in self.static_map of the wrapper.
    assert len(static_model.static_map) == 3

def test_missing_canonical_map():
    """Test that load_static_model raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_static_model("/nonexistent/path/canonical_map.json")

def test_static_weight_broadcasting(mock_canonical_map):
    """Test that static weights are stored correctly and match input."""
    base_model = MockBaseModel()
    static_model = StaticRoutingSiT(base_model, mock_canonical_map)
    
    for block_name, expected_weights in mock_canonical_map.items():
        assert block_name in static_model.static_map
        assert static_model.static_map[block_name] == expected_weights

def test_load_static_model_integration(temp_canonical_map_file):
    """Integration test for load_static_model with a real file."""
    # Mock the load_sit_xl_model to return our MockBaseModel
    with patch('src.static_model.load_sit_xl_model') as mock_loader:
        mock_base = MockBaseModel()
        mock_loader.return_value = mock_base
        
        model, static_map = load_static_model(temp_canonical_map_file)
        
        assert isinstance(model, StaticRoutingSiT)
        assert static_map is not None
        assert len(static_map) == 3
        assert model.base_model is mock_base

def test_invalid_canonical_map_format():
    """Test that load_static_model raises ValueError for invalid map format."""
    invalid_map = {
        "block_0": "not_a_list",
        "block_1": []
    }
    
    base_model = MockBaseModel()
    
    with pytest.raises(ValueError):
        StaticRoutingSiT(base_model, invalid_map)

def test_empty_canonical_map():
    """Test that load_static_model raises ValueError for empty map."""
    empty_map = {}
    base_model = MockBaseModel()
    
    with pytest.raises(ValueError):
        StaticRoutingSiT(base_model, empty_map)