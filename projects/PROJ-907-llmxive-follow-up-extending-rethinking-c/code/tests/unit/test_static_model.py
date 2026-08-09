"""
Unit tests for static_model.py
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
    """Mock base model for testing."""
    def __init__(self):
        super().__init__()
        # Create mock blocks with routing attributes
        self.blocks = torch.nn.ModuleList()
        for i in range(3):
            block = torch.nn.Module()
            # Add a mock method that would normally compute routing
            block.get_routing_weights = lambda: torch.randn(10) 
            self.blocks.append(block)
    
    def forward(self, x):
        return x

def test_static_model_instantiation():
    """Test that StaticRoutingSiT can be instantiated with a valid map."""
    # Create a temporary canonical map
    with tempfile.TemporaryDirectory() as tmpdir:
        map_path = Path(tmpdir) / "canonical_map.json"
        data = {
            "0": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            "1": [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1],
            "2": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        }
        with open(map_path, 'w') as f:
            json.dump(data, f)
        
        base_model = MockBaseModel()
        model = StaticRoutingSiT(base_model, static_map_path=str(map_path))
        
        assert model.static_map is not None
        assert len(model.static_map) == 3
        assert torch.allclose(model.static_map[0], torch.tensor(data["0"]))

def test_missing_canonical_map():
    """Test that instantiation fails if canonical map is missing."""
    base_model = MockBaseModel()
    with pytest.raises(FileNotFoundError):
        StaticRoutingSiT(base_model, static_map_path="/nonexistent/path/canonical_map.json")

def test_static_weight_broadcasting():
    """Test that static weights are correctly loaded as tensors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        map_path = Path(tmpdir) / "canonical_map.json"
        data = {
            "0": [0.1, 0.2]
        }
        with open(map_path, 'w') as f:
            json.dump(data, f)
        
        base_model = MockBaseModel()
        model = StaticRoutingSiT(base_model, static_map_path=str(map_path))
        
        assert isinstance(model.static_map[0], torch.Tensor)
        assert model.static_map[0].dtype == torch.float32

def test_load_static_model_integration():
    """Integration test for the factory function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        map_path = Path(tmpdir) / "canonical_map.json"
        data = {
            "0": [0.1, 0.2]
        }
        with open(map_path, 'w') as f:
            json.dump(data, f)
        
        # Mock load_sit_xl_model to return our MockBaseModel
        with patch('src.static_model.load_sit_xl_model') as mock_loader:
            mock_loader.return_value = MockBaseModel()
            
            model = load_static_model(static_map_path=str(map_path))
            
            assert isinstance(model, StaticRoutingSiT)
            assert len(model.static_map) == 1