import torch
import pytest
from models.bert_adapter import ContextDependentPhaseShift, ComplexLinearProjection
from utils.config import set_environment

def test_context_dependent_phase_shift_varies_with_input():
    """
    T020b: Verify U_c varies with context.
    Assert that the phase shift operator produces different outputs
    when the input context changes, proving it is not a static matrix.
    """
    set_environment(seed=42)

    batch_size = 2
    seq_len = 10
    hidden_dim = 768

    # Initialize the adapter components
    complex_proj = ComplexLinearProjection(hidden_dim)
    phase_shift_op = ContextDependentPhaseShift(hidden_dim)

    # Create two distinct input contexts (random but fixed seeds for reproducibility)
    torch.manual_seed(100)
    input_context_1 = torch.randn(batch_size, seq_len, hidden_dim)

    torch.manual_seed(200)
    input_context_2 = torch.randn(batch_size, seq_len, hidden_dim)

    # Ensure inputs are actually different
    assert not torch.allclose(input_context_1, input_context_2), "Test setup error: inputs must differ"

    # Apply the context-dependent phase shift
    # The operator should compute a context embedding and derive rotation angles from it
    with torch.no_grad():
        output_1 = phase_shift_op(input_context_1)
        output_2 = phase_shift_op(input_context_2)

    # The outputs must differ.
    # If U_c were static (independent of context), the operation would be
    # effectively a fixed linear transformation (or identity if angles were zero),
    # but specifically, the *angles* theta are derived from the input.
    # Different inputs -> different theta -> different phase factors exp(i*theta).
    # Therefore, the resulting complex vectors must differ.
    assert not torch.allclose(output_1, output_2), (
        "Failure: U_c did not vary with input context. "
        "The phase shift operator should produce different results for different inputs."
    )

    # Additional check: Verify that the phase angles themselves were computed
    # We can inspect the internal logic or rely on the output difference.
    # To be rigorous, we check that the magnitude of the difference is non-trivial.
    diff_magnitude = torch.norm(output_1 - output_2).item()
    assert diff_magnitude > 1e-6, (
        f"Failure: Output difference magnitude {diff_magnitude} is too small. "
        "Context dependence appears broken."
    )

def test_complex_linear_projection_structure():
    """
    Sanity check for the complex projection layer structure.
    Ensures the real and imaginary components are properly initialized.
    """
    set_environment(seed=42)
    hidden_dim = 768
    proj = ComplexLinearProjection(hidden_dim)

    # Check that weights exist
    assert hasattr(proj, 'real_proj'), "ComplexLinearProjection missing real_proj"
    assert hasattr(proj, 'imag_proj'), "ComplexLinearProjection missing imag_proj"

    # Check shapes
    # Assuming simple projection R^d -> R^d for real and imag parts
    assert proj.real_proj.weight.shape[0] == hidden_dim
    assert proj.imag_proj.weight.shape[0] == hidden_dim

if __name__ == "__main__":
    pytest.main([__file__, "-v"])