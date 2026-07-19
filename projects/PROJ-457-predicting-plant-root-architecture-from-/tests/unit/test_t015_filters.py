import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data_ingestion import apply_filters, detect_source_type_column, set_p_n_available

class TestT015Filters:
    """
    Unit tests for T015 filtering logic.
    Tests are designed to run independently without external data.
    """

    def setup_method(self):
        """Create a mock DataFrame with various scenarios."""
        data = {
            'species': ['A', 'A', 'A', 'A', 'A', 'B', 'B', 'B', 'C', 'C', 'D', 'D', 'D', 'D', 'D', 'E', 'E', 'E', 'E', 'E'],
            'root_length': [10, 20, 30, 40, 50, 15, 25, 35, 5, 15, 10, 20, 30, 40, 50, 10, 20, 30, 40, 50],
            'phosphorus': [1.0, 2.0, 3.0, 4.0, 5.0, 1.5, 2.5, 3.5, np.nan, 1.5, 1.0, 2.0, 3.0, 4.0, 5.0, 1.0, 2.0, 3.0, 4.0, 5.0],
            'nitrogen': [10.0, 20.0, 30.0, 40.0, 50.0, 15.0, 25.0, 35.0, 10.0, np.nan, 10.0, 20.0, 30.0, 40.0, 50.0, 10.0, 20.0, 30.0, 40.0, 50.0],
            'data_source_type': ['field', 'field', 'manipulated', 'field', 'field', 'field', 'controlled', 'field', 'field', 'field', 'field', 'field', 'field', 'field', 'field', 'field', 'field', 'field', 'field', 'field']
        }
        self.df = pd.DataFrame(data)
        set_p_n_available(True)

    def test_detect_source_type_column_existing(self):
        """Test detection of standard data_source_type column."""
        col = detect_source_type_column(self.df)
        assert col == 'data_source_type'

    def test_detect_source_type_column_alias(self):
        """Test detection of source_type alias."""
        df_alias = self.df.rename(columns={'data_source_type': 'source_type'})
        col = detect_source_type_column(df_alias)
        assert col == 'source_type'

    def test_detect_source_type_column_missing(self):
        """Test ValueError when no source type column found."""
        df_no_col = self.df.drop(columns=['data_source_type'])
        with pytest.raises(ValueError):
            detect_source_type_column(df_no_col)

    def test_exclusion_manipulated(self):
        """Test that 'manipulated' rows are excluded."""
        filtered_df, stats = apply_filters(self.df.copy())
        assert stats['excluded_source_type'] == 1
        assert 'manipulated' not in filtered_df['data_source_type'].values

    def test_exclusion_controlled(self):
        """Test that 'controlled' rows are excluded."""
        filtered_df, stats = apply_filters(self.df.copy())
        assert stats['excluded_source_type'] >= 1 # At least the 'controlled' one
        assert 'controlled' not in filtered_df['data_source_type'].values

    def test_exclusion_missing_nutrients(self):
        """Test that rows with missing P/N are excluded."""
        filtered_df, stats = apply_filters(self.df.copy())
        assert stats['excluded_missing_nutrients'] == 2 # One P missing, one N missing

    def test_exclusion_low_sample_size(self):
        """Test that species with n<20 are excluded."""
        # In our mock, species 'C' has 2 rows, 'D' has 5, 'E' has 5
        # Only 'A' (5) and 'B' (3) are >= 20? No, all are < 20 in this small sample.
        # Let's adjust the mock to have at least one species >= 20
        # Actually, the test data has 5 rows for A, 3 for B, 2 for C, 5 for D, 5 for E.
        # None meet n>=20. So ALL should be excluded by species count.
        filtered_df, stats = apply_filters(self.df.copy())
        assert stats['excluded_low_sample_size'] == len(self.df) - stats['excluded_source_type'] - stats['excluded_missing_nutrients']
        assert len(filtered_df) == 0

    def test_species_counts_report_keys(self):
        """Test that the stats dict contains required keys."""
        _, stats = apply_filters(self.df.copy())
        assert 'total_species_input' in stats
        assert 'excluded_species_count' in stats
        assert 'excluded_species_list' in stats
        assert isinstance(stats['total_species_input'], int)
        assert isinstance(stats['excluded_species_count'], int)
        assert isinstance(stats['excluded_species_list'], list)

    def test_exclusion_logic_order(self):
        """Test that exclusions happen in the correct order."""
        # Create a DataFrame where order matters
        data = {
            'species': ['A'] * 25,
            'root_length': range(25),
            'phosphorus': [1.0] * 25,
            'nitrogen': [10.0] * 25,
            'data_source_type': ['manipulated'] * 5 + ['field'] * 20
        }
        df = pd.DataFrame(data)
        set_p_n_available(True)
        
        filtered_df, stats = apply_filters(df)
        
        # First, 5 'manipulated' should be removed -> 20 left
        # Then, check species count -> 20 >= 20, so kept
        # Result: 20 rows
        assert stats['excluded_source_type'] == 5
        assert len(filtered_df) == 20
        assert stats['excluded_low_sample_size'] == 0