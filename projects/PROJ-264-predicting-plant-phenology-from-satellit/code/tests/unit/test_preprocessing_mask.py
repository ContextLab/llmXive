import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Ensure we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.preprocessing import mask_missing_phenology_labels, run_preprocessing

class TestMaskMissingPhenology:
    """
    Tests for T016: Handle missing phenology labels by masking rows.
    """

    def test_mask_missing_labels(self, tmp_path):
        """Test that missing labels are correctly masked and not imputed."""
        data = {
            'site_id': ['A', 'A', 'A', 'B', 'B', 'B'],
            'date': pd.date_range('2020-01-01', periods=6, freq='10D'),
            'ndvi': [0.1, 0.2, np.nan, 0.3, 0.4, 0.5],
            'phenology_date': [pd.Timestamp('2020-03-01'), pd.Timestamp('2020-03-01'), 
                               np.nan, pd.Timestamp('2020-04-01'), pd.Timestamp('2020-04-01'), np.nan]
        }
        df = pd.DataFrame(data)
        
        result = mask_missing_phenology_labels(df, phenology_col='phenology_date')
        
        # Check that the new column exists
        assert 'is_valid_label' in result.columns
        
        # Check that values are boolean
        assert result['is_valid_label'].dtype == bool
        
        # Check specific masks
        # Row 2 (index 2) has NaN phenology -> False
        assert result.iloc[2]['is_valid_label'] == False
        # Row 5 (index 5) has NaN phenology -> False
        assert result.iloc[5]['is_valid_label'] == False
        # Others should be True
        assert result.iloc[0]['is_valid_label'] == True
        assert result.iloc[1]['is_valid_label'] == True
        assert result.iloc[3]['is_valid_label'] == True
        assert result.iloc[4]['is_valid_label'] == True

        # Verify original data is NOT imputed (NaNs remain)
        assert pd.isna(result.iloc[2]['phenology_date'])
        assert pd.isna(result.iloc[5]['phenology_date'])

    def test_mask_all_missing(self):
        """Test behavior when all labels are missing."""
        data = {
            'site_id': ['A', 'A'],
            'date': pd.date_range('2020-01-01', periods=2, freq='10D'),
            'phenology_date': [np.nan, np.nan]
        }
        df = pd.DataFrame(data)
        result = mask_missing_phenology_labels(df)
        
        assert result['is_valid_label'].sum() == 0
        assert len(result) == 2

    def test_mask_none_missing(self):
        """Test behavior when no labels are missing."""
        data = {
            'site_id': ['A', 'A'],
            'date': pd.date_range('2020-01-01', periods=2, freq='10D'),
            'phenology_date': [pd.Timestamp('2020-03-01'), pd.Timestamp('2020-03-01')]
        }
        df = pd.DataFrame(data)
        result = mask_missing_phenology_labels(df)
        
        assert result['is_valid_label'].all()
        assert len(result) == 2

    def test_mask_missing_column_error(self):
        """Test that error is raised if phenology column is missing."""
        data = {
            'site_id': ['A', 'A'],
            'date': pd.date_range('2020-01-01', periods=2, freq='10D'),
            'ndvi': [0.1, 0.2]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="Required column 'phenology_date' not found"):
            mask_missing_phenology_labels(df, phenology_col='phenology_date')

    def test_run_preprocessing_integration(self, tmp_path):
        """Integration test for the full preprocessing pipeline including masking."""
        # Create input file
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        
        data = {
            'site_id': ['A', 'A', 'A', 'B', 'B', 'B'],
            'date': pd.date_range('2020-01-01', periods=6, freq='10D'),
            'ndvi': [0.1, 0.2, np.nan, 0.3, 0.4, 0.5],
            'phenology_date': [pd.Timestamp('2020-03-01'), pd.Timestamp('2020-03-01'), 
                               np.nan, pd.Timestamp('2020-04-01'), pd.Timestamp('2020-04-01'), np.nan]
        }
        df = pd.DataFrame(data)
        df.to_csv(input_file, index=False)
        
        # Run preprocessing
        run_preprocessing(str(input_file), str(output_file), phenology_col='phenology_date')
        
        # Verify output exists
        assert output_file.exists()
        
        # Verify output content
        result_df = pd.read_csv(output_file)
        assert 'is_valid_label' in result_df.columns
        assert result_df['is_valid_label'].sum() == 4  # 2 valid, 2 masked
        assert len(result_df) == 6  # No rows dropped, just masked
        assert pd.isna(result_df.iloc[2]['phenology_date']) # Original NaN preserved