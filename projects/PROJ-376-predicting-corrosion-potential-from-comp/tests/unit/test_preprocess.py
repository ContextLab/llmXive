import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.preprocess import (
    filter_missing_critical_fields,
    encode_weight_fractions,
    detect_and_remove_outliers,
    validate_processed_data
)
from utils.exceptions import SchemaMismatchError

class TestPreprocess:
    
    def test_filter_missing_critical_fields(self):
        """Test that records with missing pH or temperature are removed."""
        data = {
            'alloy_id': ['A1', 'A2', 'A3', 'A4'],
            'specific_alloy_designation': ['S1', 'S2', 'S3', 'S4'],
            'ph': [7.0, np.nan, 8.0, 6.0],
            'temperature': [25.0, 25.0, np.nan, 25.0],
            'potential_mV': [100.0, 110.0, 120.0, 130.0]
        }
        df = pd.DataFrame(data)
        
        df_clean = filter_missing_critical_fields(df)
        
        # Should remove A2 (missing ph) and A3 (missing temp)
        assert len(df_clean) == 2
        assert 'A2' not in df_clean['alloy_id'].values
        assert 'A3' not in df_clean['alloy_id'].values
        
    def test_filter_out_of_bounds_ph(self):
        """Test that records with pH outside 0-14 are removed."""
        data = {
            'alloy_id': ['A1', 'A2', 'A3'],
            'specific_alloy_designation': ['S1', 'S2', 'S3'],
            'ph': [-1.0, 7.0, 15.0],
            'temperature': [25.0, 25.0, 25.0],
            'potential_mV': [100.0, 110.0, 120.0]
        }
        df = pd.DataFrame(data)
        
        df_clean = filter_missing_critical_fields(df)
        
        assert len(df_clean) == 1
        assert df_clean.iloc[0]['alloy_id'] == 'A2'

    def test_encode_weight_fractions_dict(self):
        """Test encoding of composition as dictionary."""
        data = {
            'alloy_id': ['A1', 'A2'],
            'specific_alloy_designation': ['S1', 'S2'],
            'ph': [7.0, 7.0],
            'temperature': [25.0, 25.0],
            'potential_mV': [100.0, 110.0],
            'composition': [{'Cr': 18.0, 'Ni': 8.0}, {'Cr': 12.0, 'Fe': 88.0}]
        }
        df = pd.DataFrame(data)
        
        df_encoded = encode_weight_fractions(df)
        
        assert 'comp_Cr' in df_encoded.columns
        assert 'comp_Ni' in df_encoded.columns
        assert 'comp_Fe' in df_encoded.columns
        assert df_encoded.loc[0, 'comp_Cr'] == 18.0
        assert df_encoded.loc[1, 'comp_Ni'] == 0.0  # Missing in second record, should be 0

    def test_encode_weight_fractions_string(self):
        """Test encoding of composition as JSON string."""
        import json
        data = {
            'alloy_id': ['A1'],
            'specific_alloy_designation': ['S1'],
            'ph': [7.0],
            'temperature': [25.0],
            'potential_mV': [100.0],
            'composition': [json.dumps({'Cr': 18.0, 'Ni': 8.0})]
        }
        df = pd.DataFrame(data)
        
        df_encoded = encode_weight_fractions(df)
        
        assert 'comp_Cr' in df_encoded.columns
        assert df_encoded.loc[0, 'comp_Cr'] == 18.0

    def test_detect_and_remove_outliers(self):
        """Test IQR-based outlier removal."""
        # Create data with a clear outlier
        data = {
            'alloy_id': [f'A{i}' for i in range(10)],
            'specific_alloy_designation': ['S1'] * 10,
            'ph': [7.0] * 10,
            'temperature': [25.0] * 10,
            'potential_mV': [100.0] * 9 + [1000.0]  # 1000 is an outlier
        }
        df = pd.DataFrame(data)
        
        df_clean = detect_and_remove_outliers(df)
        
        # The outlier (1000.0) should be removed
        assert len(df_clean) < len(df)
        assert 1000.0 not in df_clean['potential_mV'].values

    def test_validate_processed_data_success(self):
        """Test successful validation."""
        data = {
            'alloy_id': [f'A{i}' for i in range(501)],
            'specific_alloy_designation': ['S1'] * 501,
            'ph': [7.0] * 501,
            'temperature': [25.0] * 501,
            'potential_mV': [100.0] * 501
        }
        df = pd.DataFrame(data)
        
        is_valid, details = validate_processed_data(df)
        
        assert is_valid
        assert details['record_count'] == 501
        assert details['validation_status'] == 'PASS'

    def test_validate_processed_data_failure_count(self):
        """Test validation failure due to low record count."""
        data = {
            'alloy_id': [f'A{i}' for i in range(10)],
            'specific_alloy_designation': ['S1'] * 10,
            'ph': [7.0] * 10,
            'temperature': [25.0] * 10,
            'potential_mV': [100.0] * 10
        }
        df = pd.DataFrame(data)
        
        is_valid, details = validate_processed_data(df)
        
        assert not is_valid
        assert 'less than required 500' in details.get('reason', '')

    def test_validate_processed_data_failure_nulls(self):
        """Test validation failure due to nulls."""
        data = {
            'alloy_id': [f'A{i}' for i in range(501)],
            'specific_alloy_designation': ['S1'] * 501,
            'ph': [7.0] * 500 + [np.nan],
            'temperature': [25.0] * 501,
            'potential_mV': [100.0] * 501
        }
        df = pd.DataFrame(data)
        
        is_valid, details = validate_processed_data(df)
        
        assert not is_valid
        assert details['critical_nulls'] is True