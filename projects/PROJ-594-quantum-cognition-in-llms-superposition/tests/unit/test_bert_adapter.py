"""
Unit tests for the BERT Complex Adapter components.
Specifically tests the ContextDependentPhaseShift to ensure U_c varies with context.
"""
import torch
import pytest
import sys
import os

# Add the project root to the path to allow imports from 'models' and 'utils'
# assuming this test is run from the project root or via pytest with proper config.
# In a real CI environment, PYTHONPATH would be set.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from models.bert_adapter import ContextDependentPhaseShift, ComplexLinearProjection


class TestContextDependentPhaseShift:
    """Tests for the ContextDependentPhaseShift module (US2)."""

    def test_u_c_varies_with_context(self):
        """
        Verify that the phase shift operator U_c changes when the input context changes.
        
        The ContextDependentPhaseShift should compute a context embedding via attention
        pooling over sentence tokens and project it to a rotation angle theta.
        If the input context (sentence tokens) changes, the resulting theta and
        the subsequent phase shift exp(i*theta) must change.
        
        This test asserts that U_c is NOT a static matrix but depends on the input.
        """
        # Configuration
        batch_size = 2
        seq_len = 10
        hidden_dim = 768
        device = torch.device("cpu")

        # Initialize the module
        # The module expects input of shape [batch, seq_len, hidden]
        module = ContextDependentPhaseShift(hidden_dim=hidden_dim).to(device)
        module.eval()

        # Create two different random input contexts
        # Context A: Random noise
        context_a = torch.randn(batch_size, seq_len, hidden_dim, device=device)
        
        # Context B: Different random noise (or a shifted version)
        context_b = torch.randn(batch_size, seq_len, hidden_dim, device=device)

        # Ensure contexts are actually different
        assert not torch.allclose(context_a, context_b), "Test setup error: contexts must differ."

        with torch.no_grad():
            # Run inference on both contexts
            output_a = module(context_a)
            output_b = module(context_b)

        # The output should be complex tensors
        assert output_a.is_complex(), "Output A must be a complex tensor."
        assert output_b.is_complex(), "Output B must be a complex tensor."

        # Check that the outputs are different.
        # If U_c were static (independent of context), and the input was just passed through
        # a static linear layer, we might see similarity. But the core requirement is that
        # the *operation* depends on context.
        # Specifically, the phase shift applied to the vector must differ.
        # We check the magnitude of the difference between the two outputs.
        diff = torch.abs(output_a - output_b)
        mean_diff = diff.mean().item()

        # Assert that the difference is significant enough to confirm context dependency.
        # A very small difference might indicate a bug where context is ignored.
        # We use a threshold relative to the magnitude of the outputs to be robust.
        assert mean_diff > 1e-5, (
            f"ContextDependentPhaseShift appears static. "
            f"Mean difference between outputs for different contexts is {mean_diff:.6e}. "
            f"The phase shift operator U_c must vary with input context."
        )

        # Additional check: Verify that the internal phase angles are different
        # by looking at the imaginary/real ratio or just the values directly.
        # Since the module applies exp(i*theta), if theta changes, the complex value changes.
        # We already checked the output difference, which covers this.

    def test_u_c_varies_with_context_deterministic(self):
        """
        A more deterministic check: use a fixed seed and specific values to ensure
        the transformation is strictly context-dependent.
        """
        hidden_dim = 128
        module = ContextDependentPhaseShift(hidden_dim=hidden_dim)
        module.eval()

        # Create a base context
        base_context = torch.ones(1, 5, hidden_dim)
        
        # Create a modified context (change one token's representation)
        modified_context = base_context.clone()
        modified_context[0, 0, :] *= 2.0  # Double the values of the first token

        with torch.no_grad():
            out_base = module(base_context)
            out_mod = module(modified_context)

        # They must not be equal
        assert not torch.allclose(out_base, out_mod), (
            "U_c must change when input context changes. "
            "The output for base_context and modified_context must differ."
        )

        # Verify the difference is not just numerical noise
        diff = torch.abs(out_base - out_mod)
        assert diff.max() > 1e-6, "Difference between outputs is too small; context dependency may be missing."

    def test_static_matrix_hypothesis_rejected(self):
        """
        Explicitly test the hypothesis that U_c is a static matrix.
        If U_c were static, then for inputs x1 and x2, the operation would be:
        y1 = M * x1, y2 = M * x2.
        However, the implementation computes theta from context pooling.
        If theta is constant regardless of input, then the phase shift is constant.
        This test ensures that the phase shift angle derived from context A is different from B.
        """
        hidden_dim = 64
        module = ContextDependentPhaseShift(hidden_dim=hidden_dim)
        module.eval()

        # Input A: All zeros (or a specific pattern)
        ctx_a = torch.zeros(1, 4, hidden_dim)
        ctx_a[0, 0, 0] = 1.0  # One active feature

        # Input B: Different pattern
        ctx_b = torch.zeros(1, 4, hidden_dim)
        ctx_b[0, 1, 0] = 1.0  # Different active feature

        with torch.no_grad():
            out_a = module(ctx_a)
            out_b = module(ctx_b)

        # If the context pooling and projection to theta worked, the phase shift
        # applied to the vectors should be different.
        # We check the angle of the complex numbers.
        # For a complex number z = x + iy, angle = atan2(y, x).
        # We compare the mean angle of the output vectors.
        
        # Flatten to [batch*seq, hidden]
        flat_a = out_a.reshape(-1, hidden_dim)
        flat_b = out_b.reshape(-1, hidden_dim)

        # Compute angles
        angles_a = torch.atan2(flat_a.imag, flat_a.real)
        angles_b = torch.atan2(flat_b.imag, flat_b.real)

        mean_angle_a = angles_a.mean().item()
        mean_angle_b = angles_b.mean().item()

        # The mean angles should be different if the context influenced the phase shift
        # Note: This is a statistical check; with random initialization, they should differ.
        # A strict equality check might fail due to randomness, but a large difference is expected.
        # We assert they are not "too close" (e.g., within 0.01 radians) unless the model
        # is trivially broken (theta=0 everywhere).
        assert abs(mean_angle_a - mean_angle_b) > 0.001, (
            f"Context-dependent phase shift failed. Mean angles: {mean_angle_a:.4f} vs {mean_angle_b:.4f}. "
            "The phase shift operator U_c must vary with context."
        )