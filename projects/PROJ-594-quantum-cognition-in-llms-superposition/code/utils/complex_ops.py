import torch
from typing import Optional

def to_complex(real: torch.Tensor, imag: Optional[torch.Tensor] = None) -> torch.Tensor:
    """
    Convert real tensor to complex. If imag is None, imag=0.
    """
    if imag is None:
        imag = torch.zeros_like(real)
    return torch.stack([real, imag], dim=-1).to(torch.complex64)

def phase_shift(complex_vec: torch.Tensor, theta: torch.Tensor) -> torch.Tensor:
    """
    Apply phase shift exp(i*theta) to complex vector.
    theta: [batch, seq_len] or broadcastable.
    """
    # theta shape should be broadcastable to complex_vec[..., 0]
    phase = torch.exp(1j * theta)
    return complex_vec * phase

def vector_add(c1: torch.Tensor, c2: torch.Tensor) -> torch.Tensor:
    """
    Vector addition of two complex tensors.
    """
    return c1 + c2

def born_rule(complex_vec: torch.Tensor) -> torch.Tensor:
    """
    Compute squared magnitude (Born rule probability density).
    Returns real tensor of shape same as input without last dim.
    """
    return torch.abs(complex_vec) ** 2

def interference_cross_term(c1: torch.Tensor, c2: torch.Tensor) -> torch.Tensor:
    """
    Compute the interference cross-term: 2 * Re(c1 * conj(c2)).
    This term determines whether interference is constructive (positive)
    or destructive (negative).
    
    Args:
        c1: Complex tensor of shape [batch, seq_len, hidden]
        c2: Complex tensor of shape [batch, seq_len, hidden]
        
    Returns:
        Real tensor of shape [batch, seq_len, hidden] containing the cross-term values.
    """
    # c1 * conj(c2)
    product = c1 * torch.conj(c2)
    # 2 * Re(product)
    return 2.0 * torch.real(product)
