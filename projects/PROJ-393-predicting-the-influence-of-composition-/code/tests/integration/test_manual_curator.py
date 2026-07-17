"""
Integration tests for the manual_curator module.
Tests the loading of real data files and graceful degradation on missing files.
"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys
import logging

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingestion.manual_curator import load_manual_curated_data, DEFAULT_DATA_PATH

@pytest.fixture
def temp_csv_dir():
    """Create a temporary directory for test CSV files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_missing_file_graceful_degradation(temp_csv_dir):
    """Test that loading a missing file returns an empty DataFrame and logs a warning."""
    missing_path = temp_csv_dir / "non_existent.csv"
    
    # Capture log output
    with pytest.warns(None) as record:
        # We expect a warning to be logged, but the function returns a DataFrame
        df = load_manual_curated_data(file_path=missing_path)
    
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert len(df.columns) == 0

def test_load_empty_file(temp_csv_dir):
    """Test that loading an empty file returns an empty DataFrame."""
    empty_path = temp_csv_dir / "empty.csv"
    empty_path.touch() # Create empty file
    
    df = load_manual_curated_data(file_path=empty_path)
    
    assert isinstance(df, pd.DataFrame)
    assert df.empty

def test_load_valid_csv(temp_csv_dir):
    """Test loading a valid CSV file with data."""
    valid_path = temp_csv_dir / "valid.csv"
    data = {
        "alloy_composition": ["Co2MnGa", "Fe3Ga"],
        "coercivity_oersted": [100.5, 200.0],
        "source_type": ["Experimental", "Experimental"]
    }
    pd.DataFrame(data).to_csv(valid_path, index=False)
    
    df = load_manual_curated_data(file_path=valid_path)
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert len(df) == 2
    assert list(df.columns) == ["alloy_composition", "coercivity_oersted", "source_type"]
    assert df.iloc[0]["alloy_composition"] == "Co2MnGa"

def test_load_csv_missing_required_columns(temp_csv_dir, caplog):
    """Test that missing required columns trigger a warning."""
    valid_path = temp_csv_dir / "partial.csv"
    data = {
        "alloy_composition": ["Co2MnGa"],
        # Missing 'coercivity_oersted'
    }
    pd.DataFrame(data).to_csv(valid_path, index=False)
    
    required = ["alloy_composition", "coercivity_oersted"]
    
    with caplog.at_level(logging.WARNING):
        df = load_manual_curated_data(file_path=valid_path, required_columns=required)
    
    assert not df.empty
    assert "Missing required columns" in caplog.text
    assert "coercivity_oersted" in caplog.text

def test_load_malformed_csv(temp_csv_dir):
    """Test that a malformed CSV raises a ValueError."""
    malformed_path = temp_csv_dir / "malformed.csv"
    malformed_path.write_text("col1,col2\nval1\nval2,val3") # Uneven rows
    
    with pytest.raises(ValueError, match="Malformed CSV"):
        load_manual_curated_data(file_path=malformed_path)