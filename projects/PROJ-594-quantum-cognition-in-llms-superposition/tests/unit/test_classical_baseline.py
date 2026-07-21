"""
Unit tests for the Classical Baseline implementation.
"""
import os
import sys
import json
import torch
import pytest
from typing import List

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from experiments.run_classical_baseline import compute_classical_probability

class TestClassicalBaseline:
    """Tests for the classical sum-of-squares probability calculation."""

    def test_classical_sum_positive(self):
        """Test that classical probability is sum of squared magnitudes."""
        # c1 = 1+0i, c2 = 0+1i -> ||c1||^2 = 1, ||c2||^2 = 1 -> P = 2
        c1 = torch.tensor([[1.0 + 0j]])
        c2 = torch.tensor([[0.0 + 1j]])
        
        result = compute_classical_probability(c1, c2)
        expected = torch.tensor([2.0])
        
        assert torch.allclose(result, expected), f"Expected {expected}, got {result}"

    def test_classical_sum_zero(self):
        """Test that classical probability is zero for zero amplitudes."""
        c1 = torch.tensor([[0.0 + 0j]])
        c2 = torch.tensor([[0.0 + 0j]])
        
        result = compute_classical_probability(c1, c2)
        expected = torch.tensor([0.0])
        
        assert torch.allclose(result, expected), f"Expected {expected}, got {result}"

    def test_classical_no_interference(self):
        """
        Verify that the classical baseline does NOT include the interference term.
        
        In quantum: P = ||c1 + c2||^2 = ||c1||^2 + ||c2||^2 + 2*Re(c1*c2*)
        In classical: P = ||c1||^2 + ||c2||^2
        
        If c1=1, c2=-1 (destructive interference in quantum):
        Quantum: ||1 + (-1)||^2 = 0
        Classical: ||1||^2 + ||-1||^2 = 2
        """
        c1 = torch.tensor([[1.0 + 0j]])
        c2 = torch.tensor([[-1.0 + 0j]])
        
        result = compute_classical_probability(c1, c2)
        # Classical should be 1^2 + (-1)^2 = 2
        expected = torch.tensor([2.0])
        
        assert torch.allclose(result, expected), f"Classical baseline failed to ignore interference. Expected {expected}, got {result}"
        
        # Verify quantum would be 0 (just for context)
        # c_sum = c1 + c2 = 0 -> ||0||^2 = 0
        c_sum = c1 + c2
        quantum_result = torch.abs(c_sum) ** 2
        assert torch.allclose(quantum_result, torch.tensor([0.0])), "Quantum interference check failed"

    def test_batch_processing(self):
        """Test batch processing of classical probability."""
        batch_size = 4
        c1 = torch.ones(batch_size, 1, dtype=torch.complex64)
        c2 = torch.ones(batch_size, 1, dtype=torch.complex64)
        
        result = compute_classical_probability(c1, c2)
        expected = torch.tensor([2.0, 2.0, 2.0, 2.0])
        
        assert result.shape == (batch_size,), f"Expected shape ({batch_size},), got {result.shape}"
        assert torch.allclose(result, expected), f"Expected {expected}, got {result}"

    def test_real_input_handling(self):
        """Test that real inputs (non-complex) are handled correctly."""
        c1 = torch.tensor([[1.0]])
        c2 = torch.tensor([[2.0]])
        
        result = compute_classical_probability(c1, c2)
        # ||1||^2 + ||2||^2 = 1 + 4 = 5
        expected = torch.tensor([5.0])
        
        assert torch.allclose(result, expected), f"Expected {expected}, got {result}"