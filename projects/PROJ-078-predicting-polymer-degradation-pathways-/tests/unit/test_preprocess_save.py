"""
Unit tests for T016: Dataset saving with checksums.
"""
import os
import json
import hashlib
import tempfile
from pathlib import Path
import pytest
import pandas as pd

from data_models import PolymerRecord
from preprocess import compute_checksum, save_dataset

def test_compute_checksum():
    """Test checksum computation on a known file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = f.name

    try:
        checksum = compute_checksum(temp_path)
        # SHA-256 of "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected, f"Expected {expected}, got {checksum}"
    finally:
        os.unlink(temp_path)

def test_save_dataset_creates_files():
    """Test that save_dataset creates the expected CSV and checksum files."""
    records = [
        PolymerRecord(
            id="test_1",
            smiles="CC(=O)OC",
            temperature=25.0,
            ph=7.0,
            uv_intensity=100.0,
            degradation_pathway="hydrolysis",
            source="nist",
            num_atoms=10,
            num_bonds=9
        ),
        PolymerRecord(
            id="test_2",
            smiles="COC(=O)C",
            temperature=30.0,
            ph=6.5,
            uv_intensity=120.0,
            degradation_pathway="photolysis",
            source="materials_project",
            num_atoms=8,
            num_bonds=7
        )
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        result = save_dataset(records, output_dir, "test_output", include_checksums=True)

        # Check return dictionary
        assert "file_path" in result
        assert "checksum" in result
        assert "num_records" in result
        assert result["num_records"] == 2

        # Check CSV file exists
        csv_path = Path(result["file_path"])
        assert csv_path.exists(), f"CSV file not found: {csv_path}"

        # Check CSV content
        df = pd.read_csv(csv_path)
        assert len(df) == 2
        assert "id" in df.columns
        assert "smiles" in df.columns
        assert "degradation_pathway" in df.columns

        # Check checksum file exists
        checksum_path = Path(result["checksum_file"])
        assert checksum_path.exists(), f"Checksum file not found: {checksum_path}"

        # Verify checksum content matches
        with open(checksum_path, 'r') as f:
            content = f.read().strip()
        
        # Format should be: <checksum>  <filename>
        parts = content.split("  ")
        assert len(parts) == 2
        assert parts[0] == result["checksum"]

def test_save_dataset_without_checksums():
    """Test saving without checksum generation."""
    records = [
        PolymerRecord(
            id="test_1",
            smiles="CC(=O)OC",
            temperature=25.0,
            ph=7.0,
            uv_intensity=100.0,
            degradation_pathway="hydrolysis",
            source="nist",
            num_atoms=10,
            num_bonds=9
        )
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        result = save_dataset(records, output_dir, "test_no_checksum", include_checksums=False)

        assert "checksum" not in result
        assert "checksum_file" not in result
        
        csv_path = Path(result["file_path"])
        assert csv_path.exists()

def test_save_empty_dataset():
    """Test saving an empty list of records."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        result = save_dataset([], output_dir, "empty_test", include_checksums=True)
        
        assert result["num_records"] == 0
        
        csv_path = Path(result["file_path"])
        assert csv_path.exists()
        
        df = pd.read_csv(csv_path)
        assert len(df) == 0