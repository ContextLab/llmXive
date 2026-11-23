"""
Integration test for T017: Verify output files exist and contain valid data.
"""
import os
import sys
import pytest
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from ingestion.generate_outputs import main
from utils.exceptions import DataQualityError


@pytest.fixture(scope="module")
def run_t017():
    """Run T017 once for the test module."""
    # Ensure the script runs successfully
    try:
        main()
    except Exception as e:
        pytest.fail(f"T017 execution failed: {e}")


def test_merged_dataset_exists(run_t017):
    """Verify that merged_dataset.csv exists."""
    path = project_root / 'data' / 'processed' / 'merged_dataset.csv'
    assert path.exists(), f"File {path} does not exist."


def test_excluded_summary_exists(run_t017):
    """Verify that excluded_species_summary.csv exists."""
    path = project_root / 'data' / 'processed' / 'excluded_species_summary.csv'
    assert path.exists(), f"File {path} does not exist."


def test_merged_dataset_schema(run_t017):
    """Verify merged_dataset.csv has expected columns and non-empty data."""
    path = project_root / 'data' / 'processed' / 'merged_dataset.csv'
    df = pd.read_csv(path)
    
    assert not df.empty, "Merged dataset is empty."
    assert 'species_name' in df.columns, "Missing 'species_name' column."
    
    # Check for soil columns
    soil_cols = ['soil_n', 'soil_p', 'soil_k', 'soil_ph']
    for col in soil_cols:
        if col in df.columns:
            # Check for non-null values (should be all valid)
            assert df[col].notna().all(), f"Column {col} has null values in final dataset."


def test_excluded_summary_schema(run_t017):
    """Verify excluded_species_summary.csv has correct schema."""
    path = project_root / 'data' / 'processed' / 'excluded_species_summary.csv'
    df = pd.read_csv(path)
    
    if not df.empty:
        assert 'species_name' in df.columns, "Missing 'species_name' in summary."
        assert 'observation_count' in df.columns, "Missing 'observation_count' in summary."
        assert 'reason' in df.columns, "Missing 'reason' in summary."
        
        # Verify reason contains expected text
        assert df['reason'].str.contains('observation_count < 10').any(), \
            "No rows found with 'observation_count < 10' reason."


def test_species_filter_logic(run_t017):
    """Verify that no species in the final dataset has < 10 observations."""
    path = project_root / 'data' / 'processed' / 'merged_dataset.csv'
    df = pd.read_csv(path)
    
    counts = df.groupby('species_name').size()
    assert (counts >= 10).all(), "Found species with < 10 observations in final dataset."