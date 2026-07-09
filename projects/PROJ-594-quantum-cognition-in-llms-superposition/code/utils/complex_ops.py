"""
Complex-valued linear algebra utilities for quantum-inspired LLM reasoning.

Implements core operations:
  - to_complex: Map real vectors to complex amplitudes
  - phase_shift: Apply context-dependent phase rotation
  - vector_add: Superposition (vector addition)
  - born_rule: Compute probability from squared magnitude
"""

import torch
from typing import Optional


def to_complex(real_tensor: torch.Tensor) -> torch.Tensor:
    """
    Convert a real-valued tensor to a complex tensor by treating the input
    as the real component and setting the imaginary component to zero.

    Args:
        real_tensor: Input tensor of shape [..., d] with dtype float32 or float64.

    Returns:
        Complex tensor of shape [..., d] with dtype torch.complex64.
    """
    if real_tensor.dtype not in (torch.float32, torch.float64):
        raise ValueError(f"to_complex expects float32 or float64, got {real_tensor.dtype}")

    # Ensure float32 for memory efficiency (matches torch.complex64 requirement)
    if real_tensor.dtype == torch.float64:
        real_tensor = real_tensor.float()

    return torch.view_as_complex(
        torch.stack([real_tensor, torch.zeros_like(real_tensor)], dim=-1)
    )


def phase_shift(
    complex_tensor: torch.Tensor,
    theta: torch.Tensor,
    dim: int = -1
) -> torch.Tensor:
    """
    Apply a diagonal phase shift operator U_c = diag(exp(i * theta)) to the complex tensor.

    This implements the rotation of the "arrows" (probability amplitudes) based on
    context. If theta is a scalar, it is broadcast. If theta is a tensor, it must
    be broadcastable to the target dimension.

    Args:
        complex_tensor: Input complex tensor of shape [..., d] with dtype torch.complex64.
        theta: Phase angles in radians. Can be a scalar or a tensor of shape [..., d].
        dim: The dimension along which to apply the phase shift (default: last dimension).

    Returns:
        Complex tensor of the same shape with phase shifted.
    """
    if not torch.is_complex(complex_tensor):
        raise ValueError(f"phase_shift expects complex input, got {complex_tensor.dtype}")

    # Compute exp(i * theta) = cos(theta) + i * sin(theta)
    phase_factor = torch.exp(1j * theta)

    # Ensure phase_factor is complex if theta was real
    if not torch.is_complex(phase_factor):
        phase_factor = phase_factor.to(torch.complex64)

    return complex_tensor * phase_factor


def vector_add(*tensors: torch.Tensor) -> torch.Tensor:
    """
    Perform vector addition (superposition) of multiple complex tensors.

    This corresponds to the sum-over-paths principle: amplitudes add directly,
    allowing for constructive and destructive interference.

    Args:
        *tensors: Variable number of complex tensors of the same shape.

    Returns:
        Complex tensor representing the sum of all input tensors.
    """
    if not tensors:
        raise ValueError("vector_add requires at least one tensor")

    result = tensors[0]
    if not torch.is_complex(result):
        raise ValueError(f"vector_add expects complex input, got {result.dtype}")

    for t in tensors[1:]:
        if not torch.is_complex(t):
            raise ValueError(f"vector_add expects complex input, got {t.dtype}")
        if t.shape != result.shape:
            raise ValueError(f"Shape mismatch: {result.shape} vs {t.shape}")
        result = result + t

    return result


def born_rule(complex_tensor: torch.Tensor) -> torch.Tensor:
    """
    Apply the Born rule to compute probabilities from complex amplitudes.

    P = |psi|^2 = Re(psi)^2 + Im(psi)^2

    This computes the squared magnitude of the complex tensor, returning a
    real-valued tensor of probabilities.

    Args:
        complex_tensor: Input complex tensor of shape [..., d] with dtype torch.complex64.

    Returns:
        Real tensor of shape [..., d] containing probabilities (non-negative).
    """
    if not torch.is_complex(complex_tensor):
        raise ValueError(f"born_rule expects complex input, got {complex_tensor.dtype}")

    return torch.abs(complex_tensor) ** 2


def interference_cross_term(
    c1: torch.Tensor,
    c2: torch.Tensor
) -> torch.Tensor:
    """
    Compute the interference cross-term: 2 * Re(c1 * conj(c2)).

    This term is responsible for the deviation from classical probability
    (where P = |c1|^2 + |c2|^2). In quantum mechanics, P = |c1 + c2|^2
    = |c1|^2 + |c2|^2 + 2*Re(c1*conj(c2)).

    Args:
        c1: First complex amplitude tensor.
        c2: Second complex amplitude tensor.

    Returns:
        Real tensor of the same shape containing the interference cross-term.
    """
    if not torch.is_complex(c1) or not torch.is_complex(c2):
        raise ValueError("interference_cross_term requires complex inputs")
    if c1.shape != c2.shape:
        raise ValueError(f"Shape mismatch: {c1.shape} vs {c2.shape}")

    return 2.0 * torch.real(c1 * torch.conj(c2))