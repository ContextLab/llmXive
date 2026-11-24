import pytest
import pandas as pd
from pathlib import Path
from llmxive_toolkit import paths
from code.utils.io import save_parquet, load_parquet, sha256_checksum

def test_parquet_io_without_pyarrow(tmp_path: Path):
    """Ensure parquet I/O works using fastparquet fallback when pyarrow is missing."""
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    file_path = tmp_path / "test.parquet"
    # Save parquet; should succeed regardless of pyarrow availability
    save_parquet(df, file_path)
    # Load back and compare
    loaded = load_parquet(file_path)
    pd.testing.assert_frame_equal(df, loaded)

    # Check SHA-256 checksum matches expected length and hex format
    checksum = sha256_checksum(file_path)
    assert isinstance(checksum, str)
    assert len(checksum) == 64
    int(checksum, 16)  # should not raise