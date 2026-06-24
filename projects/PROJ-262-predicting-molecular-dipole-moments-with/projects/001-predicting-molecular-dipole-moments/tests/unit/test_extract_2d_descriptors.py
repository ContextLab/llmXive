"""
Unit test for the 2‑D descriptor extraction pipeline.

The test intentionally checks for non‑empty output and the presence of a
``fingerprint`` column. The current placeholder implementation in
``extract_2d_descriptors.py`` returns an empty DataFrame, so this test will
fail until a proper descriptor extraction routine is implemented.
"""

import pytest
import pandas as pd

# Import the function under test. The project root is on the PYTHONPATH
# when pytest runs, so we can import via the package-relative path.
from code.data.extract_2d_descriptors import extract_2d_descriptors


def test_extract_2d_descriptors_nonempty():
    """
    Verify that the descriptor extraction returns a non‑empty DataFrame with
    expected columns.

    The placeholder implementation returns an empty DataFrame, causing this
    test to fail. Once the real implementation is added, the test should
    pass.
    """
    # Provide a minimal dummy molecule representation; the concrete type is
    # irrelevant for the placeholder implementation.
    dummy_molecules = ["CC"]  # Simple ethane SMILES as a stand‑in.

    df = extract_2d_descriptors(dummy_molecules)

    # The result should be a pandas DataFrame.
    assert isinstance(df, pd.DataFrame), "Result should be a pandas DataFrame"

    # Expect at least one row (one per input molecule).
    assert not df.empty, "Descriptor DataFrame should not be empty"

    # Expect a column named 'fingerprint' (common for Morgan fingerprints).
    assert "fingerprint" in df.columns, "Missing expected column 'fingerprint'"