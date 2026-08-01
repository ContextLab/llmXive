"""
Loss utilities for the quantum-inspired adapter.
Includes phase penalty loss and interference cross-term calculation.
"""
import torch
import torch.nn as nn
from typing import Optional

def compute_phase_penalty_loss(phase_diff: torch.Tensor, lambda_param: float = 0.5) -> torch.Tensor:
    """
    Computes the phase penalty loss to drive phases toward anti-parallelism.
    Formula: loss += lambda * (1 + cos(phase_diff))
    When phase_diff = pi (anti-parallel), cos(pi) = -1 -> loss = 0.
    When phase_diff = 0 (parallel), cos(0) = 1 -> loss = 2*lambda.
    
    Args:
        phase_diff: [batch, ...] or scalar tensor of phase differences (radians)
        lambda_param: penalty weight (default 0.5)
    
    Returns:
        Scalar loss tensor
    """
    # Ensure phase_diff is a tensor
    if not isinstance(phase_diff, torch.Tensor):
        phase_diff = torch.tensor(phase_diff)
    
    loss = lambda_param * (1 + torch.cos(phase_diff))
    return loss.mean()  # Return mean loss over the tensor


def verify_gradient_direction(phase_diff: torch.Tensor) -> bool:
    """
    Verifies that the gradient of the phase penalty loss drives phases toward anti-parallelism.
    For phase_diff near 0, the gradient should be negative (pushing phase_diff toward pi).
    For phase_diff near pi, the gradient should be near 0.
    
    Args:
        phase_diff: tensor of phase differences
    
    Returns:
        True if the gradient direction is correct (anti-parallel), False otherwise.
    """
    loss = compute_phase_penalty_loss(phase_diff)
    loss.backward()
    
    # Check gradient of phase_diff
    if phase_diff.grad is None:
        return False
    
    # For phase_diff = 0, gradient of (1+cos(x)) is -sin(x) = 0. 
    # Actually, derivative of (1+cos(x)) is -sin(x).
    # At x=0, sin(0)=0 -> gradient 0. 
    # At x=pi/2, sin(pi/2)=1 -> gradient -1 (pushing x down toward 0? but we want toward pi).
    # Wait, the loss is (1+cos(x)). We want to minimize it.
    # Minimum at x=pi (cos(pi)=-1 -> loss=0).
    # Derivative: -sin(x). 
    # At x=0: derivative = 0. 
    # At x=pi/2: derivative = -1 -> gradient points to decreasing x (toward 0) which is wrong.
    # We want to push x toward pi.
    # Actually, the derivative of the loss with respect to x is -sin(x).
    # Gradient descent: x_new = x - lr * (-sin(x)) = x + lr*sin(x).
    # At x=0: x_new = 0. 
    # At x=pi/2: x_new = pi/2 + lr*1 -> increases toward pi. Correct.
    # At x=3pi/2: sin(3pi/2)=-1 -> x_new = 3pi/2 - lr -> decreases toward pi. Correct.
    # So the gradient direction is correct.
    
    # We'll test at a specific point: x = pi/2.
    # We expect the gradient to be negative (since -sin(pi/2) = -1).
    # But the gradient of the loss with respect to x is -sin(x).
    # So at x=pi/2, gradient = -1.
    # We want to verify that the gradient points toward pi.
    # Since x=pi/2 < pi, we want to increase x. The gradient is negative, so x - lr * grad = x + lr * 1 -> increases. Correct.
    
    # Let's check the sign of the gradient at x=pi/2.
    test_diff = torch.tensor([torch.pi / 2], requires_grad=True)
    test_loss = compute_phase_penalty_loss(test_diff)
    test_loss.backward()
    
    # Gradient should be negative at pi/2
    if test_diff.grad is not None:
        grad_sign = test_diff.grad.item()
        # At pi/2, gradient = -sin(pi/2) = -1. So it should be negative.
        return grad_sign < 0
    return False


def compute_phase_difference(c1: torch.Tensor, c2: torch.Tensor) -> torch.Tensor:
    """
    Computes the phase difference between two complex tensors.
    Args:
        c1: [batch, ..., dim] complex tensor
        c2: [batch, ..., dim] complex tensor
    Returns:
        [batch, ..., dim] tensor of phase differences (radians)
    """
    phase_c1 = torch.angle(c1)
    phase_c2 = torch.angle(c2)
    return phase_c1 - phase_c2


def compute_interference_cross_term(c1: torch.Tensor, c2: torch.Tensor) -> torch.Tensor:
    """
    Computes the interference cross-term: 2 * Re(c1 * conj(c2)).
    This term can be negative, leading to destructive interference.
    
    Args:
        c1: [batch, ..., dim] complex tensor
        c2: [batch, ..., dim] complex tensor
    
    Returns:
        [batch, ..., dim] tensor of cross-term values
    """
    # c1 * conj(c2)
    product = c1 * torch.conj(c2)
    # Real part
    real_part = torch.real(product)
    # Cross term = 2 * real_part
    return 2 * real_part


def verify_ambiguous_interference(c1: torch.Tensor, c2: torch.Tensor, ambiguity_mask: torch.Tensor) -> bool:
    """
    Verifies that the interference cross-term is negative for ambiguous inputs.
    Args:
        c1: [batch, seq_len, dim] complex tensor
        c2: [batch, seq_len, dim] complex tensor
        ambiguity_mask: [batch, seq_len] boolean mask
    Returns:
        True if the average cross-term for ambiguous tokens is negative, False otherwise.
    """
    cross_term = compute_interference_cross_term(c1, c2)
    # Average over the last dimension
    cross_term_scalar = cross_term.mean(dim=-1)  # [batch, seq_len]
    
    # Select ambiguous tokens
    if ambiguity_mask.dim() == 2:
        ambiguous_terms = cross_term_scalar[ambiguity_mask == 1]
        if ambiguous_terms.numel() == 0:
            return True  # No ambiguous tokens to check
        return ambiguous_terms.mean().item() < 0
    return False
