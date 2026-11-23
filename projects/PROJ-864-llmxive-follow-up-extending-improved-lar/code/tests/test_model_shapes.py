"""
Contract tests for model parameter count and shape validation.

Verifies that the implemented models match the calculated feasible parameter count
and have the correct architectural dimensions.
"""
import sys
import unittest
from pathlib import Path

# Ensure imports work
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

import torch
from models.config import get_embed_dim, get_num_heads, get_num_layers, get_vocab_size, get_max_seq_length
from models.autoregressive import create_autoregressive_model
from models.diffusion import create_diffusion_model


def count_parameters(model: torch.nn.Module) -> int:
    """
    Count the total number of trainable parameters in a model.
    
    Args:
        model: PyTorch model instance
        
    Returns:
        Total number of parameters
    """
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


class TestModelShapes(unittest.TestCase):
    """Test cases for model architecture validation."""

    def test_autoregressive_model_parameters(self):
        """Verify AR model has the expected parameter count."""
        embed_dim = get_embed_dim()
        num_heads = get_num_heads()
        num_layers = get_num_layers()
        vocab_size = get_vocab_size()
        max_seq_length = get_max_seq_length()
        
        model = create_autoregressive_model()
        param_count = count_parameters(model)
        
        # Calculate expected parameters (approximate)
        # Embedding: vocab_size * embed_dim
        # Transformer blocks: num_layers * (2 * embed_dim^2 + embed_dim * embed_dim)
        # Output: embed_dim * vocab_size
        expected_embed = vocab_size * embed_dim
        expected_transformer = num_layers * (2 * embed_dim * embed_dim + embed_dim * embed_dim)
        expected_output = embed_dim * vocab_size
        expected_total = expected_embed + expected_transformer + expected_output
        
        # Allow 10% tolerance for implementation details
        tolerance = 0.10
        lower_bound = expected_total * (1 - tolerance)
        upper_bound = expected_total * (1 + tolerance)
        
        self.assertGreaterEqual(param_count, lower_bound, 
            f"AR model parameter count {param_count} is below expected {expected_total}")
        self.assertLessEqual(param_count, upper_bound,
            f"AR model parameter count {param_count} exceeds expected {expected_total}")

    def test_diffusion_model_parameters(self):
        """Verify Diffusion model has the expected parameter count."""
        embed_dim = get_embed_dim()
        num_heads = get_num_heads()
        num_layers = get_num_layers()
        vocab_size = get_vocab_size()
        max_seq_length = get_max_seq_length()
        
        model = create_diffusion_model()
        param_count = count_parameters(model)
        
        # Similar calculation as AR model
        expected_embed = vocab_size * embed_dim
        expected_transformer = num_layers * (2 * embed_dim * embed_dim + embed_dim * embed_dim)
        expected_output = embed_dim * vocab_size
        expected_total = expected_embed + expected_transformer + expected_output
        
        # Allow 10% tolerance
        tolerance = 0.10
        lower_bound = expected_total * (1 - tolerance)
        upper_bound = expected_total * (1 + tolerance)
        
        self.assertGreaterEqual(param_count, lower_bound,
            f"Diffusion model parameter count {param_count} is below expected {expected_total}")
        self.assertLessEqual(param_count, upper_bound,
            f"Diffusion model parameter count {param_count} exceeds expected {expected_total}")

    def test_model_dimensions_match_config(self):
        """Verify model dimensions match the configuration."""
        embed_dim = get_embed_dim()
        num_heads = get_num_heads()
        
        ar_model = create_autoregressive_model()
        diff_model = create_diffusion_model()
        
        # Check AR model embed dim
        ar_embed_dim = ar_model.embed_dim
        self.assertEqual(ar_embed_dim, embed_dim,
            f"AR model embed_dim {ar_embed_dim} != config {embed_dim}")
        
        # Check Diffusion model embed dim
        diff_embed_dim = diff_model.embed_dim
        self.assertEqual(diff_embed_dim, embed_dim,
            f"Diffusion model embed_dim {diff_embed_dim} != config {embed_dim}")


def run_tests():
    """Run all tests in this module."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestModelShapes)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
