"""
Unit tests for the I/O utilities in ``code/utils/io.py``.
These tests verify that parquet files can be saved and loaded correctly
(without hard-requiring pyarrow), and that the SHA-256 checksum
functions operate as expected.
"""
import pandas as pd
import pytest
from pathlib import Path

from code.utils.io import (
    save_parquet,
    load_parquet,
    compute_sha256,
    sha256_checksum,
    verify_sha256,
    get_parquet_engine,
)


def test_save_and_load_parquet(tmp_path: Path):
    """Save a simple DataFrame to parquet and load it back."""
    df_original = pd.DataFrame({"col_a": [1, 2, 3], "col_b": ["x", "y", "z"]})

    parquet_path = tmp_path / "sample.parquet"

    save_parquet(df_original, parquet_path)

    assert parquet_path.is_file(), "Parquet file was not created"

    df_loaded = load_parquet(parquet_path)

    pd.testing.assert_frame_equal(df_original, df_loaded)


def test_parquet_engine_available():
    """A parquet engine (pyarrow or fastparquet) must be usable."""
    assert get_parquet_engine() in ("pyarrow", "fastparquet")


def test_sha256_checksum_and_verification(tmp_path: Path):
    """Compute a SHA-256 checksum for a parquet file and verify it."""
    df = pd.DataFrame({"x": [10, 20], "y": [0.1, 0.2]})
    parquet_path = tmp_path / "checksum_test.parquet"

    save_parquet(df, parquet_path)

    checksum = compute_sha256(parquet_path)

    assert isinstance(checksum, str) and len(checksum) == 64

    assert verify_sha256(parquet_path, checksum) is True
    assert verify_sha256(parquet_path, "0" * 64) is False

def test_sha256_checksum_alias(tmp_path: Path):
    """sha256_checksum is an alias of compute_sha256."""
    p = tmp_path / "blob.bin"
    p.write_bytes(b"hello world")
    assert sha256_checksum(p) == compute_sha256(p)
    assert sha256_checksum(p) == (
        "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    )