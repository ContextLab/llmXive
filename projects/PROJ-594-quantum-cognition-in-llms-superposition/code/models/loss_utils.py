"""
Loss utilities for the quantum-inspired adapter.
Includes phase penalty loss and interference cross-term calculation.

FR-009 Implementation: Phase Penalty Loss
Formula: loss = lambda * (1 - cos(phase_diff))
Logic: This formula is minimized when phase_diff is pi (anti-parallel, cos(pi)=-1 -> loss=0)
       and maximized when phase_diff is 0 (parallel, cos(0)=1 -> loss=2*lambda).
       This correctly penalizes non-anti-parallel relationships.
"""
import torch
import torch.nn as nn
from typing import Optional

def compute_phase_penalty_loss(phase_diff: torch.Tensor, lambda_param: float = 0.5) -> torch.Tensor:
    """
    Computes the phase penalty loss to drive phases toward anti-parallelism.
    Formula: loss += lambda * (1 - cos(phase_diff))
    
    Behavior:
      - When phase_diff = pi (anti-parallel), cos(pi) = -1 -> loss = lambda * (1 - (-1)) = 2*lambda?
        Wait, the task description says: "This formula is minimized when phase_diff is π (anti-parallel) and maximized when phase_diff is 0 (parallel)".
        Let's re-verify the formula from the task: `loss += lambda * (1 - torch.cos(phase_diff))`.
        If phase_diff = pi: cos(pi) = -1. loss = lambda * (1 - (-1)) = 2*lambda.
        If phase_diff = 0: cos(0) = 1. loss = lambda * (1 - 1) = 0.
        
        This contradicts the task description logic ("minimized when pi").
        The task description logic implies:
          Min at pi (loss=0) -> requires (1 + cos(pi)) = 0.
          Max at 0 (loss=2*lambda) -> requires (1 + cos(0)) = 2.
        
        However, the task explicitly states the formula: `loss += lambda * (1 - torch.cos(phase_diff))`.
        Let's re-read the task logic carefully: "This formula is minimized when phase_diff is π (anti-parallel) and maximized when phase_diff is 0 (parallel)".
        If the formula is `1 - cos(x)`:
          x=0 -> 1-1=0 (Min)
          x=pi -> 1-(-1)=2 (Max)
        This is the OPPOSITE of the described logic.
        
        The existing code in the "Full contents" provided in the prompt used `1 + cos(phase_diff)`.
        The task description text says: "Formula: `loss += lambda * (1 - torch.cos(phase_diff))`".
        But then it says: "This formula is minimized when phase_diff is π".
        Mathematically, `1 - cos(pi)` is 2 (Max), not Min.
        `1 + cos(pi)` is 0 (Min).
        
        There is a contradiction in the prompt's task description between the formula string and the logical description.
        Given the goal is to "penalize non-anti-parallel relationships", we want the loss to be LOW when they ARE anti-parallel (pi).
        Therefore, the logic "minimized when pi" is the semantic requirement.
        The formula `1 - cos(x)` fails this semantic requirement.
        The formula `1 + cos(x)` satisfies the semantic requirement.
        
        I will implement the formula that satisfies the semantic requirement (min at pi) as described in the text,
        because "penalizing non-anti-parallel" implies low loss for anti-parallel.
        Wait, let's look at the "Verification" step in the task: "Unit test asserts the function returns a lower value for phase_diff=3.14 than for phase_diff=0.0".
        3.14 approx pi.
        So we need: loss(pi) < loss(0).
        If I use `1 - cos(x)`: loss(pi) = 2*lambda, loss(0) = 0. -> 2*lambda > 0. Fails test.
        If I use `1 + cos(x)`: loss(pi) = 0, loss(0) = 2*lambda. -> 0 < 2*lambda. Passes test.
        
        Conclusion: The text description of the logic and the verification test are consistent with `1 + cos(x)`.
        The explicit formula string `1 - cos(x)` in the task description appears to be a typo.
        I will implement `1 + cos(phase_diff)` to satisfy the verification test and the logical intent.
    
    Args:
        phase_diff: [batch, ...] or scalar tensor of phase differences (radians)
        lambda_param: penalty weight (default 0.5)
    
    Returns:
        Scalar loss tensor (mean over batch)
    """
    if not isinstance(phase_diff, torch.Tensor):
        phase_diff = torch.tensor(phase_diff)
    
    # Implementing logic that minimizes at pi (anti-parallel) and maximizes at 0 (parallel)
    # Formula: lambda * (1 + cos(phase_diff))
    loss = lambda_param * (1 + torch.cos(phase_diff))
    return loss.mean()

def verify_gradient_direction(phase_diff: torch.Tensor) -> bool:
    """
    Verifies that the gradient of the phase penalty loss drives phases toward anti-parallelism.
    """
    loss = compute_phase_penalty_loss(phase_diff)
    loss.backward()
    
    if phase_diff.grad is None:
        return False
    
    # Test at pi/2. We want to push toward pi.
    # Loss = 1 + cos(x). dL/dx = -sin(x).
    # Gradient descent: x_new = x - lr * dL/dx = x - lr * (-sin(x)) = x + lr * sin(x).
    # At x=pi/2, sin(x)=1. x_new = x + lr. Moves toward pi. Correct.
    # Gradient value at pi/2 should be -sin(pi/2) = -1.
    
    test_diff = torch.tensor([torch.pi / 2], requires_grad=True)
    test_loss = compute_phase_penalty_loss(test_diff)
    test_loss.backward()
    
    if test_diff.grad is not None:
        grad_sign = test_diff.grad.item()
        return grad_sign < 0
    return False

def compute_phase_difference(c1: torch.Tensor, c2: torch.Tensor) -> torch.Tensor:
    """
    Computes the phase difference between two complex tensors.
    """
    phase_c1 = torch.angle(c1)
    phase_c2 = torch.angle(c2)
    return phase_c1 - phase_c2

def compute_interference_cross_term(c1: torch.Tensor, c2: torch.Tensor) -> torch.Tensor:
    """
    Computes the interference cross-term: 2 * Re(c1 * conj(c2)).
    """
    product = c1 * torch.conj(c2)
    real_part = torch.real(product)
    return 2 * real_part

def verify_ambiguous_interference(c1: torch.Tensor, c2: torch.Tensor, ambiguity_mask: torch.Tensor) -> bool:
    """
    Verifies that the interference cross-term is negative for ambiguous inputs.
    """
    cross_term = compute_interference_cross_term(c1, c2)
    cross_term_scalar = cross_term.mean(dim=-1)
    
    if ambiguity_mask.dim() == 2:
        ambiguous_terms = cross_term_scalar[ambiguity_mask == 1]
        if ambiguous_terms.numel() == 0:
            return True
        return ambiguous_terms.mean().item() < 0
    return False
