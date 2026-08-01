"""
Unit tests for the loss function and cross-term logging in bert_adapter.py.
"""
import pytest
import torch
import json
import os
import sys
import tempfile
import shutil

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from models.bert_adapter import BERTComplexAdapter
from models.loss_utils import compute_phase_penalty_loss, compute_interference_cross_term, verify_gradient_direction


class TestBERTAdapterLoss:
    """Tests for the loss function integration in BERTComplexAdapter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.batch_size = 2
        self.seq_len = 4
        self.input_dim = 768
        self.hidden_dim = 128
        self.adapter = BERTComplexAdapter(self.input_dim, self.hidden_dim)
        self.adapter.train()

    def test_phase_penalty_loss_gradient_direction(self):
        """Verify that the gradient drives phases toward anti-parallelism."""
        # Test at phase_diff = pi/2 (should have negative gradient)
        phase_diff = torch.tensor([torch.pi / 2], requires_grad=True)
        loss = compute_phase_penalty_loss(phase_diff)
        loss.backward()
        
        # Gradient should be negative at pi/2
        assert phase_diff.grad is not None
        assert phase_diff.grad.item() < 0, "Gradient should be negative at pi/2, driving phase toward pi"

    def test_cross_term_can_be_negative(self):
        """Verify that the cross-term can be negative for anti-parallel phases."""
        # Create c1 and c2 with opposite phases
        c1 = torch.complex(torch.ones(1, 1, 10), torch.zeros(1, 1, 10))  # phase 0
        c2 = torch.complex(-torch.ones(1, 1, 10), torch.zeros(1, 1, 10))  # phase pi
        
        cross_term = compute_interference_cross_term(c1, c2)
        # Expected: 2 * Re(1 * conj(-1)) = 2 * (-1) = -2
        assert cross_term.mean().item() < 0, "Cross-term should be negative for anti-parallel phases"

    def test_forward_pass_with_ambiguity_mask(self):
        """Test forward pass with ambiguity mask and cross-term logging."""
        # Create dummy input
        x_real = torch.randn(self.batch_size, self.seq_len, self.input_dim)
        ambiguity_mask = torch.zeros(self.batch_size, self.seq_len, dtype=torch.bool)
        # Mark some tokens as ambiguous
        ambiguity_mask[0, 0] = True
        ambiguity_mask[1, 2] = True
        
        probs, metadata = self.adapter(x_real, ambiguity_mask)
        
        # Check output shape
        assert probs.shape == (self.batch_size, self.seq_len, 2)
        
        # Check that metadata contains phase_penalty if in training mode
        assert 'phase_penalty' in metadata
        assert isinstance(metadata['phase_penalty'], float)

    def test_cross_term_logging(self):
        """Test that cross-term values are logged correctly."""
        x_real = torch.randn(self.batch_size, self.seq_len, self.input_dim)
        ambiguity_mask = torch.ones(self.batch_size, self.seq_len, dtype=torch.bool)  # All ambiguous
        
        # Run multiple forward passes
        for _ in range(3):
            _, _ = self.adapter(x_real, ambiguity_mask)
        
        # Check that the log is populated
        assert len(self.adapter.cross_term_log) > 0
        assert len(self.adapter.ambiguous_indices) > 0

    def test_save_cross_term_log(self):
        """Test saving the cross-term log to a JSON file."""
        x_real = torch.randn(self.batch_size, self.seq_len, self.input_dim)
        ambiguity_mask = torch.ones(self.batch_size, self.seq_len, dtype=torch.bool)
        
        _, _ = self.adapter(x_real, ambiguity_mask)
        
        # Create a temporary directory for the test
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "test_cross_term_log.json")
        
        try:
            self.adapter.save_cross_term_log(output_path)
            
            # Verify the file was created
            assert os.path.exists(output_path)
            
            # Load and check the content
            with open(output_path, 'r') as f:
                log_data = json.load(f)
            
            assert 'cross_term_values' in log_data
            assert 'ambiguous_indices' in log_data
            assert len(log_data['cross_term_values']) > 0
            assert len(log_data['ambiguous_indices']) > 0
        finally:
            # Clean up
            shutil.rmtree(temp_dir)

    def test_gradient_drives_anti_parallelism(self):
        """Test that the gradient of the loss function drives phases toward anti-parallelism."""
        # This is a high-level test using the verify_gradient_direction function
        result = verify_gradient_direction(torch.tensor([torch.pi / 2]))
        assert result, "Gradient direction should be correct (driving toward anti-parallelism)"