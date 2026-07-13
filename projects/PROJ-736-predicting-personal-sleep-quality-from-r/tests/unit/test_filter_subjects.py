"""
Unit tests for subject filtering logic in download_hcp.py.
"""
import os
import tempfile
import json
import pandas as pd
import pytest
from pathlib import Path

# Mock the config and logging for unit tests to avoid dependency issues
import sys
from unittest.mock import patch, MagicMock

# We need to import the function directly. Since download_hcp imports config,
# we might need to mock paths if we import the whole module.
# Instead, we will test the logic by recreating the DataFrame processing.

def test_filter_logic():
    """Test the filtering logic: valid sleep score and FD <= 0.3"""
    
    # Create a mock DataFrame
    data = {
        'Subject': ['100001', '100002', '100003', '100004', '100005'],
        'Sleep_Score': [10.5, None, 12.0, 8.0, -999],
        'MeanFD': [0.2, 0.4, 0.1, 0.3, 0.2]
    }
    df = pd.DataFrame(data)
    
    # Apply logic from filter_subjects
    FD_THRESHOLD = 0.3
    
    # Valid sleep: not null, not -999
    valid_sleep = df['Sleep_Score'].notna() & (df['Sleep_Score'] != -999)
    # Valid FD: <= 0.3
    valid_fd = df['MeanFD'] <= FD_THRESHOLD
    
    final_mask = valid_sleep & valid_fd
    result = df[final_mask]
    
    # Expected:
    # 100001: Sleep=10.5 (ok), FD=0.2 (ok) -> KEEP
    # 100002: Sleep=None -> EXCLUDE
    # 100003: Sleep=12.0 (ok), FD=0.1 (ok) -> KEEP
    # 100004: Sleep=8.0 (ok), FD=0.3 (ok) -> KEEP
    # 100005: Sleep=-999 -> EXCLUDE
    
    assert len(result) == 3
    assert '100001' in result['Subject'].values
    assert '100003' in result['Subject'].values
    assert '100004' in result['Subject'].values
    assert '100002' not in result['Subject'].values
    assert '100005' not in result['Subject'].values

def test_filter_with_nan_fd():
    """Test behavior when FD is NaN"""
    data = {
        'Subject': ['100006'],
        'Sleep_Score': [10.0],
        'MeanFD': [None]
    }
    df = pd.DataFrame(data)
    FD_THRESHOLD = 0.3
    
    valid_sleep = df['Sleep_Score'].notna() & (df['Sleep_Score'] != -999)
    # Convert to numeric first as in the real code
    df['MeanFD'] = pd.to_numeric(df['MeanFD'], errors='coerce')
    valid_fd = df['MeanFD'].notna() & (df['MeanFD'] <= FD_THRESHOLD)
    
    final_mask = valid_sleep & valid_fd
    result = df[final_mask]
    
    # FD is NaN, so it should be excluded
    assert len(result) == 0

def test_filter_output_file_structure():
    """Verify the output JSON structure matches expectations"""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_csv = os.path.join(tmpdir, 'input.csv')
        output_json = os.path.join(tmpdir, 'output.json')
        
        # Create input
        data = {
            'Subject': ['100001'],
            'Sleep_Score': [10.0],
            'MeanFD': [0.1]
        }
        pd.DataFrame(data).to_csv(input_csv, index=False)
        
        # Import and run the actual function
        # We need to mock the paths module to avoid config issues in unit test
        with patch('code.data.download_hcp.get_paths') as mock_paths, \
             patch('code.data.download_hcp.ensure_dirs'):
            
            mock_paths.return_value = {
                'raw_behavioral': tmpdir,
                'processed': tmpdir
            }
            
            from code.data.download_hcp import filter_subjects
            valid_subjects, excluded = filter_subjects(input_csv, output_json)
            
            assert os.path.exists(output_json)
            with open(output_json, 'r') as f:
                content = json.load(f)
            
            assert 'valid_subjects' in content
            assert 'exclusion_criteria' in content
            assert content['total_valid'] == 1
            assert content['total_excluded'] == 0
            assert '100001' in content['valid_subjects']
