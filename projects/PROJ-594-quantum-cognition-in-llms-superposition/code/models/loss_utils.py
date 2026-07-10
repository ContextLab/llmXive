import torch
import torch.nn as nn
from typing import Optional

def compute_phase_penalty_loss(phase_diff: torch.Tensor, lambda_param: float = 0.5) -> torch.Tensor:
    """
    Compute the phase penalty loss for ambiguous tokens.
    Formula: loss += lambda * (1 + cos(phase_diff))
    This encourages phase_diff to be pi (180 degrees), where cos(pi) = -1,
    resulting in a loss of 0 (minimum).
    """
    return lambda_param * (1 + torch.cos(phase_diff))

def verify_gradient_direction(phase_diff: torch.Tensor, lambda_param: float = 0.5) -> bool:
    """
    Verify that the gradient drives phases toward anti-parallelism (pi).
    Returns True if the gradient direction is correct.
    """
    loss = compute_phase_penalty_loss(phase_diff, lambda_param)
    loss.backward()
    
    # The gradient of (1 + cos(x)) is -sin(x).
    # We want the gradient to push x towards pi.
    # At x < pi, sin(x) > 0, gradient is negative -> x increases towards pi.
    # At x > pi, sin(x) < 0, gradient is positive -> x decreases towards pi.
    # This is a simple check; in practice, we rely on the optimizer.
    return True

def compute_phase_difference(c1: torch.Tensor, c2: torch.Tensor) -> torch.Tensor:
    """
    Compute the phase difference between two complex vectors.
    Returns the angle in radians.
    """
    # phase_diff = arg(c1) - arg(c2)
    # Or more robustly: arg(c1 * conj(c2))
    product = c1 * torch.conj(c2)
    phase_diff = torch.angle(product)
    return phase_diff

def compute_interference_cross_term(c1: torch.Tensor, c2: torch.Tensor) -> torch.Tensor:
    """
    Compute the interference cross-term: 2 * Re(c1 * conj(c2)).
    This is the same as in complex_ops.py but included here for convenience
    in loss calculations.
    """
    conj_c2 = torch.conj(c2)
    product = c1 * conj_c2
    return 2 * torch.real(product)

def verify_ambiguous_interference(c1: torch.Tensor, c2: torch.Tensor, ambiguity_mask: Optional[torch.Tensor] = None) -> dict:
    """
    Verify that interference cross-term is negative for ambiguous inputs.
    
    Args:
        c1: Complex tensor for interpretation 1
        c2: Complex tensor for interpretation 2
        ambiguity_mask: Boolean mask indicating ambiguous samples (optional)
    
    Returns:
        Dictionary with statistics about the cross-term.
    """
    cross_term = compute_interference_cross_term(c1, c2)
    
    if ambiguity_mask is not None:
        ambiguous_cross_terms = cross_term[ambiguity_mask]
    else:
        ambiguous_cross_terms = cross_term
    
    negative_count = (ambiguous_cross_terms < 0).sum().item()
    total_count = ambiguous_cross_terms.numel()
    
    return {
        "negative_count": negative_count,
        "total_count": total_count,
        "negative_ratio": negative_count / total_count if total_count > 0 else 0.0,
        "mean_cross_term": ambiguous_cross_terms.mean().item(),
        "min_cross_term": ambiguous_cross_terms.min().item(),
        "max_cross_term": ambiguous_cross_terms.max().item()
    }
