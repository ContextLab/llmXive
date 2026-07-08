"""
code/models/mpnn.py
-------------------

Implementation of a minimal single‑layer Message Passing Neural Network (MPNN)
for diffusion coefficient prediction. The model is deliberately CPU‑only
(no CUDA usage) and logs the device at initialization time.

The architecture uses a single :class:`torch_geometric.nn.GCNConv` layer
followed by a linear projection to the desired output dimension.  This
satisfies the requirement for a *single‑layer* MPNN while keeping the
implementation lightweight and suitable for CPU execution.

The module provides:
  * ``SingleLayerMPNN`` – the PyTorch ``nn.Module`` implementing the network.
  * ``get_device`` – helper returning the torch device (always ``cpu``).
"""

from __future__ import annotations

import logging
from typing import Tuple

import torch
from torch import nn
from torch_geometric.nn import GCNConv
from torch_geometric.data import Data

# Project‑specific logger utility
try:
    # utils.logging is part of the project API surface
    from utils.logging import get_logger, log_info
except Exception:  # pragma: no cover
    # Fallback to a simple logger if the utility cannot be imported
    logging.basicConfig(level=logging.INFO)
    _fallback_logger = logging.getLogger(__name__)

    def get_logger(name: str) -> logging.Logger:
        return _fallback_logger

    def log_info(message: str) -> None:
        _fallback_logger.info(message)

__all__ = ["SingleLayerMPNN", "get_device"]

def get_device() -> torch.device:
    """
    Return the torch device that should be used for model computation.
    The implementation is deliberately CPU‑only to satisfy the FR‑003
    requirement.

    Returns
    -------
    torch.device
        The device object representing the CPU.
    """
    return torch.device("cpu")

class SingleLayerMPNN(nn.Module):
    """
    A minimal single‑layer Message Passing Neural Network.

    Parameters
    ----------
    in_dim : int
        Dimensionality of the input node features.
    hidden_dim : int
        Dimensionality of the hidden representation produced by the
        message‑passing layer.
    out_dim : int
        Dimensionality of the final output (e.g., a scalar diffusion
        coefficient prediction).
    """

    def __init__(self, in_dim: int, hidden_dim: int, out_dim: int) -> None:
        super().__init__()
        self.device = get_device()
        # Ensure model parameters are on the CPU
        self.to(self.device)

        # Log the chosen device – required by the unit test T016a
        log_info("Device: CPU")

        # Single GCN convolution layer
        self.conv = GCNConv(in_dim, hidden_dim)
        # Linear layer maps hidden representation to output dimension
        self.out_lin = nn.Linear(hidden_dim, out_dim)

    def forward(self, data: Data) -> torch.Tensor:
        """
        Forward pass of the MPNN.

        Parameters
        ----------
        data : torch_geometric.data.Data
            Graph data containing at least ``x`` (node features) and
            ``edge_index`` (graph connectivity).

        Returns
        -------
        torch.Tensor
            Predicted values with shape ``(num_nodes, out_dim)``.
        """
        # Move data to the correct device (CPU)
        x = data.x.to(self.device)
        edge_index = data.edge_index.to(self.device)

        # Message passing step
        x = self.conv(x, edge_index)
        x = torch.relu(x)

        # Output projection
        out = self.out_lin(x)

        return out

    def predict(self, data: Data) -> torch.Tensor:
        """
        Convenience wrapper for inference that ensures the model is in
        evaluation mode and gradients are not tracked.

        Parameters
        ----------
        data : torch_geometric.data.Data
            Input graph.

        Returns
        -------
        torch.Tensor
            Model predictions.
        """
        self.eval()
        with torch.no_grad():
            return self.forward(data)