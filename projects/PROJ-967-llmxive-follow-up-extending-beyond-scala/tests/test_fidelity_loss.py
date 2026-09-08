import pytest
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: Assuming the test runs from the project root or code is in PYTHONPATH
# In the actual pipeline, these imports are relative to code/
try:
    from code.fidelity_loss import calculate_fidelity_loss, save_summary
except ImportError:
    # Fallback for local testing if path is not set correctly
    import sys
    sys.path.insert(0, 'code')
    from fidelity_loss import calculate_fidelity_loss, save_summary

@pytest.fixture
def sample_dataframe():
    """Create a mock dataframe matching the expected schema."""
    data = {
        'sample_id': ['s1', 's2', 's3', 's4', 's5'],
        'prompt': ['p1', 'p2', 'p3', 'p4', 'p5'],
        'primary_dimension': ['Alignment', 'Realism', 'Aesthetics', None, 'Plausibility'],
        'student_scalar': [4.5, 3.2, 5.0, 2.0, 4.0],
        'human_annotations': [
            {'Alignment': 4.0, 'Realism': 3.0, 'Aesthetics': 5.0, 'Plausibility': 4.0},
            {'Alignment': 4.0, 'Realism': 3.0, 'Aesthetics': 5.0, 'Plausibility': 4.0},
            {'Alignment': 4.0, 'Realism': 3.0, 'Aesthetics': 5.0, 'Plausibility': 4.0},
            {'Alignment': 4.0, 'Realism': 3.0, 'Aesthetics': 5.0, 'Plausibility': 4.0},
            {'Alignment': 4.0, 'Realism': 3.0, 'Aesthetics': 5.0, 'Plausibility': 4.0}
        ],
        'teacher_scores': [
            {'Alignment': 4.2, 'Realism': 3.1, 'Aesthetics': 4.9, 'Plausibility': 4.1},
            {'Alignment': 4.2, 'Realism': 3.1, 'Aesthetics': 4.9, 'Plausibility': 4.1},
            {'Alignment': 4.2, 'Realism': 3.1, 'Aesthetics': 4.9, 'Plausibility': 4.1},
            {'Alignment': 4.2, 'Realism': 3.1, 'Aesthetics': 4.9, 'Plausibility': 4.1},
            {'Alignment': 4.2, 'Realism': 3.1, 'Aesthetics': 4.9, 'Plausibility': 4.1}
        ]
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_logger():
    """Mock logger to avoid console output during tests."""
    logger = MagicMock()
    return logger

def test_valid_samples_calculate_fidelity_loss(sample_dataframe, mock_logger):
    """Test that valid samples are processed and fidelity loss is calculated correctly."""
    # Mock the lineage report existence check
    with patch('pathlib.Path.exists', return_value=True):
        df_cleaned, exclusion_log = calculate_fidelity_loss(sample_dataframe, mock_logger)

    # Check that we have valid samples (s1, s2, s3, s5 - s4 excluded due to null dimension)
    assert len(df_cleaned) == 4
    assert 's4' not in df_cleaned['sample_id'].values

    # Check fidelity loss calculation for s1: |4.5 - 4.0| = 0.5
    s1_row = df_cleaned[df_cleaned['sample_id'] == 's1'].iloc[0]
    assert abs(s1_row['fidelity_loss'] - 0.5) < 1e-6

    # Check exclusion log
    assert len(exclusion_log) == 1
    assert exclusion_log[0]['sample_id'] == 's4'
    assert exclusion_log[0]['reason'] == 'missing_primary_dimension'

def test_missing_human_annotation_exclusion(sample_dataframe, mock_logger):
    """Test that samples with missing human annotation for primary dimension are excluded."""
    # Modify s2 to have missing Realism annotation
    sample_dataframe.loc[1, 'human_annotations'] = {'Alignment': 4.0} # Missing Realism
    
    with patch('pathlib.Path.exists', return_value=True):
        df_cleaned, exclusion_log = calculate_fidelity_loss(sample_dataframe, mock_logger)

    assert len(df_cleaned) == 3
    assert 's2' not in df_cleaned['sample_id'].values
    
    exclusion_s2 = next((e for e in exclusion_log if e['sample_id'] == 's2'), None)
    assert exclusion_s2 is not None
    assert 'missing_human_annotation_for_Realism' in exclusion_s2['reason']

def test_missing_student_scalar_exclusion(sample_dataframe, mock_logger):
    """Test that samples with missing student_scalar are excluded."""
    sample_dataframe.loc[2, 'student_scalar'] = None
    
    with patch('pathlib.Path.exists', return_value=True):
        df_cleaned, exclusion_log = calculate_fidelity_loss(sample_dataframe, mock_logger)

    assert len(df_cleaned) == 3
    assert 's3' not in df_cleaned['sample_id'].values
    
    exclusion_s3 = next((e for e in exclusion_log if e['sample_id'] == 's3'), None)
    assert exclusion_s3 is not None
    assert exclusion_s3['reason'] == 'missing_student_scalar'

def test_summary_calculation(sample_dataframe, mock_logger):
    """Test that summary statistics are calculated correctly."""
    with patch('pathlib.Path.exists', return_value=True):
        df_cleaned, exclusion_log = calculate_fidelity_loss(sample_dataframe, mock_logger)
    
    # Manually verify summary logic
    mean_loss = df_cleaned['fidelity_loss'].mean()
    median_loss = df_cleaned['fidelity_loss'].median()
    
    # We don't write to disk in this test, just verify the logic exists
    # The save_summary function would handle file I/O
    assert mean_loss > 0
    assert median_loss >= 0
    assert len(exclusion_log) == 1