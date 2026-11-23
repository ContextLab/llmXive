"""
Unit test for ``src.config`` seed definitions.

The test verifies that:
* Both ``MASK_DERIVATION_SEEDS`` and ``EVAL_SEEDS`` are lists.
* Their lengths match the declared constants ``N_MASK_SEEDS`` and
  ``N_EVAL_SEEDS``.
* The two seed lists are disjoint (no overlapping seed values).
"""

import pytest

from src.config import (
    MASK_DERIVATION_SEEDS,
    EVAL_SEEDS,
    N_MASK_SEEDS,
    N_EVAL_SEEDS,
)


def test_seed_lists_lengths_and_disjointness() -> None:
    """Check lengths and that the seed sets do not intersect."""
    # Basic type checks
    assert isinstance(MASK_DERIVATION_SEEDS, list), "MASK_DERIVATION_SEEDS must be a list"
    assert isinstance(EVAL_SEEDS, list), "EVAL_SEEDS must be a list"

    # Length checks against declared constants
    assert len(MASK_DERIVATION_SEEDS) == N_MASK_SEEDS, (
        f"Expected {N_MASK_SEEDS} mask‑derivation seeds, got {len(MASK_DERIVATION_SEEDS)}"
    )
    assert len(EVAL_SEEDS) == N_EVAL_SEEDS, (
        f"Expected {N_EVAL_SEEDS} evaluation seeds, got {len(EVAL_SEEDS)}"
    )

    # Disjointness check
    overlap = set(MASK_DERIVATION_SEEDS).intersection(EVAL_SEEDS)
    assert not overlap, f"Seed lists overlap: {overlap}"