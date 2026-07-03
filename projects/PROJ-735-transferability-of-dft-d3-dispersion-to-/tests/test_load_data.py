"""
Tests for the load_data module.
"""
import os
import tempfile
import zipfile
import pandas as pd
from pathlib import Path
import pytest

# Import the module under test
# We assume the module is in the 'code' directory relative to the test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from load_data import calculate_sha256, validate_checksums, load_synthetic_dataset

def test_calculate_sha256():
    """Test SHA-256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = f.name

    try:
        checksum = calculate_sha256(Path(temp_path))
        # Known SHA-256 for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected, f"Expected {expected}, got {checksum}"
    finally:
        os.unlink(temp_path)

def test_validate_checksums_missing_file():
    """Test validation when a file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        is_valid, results = validate_checksums(data_dir, expected_checksums={"missing.txt": "abc"})
        assert not is_valid
        assert results["missing.txt"] == "MISSING"

def test_validate_checksums_success():
    """Test validation when files exist and match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        # Create a dummy file
        test_file = data_dir / "test.txt"
        test_file.write_text("content")
        
        checksum = calculate_sha256(test_file)
        is_valid, results = validate_checksums(data_dir, expected_checksums={"test.txt": checksum})
        assert is_valid
        assert results["test.txt"] == checksum

def test_load_synthetic_dataset_missing_files():
    """Test loading when files are missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        with pytest.raises(FileNotFoundError):
            load_synthetic_dataset(data_dir)

def test_load_synthetic_dataset_success():
    """Test loading a valid synthetic dataset structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        
        # Create a dummy ZIP with an XYZ file
        zip_path = data_dir / "IL-Benchmark-local.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("ion_pairs.xyz", """2
            Pair 1
            H 0.0 0.0 0.0
            H 0.0 0.0 0.74
            """)
        
        # Create a dummy CSV
        csv_path = data_dir / "experimental_bulk_properties.csv"
        df = pd.DataFrame({"pair_id": ["1"], "density": [1.0]})
        df.to_csv(csv_path, index=False)
        
        ion_pairs, bulk_props = load_synthetic_dataset(data_dir)
        
        assert len(ion_pairs) == 1
        assert len(bulk_props) == 1
        assert "pair_id" in ion_pairs.columns
        assert "density" in bulk_props.columns