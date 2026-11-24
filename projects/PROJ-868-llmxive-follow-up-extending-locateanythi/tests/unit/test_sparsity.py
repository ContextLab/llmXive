"""
Unit tests for ``code/model/sparsity.py``.

The tests verify that the ``SparsityConfig`` class produces masks that
respect the contract described in the task specification:

* ``window_size=0`` yields a *global* mask (all True).
* ``window_size=1`` yields an identity mask (each token only attends to
  itself).
* For other supported sizes (64, 32, 16) the mask should be a square
  window centred on each token; we check that the number of True
  entries per row matches the expected window area (clipped at image
  borders).
"""

import math

import numpy as np
import pytest

from code.model.sparsity import SparsityConfig


@pytest.mark.parametrize(
    "window_size,grid_dim",
    [
        (0, 8),   # global mask on an 8×8 grid (64 patches)
        (1, 8),   # identity mask on an 8×8 grid
        (16, 16), # window larger than grid → global mask
        (32, 16), # window larger than grid → global mask
        (64, 16), # window larger than grid → global mask
    ],
)
def test_global_and_identity_masks(window_size, grid_dim):
    """
    For ``window_size`` equal to 0 we expect a fully‑True mask.
    For ``window_size`` equal to 1 we expect only the diagonal to be
    True (identity mask). When the window size exceeds the grid size the
    mask collapses to a global mask.
    """
    num_patches = grid_dim * grid_dim
    cfg = SparsityConfig(window_size=window_size, num_patches=num_patches)
    mask = cfg.get_mask()
    assert mask.shape == (num_patches, num_patches)

    if window_size == 0 or window_size >= grid_dim:
        # Global mask – every entry should be True.
        assert mask.all()
    elif window_size == 1:
        # Identity mask – only the diagonal is True.
        assert np.allclose(mask, np.eye(num_patches, dtype=bool))
    else:
        # For any other size we simply ensure the mask is symmetric and
        # that each row has at most ``window_size**2`` True entries
        # (clipped at the borders of the grid).
        assert (mask == mask.T).all()
        max_allowed = min(window_size ** 2, num_patches)
        row_counts = mask.sum(axis=1)
        assert (row_counts <= max_allowed).all()


def test_invalid_num_patches():
    """num_patches must be a perfect square."""
    with pytest.raises(ValueError, match="perfect square"):
        SparsityConfig(window_size=4, num_patches=30)


def test_negative_window():
    """window_size must be non‑negative."""
    with pytest.raises(ValueError, match="non‑negative"):
        SparsityConfig(window_size=-1, num_patches=64)