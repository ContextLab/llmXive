"""
Tests for the preprocessing module (User Story 2).
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
import gc

# Add code directory to path
code_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'code')
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from preprocess import clean_data, normalize_rt, detect_outliers_iqr, extract_features
from config import get_memory_threshold_mb


class TestPreprocess:
    """Tests for preprocessing functions."""

    def test_outlier_detection_iqr(self):
        """
        T028: Contract test to assert correct flagging per Condition group.
        
        Verifies that:
        1. The IQR method is calculated PER group (Condition).
        2. An outlier is flagged (column 'is_outlier' added) but rows are NOT removed.
        3. The specific outlier value is correctly identified.
        """
        # Create data with a clear outlier in Group A, but normal values in Group B.
        # Group A: [10, 12, 11, 100, 13] -> Q1=10.5, Q3=12, IQR=1.5. Upper Bound = 12 + 1.5*1.5 = 14.25. 100 is outlier.
        # Group B: [20, 22, 21] -> Q1=20.5, Q3=22, IQR=1.5. Upper Bound = 22 + 1.5*1.5 = 24.25. No outliers.
        data = {
            'Condition': ['A', 'A', 'A', 'A', 'A', 'B', 'B', 'B'],
            'ReactionTime': [10.0, 12.0, 11.0, 100.0, 13.0, 20.0, 22.0, 21.0]
        }
        df = pd.DataFrame(data)
        
        # Run outlier detection
        # Expected behavior: Adds 'is_outlier' column, does not drop rows.
        result_df = detect_outliers_iqr(df, group_col='Condition', value_col='ReactionTime')
        
        # Assert 1: Column exists
        assert 'is_outlier' in result_df.columns, "detect_outliers_iqr must add 'is_outlier' column"
        
        # Assert 2: No rows were removed (length preserved)
        assert len(result_df) == len(df), "detect_outliers_iqr must flag outliers, not remove rows"
        
        # Assert 3: The specific outlier (100.0) is flagged True
        outlier_row = result_df[result_df['ReactionTime'] == 100.0]
        assert outlier_row['is_outlier'].iloc[0] is True, "Value 100.0 should be flagged as outlier in Group A"
        
        # Assert 4: Normal values are flagged False
        normal_row_a = result_df[result_df['ReactionTime'] == 10.0]
        assert normal_row_a['is_outlier'].iloc[0] is False, "Value 10.0 should NOT be flagged"
        
        # Assert 5: Values in other groups are not affected by Group A's stats
        normal_row_b = result_df[result_df['ReactionTime'] == 22.0]
        assert normal_row_b['is_outlier'].iloc[0] is False, "Value 22.0 in Group B should NOT be flagged"

    def test_memory_usage_under_limit(self):
        """
        T029: Integration test to verify memory stays under limit (7 GB).
        
        This test generates a synthetic dataset of a specific size to stress the memory
        and verifies that the preprocessing pipeline (clean_data) completes without
        exceeding the configured threshold (7 GB).
        
        It uses psutil to measure actual RSS memory before and after processing.
        """
        # Configuration
        MAX_MEMORY_MB = get_memory_threshold_mb() # Should be 7 * 1024 = 7168
        
        # Generate a dataset large enough to be measurable but safe for 7GB limit.
        # 100,000 rows * ~20 bytes per row ~ 2MB, which is trivial.
        # To actually test memory pressure, we create a larger frame.
        # 10 million rows might be too much for the runner, but 1 million is safe.
        # Let's target ~100MB-500MB usage to ensure we are well under 7GB but above trivial.
        N_ROWS = 2_000_000 
        
        # Force garbage collection before measuring baseline
        gc.collect()
        
        try:
            import psutil
            process = psutil.Process()
            baseline_mem = process.memory_info().rss / 1024 / 1024
        except ImportError:
            pytest.skip("psutil not installed, skipping memory measurement but validating logic")
            return

        # Create data
        # We use numpy to generate arrays, then construct DataFrame to ensure we have real memory pressure
        np.random.seed(42)
        p_ids = np.repeat(np.arange(N_ROWS // 10), 10)
        conditions = np.tile(['Rejection', 'Control'], N_ROWS // 20)
        # Reaction times: float64
        rts = np.random.exponential(scale=0.5, size=N_ROWS) + 0.2 
        moods = np.random.normal(loc=5.0, scale=1.5, size=N_ROWS)

        df = pd.DataFrame({
            'Participant_ID': p_ids,
            'Condition': conditions,
            'ReactionTime': rts,
            'Mood': moods
        })

        # Measure memory after creation
        try:
            gc.collect()
            mem_after_create = process.memory_info().rss / 1024 / 1024
        except ImportError:
            mem_after_create = 0

        # Run the actual preprocessing pipeline
        # This is the code under test
        cleaned_df = clean_data(df)

        # Measure memory after processing
        gc.collect()
        try:
            mem_after_process = process.memory_info().rss / 1024 / 1024
        except ImportError:
            mem_after_process = 0

        # Assertions
        assert len(cleaned_df) > 0, "Preprocessing must not drop all data"
        assert 'is_outlier' in cleaned_df.columns, "clean_data must flag outliers"

        # Verify memory constraint
        # We allow some variance, but it must be strictly under the 7GB limit
        assert mem_after_process < MAX_MEMORY_MB, (
            f"Memory usage {mem_after_process:.2f} MB exceeds limit of {MAX_MEMORY_MB} MB. "
            f"Peak increase: {mem_after_process - baseline_mem:.2f} MB"
        )

        # Log for debugging if needed
        print(f"Memory Test: Baseline={baseline_mem:.2f}MB, AfterCreate={mem_after_create:.2f}MB, "
              f"AfterProcess={mem_after_process:.2f}MB, Limit={MAX_MEMORY_MB}MB")