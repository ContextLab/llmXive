import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ingest import flag_raw_records

class TestFlagRawRecords:
    
    def test_all_normalized(self):
        """Test case where all records have both contact_load and sliding_speed."""
        data = {
            'pulse_duration': [10.0, 20.0],
            'power': [100.0, 200.0],
            'scanning_speed': [1.0, 2.0],
            'pattern_geometry': ['A', 'B'],
            'hardness': [500.0, 600.0],
            'elastic_modulus': [200.0, 210.0],
            'contact_load': [10.0, 20.0],
            'sliding_speed': [0.1, 0.2],
            'wear_rate': [0.5, 0.6],
            'density': [7.8, 7.9],
            'geometry': ['flat', 'flat']
        }
        df = pd.DataFrame(data)
        
        result = flag_raw_records(df)
        
        assert 'normalization_method' in result.columns
        assert all(result['normalization_method'] == 'normalized')
        assert len(result) == 2

    def test_all_raw_missing_load(self):
        """Test case where contact_load is missing for all records."""
        data = {
            'pulse_duration': [10.0, 20.0],
            'power': [100.0, 200.0],
            'scanning_speed': [1.0, 2.0],
            'pattern_geometry': ['A', 'B'],
            'hardness': [500.0, 600.0],
            'elastic_modulus': [200.0, 210.0],
            'contact_load': [np.nan, np.nan],
            'sliding_speed': [0.1, 0.2],
            'wear_rate': [0.5, 0.6],
            'density': [7.8, 7.9],
            'geometry': ['flat', 'flat']
        }
        df = pd.DataFrame(data)
        
        result = flag_raw_records(df)
        
        assert 'normalization_method' in result.columns
        assert all(result['normalization_method'] == 'raw')

    def test_all_raw_missing_speed(self):
        """Test case where sliding_speed is missing for all records."""
        data = {
            'pulse_duration': [10.0, 20.0],
            'power': [100.0, 200.0],
            'scanning_speed': [1.0, 2.0],
            'pattern_geometry': ['A', 'B'],
            'hardness': [500.0, 600.0],
            'elastic_modulus': [200.0, 210.0],
            'contact_load': [10.0, 20.0],
            'sliding_speed': [np.nan, np.nan],
            'wear_rate': [0.5, 0.6],
            'density': [7.8, 7.9],
            'geometry': ['flat', 'flat']
        }
        df = pd.DataFrame(data)
        
        result = flag_raw_records(df)
        
        assert 'normalization_method' in result.columns
        assert all(result['normalization_method'] == 'raw')

    def test_mixed_records(self):
        """Test case with a mix of normalized and raw records."""
        data = {
            'pulse_duration': [10.0, 20.0, 30.0, 40.0],
            'power': [100.0, 200.0, 300.0, 400.0],
            'scanning_speed': [1.0, 2.0, 3.0, 4.0],
            'pattern_geometry': ['A', 'B', 'C', 'D'],
            'hardness': [500.0, 600.0, 700.0, 800.0],
            'elastic_modulus': [200.0, 210.0, 220.0, 230.0],
            'contact_load': [10.0, np.nan, 30.0, np.nan], # Row 0, 2 have load; 1, 3 missing
            'sliding_speed': [0.1, 0.2, np.nan, np.nan],  # Row 0, 1 have speed; 2, 3 missing
            'wear_rate': [0.5, 0.6, 0.7, 0.8],
            'density': [7.8, 7.9, 8.0, 8.1],
            'geometry': ['flat', 'flat', 'flat', 'flat']
        }
        # Row 0: Load=10, Speed=0.1 -> Normalized
        # Row 1: Load=NaN, Speed=0.2 -> Raw
        # Row 2: Load=30, Speed=NaN -> Raw
        # Row 3: Load=NaN, Speed=NaN -> Raw
        df = pd.DataFrame(data)
        
        result = flag_raw_records(df)
        
        assert 'normalization_method' in result.columns
        assert result.iloc[0]['normalization_method'] == 'normalized'
        assert result.iloc[1]['normalization_method'] == 'raw'
        assert result.iloc[2]['normalization_method'] == 'raw'
        assert result.iloc[3]['normalization_method'] == 'raw'
        
        # Verify counts
        counts = result['normalization_method'].value_counts()
        assert counts['normalized'] == 1
        assert counts['raw'] == 3

    def test_missing_optional_columns_entirely(self):
        """Test behavior when contact_load/sliding_speed columns are missing from DF."""
        data = {
            'pulse_duration': [10.0],
            'power': [100.0],
            'scanning_speed': [1.0],
            'pattern_geometry': ['A'],
            'hardness': [500.0],
            'elastic_modulus': [200.0],
            'wear_rate': [0.5],
            'density': [7.8],
            'geometry': ['flat']
            # Missing contact_load and sliding_speed
        }
        df = pd.DataFrame(data)
        
        result = flag_raw_records(df)
        
        assert 'normalization_method' in result.columns
        assert all(result['normalization_method'] == 'raw')
        assert len(result) == 1