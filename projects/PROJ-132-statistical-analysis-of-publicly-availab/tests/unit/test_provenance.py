import pytest
import json
import hashlib
import tempfile
from pathlib import Path
import polars as pl

from src.data.preprocess import generate_provenance

def test_generate_provenance_creates_mapping():
    """Test that generate_provenance creates a valid mapping file."""
    # Create sample dataframe
    df = pl.DataFrame({
        "species": ["Swainson's Thrush", "Blackpoll Warbler"],
        "grid_cell": ["45.0_-120.5", "42.5_-71.0"],
        "checklist_id": ["checklist_001", "checklist_002"]
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "provenance.json"
        
        generate_provenance(df, str(output_path))
        
        assert output_path.exists()
        
        with open(output_path, "r") as f:
            mapping = json.load(f)
        
        assert len(mapping) == 2
        assert "processed_row_id" in mapping[0]
        assert "original_checklist_id" in mapping[0]
        assert "species" in mapping[0]
        assert "grid_cell" in mapping[0]

def test_provenance_hash_uniqueness():
    """Test that each processed_row_id is unique and correctly hashed."""
    df = pl.DataFrame({
        "species": ["Species A", "Species B"],
        "grid_cell": ["40.0_-100.0", "40.0_-100.0"],
        "checklist_id": ["check_001", "check_002"]
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "provenance.json"
        generate_provenance(df, str(output_path))
        
        with open(output_path, "r") as f:
            mapping = json.load(f)
        
        processed_ids = [record["processed_row_id"] for record in mapping]
        
        # All IDs should be unique
        assert len(processed_ids) == len(set(processed_ids))
        
        # Verify hash calculation for first record
        expected_hash_input = f"{mapping[0]['original_checklist_id']}0"
        expected_hash = hashlib.sha256(expected_hash_input.encode("utf-8")).hexdigest()
        assert mapping[0]["processed_row_id"] == expected_hash

def test_provenance_with_duplicate_checklist_ids():
    """Test that row index is included in hash for duplicate checklist_ids."""
    df = pl.DataFrame({
        "species": ["Species A", "Species A"],
        "grid_cell": ["40.0_-100.0", "40.0_-100.0"],
        "checklist_id": ["same_checklist", "same_checklist"]
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "provenance.json"
        generate_provenance(df, str(output_path))
        
        with open(output_path, "r") as f:
            mapping = json.load(f)
        
        # Even with same checklist_id, hashes should differ due to row index
        assert mapping[0]["processed_row_id"] != mapping[1]["processed_row_id"]