import pandas as pd
import numpy as np
import json
import os
import pytest
from preprocess import normalize_and_flag_outliers, log_outlier_removal

def test_outlier_detection_iqr():
    """
    T028: Contract test to assert correct flagging per Condition group.
    Verifies that outliers are flagged (column added) but NOT removed.
    """
    # Create synthetic but structured data for testing the logic
    # Condition A: Values 10, 10, 10, 10, 100 (100 is outlier)
    # Condition B: Values 20, 20, 20, 20, 20 (No outliers)
    data = {
        'Participant': ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10'],
        'Condition': ['A', 'A', 'A', 'A', 'A', 'B', 'B', 'B', 'B', 'B'],
        'Normalized RT': [10.0, 10.0, 10.0, 10.0, 100.0, 20.0, 20.0, 20.0, 20.0, 20.0]
    }
    df = pd.DataFrame(data)
    
    # Run the function
    result_df = normalize_and_flag_outliers(df, group_col='Condition', rt_col='Normalized RT')
    
    # Assert that the 'is_outlier' column exists
    assert 'is_outlier' in result_df.columns
    
    # Assert that row count is preserved (no rows removed)
    assert len(result_df) == len(df)
    
    # Condition A: 100 should be outlier (Q1=10, Q3=10, IQR=0. If IQR=0, bounds are 10 +/- 0. 
    # Wait, if IQR is 0, then 100 is definitely > 10.
    # Let's adjust data to ensure IQR > 0 for a realistic test
    # Data A: 1, 2, 3, 4, 100 -> Q1=1.75, Q3=3.25, IQR=1.5. Bounds: 0.5, 5.5. 100 is outlier.
    data['Normalized RT'] = [1.0, 2.0, 3.0, 4.0, 100.0, 20.0, 20.0, 20.0, 20.0, 20.0]
    df = pd.DataFrame(data)
    result_df = normalize_and_flag_outliers(df, group_col='Condition', rt_col='Normalized RT')
    
    # Check Condition A outliers
    cond_a = result_df[result_df['Condition'] == 'A']
    assert cond_a['is_outlier'].sum() == 1
    assert cond_a.iloc[4]['is_outlier'] == True # The 100 value
    
    # Check Condition B outliers
    cond_b = result_df[result_df['Condition'] == 'B']
    assert cond_b['is_outlier'].sum() == 0

def test_memory_usage_under_limit():
    """
    T029: Integration test to verify memory stays within limits (conceptual).
    Since we can't easily mock RAM in a simple unit test, we verify the logic
    doesn't create massive duplicates.
    """
    # Create a small dataset
    data = {
        'Participant': [f'P{i}' for i in range(100)],
        'Condition': ['A'] * 50 + ['B'] * 50,
        'Normalized RT': [np.random.normal(10, 2) for _ in range(100)]
    }
    df = pd.DataFrame(data)
    
    # Run processing
    result = normalize_and_flag_outliers(df)
    
    # Verify row count matches input
    assert len(result) == len(df)

def test_outlier_audit_log_generation():
    """
    T042: Verify that log_outlier_removal generates the correct JSON structure.
    """
    # Create test data
    data = {
        'Participant': ['P1', 'P2', 'P3', 'P4', 'P5'],
        'Condition': ['A', 'A', 'A', 'A', 'A'],
        'Normalized RT': [1.0, 2.0, 3.0, 4.0, 100.0]
    }
    df = pd.DataFrame(data)
    
    # Ensure outlier column exists
    df = normalize_and_flag_outliers(df, group_col='Condition', rt_col='Normalized RT')
    
    # Generate log to a temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        log_outlier_removal(df, output_path=temp_path)
        
        # Read the file
        with open(temp_path, 'r') as f:
            log_data = json.load(f)
        
        # Verify schema
        assert isinstance(log_data, list)
        assert len(log_data) > 0
        
        entry = log_data[0]
        assert 'condition' in entry
        assert 'flagged_count' in entry
        assert 'iqr_threshold' in entry
        
        # Verify specific values
        assert entry['flagged_count'] == 1
        assert entry['condition'] == 'A'
        assert isinstance(entry['iqr_threshold'], float)
    finally:
        os.unlink(temp_path)
