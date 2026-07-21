"""
Integration tests for the Manual Curator module.
"""
import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys
import logging

# Add code/src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.ingestion.manual_curator import load_manual_curated_data, DEFAULT_DATA_PATH

@pytest.fixture
def temp_csv_dir():
    """Create a temporary directory for CSV files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_missing_file_graceful_degradation(temp_csv_dir, caplog):
    """Test that a missing file returns an empty DataFrame and logs a warning."""
    non_existent_path = temp_csv_dir / "missing.csv"
    
    with caplog.at_level(logging.WARNING):
        df = load_manual_curated_data(file_path=non_existent_path)
    
    assert df.empty, "Expected empty DataFrame for missing file"
    assert "graceful degradation" in caplog.text or "not found" in caplog.text
    assert len(df) == 0

def test_load_empty_file(temp_csv_dir):
    """Test that an empty file returns an empty DataFrame."""
    empty_file = temp_csv_dir / "empty.csv"
    empty_file.touch()
    
    df = load_manual_curated_data(file_path=empty_file)
    
    assert df.empty, "Expected empty DataFrame for empty file"

def test_load_valid_csv(temp_csv_dir):
    """Test loading a valid CSV file with data."""
    valid_file = temp_csv_dir / "valid.csv"
    data = {
        "composition": ["Co2MnGa", "Co2FeAl"],
        "coercivity_oe": [120.5, 85.3],
        "saturation_magnetization_emu_g": [450.2, 390.1]
    }
    df_data = pd.DataFrame(data)
    df_data.to_csv(valid_file, index=False)
    
    df = load_manual_curated_data(file_path=valid_file)
    
    assert not df.empty
    assert len(df) == 2
    assert list(df.columns) == list(data.keys())
    assert df.iloc[0]["composition"] == "Co2MnGa"

def test_load_csv_missing_required_columns(temp_csv_dir, caplog):
    """Test loading a CSV with missing required columns logs a warning."""
    file_path = temp_csv_dir / "partial.csv"
    data = {
        "composition": ["Co2MnGa"],
        "coercivity_oe": [120.5]
        # Missing other columns
    }
    pd.DataFrame(data).to_csv(file_path, index=False)
    
    required = ["composition", "coercivity_oe", "missing_col"]
    
    with caplog.at_level(logging.WARNING):
        df = load_manual_curated_data(file_path=file_path, required_columns=required)
    
    assert not df.empty
    assert "Missing required columns" in caplog.text

def test_load_malformed_csv(temp_csv_dir):
    """Test that a malformed CSV raises ValueError."""
    malformed_file = temp_csv_dir / "malformed.csv"
    with open(malformed_file, "w") as f:
        f.write("composition,coercivity\nCo2MnGa\nThis is not valid CSV\n")
    
    with pytest.raises(ValueError) as excinfo:
        load_manual_curated_data(file_path=malformed_file)
    
    assert "Malformed" in str(excinfo.value)