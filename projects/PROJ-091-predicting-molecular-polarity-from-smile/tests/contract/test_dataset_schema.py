"""
Contract test for the descriptor matrix schema.

This test validates that the processed descriptor matrix parquet file
conforms to the expected schema defined in `tests/contract/validators.py`.

If the required file does not exist (e.g., because the upstream data
generation step has not yet been run), the test is skipped rather than
failing. This allows the contract suite to be executed early in the
pipeline while still providing full validation once the artifact is
present.
"""
import pytest
from pathlib import Path

import pandas as pd

# Import the Pydantic model and helper validator from the same package
from .validators import DescriptorMatrix, validate_descriptor_frame


def _get_descriptors_path() -> Path:
    """Return the absolute path to the descriptors parquet file."""
    return (
        Path(__file__).resolve().parents[2]
        / "data"
        / "processed"
        / "descriptors.parquet"
    )


def test_descriptor_matrix_schema():
    """
    Verify that the descriptor matrix file exists, contains the required
    metadata columns, and includes all descriptor columns listed in
    `descriptor_names.json`.
    """
    descriptors_path = _get_descriptors_path()
    if not descriptors_path.exists():
        pytest.skip(f"Descriptor matrix not found at {descriptors_path}")

    # Load the parquet file
    df = pd.read_parquet(descriptors_path)

    # Use the helper to assert column presence and correctness.
    # This will raise a ValueError if the schema does not match.
    descriptor_columns = validate_descriptor_frame(df)

    # Spot‑check a single row with the Pydantic model. The model allows
    # extra fields (the descriptor columns) but enforces the required
    # metadata fields.
    sample_row = df.iloc[0].to_dict()
    instance = DescriptorMatrix(**sample_row)

    # Basic sanity checks
    assert isinstance(instance, DescriptorMatrix)
    assert isinstance(descriptor_columns, list)
    assert len(descriptor_columns) > 0
