import pytest
import pandas as pd
import numpy as np
import os
import sys
import json

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.preprocessing import filter_residuals, handle_sparse_satellites, preprocess_slr_data

class TestHandleSparseSatellites:
    """Tests for T018 Exclusion Logic"""

    def test_excludes_satellite_below_threshold(self):
        """Verify satellites with < 500 points are excluded and logged."""
        # Create synthetic data: Sat A has 100 points, Sat B has 1000 points
        data = {
            'satellite_id': ['SatA'] * 100 + ['SatB'] * 1000,
            'timestamp': pd.date_range('2023-01-01', periods=1100),
            'range': np.random.rand(1100) * 10000 + 6000,
            'residual': np.random.rand(1100) * 0.01  # All within 1cm
        }
        df = pd.DataFrame(data)
        
        # Run exclusion
        cleaned_df, excluded_list = handle_sparse_satellites(df, min_points=500)
        
        # Assertions
        assert 'SatA' not in cleaned_df['satellite_id'].values, "SatA should be excluded"
        assert 'SatB' in cleaned_df['satellite_id'].values, "SatB should remain"
        assert 'SatA' in excluded_list, "SatA should be in excluded list"
        assert 'SatB' not in excluded_list, "SatB should not be in excluded list"
        assert len(cleaned_df) == 1000, "Only SatB data should remain"

    def test_no_exclusion_above_threshold(self):
        """Verify no exclusion if all satellites have >= 500 points."""
        data = {
            'satellite_id': ['SatA'] * 500 + ['SatB'] * 600,
            'timestamp': pd.date_range('2023-01-01', periods=1100),
            'range': np.random.rand(1100),
            'residual': np.random.rand(1100)
        }
        df = pd.DataFrame(data)
        
        cleaned_df, excluded_list = handle_sparse_satellites(df, min_points=500)
        
        assert len(excluded_list) == 0, "No satellites should be excluded"
        assert len(cleaned_df) == 1100, "All data should remain"

    def test_all_excluded_if_below_threshold(self):
        """Verify behavior when all satellites are sparse."""
        data = {
            'satellite_id': ['SatA'] * 100 + ['SatB'] * 200,
            'timestamp': pd.date_range('2023-01-01', periods=300),
            'range': np.random.rand(300),
            'residual': np.random.rand(300)
        }
        df = pd.DataFrame(data)
        
        cleaned_df, excluded_list = handle_sparse_satellites(df, min_points=500)
        
        assert len(cleaned_df) == 0, "All data should be excluded"
        assert set(excluded_list) == {'SatA', 'SatB'}, "Both should be excluded"

class TestFilterResiduals:
    """Tests for T016 Residual Filtering"""

    def test_filters_large_residuals(self):
        """Verify residuals > 2cm are removed."""
        data = {
            'id': [1, 2, 3, 4],
            'residual': [0.01, 0.025, 0.005, 0.03]  # 1, 3 ok; 2, 4 bad
        }
        df = pd.DataFrame(data)
        
        filtered = filter_residuals(df, residual_column='residual', threshold_m=0.02)
        
        assert len(filtered) == 2
        assert 2 not in filtered['id'].values
        assert 4 not in filtered['id'].values

class TestPreprocessingPipeline:
    """Integration test for the full pipeline"""

    def test_full_pipeline_exclusion(self):
        """Verify full pipeline correctly filters and excludes."""
        data = {
            'satellite_id': ['LAGEOS'] * 100 + ['ETALON'] * 1000, # LAGEOS too sparse
            'timestamp': pd.date_range('2023-01-01', periods=1100),
            'range': np.random.rand(1100) * 10000,
            'residual': np.random.rand(1100) * 0.05 # Some will be > 2cm
        }
        df = pd.DataFrame(data)
        
        cleaned_df, excluded = preprocess_slr_data(df)
        
        # Check exclusion
        assert 'LAGEOS' not in cleaned_df['satellite_id'].values
        assert 'LAGEOS' in excluded
        
        # Check residual filtering (implicit via count reduction if any > 2cm)
        # Note: LAGEOS is excluded first, so we only check ETALON residuals
        etalon_df = cleaned_df[cleaned_df['satellite_id'] == 'ETALON']
        assert all(etalon_df['residual'] <= 0.02)