"""
Logging and numerical safety utilities for the Quantum Cognition pipeline.

Provides utilities to detect numerical instability (NaN, Inf) in tensors
and perform safe normalization operations to prevent training crashes.
"""

import torch
from typing import Optional, Tuple, List


def detect_nan_inf(
    tensor: torch.Tensor, name: Optional[str] = None
) -> Tuple[bool, bool, str]:
    """
    Detects NaN and Inf values in a tensor.

    Args:
        tensor: The torch.Tensor to check.
        name: Optional name of the tensor for error reporting.

    Returns:
        Tuple of (has_nan, has_inf, message).
        If issues are found, message contains details; otherwise empty.
    """
    has_nan = torch.isnan(tensor).any().item()
    has_inf = torch.isinf(tensor).any().item()

    if name is None:
        name = "Tensor"

    if has_nan or has_inf:
        msg_parts = [f"{name} contains"]
        if has_nan:
            nan_count = torch.isnan(tensor).sum().item()
            msg_parts.append(f" {nan_count} NaN values")
        if has_inf:
            inf_count = torch.isinf(tensor).sum().item()
            msg_parts.append(f" {inf_count} Inf values")
        return True, has_inf, ",".join(msg_parts) + "."

    return False, False, ""


def safe_normalize(
    tensor: torch.Tensor,
    dim: Optional[int] = None,
    epsilon: float = 1e-8,
    allow_nan: bool = False
) -> torch.Tensor:
    """
    Performs L2 normalization with safeguards against division by zero and NaNs.

    This function computes the norm, replaces zeros with epsilon to prevent
    division by zero, and optionally handles NaNs by replacing them with 0.0
    or raising an error.

    Args:
        tensor: Input tensor to normalize.
        dim: Dimension along which to compute the norm. If None, flattens.
        epsilon: Small constant added to the norm to prevent division by zero.
        allow_nan: If False, raises ValueError if NaNs are detected in input.
                   If True, NaNs in the output (from 0/0) are replaced with 0.0.

    Returns:
        Normalized tensor with the same shape as input.

    Raises:
        ValueError: If input contains NaNs and allow_nan is False.
    """
    if not allow_nan and torch.isnan(tensor).any():
        raise ValueError("Input tensor contains NaNs and allow_nan=False")

    # Compute L2 norm
    norm = torch.norm(tensor, p=2, dim=dim, keepdim=True)

    # Prevent division by zero
    norm = torch.clamp(norm, min=epsilon)

    normalized = tensor / norm

    # Handle any resulting NaNs (e.g., 0/0 if input was 0) if allowed
    if allow_nan:
        normalized = torch.where(
            torch.isnan(normalized),
            torch.zeros_like(normalized),
            normalized
        )

    return normalized


def log_gradient_stats(
    model: torch.nn.Module,
    step: int,
    logger: Optional[callable] = None
) -> None:
    """
    Logs statistics for gradients of all parameters in a model.

    Args:
        model: The torch.nn.Module to inspect.
        step: Current training step (for logging context).
        logger: Optional logging function. If None, prints to stdout.
    """
    def log_msg(msg: str):
        if logger:
            logger(msg)
        else:
            print(f"[Step {step}] {msg}")

    has_issues = False
    grad_norms = []

    for name, param in model.named_parameters():
        if param.grad is None:
            continue

        has_nan, has_inf, msg = detect_nan_inf(param.grad, f"grad of {name}")
        if has_nan or has_inf:
            log_msg(f"CRITICAL: {msg}")
            has_issues = True

        grad_norm = param.grad.norm().item()
        grad_norms.append(grad_norm)

    if not has_issues and grad_norms:
        avg_norm = sum(grad_norms) / len(grad_norms)
        max_norm = max(grad_norms)
        log_msg(f"Gradient stats: avg_norm={avg_norm:.4f}, max_norm={max_norm:.4f}")