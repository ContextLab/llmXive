import torch
import numpy as np
from typing import Optional, Tuple, List
import logging
from config import Config

logger = logging.getLogger(__name__)

class W2A4Quantizer:
    """
    W2A4 quantizer for activations. Provides a ``quantize`` method that optionally
    rotates the tensor with a provided orthogonal matrix before quantisation.
    """
    def __init__(self, config: Config = None):
        # ``config`` is optional for now – kept for future extensibility.
        self.config = config

    def quantize_activation(
        self,
        tensor: torch.Tensor,
        rotation_matrix: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Quantise an activation tensor. If ``rotation_matrix`` is supplied, the tensor
        is first rotated (matrix multiplication on the last dimension).

        Parameters
        ----------
        tensor : torch.Tensor
            The activation tensor to quantise.
        rotation_matrix : torch.Tensor, optional
            Orthogonal matrix of shape (D, D) where D matches the last dimension of
            ``tensor``.

        Returns
        -------
        torch.Tensor
            De‑quantised tensor (same shape as input) – useful for sanity checks.
        """
        x = tensor.float()
        if rotation_matrix is not None:
            # Assume rotation is applied on the channel dimension.
            # Reshape to (..., C) -> (..., C) @ R^T
            orig_shape = x.shape
            x = x.view(-1, x.shape[-1])
            x = torch.matmul(x, rotation_matrix.t())
            x = x.view(*orig_shape)

        # Symmetric 4‑bit quantisation: range [-8, 7]
        qmin, qmax = -8, 7
        act_min, act_max = x.min(), x.max()
        if act_max == act_min:
            scale = torch.tensor(1.0, device=x.device)
        else:
            scale = (act_max - act_min) / (qmax - qmin)

        quantized = torch.round(x / scale + (qmin + qmax) / 2)
        quantized = torch.clamp(quantized, qmin, qmax)

        # De‑quantise back to float for downstream use / testing
        return (quantized - (qmin + qmax) / 2) * scale

    # Compatibility alias used by the verification script
    def quantize(self, tensor: torch.Tensor, rotation_matrix: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Alias for ``quantize_activation`` to satisfy legacy call‑sites.
        """
        return self.quantize_activation(tensor, rotation_matrix)
