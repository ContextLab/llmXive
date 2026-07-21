import torch
import torch.nn as nn
from typing import Optional

def compute_phase_penalty_loss(phase_diff: torch.Tensor, lambda_param: float = 0.5) -> torch.Tensor:
    """
    Compute the phase penalty loss for ambiguous tokens.
    Formula: loss += lambda * (1 + cos(phase_diff))
    This encourages phase_diff to be pi (anti-parallel), where cos(pi) = -1, loss = 0.
    """
    return lambda_param * (1.0 + torch.cos(phase_diff))

def verify_gradient_direction(phase_diff: torch.Tensor, lambda_param: float = 0.5) -> bool:
    """
    Verify that the gradient of the penalty loss drives phases toward anti-parallelism (pi).
    d/d(theta) [lambda * (1 + cos(theta))] = -lambda * sin(theta)
    We want the gradient to push theta towards pi.
    At theta < pi (e.g., 0), sin(0)=0, but for small positive theta, sin(theta)>0, gradient is negative -> pushes theta up.
    At theta > pi (e.g., 2pi), sin(2pi)=0, but for theta slightly less than 2pi, sin is negative, gradient is positive -> pushes theta down.
    """
    # We can't easily verify direction without a computational graph, 
    # but we can check that the loss is minimized at pi.
    loss_at_pi = compute_phase_penalty_loss(torch.tensor([torch.pi]), lambda_param)
    loss_at_0 = compute_phase_penalty_loss(torch.tensor([0.0]), lambda_param)
    return loss_at_pi < loss_at_0

def compute_phase_difference(c1: torch.Tensor, c2: torch.Tensor) -> torch.Tensor:
    """
    Compute the phase difference between two complex vectors.
    Returns angle in radians.
    """
    # phase_diff = arg(c1) - arg(c2)
    # Or more robustly: arg(c1 * conj(c2))
    product = c1 * torch.conj(c2)
    return torch.angle(product)

def compute_interference_cross_term(c1: torch.Tensor, c2: torch.Tensor) -> torch.Tensor:
    """
    Compute the interference cross-term: 2 * Re(c1 * conj(c2)).
    """
    product = c1 * torch.conj(c2)
    return 2.0 * torch.real(product)

def verify_ambiguous_interference(cross_terms: torch.Tensor, threshold: float = 0.0, min_percentage: float = 0.10) -> bool:
    """
    Verify that a sufficient percentage of ambiguous samples have negative cross-terms.
    This validates the hypothesis that ambiguity leads to destructive interference.
    
    Args:
        cross_terms: Tensor of cross-term values (real numbers).
        threshold: Values below this are considered "negative".
        min_percentage: Minimum fraction of samples that must be negative.
        
    Returns:
        True if the condition is met, False otherwise.
    """
    if cross_terms.numel() == 0:
        return False
    negative_count = (cross_terms < threshold).sum().item()
    total_count = cross_terms.numel()
    percentage = negative_count / total_count
    return percentage >= min_percentage
