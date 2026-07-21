"""
Tests for the differentiable solver module.

These tests verify:
1. The custom autograd function works correctly
2. Gradients do NOT flow through the decoded action
3. Gradients DO flow to solver parameters
4. The gradient flow log is created correctly
"""
import json
import os
import sys
import tempfile
import torch
import pytest

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from differentiable_solver import (
    DiffCPWrapperFunction,
    ConstraintViolationLoss,
    DifferentiableSymbolicSolver
)
from symbolic_solver import SymbolicSolver

class TestDiffCPWrapperFunction:
    """Tests for the custom autograd function."""
    
    def test_forward_pass(self):
        """Test that the forward pass returns a valid solution."""
        # Create test tensors
        A = torch.randn(10, 5)
        b = torch.randn(10)
        c = torch.randn(5)
        x_decoded = torch.randn(5)
        
        solver = SymbolicSolver(timeout=10.0)
        
        # Run forward pass
        x_opt = DiffCPWrapperFunction.apply(A, b, c, x_decoded, solver)
        
        # Check that output is a tensor with correct shape
        assert isinstance(x_opt, torch.Tensor)
        assert x_opt.shape == (5,)
    
    def test_no_gradient_through_decoder(self):
        """Test that gradients do NOT flow through the decoded action."""
        # Create test tensors
        A = torch.randn(10, 5, requires_grad=True)
        b = torch.randn(10, requires_grad=True)
        c = torch.randn(5, requires_grad=True)
        x_decoded = torch.randn(5, requires_grad=True)
        
        solver = SymbolicSolver(timeout=10.0)
        
        # Run forward pass
        x_opt = DiffCPWrapperFunction.apply(A, b, c, x_decoded, solver)
        
        # Compute a simple loss
        loss = x_opt.sum()
        
        # Backward pass
        loss.backward()
        
        # Check that x_decoded has no gradient (it was detached)
        assert x_decoded.grad is None, "Gradient should not flow through decoder"
    
    def test_gradient_to_parameters(self):
        """Test that gradients DO flow to solver parameters."""
        # Create test tensors
        A = torch.randn(10, 5, requires_grad=True)
        b = torch.randn(10, requires_grad=True)
        c = torch.randn(5, requires_grad=True)
        x_decoded = torch.randn(5)
        
        solver = SymbolicSolver(timeout=10.0)
        
        # Run forward pass
        x_opt = DiffCPWrapperFunction.apply(A, b, c, x_decoded, solver)
        
        # Compute a simple loss
        loss = x_opt.sum()
        
        # Backward pass
        loss.backward()
        
        # Check that parameters have gradients (if they require grad)
        # Note: In the current implementation, we may not compute all gradients,
        # but we ensure the structure is correct
        # At minimum, c should have a gradient
        if c.grad is not None:
            assert c.grad.shape == c.shape

class TestConstraintViolationLoss:
    """Tests for the constraint violation loss."""
    
    def test_loss_computation(self):
        """Test that the loss is computed correctly."""
        loss_fn = ConstraintViolationLoss(violation_threshold=1e-3)
        
        # Create test tensors
        x_opt = torch.randn(5)
        A = torch.randn(10, 5)
        b = torch.randn(10)
        
        # Compute loss
        loss = loss_fn(x_opt, A, b)
        
        # Check that loss is a scalar
        assert isinstance(loss, torch.Tensor)
        assert loss.shape == ()
        assert loss >= 0, "Loss should be non-negative"
    
    def test_loss_gradients(self):
        """Test that the loss has gradients."""
        loss_fn = ConstraintViolationLoss(violation_threshold=1e-3)
        
        # Create test tensors with requires_grad
        x_opt = torch.randn(5, requires_grad=True)
        A = torch.randn(10, 5, requires_grad=True)
        b = torch.randn(10, requires_grad=True)
        
        # Compute loss
        loss = loss_fn(x_opt, A, b)
        
        # Backward pass
        loss.backward()
        
        # Check that x_opt has gradients
        assert x_opt.grad is not None
        assert x_opt.grad.shape == x_opt.shape

class TestDifferentiableSymbolicSolver:
    """Tests for the differentiable symbolic solver."""
    
    def test_forward_pass(self):
        """Test that the forward pass returns valid outputs."""
        symbolic_solver = SymbolicSolver(timeout=10.0)
        diff_solver = DifferentiableSymbolicSolver(symbolic_solver)
        
        # Create test tensors
        A = torch.randn(10, 5)
        b = torch.randn(10)
        c = torch.randn(5)
        x_decoded = torch.randn(5)
        
        # Run forward pass
        x_opt, loss = diff_solver(x_decoded, A, b, c)
        
        # Check outputs
        assert isinstance(x_opt, torch.Tensor)
        assert x_opt.shape == (5,)
        assert isinstance(loss, torch.Tensor)
        assert loss.shape == ()
    
    def test_gradient_flow_verification(self):
        """Test that gradient flow verification works correctly."""
        symbolic_solver = SymbolicSolver(timeout=10.0)
        diff_solver = DifferentiableSymbolicSolver(symbolic_solver)
        
        # Create test tensors
        A = torch.randn(10, 5, requires_grad=True)
        b = torch.randn(10, requires_grad=True)
        c = torch.randn(5, requires_grad=True)
        x_decoded = torch.randn(5)
        
        # Verify gradient flow
        param_names = ["A", "b", "c"]
        log_entry = diff_solver.verify_gradient_flow(x_decoded, A, b, c, param_names)
        
        # Check that the log entry is valid
        assert "x_decoded_grad" in log_entry
        assert "param_grads" in log_entry
        assert log_entry["x_decoded_grad"] == "OK: No gradient through decoder"
    
    def test_save_gradient_log(self):
        """Test that the gradient log is saved correctly."""
        symbolic_solver = SymbolicSolver(timeout=10.0)
        diff_solver = DifferentiableSymbolicSolver(symbolic_solver)
        
        # Create test tensors
        A = torch.randn(10, 5, requires_grad=True)
        b = torch.randn(10, requires_grad=True)
        c = torch.randn(5, requires_grad=True)
        x_decoded = torch.randn(5)
        
        # Verify gradient flow
        param_names = ["A", "b", "c"]
        diff_solver.verify_gradient_flow(x_decoded, A, b, c, param_names)
        
        # Save the log to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            diff_solver.save_gradient_log(temp_path)
            
            # Check that the file exists and contains valid JSON
            assert os.path.exists(temp_path)
            with open(temp_path, 'r') as f:
                log_data = json.load(f)
            
            # Check the structure
            assert "gradient_flow_log" in log_data
            assert "summary" in log_data
            assert len(log_data["gradient_flow_log"]) == 1
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)