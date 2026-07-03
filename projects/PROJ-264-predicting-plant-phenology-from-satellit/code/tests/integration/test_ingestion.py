"""
Integration test for T011: Satellite Data Ingestion.

This test verifies that the ingestion script runs without error (assuming
GEE credentials are available) and produces a valid CSV file with the expected schema.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import get_config
from src.data.ingestion import run_satellite_ingestion, save_ingested_data
from src.lib.utils import ensure_dir

@pytest.mark.integration
def test_ingestion_script_execution():
    """
    Test that the ingestion script can be executed and produces a file.
    Note: This test may be skipped if GEE credentials are not present in the environment.
    """
    # Skip if no GEE credentials
    if not os.environ.get("GOOGLE_EARTH_ENGINE_CREDENTIALS"):
        pytest.skip("GOOGLE_EARTH_ENGINE_CREDENTIALS not set. Skipping integration test.")

    try:
        # Run the ingestion
        df = run_satellite_ingestion()
        
        # Verify output file exists
        config = get_config()
        output_file = Path(config.get("paths", {}).get("processed_data", "data/processed")) / "sentinel_indices_2018_2023.csv"
        
        assert output_file.exists(), f"Output file {output_file} was not created."
        
        # Verify schema
        expected_columns = {"site_id", "date", "ndvi", "evi", "latitude", "longitude"}
        assert set(df.columns) == expected_columns, f"Columns mismatch: {set(df.columns)} vs {expected_columns}"
        
        # Verify data types
        assert pd.api.types.is_datetime64_any_dtype(df['date']), "Date column is not datetime."
        assert pd.api.types.is_numeric_dtype(df['ndvi']), "NDVI column is not numeric."
        assert pd.api.types.is_numeric_dtype(df['evi']), "EVI column is not numeric."
        
        # Verify no NaN in critical columns
        assert not df['ndvi'].isna().all(), "All NDVI values are NaN."
        
    except ImportError as e:
        # If GEE is not installed, skip
        pytest.skip(f"Google Earth Engine not installed: {e}")
    except Exception as e:
        pytest.fail(f"Ingestion script failed: {e}")

@pytest.mark.unit
def test_save_ingested_data_creates_file(tmp_path):
    """
    Test that save_ingested_data correctly writes a CSV and updates provenance.
    """
    output_dir = tmp_path / "test_data"
    output_file = output_dir / "test.csv"
    
    df = pd.DataFrame({
        "site_id": ["A", "B"],
        "date": pd.to_datetime(["2020-01-01", "2020-01-02"]),
        "ndvi": [0.5, 0.6],
        "evi": [0.2, 0.3],
        "latitude": [40.0, 41.0],
        "longitude": [-74.0, -75.0]
    })
    
    # Mock provenance to avoid side effects in unit test
    import src.data.provenance as prov
    original_add = prov.add_provenance_entry
    prov.add_provenance_entry = lambda **kwargs: None
    
    try:
        save_ingested_data(df, str(output_file), "test")
        
        assert output_file.exists()
        loaded_df = pd.read_csv(output_file)
        assert len(loaded_df) == 2
        assert list(loaded_df.columns) == list(df.columns)
    finally:
        prov.add_provenance_entry = original_add
