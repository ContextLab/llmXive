"""
test_extract_3d_coords.py
-------------------------
Unit test for the 3‑D coordinate extraction routine.

The test follows a test‑first approach: it defines the expected behaviour
(return a NumPy array of shape (n_atoms, 3) with float values) before the
actual implementation exists. Consequently, the test will currently fail
(or error) until ``extract_3d_coordinates`` is properly implemented in
``code/data/preprocess_3d.py``.
"""

import os
import sys

import numpy as np
import pytest


# Ensure the code directory is on the import path
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../../code"))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Import the stub implementation
from data.preprocess_3d import extract_3d_coordinates


def test_extract_3d_coordinates_returns_numpy_array():
    """
    Provide a minimal mock molecule and assert that the extraction function
    returns a NumPy array of the correct shape and dtype.

    The mock molecule mimics the expected input format: a dictionary with a
    ``'positions'`` key holding an iterable of (x, y, z) tuples.
    """
    # Mock molecule with three atoms
    mock_molecule = {
        "positions": [
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        ]
    }

    # Call the function under test
    coords = extract_3d_coordinates(mock_molecule)

    # The function should return a NumPy ndarray of shape (3, 3)
    assert isinstance(coords, np.ndarray), "Result should be a NumPy array"
    assert coords.shape == (3, 3), f"Expected shape (3, 3), got {coords.shape}"
    assert coords.dtype == np.float64, "Array dtype should be float64"

    # Verify the coordinates match the input (within a tolerance)
    expected = np.array(mock_molecule["positions"], dtype=np.float64)
    np.testing.assert_allclose(coords, expected, rtol=1e-7, atol=1e-9)


# The following test ensures that the current stub raises NotImplementedError.
# It is expected to fail (error) until the real implementation is provided.
def test_extract_3d_coordinates_not_implemented():
    mock_molecule = {"positions": [(0.0, 0.0, 0.0)]}
    with pytest.raises(NotImplementedError):
        extract_3d_coordinates(mock_molecule)