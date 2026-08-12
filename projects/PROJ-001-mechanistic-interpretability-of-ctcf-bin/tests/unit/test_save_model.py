"""
Unit Tests for Model Saving Functionality (T024)

Tests the ensure_output_dir, load_best_model_state, and save_model_weights
functions to ensure they correctly persist model artifacts.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
import torch
import torch.nn as nn

# Add parent directory to path to allow imports from code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.save_model import (
    ensure_output_dir, 
    load_best_model_state, 
    save_model_weights
)

class MockModel(nn.Module):
    """A simple mock model for testing."""
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(10, 2)
    
    def forward(self, x):
        return self.linear(x)

class TestEnsureOutputDir(unittest.TestCase):
    
    def test_creates_nested_directories(self):
        """Test that ensure_output_dir creates parent directories if missing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            deep_path = Path(tmp_dir) / "level1" / "level2" / "output.pth"
            ensure_output_dir(deep_path)
            self.assertTrue(Path(tmp_dir).exists())
            self.assertTrue((Path(tmp_dir) / "level1").exists())
            self.assertTrue((Path(tmp_dir) / "level1" / "level2").exists())
    
    def test_raises_if_file_exists_as_dir(self):
        """Test that a NotADirectoryError is raised if the path exists but is not a dir."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "exists"
            file_path.touch() # Create a file
            
            with self.assertRaises(NotADirectoryError):
                ensure_output_dir(file_path / "subdir")

class TestLoadBestModelState(unittest.TestCase):
    
    def test_loads_from_metrics(self):
        """Test that the function prioritizes 'best_model_state' in metrics."""
        model = MockModel()
        state = model.state_dict()
        metrics = {"best_model_state": state, "val_auc": 0.9}
        
        result = load_best_model_state(model, metrics)
        self.assertEqual(result, state)
    
    def test_fallback_to_model_state(self):
        """Test that it falls back to current model state if not in metrics."""
        model = MockModel()
        metrics = {"val_auc": 0.9}
        
        result = load_best_model_state(model, metrics)
        expected = model.state_dict()
        
        # Check keys match
        self.assertEqual(result.keys(), expected.keys())
        # Check tensor values match
        for key in result:
            self.assertTrue(torch.equal(result[key], expected[key]))

class TestSaveModelWeights(unittest.TestCase):
    
    def test_saves_to_custom_path(self):
        """Test saving model to a specific temporary path."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test_model.pth"
            model = MockModel()
            metrics = {"val_auc": 0.95, "best_model_state": model.state_dict()}
            
            result_path = save_model_weights(model, metrics, output_path)
            
            self.assertTrue(result_path.exists())
            self.assertEqual(result_path, output_path)
            
            # Verify we can load it back
            checkpoint = torch.load(str(result_path), weights_only=False)
            self.assertIn("model_state_dict", checkpoint)
            self.assertIn("metrics", checkpoint)
            self.assertEqual(checkpoint["metrics"]["val_auc"], 0.95)
    
    def test_saves_to_default_path_structure(self):
        """Test that the default path creates the data/models directory structure."""
        # We can't easily test the absolute default path without affecting the real repo,
        # so we mock the PROJECT_ROOT behavior or just ensure the function works
        # with a relative path that mimics the structure.
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Simulate the expected directory structure relative to a fake root
            fake_root = Path(tmp_dir)
            data_models = fake_root / "data" / "models"
            output_path = data_models / "best_ctcf_predictor.pth"
            
            model = MockModel()
            metrics = {"val_auc": 0.88}
            
            # Force the save to our temp location
            result_path = save_model_weights(model, metrics, output_path)
            
            self.assertTrue(result_path.exists())
            self.assertTrue(data_models.exists())

if __name__ == "__main__":
    unittest.main()