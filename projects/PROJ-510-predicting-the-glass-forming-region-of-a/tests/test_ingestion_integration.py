"""
Additional integration tests for ingestion pipeline focusing on real data constraints.
"""
import pytest
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.ingestion import load_glass_data, filter_ternary_alloys, clean_data

class TestRealDataConstraints:
    def test_ternary_filter_logic(self):
        """
        Verify that the ternary filter correctly identifies 3-element alloys.
        """
        # Create mock data mimicking the structure
        data = {
            'composition': ['Cu50Zr50', 'Cu60Zr30Al10', 'Fe40Ni40P20', 'Au100'],
            'critical_cooling_rate': [10.0, 20.0, 5.0, 100.0]
        }
        df = pd.DataFrame(data)
        
        # Apply filter
        filtered = filter_ternary_alloys(df)
        
        # Expected: 3 rows (Cu60Zr30Al10, Fe40Ni40P20, and maybe Au100 if parsed as 1 element? 
        # Actually Au100 is 1 element. Cu50Zr50 is 2. So only 2 should remain: Cu60... and Fe40...)
        # Let's check the logic: Cu60Zr30Al10 (3), Fe40Ni40P20 (3).
        assert len(filtered) == 2, f"Expected 2 ternary alloys, got {len(filtered)}"
        assert 'Cu60Zr30Al10' in filtered['composition'].values
        assert 'Fe40Ni40P20' in filtered['composition'].values

    def test_data_cleaning_removes_nan(self):
        """Verify that clean_data removes rows with NaN in critical columns."""
        data = {
            'composition': ['Cu50Zr50', 'Cu60Zr30Al10', 'Fe40Ni40P20'],
            'critical_cooling_rate': [10.0, None, 5.0]
        }
        df = pd.DataFrame(data)
        
        cleaned = clean_data(df)
        
        assert len(cleaned) == 2, f"Expected 2 rows after cleaning, got {len(cleaned)}"
        assert not cleaned['critical_cooling_rate'].isna().any()
