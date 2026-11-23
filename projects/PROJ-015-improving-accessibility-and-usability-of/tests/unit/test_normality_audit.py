import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
from analysis.stat_utils import log_normality_test

def test_shapiro_wilk_normality():
    """
    Test that log_normality_test correctly computes Shapiro-Wilk statistics
    and writes the output file.
    """
    # Create mock data
    # We need a structure where we can pivot by participant and interface
    np.random.seed(42)
    n_participants = 20
    
    data_rows = []
    for i in range(n_participants):
        # Traditional
        data_rows.append({
            'participant_id': f'P{i}',
            'interface_type': 'traditional',
            'completion_time_seconds': np.random.normal(100, 10),
            'error_count': np.random.randint(0, 5),
            'sus_score': np.random.normal(50, 15)
        })
        # Explainable
        data_rows.append({
            'participant_id': f'P{i}',
            'interface_type': 'explainable',
            'completion_time_seconds': np.random.normal(90, 10), # Slightly faster
            'error_count': np.random.randint(0, 4),
            'sus_score': np.random.normal(60, 15)
        })
    
    df = pd.DataFrame(data_rows)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'normality_log.csv')
        
        # Run the function
        result_df = log_normality_test(df, output_path)
        
        # Verify output file exists
        assert os.path.exists(output_path), "Output file was not created"
        
        # Verify content
        loaded_df = pd.read_csv(output_path)
        assert 'metric' in loaded_df.columns
        assert 'shapiro_statistic' in loaded_df.columns
        assert 'p_value' in loaded_df.columns
        assert len(loaded_df) == 3 # 3 metrics tested
        
        # Verify values are numeric and within valid ranges (stat ~ 0-1, p ~ 0-1)
        for _, row in loaded_df.iterrows():
            if not np.isnan(row['shapiro_statistic']):
                assert 0 <= row['shapiro_statistic'] <= 1
            if not np.isnan(row['p_value']):
                assert 0 <= row['p_value'] <= 1
                
def test_shapiro_wilk_insufficient_data():
    """
    Test behavior when there are too few participants to run Shapiro-Wilk.
    """
    # Create data with only 2 participants (Shapiro-Wilk requires n >= 3)
    data_rows = []
    for i in range(2):
        data_rows.append({
            'participant_id': f'P{i}',
            'interface_type': 'traditional',
            'completion_time_seconds': 100.0,
            'error_count': 1,
            'sus_score': 50.0
        })
        data_rows.append({
            'participant_id': f'P{i}',
            'interface_type': 'explainable',
            'completion_time_seconds': 90.0,
            'error_count': 0,
            'sus_score': 60.0
        })
    
    df = pd.DataFrame(data_rows)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'normality_log.csv')
        
        result_df = log_normality_test(df, output_path)
        
        # Should handle gracefully, likely logging NaNs or skipping
        assert os.path.exists(output_path)
        loaded_df = pd.read_csv(output_path)
        # We expect NaNs or warnings in the log, but the script should not crash
        assert 'metric' in loaded_df.columns
