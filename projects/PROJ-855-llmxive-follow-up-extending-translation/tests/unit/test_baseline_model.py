"""
Unit tests for the Geometry-Only Baseline model training.

Verifies:
1. The model architecture accepts 6 input features.
2. The model produces a single output logit.
3. The dataset correctly extracts 'initial_object_bounds'.
"""
import pytest
import torch
import numpy as np
import pandas as pd
import tempfile
import os
import sys

# Add code/ to path if running from project root
code_path = os.path.join(os.path.dirname(__file__), '..', 'code')
if code_path not in sys.path:
    sys.path.insert(0, code_path)

from train_baseline import GeometryBaselineModel, GeometryOnlyDataset

class TestGeometryBaselineModel:
    def test_input_shape(self):
        """Test that model accepts input of shape (batch, 6)."""
        model = GeometryBaselineModel(input_dim=6, hidden_dim=32)
        dummy_input = torch.randn(4, 6)
        output = model(dummy_input)
        assert output.shape == (4, 1), f"Expected shape (4, 1), got {output.shape}"

    def test_parameter_count(self):
        """Test that model has a reasonable number of parameters (small)."""
        model = GeometryBaselineModel(input_dim=6, hidden_dim=32)
        total_params = sum(p.numel() for p in model.parameters())
        # 6*32 + 32 + 32*16 + 16 + 16*1 + 1 = 192+32+512+16+16+1 = 769 approx
        assert total_params < 10000, f"Model has too many parameters: {total_params}"

class TestGeometryOnlyDataset:
    def test_extract_bounds(self):
        """Test that dataset correctly extracts initial_object_bounds."""
        # Create dummy data
        data = {
            'initial_object_bounds': [
                [0.0, 0.0, 0.0, 1.0, 1.0, 1.0],
                [0.1, 0.1, 0.1, 1.1, 1.1, 1.1],
                [0.2, 0.2, 0.2, 1.2, 1.2, 1.2]
            ],
            'stability': [1, 0, 1],
            'other_col': ['ignore', 'this', 'col']
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.parquet")
            df.to_parquet(path)
            
            dataset = GeometryOnlyDataset(path)
            
            # Check features shape
            assert dataset.features.shape == (3, 6), f"Expected (3, 6), got {dataset.features.shape}"
            
            # Check specific values
            assert np.allclose(dataset.features[0], [0.0, 0.0, 0.0, 1.0, 1.0, 1.0])
            assert np.allclose(dataset.features[1], [0.1, 0.1, 0.1, 1.1, 1.1, 1.1])
            
            # Check targets
            assert np.array_equal(dataset.targets, [1.0, 0.0, 1.0])

    def test_missing_column(self):
        """Test that dataset raises error if initial_object_bounds is missing."""
        data = {
            'other_col': [1, 2, 3],
            'stability': [1, 0, 1]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.parquet")
            df.to_parquet(path)
            
            with pytest.raises(ValueError, match="initial_object_bounds"):
                GeometryOnlyDataset(path)

    def test_wrong_bounds_length(self):
        """Test that dataset raises error if bounds length is not 6."""
        data = {
            'initial_object_bounds': [
                [0.0, 0.0, 0.0], # Only 3 values
                [1.0, 1.0, 1.0]
            ],
            'stability': [1, 0]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.parquet")
            df.to_parquet(path)
            
            with pytest.raises(ValueError, match="Expected 6 bounds"):
                GeometryOnlyDataset(path)