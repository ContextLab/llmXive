"""
Unit tests for the Controller Adapter module.

Tests the LinearProbe architecture, weight loading, and pipeline execution.
"""
import pytest
import torch
import os
import tempfile
from unittest.mock import MagicMock, patch
import sys
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from controller_adapter import LinearProbe, run_adapter_pipeline, load_adapter_weights
from vision_encoder import VisionEncoder

class TestLinearProbe:
    """Tests for the LinearProbe model architecture."""
    
    def test_initialization(self):
        """Test that LinearProbe initializes correctly."""
        model = LinearProbe(input_dim=512, output_dim=6)
        
        assert isinstance(model, torch.nn.Module)
        assert model.linear.in_features == 512
        assert model.linear.out_features == 6
        assert hasattr(model, 'relu')
        
    def test_forward_pass(self):
        """Test forward pass produces correct output shape."""
        model = LinearProbe(input_dim=512, output_dim=6)
        model.eval()
        
        # Create dummy input
        x = torch.randn(32, 512)
        
        with torch.no_grad():
            output = model(x)
        
        assert output.shape == (32, 6)
        
    def test_gradient_flow(self):
        """Test that gradients flow through the model."""
        model = LinearProbe(input_dim=512, output_dim=6)
        model.train()
        
        x = torch.randn(32, 512)
        y = torch.randn(32, 6)
        
        output = model(x)
        loss = torch.nn.functional.mse_loss(output, y)
        loss.backward()
        
        # Check that gradients exist
        assert model.linear.weight.grad is not None
        assert model.linear.bias.grad is not None

class TestLoadAdapterWeights:
    """Tests for weight loading functionality."""
    
    def test_load_weights(self):
        """Test loading weights from a checkpoint."""
        model = LinearProbe(input_dim=512, output_dim=6)
        
        with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as tmp:
            checkpoint = {
                'model_state_dict': model.state_dict(),
                'epoch': 10
            }
            torch.save(checkpoint, tmp.name)
            
            loaded = load_adapter_weights(model, tmp.name)
            assert 'model_state_dict' in loaded
            assert loaded['epoch'] == 10
            
            os.unlink(tmp.name)
    
    def test_load_nonexistent_file(self):
        """Test that loading from a non-existent file raises an error."""
        model = LinearProbe()
        
        with pytest.raises(FileNotFoundError):
            load_adapter_weights(model, "/nonexistent/path.pt")

class TestAdapterPipeline:
    """Tests for the full adapter training pipeline."""
    
    @patch('controller_adapter.stream_robodojo_tasks')
    @patch('controller_adapter.VisionEncoder')
    def test_run_pipeline_with_mock_data(self, mock_encoder_class, mock_stream):
        """Test pipeline execution with mocked data."""
        # Setup mocks
        mock_encoder = MagicMock(spec=VisionEncoder)
        mock_encoder.encode.return_value = torch.randn(32, 512)
        mock_encoder_class.return_value = mock_encoder
        
        # Create mock tasks
        mock_task = {
            'id': 'task_001',
            'frames': [np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)],
            'target_actions': np.random.randn(6).astype(np.float32)
        }
        mock_stream.return_value = [mock_task] * 18  # 18 tasks
        
        # Run pipeline with minimal epochs
        adapter, metrics = run_adapter_pipeline(
            num_epochs=2,
            train_split=0.5,
            validation_split=0.25
        )
        
        # Verify outputs
        assert isinstance(adapter, LinearProbe)
        assert 'train_losses' in metrics
        assert 'val_losses' in metrics
        assert len(metrics['train_losses']) == 2
        
    @patch('controller_adapter.stream_robodojo_tasks')
    @patch('controller_adapter.VisionEncoder')
    def test_pipeline_saves_weights(self, mock_encoder_class, mock_stream):
        """Test that pipeline saves weights to the correct location."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_weights.pt")
            
            # Setup mocks
            mock_encoder = MagicMock(spec=VisionEncoder)
            mock_encoder.encode.return_value = torch.randn(32, 512)
            mock_encoder_class.return_value = mock_encoder
            
            mock_task = {
                'id': 'task_001',
                'frames': [np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)],
                'target_actions': np.random.randn(6).astype(np.float32)
            }
            mock_stream.return_value = [mock_task] * 18
            
            # Run pipeline
            adapter, metrics = run_adapter_pipeline(
                output_path=output_path,
                num_epochs=2
            )
            
            # Verify file was created
            assert os.path.exists(output_path)
            
            # Verify file is loadable
            checkpoint = torch.load(output_path, map_location='cpu', weights_only=True)
            assert 'model_state_dict' in checkpoint
            assert 'training_metrics' in checkpoint

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
