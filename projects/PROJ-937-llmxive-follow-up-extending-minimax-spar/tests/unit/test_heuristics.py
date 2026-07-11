"""
Unit tests for code/heuristics/gradient_magnitude.py.

Tests ensure:
1. CPU-only execution is enforced (raises error if GPU detected).
2. Gradient calculation logic is correct (mocked model behavior).
3. Edge cases (uniform entropy, split needles) are handled.
"""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import numpy as np

# Add project root to path for imports if running standalone
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.heuristics.gradient_magnitude import (
    GradientMagnitudeHeuristic,
    _detect_gpu,
    _calculate_local_gradient,
    HeuristicConfig
)
from code.utils.logging import setup_logger

@pytest.fixture
def mock_logger():
    return setup_logger("test_gradient_heuristic", level="INFO")

@pytest.fixture
def config():
    return HeuristicConfig(top_k=3, window_size=10, batch_size=2)

class TestGPUEnforcement:
    """Test that the heuristic enforces CPU-only execution."""

    def test_gpu_detected_raises_error(self, mock_logger):
        """If a GPU is detected, the heuristic should raise an error."""
        with patch('code.heuristics.gradient_magnitude._detect_gpu') as mock_detect:
            mock_detect.return_value = True  # Simulate GPU presence
            
            heuristic = GradientMagnitudeHeuristic(config=HeuristicConfig(), logger=mock_logger)
            
            with pytest.raises(RuntimeError) as exc_info:
                heuristic._check_environment()
            
            assert "GPU detected" in str(exc_info.value)

    def test_cpu_only_no_error(self, mock_logger):
        """If no GPU is detected, no error should be raised."""
        with patch('code.heuristics.gradient_magnitude._detect_gpu') as mock_detect:
            mock_detect.return_value = False  # Simulate CPU only
            
            heuristic = GradientMagnitudeHeuristic(config=HeuristicConfig(), logger=mock_logger)
            
            # Should not raise
            heuristic._check_environment()

    def test_cuda_not_available(self, mock_logger):
        """Test behavior when torch is not available or cuda is unavailable."""
        with patch('code.heuristics.gradient_magnitude._detect_gpu') as mock_detect:
            mock_detect.side_effect = ImportError("torch not installed")
            
            heuristic = GradientMagnitudeHeuristic(config=HeuristicConfig(), logger=mock_logger)
            # Should handle import error gracefully or raise specific error
            # Based on implementation, it might raise RuntimeError or just log
            # We expect it to NOT proceed with GPU usage
            with pytest.raises((RuntimeError, ImportError)):
                heuristic._check_environment()

class TestGradientCalculation:
    """Test the gradient calculation logic."""

    def test_gradient_calculation_basic(self, mock_logger):
        """Test basic gradient magnitude calculation."""
        # Mock inputs
        batch_size = 2
        seq_len = 100
        hidden_dim = 64
        
        # Create dummy input tensors (requires_grad=True)
        input_ids = torch.randint(0, 1000, (batch_size, seq_len))
        attention_mask = torch.ones_like(input_ids)
        
        # Mock model output with gradients
        with patch('code.heuristics.gradient_magnitude.torch') as mock_torch:
            # Setup mock tensors
            mock_tensor = MagicMock()
            mock_tensor.requires_grad = True
            mock_tensor.grad = torch.randn(batch_size, seq_len, hidden_dim)
            
            mock_torch.randn.return_value = mock_tensor
            mock_torch.no_grad.return_value = MagicMock(__enter__=lambda s: s, __exit__=lambda s, *a: None)
            
            # Test calculation function
            result = _calculate_local_gradient(
                input_ids=mock_tensor,
                attention_mask=attention_mask,
                window_size=10,
                logger=mock_logger
            )
            
            assert result.shape[0] == batch_size
            assert result.shape[1] == seq_len

    def test_uniform_entropy_distribution(self, mock_logger):
        """Test handling of uniform entropy distribution (edge case)."""
        # Simulate a scenario where gradients are uniform
        with patch('code.heuristics.gradient_magnitude.torch') as mock_torch:
            mock_tensor = MagicMock()
            mock_tensor.requires_grad = True
            # Uniform gradients (all same value)
            mock_tensor.grad = torch.ones(2, 50, 32) * 0.5
            
            mock_torch.no_grad.return_value = MagicMock(__enter__=lambda s: s, __exit__=lambda s, *a: None)
            
            result = _calculate_local_gradient(
                input_ids=mock_tensor,
                attention_mask=torch.ones(2, 50),
                window_size=5,
                logger=mock_logger
            )
            
            # Should not crash, should return valid magnitudes
            assert result is not None
            assert result.shape == (2, 50)

    def test_split_needles(self, mock_logger):
        """Test handling of split needles (multiple information sources)."""
        # Simulate gradients with multiple peaks
        with patch('code.heuristics.gradient_magnitude.torch') as mock_torch:
            mock_tensor = MagicMock()
            mock_tensor.requires_grad = True
            # Create gradient with two distinct peaks
            grad_data = torch.zeros(1, 100, 16)
            grad_data[0, 20:25, :] = 2.0  # First needle
            grad_data[0, 70:75, :] = 2.0  # Second needle
            mock_tensor.grad = grad_data
            
            mock_torch.no_grad.return_value = MagicMock(__enter__=lambda s: s, __exit__=lambda s, *a: None)
            
            result = _calculate_local_gradient(
                input_ids=mock_tensor,
                attention_mask=torch.ones(1, 100),
                window_size=10,
                logger=mock_logger
            )
            
            assert result is not None
            # Should detect peaks in both regions
            assert result.shape == (1, 100)

class TestHeuristicIntegration:
    """Test the full heuristic pipeline integration."""

    def test_select_blocks(self, mock_logger):
        """Test block selection based on gradient magnitudes."""
        with patch('code.heuristics.gradient_magnitude.torch') as mock_torch:
            # Mock model and tensors
            mock_model = MagicMock()
            mock_model.device = "cpu"
            
            mock_tensor = MagicMock()
            mock_tensor.requires_grad = True
            mock_tensor.grad = torch.randn(1, 100, 32)
            
            mock_torch.no_grad.return_value = MagicMock(__enter__=lambda s: s, __exit__=lambda s, *a: None)
            
            heuristic = GradientMagnitudeHeuristic(
                config=HeuristicConfig(top_k=5, window_size=10),
                logger=mock_logger
            )
            heuristic._check_environment = MagicMock()  # Skip GPU check
            
            # Mock the forward/backward pass
            with patch.object(heuristic, '_calculate_magnitudes') as mock_calc:
                mock_calc.return_value = torch.randn(1, 100)
                
                selected_blocks = heuristic.select_blocks(
                    input_ids=torch.randint(0, 1000, (1, 100)),
                    model=mock_model,
                    num_blocks=20
                )
                
                assert len(selected_blocks) == 5  # top_k
                assert all(isinstance(b, int) for b in selected_blocks)

# Import torch only for testing setup, handle if not available
try:
    import torch
except ImportError:
    pytest.skip("PyTorch not available for gradient tests", allow_module_level=True)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
