import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

# Mock the config import to avoid dependency on full project structure in test env
# In real execution, this would be: from code import loaders
# Here we assume the runner sets PYTHONPATH correctly or we import relative to root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code import loaders
from code.config import DATASET_LIST

def test_ensure_dirs():
    """Test that _ensure_dirs creates necessary directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the global DATA_RAW_DIR
        original_dir = loaders.DATA_RAW_DIR
        loaders.DATA_RAW_DIR = Path(tmpdir) / "raw"
        
        try:
            loaders._ensure_dirs()
            assert loaders.DATA_RAW_DIR.exists()
            assert (loaders.DATA_RAW_DIR.parent / "processed").exists()
        finally:
            loaders.DATA_RAW_DIR = original_dir

def test_compute_file_checksum():
    """Test checksum computation."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test data")
        f.flush()
        filepath = Path(f.name)
    
    try:
        checksum = loaders._compute_file_checksum(filepath)
        assert len(checksum) == 64  # SHA256 hex length
    finally:
        os.unlink(filepath)

def test_scan_for_pii():
    """Test PII detection."""
    df = pd.DataFrame({
        "normal": [1, 2, 3],
        "ssn": ["123-45-6789", "987-65-4321"],
        "email": ["test@example.com", "user@domain.org"]
    })
    
    pii_cols = loaders._scan_for_pii(df)
    assert "ssn" in pii_cols
    assert "email" in pii_cols
    assert "normal" not in pii_cols

def test_validate_dataset_counts():
    """Test that config has correct counts."""
    from code.config import validate_dataset_counts
    assert validate_dataset_counts() is True

def test_load_dataset_missing_target():
    """Test error when target column is missing."""
    # Create a mock dataset info with a non-existent target
    ds_info = {
        "id": "test_missing",
        "name": "Test Missing",
        "url": "https://example.com/data.csv",
        "type": "binary",
        "target_col": "non_existent_column"
    }
    
    # Create a fake CSV with different columns
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "raw"
        raw_dir.mkdir()
        file_path = raw_dir / "test_missing.csv"
        file_path.write_text("col_a,col_b\n1,2\n3,4")
        
        # Mock the URL fetch to do nothing, use existing file
        with patch.object(loaders, '_fetch_dataset', return_value=file_path):
            with patch.object(loaders, 'DATA_RAW_DIR', raw_dir):
                with pytest.raises(ValueError, match="Target column"):
                    loaders.load_dataset(ds_info)
