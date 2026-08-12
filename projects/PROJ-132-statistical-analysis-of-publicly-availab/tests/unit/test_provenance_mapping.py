import pytest
import json
from pathlib import Path
import polars as pl
from src.data.preprocess import generate_provenance

@pytest.fixture
def sample_df():
    """Create a sample Polars DataFrame for testing."""
    data = {
        "species": ["Species_A", "Species_B"],
        "week": ["2020-10", "2020-11"],
        "grid_cell": ["1_2", "3_4"],
        "total_count": [100, 200],
        "first_checklist_id": ["CL_001", "CL_002"]
    }
    return pl.DataFrame(data)

@pytest.fixture
def temp_output_path(tmp_path):
    """Create a temporary path for the output JSON file."""
    return str(tmp_path / "row_mapping.json")

def test_generate_provenance_creates_file(sample_df, temp_output_path):
    """Test that generate_provenance creates the output file."""
    generate_provenance(sample_df, temp_output_path)
    assert Path(temp_output_path).exists()

def test_generate_provenance_schema(sample_df, temp_output_path):
    """Test that the generated JSON has the correct schema."""
    generate_provenance(sample_df, temp_output_path)
    
    with open(temp_output_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    
    assert isinstance(mapping, list)
    assert len(mapping) == len(sample_df)
    
    for record in mapping:
        assert "processed_row_id" in record
        assert "original_checklist_id" in record
        assert "species" in record
        assert "grid_cell" in record
        assert isinstance(record["processed_row_id"], str)
        assert isinstance(record["original_checklist_id"], str)
        assert isinstance(record["species"], str)
        assert isinstance(record["grid_cell"], str)

def test_generate_provenance_content(sample_df, temp_output_path):
    """Test that the content of the mapping is correct."""
    generate_provenance(sample_df, temp_output_path)
    
    with open(temp_output_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    
    # Check first record
    assert mapping[0]["original_checklist_id"] == "CL_001"
    assert mapping[0]["species"] == "Species_A"
    assert mapping[0]["grid_cell"] == "1_2"
    assert mapping[0]["processed_row_id"] == "0"
    
    # Check second record
    assert mapping[1]["original_checklist_id"] == "CL_002"
    assert mapping[1]["species"] == "Species_B"
    assert mapping[1]["grid_cell"] == "3_4"
    assert mapping[1]["processed_row_id"] == "1"