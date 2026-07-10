import pytest
import torch
import torch.nn as nn
import sys
import os

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from models.bert_adapter import BERTComplexAdapter
from models.loss_utils import compute_phase_penalty_loss, verify_gradient_direction

class TestBERTAdapterLoss:
    """
    Unit tests for the loss function with phase penalty term in BERTComplexAdapter.
    Verifies that the gradient drives phases toward anti-parallelism.
    """
    
    def test_phase_penalty_computation(self):
        """Test that phase penalty loss is computed correctly."""
        batch_size = 4
        seq_len = 10
        hidden_dim = 768
        
        # Create complex states with known phases
        complex_states = torch.randn(batch_size, seq_len, hidden_dim, dtype=torch.complex64)
        
        # Compute phase penalty loss
        loss = compute_phase_penalty_loss(complex_states, lambda_penalty=0.5)
        
        # Loss should be a scalar tensor
        assert isinstance(loss, torch.Tensor)
        assert loss.dim() == 0
        assert not torch.isnan(loss)
        assert not torch.isinf(loss)
        
    def test_gradient_drives_anti_parallelism(self):
        """
        Verify that gradient of phase penalty drives phases toward anti-parallelism.
        This is the core requirement of T023.
        """
        batch_size = 2
        seq_len = 5
        hidden_dim = 64
        
        # Create complex states with requires_grad=True
        complex_states = torch.randn(batch_size, seq_len, hidden_dim, dtype=torch.complex64, requires_grad=True)
        
        # Compute loss
        lambda_penalty = 0.5
        loss = compute_phase_penalty_loss(complex_states, lambda_penalty=lambda_penalty)
        
        # Backpropagate
        loss.backward()
        
        # Check that gradients exist and are not zero
        assert complex_states.grad is not None
        assert not torch.allclose(complex_states.grad, torch.zeros_like(complex_states.grad))
        
        # The gradient should push phases toward anti-parallelism
        # This is verified by checking that the gradient direction is consistent
        # with the phase penalty formula: loss += lambda * (1 + cos(phase_diff))
        # For anti-parallel phases (phase_diff = pi), cos(pi) = -1, so loss = 0 (minimum)
        # For parallel phases (phase_diff = 0), cos(0) = 1, so loss = 2*lambda (maximum)
        
        # Verify gradient direction using the helper function
        gradient_direction = verify_gradient_direction(complex_states)
        assert gradient_direction, "Gradient should drive phases toward anti-parallelism"
        
    def test_loss_integration_with_adapter(self):
        """Test that the loss function integrates correctly with BERTComplexAdapter."""
        hidden_dim = 128
        model = BERTComplexAdapter(hidden_dim=hidden_dim, num_classes=2)
        
        # Create dummy inputs
        batch_size = 4
        seq_len = 10
        hidden_states = torch.randn(batch_size, seq_len, hidden_dim)
        labels = torch.randint(0, 2, (batch_size, seq_len))
        
        # Compute loss
        total_loss, phase_penalty_loss = model.compute_loss(hidden_states, labels, lambda_penalty=0.5)
        
        # Check loss values
        assert isinstance(total_loss, torch.Tensor)
        assert isinstance(phase_penalty_loss, torch.Tensor)
        assert total_loss.dim() == 0
        assert phase_penalty_loss.dim() == 0
        
        # Check that loss is finite
        assert not torch.isnan(total_loss)
        assert not torch.isinf(total_loss)
        assert not torch.isnan(phase_penalty_loss)
        assert not torch.isinf(phase_penalty_loss)
        
        # Check that total_loss >= phase_penalty_loss (since CE loss is non-negative)
        assert total_loss >= phase_penalty_loss
        
    def test_gradient_flow_through_adapter(self):
        """Test that gradients flow correctly through the entire adapter."""
        hidden_dim = 128
        model = BERTComplexAdapter(hidden_dim=hidden_dim, num_classes=2)
        
        # Create dummy inputs
        batch_size = 2
        seq_len = 5
        hidden_states = torch.randn(batch_size, seq_len, hidden_dim)
        labels = torch.randint(0, 2, (batch_size, seq_len))
        
        # Compute loss
        total_loss, _ = model.compute_loss(hidden_states, labels, lambda_penalty=0.5)
        
        # Backpropagate
        total_loss.backward()
        
        # Check that all parameters have gradients
        for name, param in model.named_parameters():
            assert param.grad is not None, f"Parameter {name} has no gradient"
            assert not torch.allclose(param.grad, torch.zeros_like(param.grad)), \
                f"Parameter {name} has zero gradient"
        
    def test_lambda_penalty_scaling(self):
        """Test that the lambda penalty scales the loss correctly."""
        hidden_dim = 64
        model = BERTComplexAdapter(hidden_dim=hidden_dim, num_classes=2)
        
        # Create dummy inputs
        batch_size = 2
        seq_len = 5
        hidden_states = torch.randn(batch_size, seq_len, hidden_dim)
        labels = torch.randint(0, 2, (batch_size, seq_len))
        
        # Compute loss with different lambda values
        lambda_values = [0.0, 0.5, 1.0, 2.0]
        losses = []
        
        for lambda_val in lambda_values:
            total_loss, phase_penalty_loss = model.compute_loss(hidden_states, labels, lambda_penalty=lambda_val)
            losses.append((lambda_val, total_loss.item(), phase_penalty_loss.item()))
        
        # Verify that increasing lambda increases the phase penalty contribution
        # Note: This is a loose check since the actual loss values depend on the data
        for i in range(len(losses) - 1):
            lambda1, loss1, penalty1 = losses[i]
            lambda2, loss2, penalty2 = losses[i + 1]
            
            # Higher lambda should result in higher or equal total loss (if phase_penalty > 0)
            if penalty1 > 0:
                assert loss2 >= loss1 - 1e-6, \
                    f"Loss should increase with lambda: {loss1} -> {loss2}"
                
    def test_anti_parallel_phase_minimum(self):
        """
        Test that anti-parallel phases produce minimum loss.
        This validates the core quantum-inspired mechanism.
        """
        # Create two complex vectors that are anti-parallel
        # Phase difference = pi (180 degrees)
        batch_size = 1
        seq_len = 1
        hidden_dim = 4
        
        # Create states with anti-parallel phases
        # c1 = 1 + 0j, c2 = -1 + 0j (phase difference = pi)
        complex_states = torch.tensor([
            [[1.0 + 0.0j, 0.0 + 1.0j, -1.0 + 0.0j, 0.0 - 1.0j]]
        ], dtype=torch.complex64, requires_grad=True)
        
        # Compute loss
        loss = compute_phase_penalty_loss(complex_states, lambda_penalty=1.0)
        
        # For anti-parallel phases, loss should be close to 0 (minimum)
        # Note: The exact value depends on the implementation details
        assert loss.item() < 0.5, f"Anti-parallel phases should have low loss, got {loss.item()}"
        
        # Backpropagate
        loss.backward()
        
        # Gradient should be small for anti-parallel phases (near minimum)
        assert torch.allclose(complex_states.grad, torch.zeros_like(complex_states.grad), atol=1e-5), \
            "Gradient should be near zero for anti-parallel phases"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
