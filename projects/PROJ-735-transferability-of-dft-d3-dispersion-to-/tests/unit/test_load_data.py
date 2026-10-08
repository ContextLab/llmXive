import pytest
import os
import tempfile
from pathlib import Path
import zipfile
import json
import pandas as pd

from load_data import load_synthetic_dataset, validate_checksums, _validate_xyz_content, _validate_csv_columns

def test_load_data_invalid_xyz():
    """Test that loading an invalid XYZ file raises ValueError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        zip_path = tmpdir / "invalid.zip"
        
        # Create a mock zip with invalid XYZ content
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Write an invalid XYZ file (non-numeric coordinates)
            invalid_xyz = "1\nTest\nC not_a_number not_a_number not_a_number\n"
            zf.writestr("invalid.xyz", invalid_xyz)
        
        # The load_synthetic_dataset function should raise a ValueError
        with pytest.raises(ValueError) as excinfo:
            load_synthetic_dataset(zip_path)
        
        assert "Invalid coordinate format" in str(excinfo.value) or "non-numeric" in str(excinfo.value).lower()

def test_load_data_valid_xyz():
    """Test that loading a valid XYZ file does not raise an error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        zip_path = tmpdir / "valid.zip"
        
        # Create a mock zip with valid XYZ content
        with zipfile.ZipFile(zip_path, 'w') as zf:
            valid_xyz = "1\nTest\nC 0.0 0.0 0.0\n"
            zf.writestr("valid.xyz", valid_xyz)
            # Also need a meta.json for the function to not fail on empty pairs
            meta = {"pair_id": "test", "reference_energy": 1.0}
            zf.writestr("test_meta.json", json.dumps(meta))
        
        # Create a dummy CSV file for bulk properties
        csv_path = tmpdir / "experimental_bulk_properties.csv"
        df = pd.DataFrame({
            "pair_id": ["test"],
            "density": [1.0],
            "viscosity": [1.0]
        })
        df.to_csv(csv_path, index=False)
        
        # This should succeed
        pairs, bulk = load_synthetic_dataset(zip_path)
        assert len(pairs) == 1
        assert bulk.shape[0] == 1

def test_load_data_missing_csv_columns():
    """Test that loading a CSV with missing columns raises ValueError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        zip_path = tmpdir / "missing_cols.zip"
        
        # Create a mock zip with valid XYZ
        with zipfile.ZipFile(zip_path, 'w') as zf:
            valid_xyz = "1\nTest\nC 0.0 0.0 0.0\n"
            zf.writestr("valid.xyz", valid_xyz)
            meta = {"pair_id": "test", "reference_energy": 1.0}
            zf.writestr("test_meta.json", json.dumps(meta))
        
        # Create a CSV with missing required columns
        csv_path = tmpdir / "experimental_bulk_properties.csv"
        df = pd.DataFrame({
            "id": ["test"],
            "value": [1.0]
            # Missing 'pair_id', 'density', 'viscosity'
        })
        df.to_csv(csv_path, index=False)
        
        # This should raise ValueError
        with pytest.raises(ValueError) as excinfo:
            load_synthetic_dataset(zip_path)
        
        assert "missing required columns" in str(excinfo.value).lower()

def test_validate_xyz_content_valid():
    """Test validation of valid XYZ content."""
    valid_xyz = "3\nComment\nH 0.0 0.0 0.0\nH 1.0 0.0 0.0\nH 0.0 1.0 0.0\n"
    assert _validate_xyz_content(valid_xyz) is True

def test_validate_xyz_content_invalid_coords():
    """Test validation rejects non-numeric coordinates."""
    invalid_xyz = "1\nComment\nC a b c\n"
    with pytest.raises(ValueError):
        _validate_xyz_content(invalid_xyz)

def test_validate_xyz_content_invalid_count():
    """Test validation rejects mismatched atom count."""
    invalid_xyz = "2\nComment\nH 0.0 0.0 0.0\n"  # Says 2, only 1 atom
    with pytest.raises(ValueError):
        _validate_xyz_content(invalid_xyz)

def test_validate_csv_columns_valid():
    """Test validation of DataFrame with required columns."""
    df = pd.DataFrame({
        "pair_id": [1],
        "density": [1.0],
        "viscosity": [1.0]
    })
    assert _validate_csv_columns(df, ["pair_id", "density", "viscosity"]) is True

def test_validate_csv_columns_missing():
    """Test validation rejects DataFrame with missing columns."""
    df = pd.DataFrame({
        "pair_id": [1],
        "density": [1.0]
        # Missing viscosity
    })
    with pytest.raises(ValueError) as excinfo:
        _validate_csv_columns(df, ["pair_id", "density", "viscosity"])
    assert "missing required columns" in str(excinfo.value).lower()