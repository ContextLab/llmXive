import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import numpy as np

from code.data_ingestion import filter_and_impute, validate_rotation_period

class TestDataIngestion:
    """Unit tests for data ingestion filtering and imputation logic."""

    def test_filter_non_mdwarf(self):
        """Test that non-M-dwarf hosts are excluded."""
        df = pd.DataFrame({
            'spectral_type': ['M0', 'K5', 'M3', 'G2'],
            'flare_count': [15, 20, 12, 8],
            'mass': [0.5, 0.8, 0.4, 1.0],
            'radius': [0.5, 0.7, 0.4, 1.0],
            'semi_major_axis': [0.1, 0.2, 0.15, 0.3]
        })
        
        result = filter_and_impute(df)
        
        # Only M-dwarfs should remain
        assert all(result['spectral_type'].str.contains('M', case=False))
        assert len(result) == 2  # M0 and M3

    def test_filter_low_flare_count(self):
        """Test that systems with <10 flares are excluded."""
        df = pd.DataFrame({
            'spectral_type': ['M0', 'M1', 'M2'],
            'flare_count': [5, 15, 8],
            'mass': [0.5, 0.6, 0.4],
            'radius': [0.5, 0.6, 0.4],
            'semi_major_axis': [0.1, 0.15, 0.1]
        })
        
        result = filter_and_impute(df)
        
        # Only M1 with 15 flares should remain
        assert len(result) == 1
        assert result.iloc[0]['flare_count'] == 15

    def test_filter_missing_values(self):
        """Test that records with missing mass, radius, or semi_major_axis are excluded."""
        df = pd.DataFrame({
            'spectral_type': ['M0', 'M1', 'M2'],
            'flare_count': [15, 20, 12],
            'mass': [0.5, np.nan, 0.4],
            'radius': [0.5, 0.6, np.nan],
            'semi_major_axis': [0.1, 0.15, 0.1]
        })
        
        result = filter_and_impute(df)
        
        # Only M0 with complete data should remain
        assert len(result) == 1
        assert result.iloc[0]['spectral_type'] == 'M0'

    def test_impute_missing_age(self):
        """Test that missing system_age is imputed with DEFAULT_M_DWARF_AGE."""
        from code import config
        
        df = pd.DataFrame({
            'spectral_type': ['M0', 'M1'],
            'flare_count': [15, 20],
            'mass': [0.5, 0.6],
            'radius': [0.5, 0.6],
            'semi_major_axis': [0.1, 0.15],
            'system_age': [5.0, np.nan]
        })
        
        result = filter_and_impute(df)
        
        assert result.iloc[0]['system_age'] == 5.0
        assert result.iloc[1]['system_age'] == config.DEFAULT_M_DWARF_AGE

    def test_validate_rotation_period_present(self):
        """Test validation when Rotation Period column is present."""
        df = pd.DataFrame({
            'Rotation Period': [10.0, 20.0],
            'mass': [0.5, 0.6]
        })
        
        result = validate_rotation_period(df)
        assert result is True

    def test_validate_rotation_period_missing(self):
        """Test validation when Rotation Period column is missing."""
        df = pd.DataFrame({
            'mass': [0.5, 0.6]
        })
        
        result = validate_rotation_period(df)
        assert result is False
