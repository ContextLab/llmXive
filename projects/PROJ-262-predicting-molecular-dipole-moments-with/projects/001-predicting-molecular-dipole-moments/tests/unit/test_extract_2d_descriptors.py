"""
Unit test for 2D descriptor generation (T014).

This test validates that the ``compute_fingerprints`` function from
``code.data.extract_2d_descriptors`` returns an array of the expected
shape and dtype for a small set of SMILES strings.
"""

from __future__ import annotations

import numpy as np

# Import the function under test.
from code.data.extract_2d_descriptors import compute_fingerprints


def test_compute_fingerprints_basic() -> None:
    """
    Verify that fingerprints are generated for a few known SMILES strings
    and that the output has the correct dimensions and dtype.
    """
    # A tiny, diverse set of molecules.
    smiles = [
        "CCO",          # ethanol
        "c1ccccc1",     # benzene
        "C[N+](C)(C)C", # tetramethylammonium
    ]

    n_bits = 1024
    fp_array = compute_fingerprints(smiles, n_bits=n_bits)

    # The result should be a NumPy ndarray.
    assert isinstance(fp_array, np.ndarray), "Output is not a NumPy array"

    # Shape should be (num_molecules, n_bits).
    assert fp_array.shape == (len(smiles), n_bits), (
        f"Expected shape {(len(smiles), n_bits)}, got {fp_array.shape}"
    )

    # dtype should be unsigned 8‑bit integer (0/1 values).
    assert fp_array.dtype == np.uint8, f"Unexpected dtype {fp_array.dtype}"

    # Values should be 0 or 1 only.
    unique_vals = np.unique(fp_array)
    assert set(unique_vals).issubset({0, 1}), (
        f"Fingerprint contains values outside {{0,1}}: {unique_vals}"
    )