"""
Unit tests for the ingest module (TDD - written before implementation).

Tests verify:
1. Row counts in the unified dataset match the intersection of reefs and species.
2. Critical columns (SST, DHW, thermal_tolerance, bleaching_label) are present.
3. Null handling is correct (no nulls in critical columns).
"""
import os
import sys
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Add the project root to the path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from ingest import merge_datasets

# Mock data generators for unit testing without downloading real data
def create_mock_noaa_data(n_rows=100):
    """Generate mock NOAA SST/DHW data."""
    data = {
        'reef_id': [f'REEF_{i}' for i in range(n_rows)],
        'year': [2023] * n_rows,
        'month': list(range(1, 13)) * (n_rows // 12) + [1] * (n_rows % 12),
        'sst': np.random.uniform(28.0, 30.5, n_rows),
        'dhw': np.random.uniform(0.0, 8.0, n_rows),
    }
    return pd.DataFrame(data)

def create_mock_coral_traits(n_rows=50):
    """Generate mock Coral Trait Database data."""
    data = {
        'species_id': [f'SPEC_{i}' for i in range(n_rows)],
        'thermal_tolerance': np.random.uniform(1.0, 3.0, n_rows),
        'bleaching_response': np.random.choice(['resistant', 'sensitive', 'unknown'], n_rows),
    }
    return pd.DataFrame(data)

def create_mock_unep_reefs(n_rows=100):
    """Generate mock UNEP Reef geometries data."""
    data = {
        'reef_id': [f'REEF_{i}' for i in range(n_rows)],
        'lat': np.random.uniform(-30.0, 30.0, n_rows),
        'lon': np.random.uniform(0.0, 180.0, n_rows),
        'region': np.random.choice(['Western Pacific', 'Eastern Pacific', 'Indian Ocean', 'Caribbean'], n_rows),
    }
    return pd.DataFrame(data)

def create_mock_reefbase_events(n_rows=50):
    """Generate mock ReefBase bleaching events data."""
    data = {
        'reef_id': [f'REEF_{i}' for i in range(n_rows)],
        'year': [2023] * n_rows,
        'bleaching_severity': np.random.choice(['none', 'low', 'medium', 'high'], n_rows),
    }
    return pd.DataFrame(data)

class TestIngestMerge:
    """Tests for the merge_datasets function."""

    def test_row_count_intersection(self):
        """Verify row counts match the intersection of reefs and species."""
        # Create mock data with overlapping reef IDs
        mock_noaa = create_mock_noaa_data(n_rows=100)
        mock_traits = create_mock_coral_traits(n_rows=50)
        mock_reefs = create_mock_unep_reefs(n_rows=100)
        mock_events = create_mock_reefbase_events(n_rows=50)

        # Manually set overlapping reef IDs for testing
        mock_noaa['reef_id'] = [f'REEF_{i}' for i in range(50)]  # 50 unique reefs
        mock_reefs['reef_id'] = [f'REEF_{i}' for i in range(50)]  # Same 50 reefs
        
        # Traits should be associated with species, not reefs directly in this mock
        # The merge logic should handle this appropriately
        
        # Perform the merge
        unified_df = merge_datasets(
            noaa_df=mock_noaa,
            traits_df=mock_traits,
            reefs_df=mock_reefs,
            events_df=mock_events
        )

        # The unified dataset should have rows for each reef-species combination
        # For this mock, we expect at least 50 rows (one per reef)
        assert len(unified_df) >= 50, f"Expected at least 50 rows, got {len(unified_df)}"

    def test_critical_columns_present(self):
        """Verify critical columns are present in the unified dataset."""
        mock_noaa = create_mock_noaa_data(n_rows=100)
        mock_traits = create_mock_coral_traits(n_rows=50)
        mock_reefs = create_mock_unep_reefs(n_rows=100)
        mock_events = create_mock_reefbase_events(n_rows=50)

        unified_df = merge_datasets(
            noaa_df=mock_noaa,
            traits_df=mock_traits,
            reefs_df=mock_reefs,
            events_df=mock_events
        )

        critical_columns = ['sst', 'dhw', 'thermal_tolerance', 'bleaching_label']
        missing_cols = [col for col in critical_columns if col not in unified_df.columns]
        
        assert len(missing_cols) == 0, f"Missing critical columns: {missing_cols}"

    def test_no_nulls_in_critical_columns(self):
        """Verify no null values in critical columns."""
        mock_noaa = create_mock_noaa_data(n_rows=100)
        mock_traits = create_mock_coral_traits(n_rows=50)
        mock_reefs = create_mock_unep_reefs(n_rows=100)
        mock_events = create_mock_reefbase_events(n_rows=50)

        unified_df = merge_datasets(
            noaa_df=mock_noaa,
            traits_df=mock_traits,
            reefs_df=mock_reefs,
            events_df=mock_events
        )

        critical_columns = ['sst', 'dhw', 'thermal_tolerance', 'bleaching_label']
        
        for col in critical_columns:
            null_count = unified_df[col].isnull().sum()
            assert null_count == 0, f"Column '{col}' has {null_count} null values"

    def test_data_types_correct(self):
        """Verify data types are correct for critical columns."""
        mock_noaa = create_mock_noaa_data(n_rows=100)
        mock_traits = create_mock_coral_traits(n_rows=50)
        mock_reefs = create_mock_unep_reefs(n_rows=100)
        mock_events = create_mock_reefbase_events(n_rows=50)

        unified_df = merge_datasets(
            noaa_df=mock_noaa,
            traits_df=mock_traits,
            reefs_df=mock_reefs,
            events_df=mock_events
        )

        # Check numeric columns are numeric
        assert pd.api.types.is_numeric_dtype(unified_df['sst']), "SST should be numeric"
        assert pd.api.types.is_numeric_dtype(unified_df['dhw']), "DHW should be numeric"
        assert pd.api.types.is_numeric_dtype(unified_df['thermal_tolerance']), "Thermal tolerance should be numeric"

        # Check bleaching_label is categorical or string
        assert unified_df['bleaching_label'].dtype in ['object', 'category'], "Bleaching label should be categorical or string"

    def test_merge_with_missing_data(self):
        """Verify handling of missing data in source datasets."""
        # Create mock data with some missing values
        mock_noaa = create_mock_noaa_data(n_rows=100)
        mock_noaa.loc[0:9, 'sst'] = np.nan  # Introduce nulls in NOAA data
        
        mock_traits = create_mock_coral_traits(n_rows=50)
        mock_traits.loc[0:4, 'thermal_tolerance'] = np.nan  # Introduce nulls in traits
        
        mock_reefs = create_mock_unep_reefs(n_rows=100)
        mock_events = create_mock_reefbase_events(n_rows=50)

        # The merge function should handle missing data appropriately
        # (either by imputation or exclusion)
        unified_df = merge_datasets(
            noaa_df=mock_noaa,
            traits_df=mock_traits,
            reefs_df=mock_reefs,
            events_df=mock_events
        )

        # Verify critical columns still have no nulls after merge
        critical_columns = ['sst', 'dhw', 'thermal_tolerance', 'bleaching_label']
        for col in critical_columns:
            null_count = unified_df[col].isnull().sum()
            assert null_count == 0, f"Column '{col}' has {null_count} null values after merge"

    def test_reef_species_intersection(self):
        """Verify the dataset represents the correct intersection of reefs and species."""
        # Create mock data with specific reef and species combinations
        mock_noaa = create_mock_noaa_data(n_rows=100)
        mock_traits = create_mock_coral_traits(n_rows=50)
        mock_reefs = create_mock_unep_reefs(n_rows=100)
        mock_events = create_mock_reefbase_events(n_rows=50)

        # Set specific reef IDs for testing
        reef_ids = [f'REEF_{i}' for i in range(20)]
        mock_noaa['reef_id'] = reef_ids * 5  # 20 reefs, 5 records each
        mock_reefs['reef_id'] = reef_ids

        unified_df = merge_datasets(
            noaa_df=mock_noaa,
            traits_df=mock_traits,
            reefs_df=mock_reefs,
            events_df=mock_events
        )

        # Verify all reef IDs from the intersection are present
        assert set(unified_df['reef_id']).issubset(set(reef_ids)), "Unexpected reef IDs in unified dataset"
        assert len(unified_df['reef_id'].unique()) == 20, "Expected 20 unique reef IDs"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])