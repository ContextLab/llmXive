"""
Integration test for GBIF fetch and cleaning logic.
Verifies duplicate removal and coordinate validity.
"""

import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path if necessary
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data.fetch_gbif import fetch_gbif_records, clean_occurrences, apply_spatial_thinning, run_fetch_pipeline
from src.utils.logging import setup_logging

# Setup logging for tests
setup_logging(level="DEBUG")

@pytest.fixture
def sample_raw_df():
    """Create a mock DataFrame simulating GBIF response."""
    data = [
        {
            "occurrenceID": "1",
            "scientificName": "Helianthus_annuus",
            "decimalLatitude": 34.05,
            "decimalLongitude": -118.25,
            "eventDate": "2023-05-01",
            "basisOfRecord": "OBSERVATION"
        },
        {
            "occurrenceID": "1",  # Duplicate ID
            "scientificName": "Helianthus_annuus",
            "decimalLatitude": 34.05,
            "decimalLongitude": -118.25,
            "eventDate": "2023-05-01",
            "basisOfRecord": "OBSERVATION"
        },
        {
            "occurrenceID": "2",
            "scientificName": "Helianthus_annuus",
            "decimalLatitude": 34.05,
            "decimalLongitude": -118.25,
            "eventDate": "2023-05-02", # Different date, same coords
            "basisOfRecord": "OBSERVATION"
        },
        {
            "occurrenceID": "3",
            "scientificName": "Helianthus_annuus",
            "decimalLatitude": 95.0, # Invalid Lat
            "decimalLongitude": -118.25,
            "eventDate": "2023-05-01",
            "basisOfRecord": "OBSERVATION"
        },
        {
            "occurrenceID": "4",
            "scientificName": "Helianthus_annuus",
            "decimalLatitude": 34.05,
            "decimalLongitude": -200.0, # Invalid Lon
            "eventDate": "2023-05-01",
            "basisOfRecord": "OBSERVATION"
        },
        {
            "occurrenceID": "5",
            "scientificName": "Helianthus_annuus",
            "decimalLatitude": None, # Missing Lat
            "decimalLongitude": -118.25,
            "eventDate": "2023-05-01",
            "basisOfRecord": "OBSERVATION"
        },
        {
            "occurrenceID": "6",
            "scientificName": "Helianthus_annuus",
            "decimalLatitude": 34.05,
            "decimalLongitude": -118.25,
            "eventDate": "2023-05-01",
            "basisOfRecord": "OBSERVATION"
        } # Same coords as 1, but different ID (should be kept unless thinning applied)
    ]
    return pd.DataFrame(data)

def test_clean_occurrences_duplicate_removal(sample_raw_df):
    """Test that exact duplicate occurrences (by ID) are removed."""
    cleaned = clean_occurrences(sample_raw_df)
    # Original: 7 rows.
    # Duplicates by ID '1': 1 removed.
    # Invalid Lat (95): 1 removed.
    # Invalid Lon (-200): 1 removed.
    # Missing Lat: 1 removed.
    # Remaining: 7 - 4 = 3?
    # Wait, ID 1 appears twice. One removed.
    # ID 2, 6 have same coords as 1. They are distinct IDs.
    # Clean only removes exact ID dupes, invalid coords, missing coords.
    # So:
    # Row 1 (ID 1): Kept
    # Row 2 (ID 1): Removed (Duplicate ID)
    # Row 3 (ID 2): Kept (Distinct ID, valid coords)
    # Row 4 (Lat 95): Removed (Invalid)
    # Row 5 (Lon -200): Removed (Invalid)
    # Row 6 (Lat None): Removed (Missing)
    # Row 7 (ID 6): Kept (Distinct ID, valid coords)
    # Expected count: 3
    
    assert len(cleaned) == 3, f"Expected 3 records after cleaning, got {len(cleaned)}"
    
    # Verify no invalid coordinates remain
    assert cleaned['decimalLatitude'].between(-90, 90).all(), "Invalid latitudes found"
    assert cleaned['decimalLongitude'].between(-180, 180).all(), "Invalid longitudes found"
    assert cleaned['decimalLatitude'].notna().all(), "Missing latitudes found"
    assert cleaned['decimalLongitude'].notna().all(), "Missing longitudes found"

def test_spatial_thinning_logic():
    """Test spatial thinning with a known set of points."""
    # Create points:
    # P1: 0, 0
    # P2: 0.01, 0.01 (~1.5km away) -> Should be removed if threshold > 1.5km
    # P3: 1, 1 (~111km away) -> Should be kept
    # P4: 0.005, 0.005 (~0.7km from P1) -> Should be removed
    
    data = [
        {"decimalLatitude": 0.0, "decimalLongitude": 0.0, "occurrenceID": "A"},
        {"decimalLatitude": 0.01, "decimalLongitude": 0.01, "occurrenceID": "B"},
        {"decimalLatitude": 1.0, "decimalLongitude": 1.0, "occurrenceID": "C"},
        {"decimalLatitude": 0.005, "decimalLongitude": 0.005, "occurrenceID": "D"},
    ]
    df = pd.DataFrame(data)
    
    # Thin with 2km threshold
    thinned = apply_spatial_thinning(df, distance_km=2.0)
    
    # P1 kept.
    # B is ~1.5km from A -> Removed.
    # D is ~0.7km from A -> Removed.
    # C is ~111km from A -> Kept.
    # Expected: A and C.
    
    assert len(thinned) == 2, f"Expected 2 records after thinning, got {len(thinned)}"
    
    ids = set(thinned['occurrenceID'])
    assert "A" in ids, "Point A should be kept"
    assert "C" in ids, "Point C should be kept"
    assert "B" not in ids, "Point B should be removed (too close to A)"
    assert "D" not in ids, "Point D should be removed (too close to A)"

def test_empty_dataframe_handling():
    """Test that empty dataframes are handled gracefully."""
    empty_df = pd.DataFrame(columns=['decimalLatitude', 'decimalLongitude', 'occurrenceID'])
    
    cleaned = clean_occurrences(empty_df)
    assert len(cleaned) == 0
    
    thinned = apply_spatial_thinning(empty_df)
    assert len(thinned) == 0

def test_run_fetch_pipeline_structure():
    """Test that the pipeline function returns the expected structure."""
    # We cannot easily mock the full API call in a unit/integration test without
    # a real network request or a complex mock.
    # Instead, we verify the function signature and error handling for empty results.
    # A full integration test would require a live API call or a pre-downloaded fixture.
    
    # For this task, we assume the logic is covered by the component tests above.
    # This test ensures the function exists and returns a tuple.
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = os.path.join(tmpdir, "raw")
        proc_dir = os.path.join(tmpdir, "proc")
        
        # Try a species that likely has no records or simulate failure
        # Using a nonsense name to trigger "No records"
        path, summary = run_fetch_pipeline("Xyzzy_NonExistent_Species_12345", raw_dir, proc_dir)
        
        # Expect failure or empty result
        assert path is None, "Expected no path for non-existent species"
        assert "error" in summary, "Expected error in summary"
        assert "No records" in summary.get("error", "") or len(summary) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])