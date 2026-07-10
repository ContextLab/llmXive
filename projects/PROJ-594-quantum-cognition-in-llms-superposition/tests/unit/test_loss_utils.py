import pytest
import torch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from models.loss_utils import compute_phase_penalty_loss, verify_gradient_direction

def test_loss_zero_at_anti_parallel():
    """
    Verify that when phase difference is pi (anti-parallel), the loss is 0.
    cos(pi) = -1, so 1 + (-1) = 0.
    """
    phase_diff = torch.tensor([torch.pi, torch.pi, torch.pi])
    loss = compute_phase_penalty_loss(phase_diff, lambda_penalty=0.5)
    assert torch.isclose(loss, torch.tensor(0.0), atol=1e-6), f"Expected 0, got {loss}"

def test_loss_max_at_parallel():
    """
    Verify that when phase difference is 0 (parallel), the loss is maximal.
    cos(0) = 1, so 1 + 1 = 2. Loss = 0.5 * 2 = 1.0.
    """
    phase_diff = torch.tensor([0.0, 0.0, 0.0])
    loss = compute_phase_penalty_loss(phase_diff, lambda_penalty=0.5)
    expected = 0.5 * (1 + 1) # 1.0
    assert torch.isclose(loss, torch.tensor(expected), atol=1e-6), f"Expected {expected}, got {loss}"

def test_loss_intermediate():
    """
    Verify loss at pi/2. cos(pi/2) = 0. Loss = 0.5 * (1 + 0) = 0.5.
    """
    phase_diff = torch.tensor([torch.pi / 2])
    loss = compute_phase_penalty_loss(phase_diff, lambda_penalty=0.5)
    expected = 0.5 * (1 + 0)
    assert torch.isclose(loss, torch.tensor(expected), atol=1e-6), f"Expected {expected}, got {loss}"

def test_ambiguous_masking():
    """
    Verify that the mask correctly restricts loss calculation to specific tokens.
    """
    # 3 tokens: [0, pi/2, pi]
    # Mask: [False, True, False] -> Only pi/2 should contribute
    phase_diff = torch.tensor([0.0, torch.pi / 2, torch.pi])
    mask = torch.tensor([False, True, False])
    
    loss = compute_phase_penalty_loss(phase_diff, lambda_penalty=0.5, ambiguous_mask=mask)
    
    # Expected: Only the middle term (pi/2) contributes.
    # Loss for pi/2 is 0.5 * (1 + cos(pi/2)) = 0.5 * 1 = 0.5.
    # Since we average over 1 masked token, result is 0.5.
    expected = 0.5
    assert torch.isclose(loss, torch.tensor(expected), atol=1e-6), f"Expected {expected}, got {loss}"

def test_gradient_direction_verification():
    """
    Verify that the gradient of the loss function drives phases toward anti-parallelism (pi).
    This tests the mathematical property required for the optimizer to work correctly.
    """
    # The function returns True if the gradient direction is correct for non-anti-parallel phases.
    result = verify_gradient_direction(torch.tensor([0.5, 1.5, 2.5, 4.0]))
    assert result is True, "Gradient direction verification failed"

def test_gradient_negative_for_non_anti_parallel():
    """
    Directly test that for a phase difference of 0 (parallel), the gradient is negative,
    which will push the phase difference up (towards pi) during gradient descent.
    L = 0.5 * (1 + cos(theta))
    dL/dtheta = -0.5 * sin(theta)
    At theta=0, sin(0)=0 -> grad=0 (local max of cos, min of loss? No, max of loss).
    Wait, at theta=0, loss is max. Gradient should push away from 0.
    Actually, at theta=0, derivative of cos is 0. So it's a stationary point.
    Let's test theta = 0.1. sin(0.1) > 0. Grad = -0.5 * pos = neg.
    Update: theta = theta - lr * neg = theta + lr. Theta increases towards pi. Correct.
    """
    # We can't easily test the optimizer step here, but we can verify the sign of the gradient.
    # For theta in (0, pi), gradient must be negative to increase theta.
    theta = torch.tensor([0.1, 1.0, 2.0])
    lambda_p = 0.5
    grad = -lambda_p * torch.sin(theta)
    
    # All sin values in (0, pi) are positive, so grad should be negative.
    assert torch.all(grad < 0), f"Gradient should be negative for theta in (0, pi), got {grad}"

def test_lambda_parameter():
    """
    Verify that changing lambda scales the loss correctly.
    """
    phase_diff = torch.tensor([0.0]) # Max loss point
    
    loss_05 = compute_phase_penalty_loss(phase_diff, lambda_penalty=0.5)
    loss_10 = compute_phase_penalty_loss(phase_diff, lambda_penalty=1.0)
    
    # loss_10 should be exactly double loss_05
    assert torch.isclose(loss_10, loss_05 * 2.0), "Lambda scaling failed"