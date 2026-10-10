"""
Unit tests for the I/O utilities in ``code/utils/io.py``.
These tests verify that parquet files can be saved and loaded correctly,
and that the MD5 checksum functions operate as expected.
"""
import pandas as pd
import pytest
from pathlib import Path

# Import the utilities from the project's utils package
from utils.io import save_parquet, load_parquet, compute_md5, verify_md5


def test_save_and_load_parquet(tmp_path: Path):
    """Save a simple DataFrame to parquet and load it back."""
    # Create a small DataFrame
    df_original = pd.DataFrame({"col_a": [1, 2, 3], "col_b": ["x", "y", "z"]})

    # Define the output parquet path
    parquet_path = tmp_path / "sample.parquet"

    # Save the DataFrame
    save_parquet(df_original, parquet_path)

    # Ensure the file was created
    assert parquet_path.is_file(), "Parquet file was not created"

    # Load the DataFrame back
    df_loaded = load_parquet(parquet_path)

    # Verify that the loaded DataFrame matches the original
    pd.testing.assert_frame_equal(df_original, df_loaded)


def test_md5_checksum_and_verification(tmp_path: Path):
    """Compute an MD5 checksum for a parquet file and verify it."""
    df = pd.DataFrame({"x": [10, 20], "y": [0.1, 0.2]})
    parquet_path = tmp_path / "checksum_test.parquet"

    # Save the DataFrame so we have a real file on disk
    save_parquet(df, parquet_path)

    # Compute the checksum
    checksum = compute_md5(parquet_path)

    # The checksum should be a 32‑character hexadecimal string
    assert isinstance(checksum, str) and len(checksum) == 32

    # Verification should succeed with the correct checksum
    assert verify_md5(parquet_path, checksum) is True

    # Verification should fail with an incorrect checksum
    assert verify_md5(parquet_path, "0" * 32) is False
