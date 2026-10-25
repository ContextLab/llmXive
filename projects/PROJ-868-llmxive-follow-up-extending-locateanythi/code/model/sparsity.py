"""
Sparsity configuration for the LocateAnything model.

The ``SparsityConfig`` class produces a binary attention mask that limits
each token's receptive field to a square window of ``window_size`` patches.
The mask is a ``numpy.ndarray`` of shape ``(N, N)`` where ``N`` is the
total number of tokens (including the class token).  The implementation
is deliberately simple – it partitions the token sequence into contiguous
windows of size ``window_size`` and allows full attention *within* a
window while masking attention *across* windows.

Special cases:
* ``window_size == 0`` – global attention (all entries ``True``).
* ``window_size == 1`` – identity mask (only self‑attention).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

@dataclass
class SparsityConfig:
    """
    Configuration object that generates an attention mask for a given
    ``window_size``.  ``window_size`` is interpreted as the number of
    tokens per square patch.  A value of ``0`` disables sparsity
    (global attention).  The ``mask`` method returns a ``bool`` array
    suitable for element‑wise multiplication with an attention matrix.
    """
    window_size: int

    def __post_init__(self) -> None:
        if not isinstance(self.window_size, int) or self.window_size < 0:
            raise ValueError("window_size must be a non‑negative integer")

    def mask(self, num_tokens: int) -> np.ndarray:
        """
        Return an ``(num_tokens, num_tokens)`` binary mask.

        Parameters
        ----------
        num_tokens: int
            Total number of tokens (including any class token).  The mask
            is square with this dimension.

        Returns
        -------
        np.ndarray
            Boolean mask where ``True`` indicates that attention is allowed.
        """
        if self.window_size == 0:
            # Global attention – everything is allowed.
            return np.ones((num_tokens, num_tokens), dtype=bool)

        if self.window_size == 1:
            # Identity mask – each token only attends to itself.
            return np.eye(num_tokens, dtype=bool)

        # For window sizes > 1 we create block‑diagonal masks.
        # Tokens are grouped into windows of size ``window_size``.
        # Tokens in the same window attend to each other; cross‑window
        # connections are masked out.
        mask = np.zeros((num_tokens, num_tokens), dtype=bool)

        # Number of full windows.
        num_windows = math.ceil(num_tokens / self.window_size)

        for w in range(num_windows):
            start = w * self.window_size
            end = min(start + self.window_size, num_tokens)
            mask[start:end, start:end] = True

        return mask
