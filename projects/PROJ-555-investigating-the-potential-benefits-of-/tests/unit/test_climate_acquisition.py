"""
Unit tests for climate data acquisition logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_acquisition_climate import (
    load_site_coordinates,
    fetch_nasa_power_climate_data,
    merge_climate_data
)


def test_load_site_coordinates_missing_file():
    """Test that load_site_coordinates raises error if file missing."""
    # Ensure the file doesn't exist for this test
    fake_path = Path("data/raw/nonexistent_sites.csv")
    if fake_path.exists():
        fake_path.unlink()
    
    # We expect a FileNotFoundError
    with pytest.raises(FileNotFoundError):
        # Temporarily patch the function to look at a fake path?
        # Or just rely on the default path check.
        # Since load_site_coordinates hardcodes the path, we test the exception.
        load_site_coordinates()


def test_fetch_nasa_power_climate_data_structure():
    """
    Test that fetch_nasa_power_climate_data returns a DataFrame with expected structure.
    Note: This test actually hits the API. For a pure unit test, we would mock requests.
    However, per the "real data" constraint, we verify the logic works with a small subset.
    If the API is down, this test fails loudly (which is desired).
    """
    # Use a known location (e.g., Amazon) and a short date range to avoid rate limits/timeouts
    # 2000-01-01 to 2000-01-05
    df = fetch_nasa_power_climate_data(
        lat=-3.4653, 
        lon=-62.2159, 
        start_date="2000-01-01", 
        end_date="2000-01-05", 
        parameters=["PRECIPITATION", "T2M"]
    )
    
    assert isinstance(df, pd.DataFrame)
    assert "PRECIPITATION" in df.columns
    assert "T2M" in df.columns
    assert len(df) == 5
    assert not df.isna().all().all() # At least some data should be present


def test_merge_climate_data():
    """Test merging of site metadata with climate data."""
    # Create mock site data
    sites = pd.DataFrame({
        "site_id": ["SITE_A", "SITE_B"],
        "latitude": [-3.0, -4.0],
        "longitude": [-62.0, -63.0]
    })
    
    # Create mock climate data
    climate_a = pd.DataFrame({
        "date": pd.date_range("2000-01-01", periods=3),
        "PRECIPITATION": [1.0, 2.0, 3.0],
        "T2M": [290.0, 291.0, 292.0]
    }).set_index("date")
    
    climate_b = pd.DataFrame({
        "date": pd.date_range("2000-01-01", periods=3),
        "PRECIPITATION": [0.5, 1.5, 2.5],
        "T2M": [285.0, 286.0, 287.0]
    }).set_index("date")
    
    climate_map = {"SITE_A": climate_a, "SITE_B": climate_b}
    
    merged = merge_climate_data(sites, climate_map)
    
    assert len(merged) == 6 # 3 days * 2 sites
    assert "site_id" in merged.columns
    assert "latitude" in merged.columns
    assert "longitude" in merged.columns
    assert merged["site_id"].nunique() == 2
    assert set(merged["site_id"]) == {"SITE_A", "SITE_B"}
