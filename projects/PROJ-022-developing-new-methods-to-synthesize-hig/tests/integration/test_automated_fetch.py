"""
Integration tests for automated_fetch module.
Tests real data fetching capabilities.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion.automated_fetch import (
    fetch_openpolymer_data,
    load_manual_extraction_data,
    extract_automated_literature_data
)
from utils.errors import DataInsufficientError

class TestOpenPolymerFetch:
    """Tests for OpenPolymer dataset fetching."""
    
    def test_fetch_openpolymer_returns_dataframe(self):
        """Test that OpenPolymer fetch returns a non-empty DataFrame."""
        df = fetch_openpolymer_data()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0, "OpenPolymer dataset should contain records"
    
    def test_fetch_openpolymer_has_required_columns(self):
        """Test that the fetched data has expected columns."""
        df = fetch_openpolymer_data()
        # Check for at least some expected columns
        expected_cols = ['polymer_name', 'smiles', 'source']
        # The dataset might have different column names, so we check for existence
        assert 'source' in df.columns or 'Source' in df.columns, "Source column should exist"
        assert 'smiles' in df.columns or 'SMILES' in df.columns or 'smiles' in df.columns, "SMILES column should exist"

class TestManualExtraction:
    """Tests for manual extraction loading."""
    
    def test_load_manual_returns_dataframe_or_empty(self):
        """Test that manual extraction load returns a DataFrame."""
        df = load_manual_extraction_data()
        assert isinstance(df, pd.DataFrame)
        # It might be empty if no manual data exists, but it should be a DataFrame

class TestAutomatedExtraction:
    """Tests for the full automated extraction pipeline."""
    
    def test_extract_combined_data(self):
        """Test that the full extraction pipeline works."""
        df = extract_automated_literature_data()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0, "Combined dataset should contain records"
        assert 'source' in df.columns, "Source column should exist in combined data"
    
    def test_output_file_created(self):
        """Test that the output file is created."""
        # Run the extraction
        df = extract_automated_literature_data()
        
        # Check if file exists
        output_path = Path("data/raw/automated_literature_data.csv")
        assert output_path.exists(), "Output CSV file should be created"
        
        # Verify file is not empty
        file_size = output_path.stat().st_size
        assert file_size > 0, "Output file should not be empty"
        
        # Verify it can be read back
        reloaded_df = pd.read_csv(output_path)
        assert len(reloaded_df) == len(df), "Reloaded dataframe should match original"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])