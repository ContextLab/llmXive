import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path to import ingest
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from ingest import merge_datasets, impute_missing_values, flag_missing_trait_data

class TestIngestMerge:
    """
    Test the merge logic for T014.
    Verifies row counts, column presence, and null handling in the unified dataset.
    """

    def test_merge_produces_unified_csv(self, tmp_path):
        """
        Mock the data loading functions to test the merge logic without real data.
        Since T013 is a prerequisite, we simulate the output of T013.
        """
        # Setup mock data
        mock_climate = pd.DataFrame({
            'reef_id': ['R1', 'R2', 'R3'],
            'lon': [10.0, 11.0, 12.0],
            'lat': [20.0, 21.0, 22.0],
            'sst_avg': [28.5, 29.0, 27.5],
            'dhw_avg': [1.0, 0.5, 2.0]
        })
        
        mock_traits = pd.DataFrame({
            'reef_id': ['R1', 'R2'], # R3 missing traits
            'thermal_tolerance': [2.5, 3.0],
            'species_count': [10, 15]
        })
        
        mock_reefs = pd.DataFrame({
            'reef_id': ['R1', 'R2', 'R3'],
            'lon': [10.0, 11.0, 12.0],
            'lat': [20.0, 21.0, 22.0],
            'name': ['Reef1', 'Reef2', 'Reef3']
        })
        
        mock_events = pd.DataFrame({
            'reef_id': ['R1', 'R3'],
            'bleaching_severity': ['high', 'medium']
        })

        # Patch the loader functions
        import ingest
        original_load_climate = ingest.load_noaa_sst_dhw
        original_load_traits = ingest.load_coral_traits
        original_load_reefs = ingest.load_unep_reefs
        original_load_events = ingest.load_reefbase_events

        ingest.load_noaa_sst_dhw = lambda: mock_climate
        ingest.load_coral_traits = lambda: mock_traits
        ingest.load_unep_reefs = lambda: mock_reefs
        ingest.load_reefbase_events = lambda: mock_events

        try:
            # Run merge
            result_df = ingest.merge_datasets()

            # Assertions
            assert len(result_df) == 3, f"Expected 3 rows (one per reef), got {len(result_df)}"
            assert 'reef_id' in result_df.columns
            assert 'lon' in result_df.columns
            assert 'lat' in result_df.columns
            assert 'sst_avg' in result_df.columns
            assert 'thermal_tolerance' in result_df.columns
            assert 'bleaching_severity' in result_df.columns

            # Check null handling: R3 should have NaN for thermal_tolerance
            r3_row = result_df[result_df['reef_id'] == 'R3']
            assert pd.isna(r3_row['thermal_tolerance'].iloc[0]), "R3 should have NaN for missing traits"
            
            # Check grid resolution
            assert 'grid_lat' in result_df.columns
            assert 'grid_lon' in result_df.columns

        finally:
            # Restore
            ingest.load_noaa_sst_dhw = original_load_climate
            ingest.load_coral_traits = original_load_traits
            ingest.load_unep_reefs = original_load_reefs
            ingest.load_reefbase_events = original_load_events

    def test_impute_missing_values(self):
        """Test imputation logic."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-04']),
            'value': [1.0, np.nan, 3.0]
        })
        result = impute_missing_values(df)
        # Forward fill should fill the nan with 1.0
        assert result['value'].iloc[1] == 1.0

    def test_flag_missing_trait_data(self):
        """Test flagging logic."""
        df = pd.DataFrame({
            'reef_id': ['R1', 'R2'],
            'thermal_tolerance': [2.5, np.nan]
        })
        result = flag_missing_trait_data(df)
        assert result['trait_missing_flag'].iloc[0] == False
        assert result['trait_missing_flag'].iloc[1] == True