"""
SchNet‑style Graph Neural Network for predicting molecular dipole moments.

This implementation provides a lightweight, CPU‑only architecture that follows the
spirit of the original SchNet model while keeping dependencies minimal.  It
consists of:

* An atom embedding layer (learned embeddings for atomic numbers).
* Simple interaction blocks that aggregate neighbour information using a
  distance‑based radial basis function (RBF) and a linear filter.
* A read‑out MLP that maps the per‑molecule representation to a scalar dipole
  moment prediction.

The model expects inputs compatible with the data pipelines in the project:
``z`` – a ``LongTensor`` of atomic numbers,
``pos`` – a ``FloatTensor`` of shape ``(N_atoms, 3)`` containing Cartesian
coordinates,
``batch`` – a ``LongTensor`` of shape ``(N_atoms,)`` indicating the molecule
index for each atom (optional; if omitted all atoms belong to a single
molecule).

The forward pass returns a tensor of shape ``(batch_size, 1)`` with the
predicted dipole moments.
"""

from __future__ import annotations

import math
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

__all__ = ["SchNetGNN"]


class RBFExpansion(nn.Module):
    """
    Radial‑basis‑function expansion of inter‑atomic distances.
    Implements the Gaussian RBFs used in the original SchNet paper.
    """

    def __init__(self, num_rbf: int = 32, cutoff: float = 5.0, rbf_gamma: Optional[float] = None):
        super().__init__()
        self.num_rbf = num_rbf
        self.cutoff = cutoff
        # centres are linearly spaced between 0 and cutoff
        self.centers = torch.linspace(0.0, cutoff, steps=num_rbf)
        if rbf_gamma is None:
            # default gamma ensures reasonable overlap of neighbouring RBFs
            rbf_gamma = 10.0 / (self.centers[1] - self.centers[0]) ** 2
        self.gamma = rbf_gamma

    def forward(self, distances: torch.Tensor) -> torch.Tensor:
        """
        Args:
            distances: Tensor of shape (..., 1) containing pairwise distances.
        Returns:
            Tensor of shape (..., num_rbf) with RBF features.
        """
        # distances shape (..., 1)
        d = distances.unsqueeze(-1)  # (..., 1, 1)
        c = self.centers.to(distances.device)  # (num_rbf,)
        return torch.exp(-self.gamma * (d - c) ** 2)


class InteractionBlock(nn.Module):
    """
    A single interaction block as described in SchNet.  It updates atom
    embeddings by aggregating messages from neighbours using a continuous‑filter
    convolution (CFConv) built on top of an RBF expansion.
    """

    def __init__(self, hidden_dim: int, num_rbf: int, cutoff: float):
        super().__init__()
        self.rbf = RBFExpansion(num_rbf=num_rbf, cutoff=cutoff)
        self.filter_net = nn.Sequential(
            nn.Linear(num_rbf, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )
        self.lin = nn.Linear(hidden_dim, hidden_dim)
        self.act = nn.SiLU()

    def forward(
        self,
        x: torch.Tensor,
        pos: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:
            x: Atom embeddings, shape (N, hidden_dim)
            pos: Cartesian coordinates, shape (N, 3)
            edge_index: Tensor of shape (2, E) with source and target atom indices.
        Returns:
            Updated atom embeddings, shape (N, hidden_dim)
        """
        src, dst = edge_index
        # compute distance vectors and distances
        dist_vec = pos[dst] - pos[src]  # (E, 3)
        distances = torch.norm(dist_vec, dim=1, keepdim=True)  # (E, 1)

        # radial basis expansion
        rbf = self.rbf(distances)  # (E, num_rbf)

        # filter network
        W = self.filter_net(rbf)  # (E, hidden_dim)

        # message = W * x_src
        msg = W * x[src]  # (E, hidden_dim)

        # aggregate messages per target atom
        agg = torch.zeros_like(x)
        agg = agg.index_add_(0, dst, msg)

        # linear transformation + residual
        out = self.lin(agg) + x
        return self.act(out)


class SchNetGNN(nn.Module):
    """
    Minimal SchNet‑style GNN for dipole moment regression.

    The architecture is intentionally lightweight to satisfy the CPU‑only
    requirement while still providing a graph‑convolutional backbone that
    respects 3‑D geometry.
    """

    def __init__(
        self,
        hidden_dim: int = 128,
        num_interactions: int = 3,
        num_rbf: int = 32,
        cutoff: float = 5.0,
        max_z: int = 100,
        num_targets: int = 1,
    ):
        """
        Args:
            hidden_dim: Dimensionality of atom embeddings.
            num_interactions: Number of interaction blocks.
            num_rbf: Number of radial basis functions.
            cutoff: Distance cutoff for neighbour search (Å).
            max_z: Maximum atomic number supported (defines embedding size).
            num_targets: Number of regression targets (1 for dipole magnitude).
        """
        super().__init__()
        self.hidden_dim = hidden_dim
        self.cutoff = cutoff
        self.embedding = nn.Embedding(max_z + 1, hidden_dim, padding_idx=0)
        self.interactions = nn.ModuleList(
            [
                InteractionBlock(hidden_dim, num_rbf, cutoff)
                for _ in range(num_interactions)
            ]
        )
        # read‑out MLP
        self.readout = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.SiLU(),
            nn.Linear(hidden_dim // 2, num_targets),
        )

    def _build_edge_index(self, pos: torch.Tensor) -> torch.Tensor:
        """
        Naïve O(N²) neighbour search respecting the cutoff.
        For small molecules (typical QM9 size) this is acceptable on CPU.
        Returns edge_index of shape (2, E).
        """
        N = pos.size(0)
        # compute pairwise distance matrix
        diff = pos.unsqueeze(1) - pos.unsqueeze(0)  # (N, N, 3)
        dist = torch.norm(diff, dim=-1)  # (N, N)
        # mask self‑loops and distances > cutoff
        mask = (dist > 0) & (dist <= self.cutoff)
        src, dst = torch.nonzero(mask, as_tuple=True)
        edge_index = torch.stack([src, dst], dim=0)  # (2, E)
        return edge_index

    def forward(
        self,
        z: torch.Tensor,
        pos: torch.Tensor,
        batch: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Args:
            z: Atomic numbers, shape (N_atoms,)
            pos: Cartesian coordinates, shape (N_atoms, 3)
            batch: Optional batch vector mapping atoms to molecules,
                   shape (N_atoms,).  If ``None`` a single‑molecule batch is
                   assumed.
        Returns:
            Tensor of shape (batch_size, num_targets) with predictions.
        """
        if batch is None:
            batch = torch.zeros(z.size(0), dtype=torch.long, device=z.device)

        # initial atom embeddings
        x = self.embedding(z)  # (N, hidden_dim)

        # build edge index respecting cutoff
        edge_index = self._build_edge_index(pos)

        # interaction blocks
        for block in self.interactions:
            x = block(x, pos, edge_index)

        # aggregate atom embeddings per molecule (mean pooling)
        batch_size = int(batch.max().item()) + 1
        # sum per batch
        batch_sum = torch.zeros(batch_size, self.hidden_dim, device=x.device)
        batch_sum = batch_sum.index_add_(0, batch, x)
        # count atoms per batch
        ones = torch.ones_like(batch, dtype=x.dtype).unsqueeze(1)
        batch_count = torch.zeros(batch_size, 1, device=x.device)
        batch_count = batch_count.index_add_(0, batch, ones)
        # avoid division by zero
        batch_mean = batch_sum / batch_count.clamp(min=1)

        # read‑out
        out = self.readout(batch_mean)  # (batch_size, num_targets)
        return out