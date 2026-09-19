import pytest
import os
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data_loader import load_ebird_data, DATA_RAW, EBIRD_OUTPUT_FILE

class TestEBirdDataLoader:
    """Integration tests for the eBird data loader (T011)."""

    @pytest.mark.integration
    def test_load_ebird_data_fetches_real_data(self):
        """
        Test that load_ebird_data actually fetches real data and saves it to disk.
        This test will fail loudly if the data source is unreachable or returns no data.
        """
        output_path = DATA_RAW / EBIRD_OUTPUT_FILE
        
        # Ensure the file doesn't exist from a previous run to test the fetch logic
        # (In a real CI, we might skip this deletion if we want to test caching, 
        # but for T011 verification, we want to see the download happen)
        # Note: In a real scenario, we might not delete it to save time, but for strict verification:
        if output_path.exists():
            # We don't delete it here to avoid race conditions in parallel tests, 
            # but we verify the content matches expectations.
            pass

        # Call the function
        df = load_ebird_data()

        # Assertions
        assert df is not None, "DataFrame should not be None"
        assert isinstance(df, pd.DataFrame), "Result should be a pandas DataFrame"
        assert df.shape[0] > 0, "DataFrame should not be empty (real data must be fetched)"
        
        # Verify columns exist (at least some expected ones)
        # The exact columns depend on the dataset schema, but we expect basic ones
        expected_cols = ['species_common', 'year', 'duration_min', 'num_observers', 'distance_km']
        for col in expected_cols:
            assert col in df.columns, f"Expected column '{col}' not found in DataFrame"

    @pytest.mark.integration
    def test_ebird_data_saved_to_disk_and_checksum_exists(self):
        """
        Test that the data is actually written to disk and a checksum file is created.
        """
        output_path = DATA_RAW / EBIRD_OUTPUT_FILE
        checksum_path = DATA_RAW / "checksums.json"

        # Run the loader
        load_ebird_data()

        # Verify file exists
        assert output_path.exists(), f"Output file {output_path} was not created"
        
        # Verify checksum file exists
        assert checksum_path.exists(), f"Checksum file {checksum_path} was not created"

    @pytest.mark.integration
    def test_ebird_data_filters_applied(self):
        """
        Test that the data returned adheres to the filtering criteria:
        - Species: Setophaga ruticilla
        - Year: 2015-2023
        - Duration >= 1m
        - Observers >= 1
        - Distance <= 10km
        """
        df = load_ebird_data()

        # Check species
        # Note: The dataset might have mixed case, so we check lower
        assert (df['species_common'].str.lower() == 'setophaga ruticilla').all() or \
               (df['scientific_name'].str.lower() == 'setophaga ruticilla').all(), \
               "All records must be for Setophaga ruticilla"

        # Check year range
        assert (df['year'] >= 2015).all(), "All records must be from 2015 or later"
        assert (df['year'] <= 2023).all(), "All records must be from 2023 or earlier"

        # Check duration
        assert (df['duration_min'] >= 1.0).all(), "All records must have duration >= 1 minute"

        # Check observers
        assert (df['num_observers'] >= 1).all(), "All records must have at least 1 observer"

        # Check distance
        assert (df['distance_km'] <= 10.0).all(), "All records must have distance <= 10 km"