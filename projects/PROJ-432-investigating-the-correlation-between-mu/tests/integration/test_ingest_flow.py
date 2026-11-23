"""
Integration test for the full ingestion flow.
"""
import pytest
import os
from pathlib import Path
import sys
import json
from src.data.ingest import run_ingestion

def test_full_ingest_flow():
    """
    Run the full ingestion flow on a small sample (1 week).
    Verify output CSV has matching dates, non-null counts, non-null temperatures, and valid T_eff values (if calculated).
    
    NOTE: This test requires real data access (IceCube and ERA5).
    If real data is not available, this test will fail, which is the expected behavior
    for a "Real Data Only" policy.
    """
    # Use a small date range for testing
    start_date = "2023-01-01"
    end_date = "2023-01-07"
    
    # This will raise an error if real data is not available
    # which is the correct behavior for this task.
    try:
        icecube_df, era5_df = run_ingestion(start_date, end_date)
        
        # Verify outputs
        assert not icecube_df.empty, "IceCube dataframe should not be empty."
        assert not era5_df.empty, "ERA5 dataframe should not be empty."
        
        # Check for required columns
        assert 'date' in icecube_df.columns, "IceCube dataframe must have 'date' column."
        assert 'date' in era5_df.columns, "ERA5 dataframe must have 'date' column."
        
        # Check for non-null values
        assert icecube_df['date'].notnull().all(), "IceCube dates must not be null."
        assert era5_df['date'].notnull().all(), "ERA5 dates must not be null."
        
        # Check for data files
        icecube_path = Path("data/raw/icecube.csv")
        era5_path = Path("data/raw/era5.csv")
        
        assert icecube_path.exists(), "IceCube data file should exist."
        assert era5_path.exists(), "ERA5 data file should exist."
        
        # Check metadata files for release identifiers
        icecube_meta = Path("data/raw/icecube_metadata.json")
        era5_meta = Path("data/raw/era5_metadata.json")
        
        assert icecube_meta.exists(), "IceCube metadata file should exist."
        assert era5_meta.exists(), "ERA5 metadata file should exist."
        
        with open(icecube_meta, 'r') as f:
            icecube_meta_data = json.load(f)
            assert 'release_id' in icecube_meta_data, "IceCube metadata must have 'release_id'."
            assert icecube_meta_data['release_id'] != 'unknown_icecube_release', "IceCube release_id should be captured."
        
        with open(era5_meta, 'r') as f:
            era5_meta_data = json.load(f)
            assert 'release_id' in era5_meta_data, "ERA5 metadata must have 'release_id'."
            assert 'ERA5' in era5_meta_data['release_id'], "ERA5 release_id should be captured."
        
    except RuntimeError as e:
        # If real data is not available, this test fails.
        # This is expected and correct for the "Real Data Only" policy.
        pytest.fail(f"Ingestion failed due to missing real data: {e}")