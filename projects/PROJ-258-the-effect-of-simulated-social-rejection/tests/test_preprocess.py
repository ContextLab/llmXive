"""
Tests for the preprocessing module (User Story 2).
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add code directory to path
code_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'code')
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from preprocess import clean_data, normalize_rt, detect_outliers_iqr, extract_features


class TestPreprocess:
    """Tests for preprocessing functions."""

    def test_outlier_detection_iqr(self):
        """
        T018: Contract test to assert correct flagging per Condition group.
        """
        # Create data with a clear outlier
        data = {
            'Condition': ['A', 'A', 'A', 'A', 'A', 'B', 'B', 'B'],
            'Value': [10, 12, 11, 100, 13, 20, 22, 21] # 100 is an outlier in A
        }
        df = pd.DataFrame(data)
        
        # Run outlier detection
        # Assuming detect_outliers_iqr returns a modified DF or flags
        # We need to check if the outlier is identified
        result_df = detect_outliers_iqr(df, group_col='Condition', value_col='Value')
        
        # Check if the outlier (100) is flagged
        # Implementation dependent: usually adds a column 'is_outlier'
        if 'is_outlier' in result_df.columns:
            outlier_row = result_df[result_df['Value'] == 100]
            assert outlier_row['is_outlier'].iloc[0] == True, "Outlier 100 should be flagged"
        else:
            # If it removes outliers, check length
            assert len(result_df) < len(df), "Outliers should be removed or flagged"

    def test_memory_usage_under_limit(self):
        """
        T019: Integration test to verify memory stays under limit (simulated).
        """
        # Create a reasonably large dataset for testing
        # N=10000 should be fine in memory
        data = {
            'Participant_ID': np.repeat(range(1000), 10),
            'Condition': np.tile(['A', 'B'], 5000),
            'Value': np.random.rand(10000)
        }
        df = pd.DataFrame(data)
        
        # Run preprocessing
        cleaned = clean_data(df)
        
        # Check memory (mock check)
        # In real CI, this might be checked via psutil
        # Here we just ensure it runs without OOM
        assert len(cleaned) > 0, "Preprocessing should not drop all data"
        
        # Simulate memory check
        import psutil
        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024
        assert mem_mb < 7000, f"Memory usage {mem_mb:.2f} MB exceeds 7 GB limit"
