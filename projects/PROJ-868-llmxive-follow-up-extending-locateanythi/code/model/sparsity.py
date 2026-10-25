"""
Sparsity configuration utilities for the LocateAnything study.

This module defines a simple, deterministic mask generator that can be
used to restrict attention windows in vision‑transformer style models.
The implementation is deliberately lightweight and relies only on
NumPy; it does **not** depend on any specific model code so that it can
be unit‑tested in isolation.

The public API consists of the ``SparsityConfig`` class:

* ``window_size`` – integer specifying the side length of the square
  attention window (in patch units). ``0`` is a special value that
  denotes a *global* mask (all tokens attend to all others). ``1``
  therefore limits attention to the token itself (identity mask).

* ``num_patches`` – total number of patches in the image. The code
  assumes a square grid (i.e. ``sqrt(num_patches)`` is an integer). A
  ``ValueError`` is raised otherwise.

* ``mask`` – a ``bool`` NumPy array of shape ``(num_patches,
  num_patches)`` where ``True`` indicates that the source token may
  attend to the target token.

The mask is constructed such that each token can attend to all tokens
whose *grid* coordinates lie within a square window of side
``window_size`` centred on the token (excluding the token itself when
``window_size`` > 0). Edge tokens naturally have a smaller effective
window because the calculation respects image boundaries.

Example usage
-------------
>>> cfg = SparsityConfig(window_size=32, num_patches=256)  # 16×16 grid
>>> cfg.mask.shape
(256, 256)
>>> cfg.mask.sum()  # total number of allowed attentions
10496
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

__all__ = ["SparsityConfig"]


@dataclass
class SparsityConfig:
    """
    Configuration object that generates an attention mask based on a
    square window size.

    Parameters
    ----------
    window_size : int
        Size of the square attention window measured in **patches**.
        ``0`` denotes a global mask (every token can attend to every
        other token). ``1`` limits attention to the token itself.
    num_patches : int
        Total number of patches in the image. Must be a perfect square
        because we treat the patches as a 2‑D grid.
    """

    window_size: int
    num_patches: int

    def __post_init__(self) -> None:
        if self.window_size < 0:
            raise ValueError("window_size must be non‑negative")
        if self.num_patches <= 0:
            raise ValueError("num_patches must be a positive integer")
        # Ensure a square grid – this is a strict requirement for the
        # simple mask construction used in the study.
        sqrt = int(math.isqrt(self.num_patches))
        if sqrt * sqrt != self.num_patches:
            raise ValueError(
                f"num_patches ({self.num_patches}) is not a perfect square"
            )
        self._grid_dim = sqrt
        self.mask = self._create_mask()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _create_mask(self) -> np.ndarray:
        """
        Build the boolean mask.

        Returns
        -------
        np.ndarray
            A ``(num_patches, num_patches)`` boolean mask.
        """
        if self.window_size == 0:
            # Global mask – every token can attend to every other token.
            return np.ones((self.num_patches, self.num_patches), dtype=bool)

        # For non‑zero window sizes we construct a square window centred
        # on each token. Tokens whose Manhattan distance in the grid is
        # less than ``window_size`` in both row and column directions are
        # considered reachable.
        mask = np.zeros((self.num_patches, self.num_patches), dtype=bool)

        for src_idx in range(self.num_patches):
            src_row, src_col = divmod(src_idx, self._grid_dim)

            # Determine the allowable row/col range for the target token.
            row_min = max(0, src_row - self.window_size + 1)
            row_max = min(self._grid_dim, src_row + self.window_size)
            col_min = max(0, src_col - self.window_size + 1)
            col_max = min(self._grid_dim, src_col + self.window_size)

            # Vectorised assignment for the current source token.
            target_rows = np.arange(row_min, row_max)
            target_cols = np.arange(col_min, col_max)
            target_grid = np.add.outer(target_rows, target_cols * self._grid_dim)
            mask[src_idx, target_grid.ravel()] = True

        return mask

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_mask(self) -> np.ndarray:
        """
        Return the pre‑computed mask.

        Returns
        -------
        np.ndarray
            Boolean mask of shape ``(num_patches, num_patches)``.
        """
        return self.mask.copy()
