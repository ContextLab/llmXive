import os
import json
import tempfile
import pytest
import polars as pl
from pathlib import Path
from src.data.preprocess import generate_provenance

def test_generate_provenance_basic():
    """Test that generate_provenance creates the correct JSON structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "row_mapping.json")
        
        # Create a mock DataFrame
        data = {
            "checklist_id": ["CHK001", "CHK002", "CHK003"],
            "species": ["Turdus migratorius", "Turdus migratorius", "Setophaga ruticilla"],
            "lat": [40.1, 40.6, 35.2],
            "lon": [-75.1, -74.9, -80.5]
        }
        df = pl.DataFrame(data)
        
        generate_provenance(df, output_path)
        
        assert os.path.exists(output_path), "Output JSON file was not created."
        
        with open(output_path, "r") as f:
            mapping = json.load(f)
        
        assert isinstance(mapping, list), "Mapping should be a list."
        assert len(mapping) == 3, "Mapping should have 3 entries."
        
        # Check schema
        first_entry = mapping[0]
        assert "processed_row_id" in first_entry
        assert "original_checklist_id" in first_entry
        assert "species" in first_entry
        assert "grid_cell" in first_entry
        
        # Check values
        assert first_entry["original_checklist_id"] == "CHK001"
        assert first_entry["species"] == "Turdus migratorius"
        # Check grid cell calculation (0.5 resolution)
        # 40.1 -> 40.0, -75.1 -> -75.5 (floor logic) or -75.0? 
        # Logic in code: (lat / res).floor() * res
        # 40.1 / 0.5 = 80.2 -> floor 80 -> 40.0
        # -75.1 / 0.5 = -150.2 -> floor -151 -> -75.5
        assert "lat_40.0" in first_entry["grid_cell"]

def test_generate_provenance_empty():
    """Test that generate_provenance handles empty DataFrames."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "row_mapping.json")
        df = pl.DataFrame({"checklist_id": [], "species": [], "lat": [], "lon": []})
        
        generate_provenance(df, output_path)
        
        with open(output_path, "r") as f:
            mapping = json.load(f)
        
        assert len(mapping) == 0

def test_generate_provenance_existing_grid_cell():
    """Test that generate_provenance uses existing grid_cell column if present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "row_mapping.json")
        
        data = {
            "checklist_id": ["CHK001"],
            "species": ["Species A"],
            "grid_cell": ["custom_grid_X"]
        }
        df = pl.DataFrame(data)
        
        generate_provenance(df, output_path)
        
        with open(output_path, "r") as f:
            mapping = json.load(f)
        
        assert mapping[0]["grid_cell"] == "custom_grid_X"