import torch
from typing import Optional

def to_complex(real_tensor: torch.Tensor, imag_tensor: Optional[torch.Tensor] = None) -> torch.Tensor:
    """
    Convert real and imaginary tensors to a complex tensor.
    If imag_tensor is None, assumes a zero imaginary part.
    """
    if imag_tensor is None:
        imag_tensor = torch.zeros_like(real_tensor)
    return torch.complex(real_tensor, imag_tensor)

def phase_shift(complex_tensor: torch.Tensor, theta: torch.Tensor) -> torch.Tensor:
    """
    Apply a phase shift exp(i*theta) to a complex tensor.
    theta should be broadcastable to the tensor shape.
    """
    # exp(i*theta) = cos(theta) + i*sin(theta)
    cos_theta = torch.cos(theta)
    sin_theta = torch.sin(theta)
    shift_factor = torch.complex(cos_theta, sin_theta)
    return complex_tensor * shift_factor

def vector_add(vec1: torch.Tensor, vec2: torch.Tensor) -> torch.Tensor:
    """
    Perform vector addition of two complex tensors.
    """
    return vec1 + vec2

def born_rule(complex_tensor: torch.Tensor) -> torch.Tensor:
    """
    Apply the Born rule: P = |psi|^2 = real^2 + imag^2.
    Returns the squared magnitude.
    """
    return torch.abs(complex_tensor) ** 2

def interference_cross_term(c1: torch.Tensor, c2: torch.Tensor) -> torch.Tensor:
    """
    Compute the interference cross-term: 2 * Re(c1 * conj(c2)).
    
    This term is responsible for constructive (positive) or destructive (negative)
    interference in the quantum probability model.
    
    Args:
        c1: Complex tensor of shape [batch, ...]
        c2: Complex tensor of shape [batch, ...]
    
    Returns:
        Tensor of shape [batch] containing the cross-term values.
    """
    # c1 * conj(c2)
    conj_c2 = torch.conj(c2)
    product = c1 * conj_c2
    # 2 * Re(product)
    return 2 * torch.real(product)
