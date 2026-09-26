"""
Unit tests for code/ingestion/cleaner.py
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
import sys

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion.cleaner import DataCleaner
from config import get_max_elements, get_composition_sum_threshold, get_room_temp_threshold, get_room_temp_tolerance


class TestDataCleaner:
    """Tests for DataCleaner class functionality."""

    @pytest.fixture
    def sample_raw_data(self):
        """Create a sample dataframe with various edge cases."""
        return pd.DataFrame({
            'alloy_id': [1, 2, 3, 4, 5, 6],
            'Sn': [0.95, 0.60, 0.50, 0.90, 0.99, 0.80],
            'Ag': [0.03, 0.03, 0.03, 0.05, 0.01, 0.05],
            'Cu': [0.02, 0.03, 0.03, 0.05, 0.00, 0.05],
            'Bi': [0.00, 0.00, 0.00, 0.00, 0.00, 0.05],  # 4th element
            'In': [0.00, 0.00, 0.00, 0.00, 0.00, 0.05],  # 5th element
            'Pb': [0.00, 0.00, 0.00, 0.00, 0.00, 0.00],  # 6th element (exceeds max)
            'hardness_hv': [60.0, 25.0, np.nan, 45.0, 55.0, 30.0],
            'measurement_temp_c': [25.0, 25.0, 25.0, 30.0, 40.0, 25.0],
            'source': ['src1', 'src2', 'src3', 'src4', 'src5', 'src6']
        })

    @pytest.fixture
    def cleaner(self):
        """Create a DataCleaner instance."""
        return DataCleaner()

    def test_filter_by_max_elements(self, sample_raw_data, cleaner):
        """Test exclusion of alloys with > MAX_ELEMENTS."""
        max_elements = get_max_elements()
        # Record 6 has 6 elements with non-zero values (Sn, Ag, Cu, Bi, In, Pb)
        # It should be excluded
        
        # We need to simulate the composition columns detection
        composition_cols = ['Sn', 'Ag', 'Cu', 'Bi', 'In', 'Pb']
        
        # Count non-zero elements per row
        non_zero_counts = (sample_raw_data[composition_cols] > 0).sum(axis=1)
        
        # Record 6 should have 6 non-zero elements
        assert non_zero_counts.iloc[5] > max_elements
        
        # Apply filter
        filtered = cleaner._filter_by_max_elements(sample_raw_data, composition_cols, max_elements)
        
        # Record 6 should be excluded
        assert len(filtered) == len(sample_raw_data) - 1
        assert 6 not in filtered['alloy_id'].values

    def test_filter_by_composition_sum(self, sample_raw_data, cleaner):
        """Test exclusion of records with composition sum < threshold."""
        threshold = get_composition_sum_threshold()  # 95.0
        
        composition_cols = ['Sn', 'Ag', 'Cu', 'Bi', 'In', 'Pb']
        
        # Record 3 has Sn+Ag+Cu = 0.50+0.03+0.03 = 0.56 (56%) which is < 95%
        # It should be excluded
        
        sums = sample_raw_data[composition_cols].sum(axis=1)
        assert sums.iloc[2] < threshold
        
        # Apply filter
        filtered = cleaner._filter_by_composition_sum(sample_raw_data, composition_cols, threshold)
        
        # Record 3 should be excluded
        assert len(filtered) == len(sample_raw_data) - 1
        assert 3 not in filtered['alloy_id'].values

    def test_filter_room_temp_measurements(self, sample_raw_data, cleaner):
        """Test filtering for room temperature measurements."""
        temp_threshold = get_room_temp_threshold()  # 25.0
        temp_tolerance = get_room_temp_tolerance()  # 5.0
        
        composition_cols = ['Sn', 'Ag', 'Cu', 'Bi', 'In', 'Pb']
        
        # Record 4: 30.0 (within tolerance: 20-30)
        # Record 5: 40.0 (outside tolerance: 20-30)
        
        # Apply filter
        filtered = cleaner._filter_room_temp_measurements(
            sample_raw_data, 
            composition_cols, 
            temp_threshold, 
            temp_tolerance
        )
        
        # Record 5 (40.0 C) should be excluded
        assert len(filtered) == len(sample_raw_data) - 1
        assert 5 not in filtered['alloy_id'].values

    def test_standardize_hardness_units(self, cleaner):
        """Test hardness unit standardization."""
        # Assuming input is already in HV, no conversion needed
        # If conversion factors were defined, this would test them
        df = pd.DataFrame({'hardness_hv': [50.0, 60.0, 70.0]})
        result = cleaner._standardize_hardness_units(df)
        pd.testing.assert_frame_equal(result, df)

    def test_handle_missing_hardness(self, sample_raw_data, cleaner):
        """Test handling of missing hardness values."""
        composition_cols = ['Sn', 'Ag', 'Cu', 'Bi', 'In', 'Pb']
        
        # Record 3 has NaN hardness
        assert pd.isna(sample_raw_data['hardness_hv'].iloc[2])
        
        # Apply filter
        filtered = cleaner._handle_missing_hardness(sample_raw_data, composition_cols)
        
        # Record 3 should be excluded
        assert len(filtered) == len(sample_raw_data) - 1
        assert 3 not in filtered['alloy_id'].values

    def test_full_cleaning_pipeline(self, sample_raw_data, cleaner, tmp_path):
        """Test the complete cleaning pipeline."""
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        
        # Save raw data
        raw_path = output_dir / "solder_hardness_cleaned.csv"
        
        # Mock excluded records file path
        excluded_path = output_dir / "excluded_records.csv"
        
        # Run cleaning
        cleaned_df, excluded_df = cleaner.clean_data(
            sample_raw_data,
            str(output_dir),
            str(output_dir)
        )
        
        # Verify outputs exist
        assert cleaned_df is not None
        assert len(cleaned_df) > 0
        
        # Verify excluded records are tracked
        # Should have excluded records for:
        # - Record 3: low composition sum
        # - Record 5: temp out of range
        # - Record 6: too many elements
        # - Record 3: also missing hardness (but already excluded)
        
        # At minimum, we expect some exclusions
        assert len(excluded_df) >= 2

    def test_identify_manual_review_candidates(self, sample_raw_data, cleaner):
        """Test identification of manual review candidates."""
        composition_cols = ['Sn', 'Ag', 'Cu', 'Bi', 'In', 'Pb']
        temp_threshold = get_room_temp_threshold()
        temp_tolerance = get_room_temp_tolerance()
        
        # Record 4: 30.0 (within tolerance: 20-30) - NOT manual review
        # Record 5: 40.0 (outside tolerance: 20-30) - EXCLUDED, not manual review
        
        # Add a record that is in manual review range (30-35)
        sample_with_review = sample_raw_data.copy()
        sample_with_review.loc[7] = [
            7, 0.95, 0.03, 0.02, 0.00, 0.00, 0.00, 50.0, 32.0, 'src7'
        ]
        
        manual_review = cleaner._identify_manual_review_candidates(
            sample_with_review,
            composition_cols,
            temp_threshold,
            temp_tolerance
        )
        
        # Record 7 (32.0 C) should be in manual review
        assert len(manual_review) == 1
        assert manual_review['alloy_id'].iloc[0] == 7
