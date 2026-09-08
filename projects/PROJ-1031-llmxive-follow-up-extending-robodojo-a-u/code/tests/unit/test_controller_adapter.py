"""
Unit tests for the Controller Adapter module.
"""
import pytest
import sys
import torch
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from controller_adapter import LinearProbe, ValidationFailedError, run_adapter_pipeline

class TestLinearProbe:
    def test_init(self):
        """Test LinearProbe initialization."""
        model = LinearProbe(input_dim=512, output_dim=7)
        assert model.input_dim == 512
        assert model.output_dim == 7
        assert isinstance(model.probe, torch.nn.Sequential)

    def test_forward_shape(self):
        """Test forward pass output shape."""
        model = LinearProbe(input_dim=512, output_dim=7)
        x = torch.randn(10, 512)
        out = model(x)
        assert out.shape == (10, 7)

    def test_forward_single_input(self):
        """Test forward pass with single input (1D)."""
        model = LinearProbe(input_dim=512, output_dim=7)
        x = torch.randn(512)
        out = model(x)
        assert out.shape == (1, 7)

class TestLoadAdapterWeights:
    def test_save_and_load(self):
        """Test saving and loading weights."""
        from controller_adapter import load_adapter_weights
        
        model = LinearProbe(input_dim=10, output_dim=2)
        temp_dir = tempfile.mkdtemp()
        path = os.path.join(temp_dir, "test.pt")
        
        # Save dummy state
        torch.save({'model_state_dict': model.state_dict()}, path)
        
        # Load into new model
        new_model = LinearProbe(input_dim=10, output_dim=2)
        loaded_model = load_adapter_weights(new_model, path)
        
        # Check keys match
        for k, v in model.state_dict().items():
            assert torch.equal(v, loaded_model.state_dict()[k])
        
        os.remove(path)
        os.rmdir(temp_dir)

@pytest.mark.skip(reason="Requires real dataset access and GPU/CPU resources for full training")
def test_run_adapter_pipeline_full():
    """
    Integration test for the full pipeline.
    Skipped by default as it requires real data and significant compute.
    """
    with patch('controller_adapter._prepare_dataset_splits') as mock_split:
        # Mock data
        X_train = torch.randn(100, 512)
        y_train = torch.randn(100, 7)
        X_val = torch.randn(20, 512)
        y_val = torch.randn(20, 7)
        
        train_ds = torch.utils.data.TensorDataset(X_train, y_train)
        val_ds = torch.utils.data.TensorDataset(X_val, y_val)
        
        mock_split.return_value = (train_ds, val_ds)
        
        # Run pipeline
        result = run_adapter_pipeline(epochs=2, val_threshold=0.1) # Low threshold for test
        assert result is True
