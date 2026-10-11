import pytest
import pandas as pd
from pathlib import Path
import hashlib
from code.download import compute_sha256, cap_dataframe

def test_compute_sha256(tmp_path):
    """Test that SHA256 checksum is computed correctly."""
    test_file = tmp_path / "test.txt"
    content = b"hello world"
    test_file.write_bytes(content)
    
    expected_hash = hashlib.sha256(content).hexdigest()
    assert compute_sha256(test_file) == expected_hash

def test_cap_dataframe_oversize():
    """Test that dataframe is capped to 5000 samples with seed 42."""
    # Create a dataframe with 6000 rows
    df = pd.DataFrame({"a": range(6000)})
    capped_df = cap_dataframe(df)
    assert len(capped_df) == 5000
    
    # Verify reproducibility with seed 42
    df2 = pd.DataFrame({"a": range(6000)})
    capped_df2 = cap_dataframe(df2)
    pd.testing.assert_frame_equal(capped_df, capped_df2)

def test_cap_dataframe_undersize():
    """Test that dataframe is not capped if it's smaller than 5000."""
    df = pd.DataFrame({"a": range(100)})
    capped_df = cap_dataframe(df)
    assert len(capped_df) == 100
    pd.testing.assert_frame_equal(df, capped_df)