"""
Saliency mapping utilities for GNN models.

This module provides a simple gradient‑based saliency computation that can be
used as a baseline for the integration test. It works with any torch.nn.Module
that accepts a tensor of shape (batch_size, num_features) and returns a tensor
of shape (batch_size, 1) or (batch_size,).
"""

from __future__ import annotations

import numpy as np
import torch
from torch import Tensor
from typing import Callable


def compute_saliency(
    model: torch.nn.Module,
    inputs: Tensor,
    reduction: Callable[[Tensor], Tensor] = torch.mean,
) -> np.ndarray:
    """
    Compute feature‑wise saliency scores for a batch of inputs.

    Parameters
    ----------
    model: torch.nn.Module
        The model whose predictions we want to explain. It should return a
        scalar (or 1‑D tensor) per sample.
    inputs: Tensor
        Input tensor of shape (batch_size, num_features). Gradients will be
        computed w.r.t. this tensor.
    reduction: Callable
        Function used to reduce per‑sample gradients to a single saliency value
        per feature. By default the mean absolute gradient across the batch is
        used.

    Returns
    -------
    np.ndarray
        Array of shape (num_features,) containing the saliency score for each
        input feature.
    """
    if not isinstance(inputs, Tensor):
        raise TypeError("inputs must be a torch Tensor")
    if inputs.requires_grad:
        # detach any existing graph to avoid side‑effects
        inputs = inputs.detach()
    # Ensure gradients can be computed w.r.t. inputs
    inputs = inputs.clone().detach().requires_grad_(True)

    model.eval()
    with torch.enable_grad():
        outputs = model(inputs)
        if outputs.dim() > 1:
            # flatten to (batch_size,)
            outputs = outputs.squeeze(-1)
        # Sum over batch to get a scalar for gradient computation
        loss = outputs.sum()
        grads = torch.autograd.grad(loss, inputs, retain_graph=False)[0]
        # Absolute value and reduce across the batch dimension
        saliency = reduction(grads.abs(), dim=0)
        # Convert to NumPy
        return saliency.detach().cpu().numpy()