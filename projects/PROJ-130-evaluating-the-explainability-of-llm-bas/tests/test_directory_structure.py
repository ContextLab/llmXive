import os
import pytest
from pathlib import Path

def test_t001_data_directories_exist():
    """
    Verification test for T001:
    Ensure that 'data/' and 'data/defects4j/' directories exist.
    """
    root = Path(__file__).parent.parent
    
    data_dir = root / "data"
    defects4j_dir = root / "data" / "defects4j"

    assert data_dir.exists(), f"Directory missing: {data_dir}"
    assert data_dir.is_dir(), f"Path exists but is not a directory: {data_dir}"

    assert defects4j_dir.exists(), f"Directory missing: {defects4j_dir}"
    assert defects4j_dir.is_dir(), f"Path exists but is not a directory: {defects4j_dir}"