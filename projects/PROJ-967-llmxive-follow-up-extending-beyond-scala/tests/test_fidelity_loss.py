"""
Tests for T024: Dimensional Fidelity Loss Calculation.
"""

import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the module functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from fidelity_loss import (
    load_raw_data,
    calculate_fidelity_loss,
    save_cleaned_data,
    save_summary
)


def create_test_dataframe():
    """Create a mock dataframe with the expected schema."""
    data = {
        'sample_id': ['s1', 's2', 's3', 's4', 's5'],
        'prompt': ['p1', 'p2', 'p3', 'p4', 'p5'],
        'image_url': ['i1', 'i2', 'i3', 'i4', 'i5'],
        'teacher_scores': [
            {'Alignment': 0.5, 'Realism': 0.6, 'Aesthetics': 0.7, 'Plausibility': 0.8},
            {'Alignment': 0.4, 'Realism': 0.5, 'Aesthetics': 0.6, 'Plausibility': 0.7},
            {'Alignment': 0.3, 'Realism': 0.4, 'Aesthetics': 0.5, 'Plausibility': 0.6},
            {'Alignment': 0.2, 'Realism': 0.3, 'Aesthetics': 0.4, 'Plausibility': 0.5},
            {'Alignment': 0.1, 'Realism': 0.2, 'Aesthetics': 0.3, 'Plausibility': 0.4}
        ],
        'student_scalar': [0.6, 0.5, 0.4, np.nan, 0.2], # s4 missing scalar
        'human_annotations': [
            {'Alignment': 0.55, 'Realism': 0.65, 'Aesthetics': 0.75, 'Plausibility': 0.85},
            {'Alignment': 0.45, 'Realism': 0.55, 'Aesthetics': 0.65, 'Plausibility': 0.75},
            {'Alignment': 0.35, 'Realism': 0.45, 'Aesthetics': 0.55, 'Plausibility': 0.65},
            {'Alignment': 0.25, 'Realism': 0.35, 'Aesthetics': 0.45, 'Plausibility': 0.55},
            {'Alignment': 0.15, 'Realism': 0.25, 'Aesthetics': 0.35, 'Plausibility': 0.45}
        ],
        'primary_dimension': [
            'Alignment',
            'Realism',
            'Aesthetics',
            'Plausibility', # Will be excluded due to missing student_scalar
            'Alignment'
        ]
    }
    return pd.DataFrame(data)


def test_calculate_fidelity_loss_basic():
    """Test basic calculation of fidelity loss."""
    df = create_test_dataframe()
    result = calculate_fidelity_loss(df)

    # Check that s4 (missing student_scalar) is excluded
    assert 's4' not in result['sample_id'].values

    # Check that remaining rows have fidelity_loss
    assert 'fidelity_loss' in result.columns
    assert len(result) == 4 # s1, s2, s3, s5

    # Verify calculation for s1: |0.6 - 0.55| = 0.05
    s1_row = result[result['sample_id'] == 's1'].iloc[0]
    assert abs(s1_row['fidelity_loss'] - 0.05) < 1e-6

    # Verify calculation for s2: |0.5 - 0.55| = 0.05 (Realism)
    s2_row = result[result['sample_id'] == 's2'].iloc[0]
    assert abs(s2_row['fidelity_loss'] - 0.05) < 1e-6


def test_calculate_fidelity_loss_missing_primary_dimension():
    """Test handling of missing primary_dimension."""
    df = create_test_dataframe()
    df.loc[df['sample_id'] == 's1', 'primary_dimension'] = None

    result = calculate_fidelity_loss(df)

    # s1 should be excluded
    assert 's1' not in result['sample_id'].values
    # s4 should also be excluded (missing scalar)
    assert 's4' not in result['sample_id'].values
    assert len(result) == 3


def test_calculate_fidelity_loss_missing_human_annotation_key():
    """Test handling when the primary dimension is missing in human_annotations."""
    df = create_test_dataframe()
    # Modify s2's human_annotations to not have 'Realism'
    df.loc[df['sample_id'] == 's2', 'human_annotations'] = {'Alignment': 0.45}

    result = calculate_fidelity_loss(df)

    # s2 should be excluded
    assert 's2' not in result['sample_id'].values
    # s4 should also be excluded
    assert 's4' not in result['sample_id'].values
    assert len(result) == 3


def test_save_summary(tmp_path):
    """Test saving the summary JSON."""
    df = create_test_dataframe()
    cleaned_df = calculate_fidelity_loss(df)
    
    summary_path = tmp_path / "summary.json"
    save_summary(cleaned_df, str(summary_path))

    assert summary_path.exists()
    with open(summary_path, 'r') as f:
        summary = json.load(f)

    assert 'count' in summary
    assert 'mean' in summary
    assert 'median' in summary
    assert summary['count'] == 4 # s1, s2, s3, s5

def test_load_raw_data_missing_file():
    """Test that load_raw_data raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_raw_data("non_existent_path.parquet")

def test_empty_dataframe_handling():
    """Test handling of empty dataframe."""
    df = pd.DataFrame(columns=['sample_id', 'primary_dimension', 'student_scalar', 'human_annotations'])
    result = calculate_fidelity_loss(df)
    assert result.empty