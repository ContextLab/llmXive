import pytest
import json
import hashlib
from pathlib import Path
import polars as pl
from datetime import datetime, timedelta
import tempfile
import os

from src.data.preprocess import generate_provenance

def test_generate_provenance_basic():
    """Test that generate_provenance creates the correct JSON mapping."""
    # Create a small mock DataFrame
    data = {
        "species": ["SpeciesA", "SpeciesB"],
        "grid_cell": ["45.0_-120.5", "45.5_-121.0"],
        "checklist_id": ["chk_001", "chk_002"],
        "count": [10, 20]
    }
    df = pl.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "row_mapping.json"
        generate_provenance(df, output_path)
        
        assert output_path.exists(), "Output file not created."
        
        with open(output_path, 'r') as f:
            mapping = json.load(f)
        
        assert isinstance(mapping, list), "Mapping should be a list of records."
        assert len(mapping) == 2, "Mapping should have 2 records."
        
        # Verify structure of first record
        rec = mapping[0]
        assert "processed_row_id" in rec
        assert "original_checklist_id" in rec
        assert "species" in rec
        assert "grid_cell" in rec
        
        # Verify hash correctness
        expected_hash_input = f"{rec['original_checklist_id']}0".encode('utf-8')
        expected_hash = hashlib.sha256(expected_hash_input).hexdigest()
        assert rec["processed_row_id"] == expected_hash, "Hash mismatch."
        
        assert rec["original_checklist_id"] == "chk_001"
        assert rec["species"] == "SpeciesA"

def test_generate_provenance_empty():
    """Test that generate_provenance handles empty DataFrame gracefully."""
    df = pl.DataFrame({"species": [], "grid_cell": [], "checklist_id": []})
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "row_mapping.json"
        generate_provenance(df, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            mapping = json.load(f)
        
        assert len(mapping) == 0

def test_generate_provenance_missing_checklist_id():
    """Test that generate_provenance raises error if checklist_id is missing."""
    df = pl.DataFrame({"species": ["A"], "grid_cell": ["45.0_-120.5"]})
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "row_mapping.json"
        with pytest.raises(ValueError, match="DataFrame must contain 'checklist_id' column"):
            generate_provenance(df, output_path)
