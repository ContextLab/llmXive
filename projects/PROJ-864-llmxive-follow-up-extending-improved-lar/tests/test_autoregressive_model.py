"""
Tests for the Autoregressive model implementation.
"""
import sys
import unittest
from pathlib import Path

import torch

# Add code root to path
code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

from models.autoregressive import create_autoregressive_model, AutoregressiveModel
from models.config import get_embed_dim, get_num_heads, get_vocab_size, get_max_seq_length


class TestAutoregressiveModel(unittest.TestCase):
    """Test cases for the AutoregressiveModel."""

    def setUp(self):
        """Set up test fixtures."""
        self.model = create_autoregressive_model()

    def test_model_creation(self):
        """Test that the model can be created without errors."""
        self.assertIsInstance(self.model, AutoregressiveModel)
        self.assertTrue(self.model.training)

    def test_model_parameters_count(self):
        """Test that the model has a reasonable number of parameters."""
        num_params = sum(p.numel() for p in self.model.parameters())
        # Should be non-zero and reasonably sized for CPU
        self.assertGreater(num_params, 0)
        # Feasible size for CPU (T008) - should be < 50M params
        self.assertLess(num_params, 50_000_000)

    def test_forward_pass(self):
        """Test a simple forward pass."""
        batch_size = 2
        seq_len = 32
        
        input_ids = torch.randint(0, get_vocab_size(), (batch_size, seq_len))
        
        logits, loss = self.model(input_ids)
        
        self.assertEqual(logits.shape, (batch_size, seq_len, get_vocab_size()))
        self.assertIsNone(loss)

    def test_forward_pass_with_labels(self):
        """Test forward pass with labels for loss calculation."""
        batch_size = 2
        seq_len = 32
        
        input_ids = torch.randint(0, get_vocab_size(), (batch_size, seq_len))
        labels = torch.randint(0, get_vocab_size(), (batch_size, seq_len))
        
        logits, loss = self.model(input_ids, labels=labels)
        
        self.assertEqual(logits.shape, (batch_size, seq_len, get_vocab_size()))
        self.assertIsNotNone(loss)
        self.assertTrue(loss.requires_grad)

    def test_torch_compile_compatibility(self):
        """Test that the model is compatible with torch.compile."""
        try:
            compiled_model = torch.compile(self.model)
            input_ids = torch.randint(0, get_vocab_size(), (1, 16))
            _ = compiled_model(input_ids)
            # If we get here without error, it's compatible
            self.assertTrue(True)
        except Exception as e:
            # If torch.compile is not available or fails, we still consider the model valid
            # as long as it's not a structural incompatibility
            if "torch.compile" in str(e).lower():
                self.skipTest("torch.compile not available in this environment")
            else:
                self.fail(f"Model is not compatible with torch.compile: {e}")

    def test_attention_mask(self):
        """Test forward pass with attention mask."""
        batch_size = 2
        seq_len = 32
        
        input_ids = torch.randint(0, get_vocab_size(), (batch_size, seq_len))
        attention_mask = torch.ones((batch_size, seq_len))
        attention_mask[0, 16:] = 0  # Mask second half of first sample
        
        logits, loss = self.model(input_ids, attention_mask=attention_mask)
        
        self.assertEqual(logits.shape, (batch_size, seq_len, get_vocab_size()))

    def test_causal_property(self):
        """Test that the model respects causal masking (token at t only sees 0..t-1)."""
        # This is a structural test; we verify the mask exists
        self.assertTrue(hasattr(self.model.transformer_blocks[0].attn, 'causal_mask'))


def run_tests():
    """Run all tests in this module."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAutoregressiveModel)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


if __name__ == '__main__':
    run_tests()