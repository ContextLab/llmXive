import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path

# Import the functions to test
from code.fidelity_loss import (
    load_raw_data,
    calculate_fidelity_loss,
    save_cleaned_data,
    save_summary
)

@pytest.fixture
def sample_raw_data():
    """Create a minimal mock dataset matching the expected schema."""
    data = {
        'prompt': ['p1', 'p2', 'p3', 'p4', 'p5'],
        'image_url': ['u1', 'u2', 'u3', 'u4', 'u5'],
        'teacher_scores': [
            {'Alignment': 5.0, 'Realism': 4.0, 'Aesthetics': 3.0, 'Plausibility': 4.5},
            {'Alignment': 6.0, 'Realism': 5.0, 'Aesthetics': 4.0, 'Plausibility': 5.0},
            {'Alignment': 7.0, 'Realism': 6.0, 'Aesthetics': 5.0, 'Plausibility': 6.0},
            {'Alignment': 8.0, 'Realism': 7.0, 'Aesthetics': 6.0, 'Plausibility': 7.0},
            {'Alignment': 9.0, 'Realism': 8.0, 'Aesthetics': 7.0, 'Plausibility': 8.0}
        ],
        'student_scalar': [5.5, 6.5, 7.5, 8.5, 9.5],
        'human_annotations': [
            {'Alignment': 5.0, 'Realism': 4.0, 'Aesthetics': 3.0, 'Plausibility': 4.5},
            {'Alignment': 6.0, 'Realism': 5.0, 'Aesthetics': 4.0, 'Plausibility': 5.0},
            {'Alignment': 7.0, 'Realism': 6.0, 'Aesthetics': 5.0, 'Plausibility': 6.0},
            {'Alignment': 8.0, 'Realism': 7.0, 'Aesthetics': 6.0, 'Plausibility': 7.0},
            {'Alignment': 9.0, 'Realism': 8.0, 'Aesthetics': 7.0, 'Plausibility': 8.0}
        ],
        'primary_dimension': ['Alignment', 'Realism', None, 'Aesthetics', 'Plausibility'],
        'excluded_reason': [None, None, 'missing_primary_dimension', None, None]
    }
    return pd.DataFrame(data)

def test_calculate_fidelity_loss_valid_samples(sample_raw_data):
    """Test that valid samples are processed correctly and loss is calculated."""
    df, summary = calculate_fidelity_loss(sample_raw_data)
    
    # Check count
    assert summary['count'] == 4  # Row 2 (index 2) has None primary_dimension
    assert summary['excluded_count'] == 1
    
    # Check that 'fidelity_loss' column exists in result
    assert 'fidelity_loss' in df.columns
    
    # Check specific loss values (absolute difference)
    # Row 0: |5.5 - 5.0| = 0.5
    # Row 1: |6.5 - 6.0| = 0.5
    # Row 3: |8.5 - 6.0| = 2.5 (Aesthetics: student 8.5, human 6.0) -> Wait, primary is Aesthetics for row 3
    # Row 3: primary='Aesthetics', student=8.5, human=Aesthetics=6.0 -> |8.5 - 6.0| = 2.5
    # Row 4: primary='Plausibility', student=9.5, human=Plausibility=8.0 -> |9.5 - 8.0| = 1.5
    
    losses = sorted(df['fidelity_loss'].tolist())
    # Expected: 0.5, 0.5, 2.5, 1.5 -> sorted: 0.5, 0.5, 1.5, 2.5
    expected_losses = [0.5, 0.5, 1.5, 2.5]
    
    assert len(losses) == 4
    for i in range(4):
        assert abs(losses[i] - expected_losses[i]) < 1e-6

def test_calculate_fidelity_loss_missing_primary_dimension(sample_raw_data):
    """Test that samples with missing primary_dimension are excluded."""
    df, summary = calculate_fidelity_loss(sample_raw_data)
    
    # Verify excluded reason is recorded
    assert 'missing_primary_dimension' in summary['excluded_reasons']
    
    # Verify count matches expectation
    assert summary['count'] == 4

def test_calculate_fidelity_loss_missing_student_scalar():
    """Test behavior when student_scalar is missing."""
    data = {
        'prompt': ['p1'],
        'image_url': ['u1'],
        'teacher_scores': [{'Alignment': 5.0}],
        'student_scalar': [np.nan],
        'human_annotations': [{'Alignment': 5.0}],
        'primary_dimension': ['Alignment']
    }
    df = pd.DataFrame(data)
    
    _, summary = calculate_fidelity_loss(df)
    
    assert summary['count'] == 0
    assert summary['excluded_count'] == 1
    assert 'missing_student_scalar' in summary['excluded_reasons']

def test_calculate_fidelity_loss_missing_human_annotation():
    """Test behavior when human annotation for primary dimension is missing."""
    data = {
        'prompt': ['p1'],
        'image_url': ['u1'],
        'teacher_scores': [{'Alignment': 5.0}],
        'student_scalar': [5.0],
        'human_annotations': [{'Realism': 4.0}], # Missing Alignment
        'primary_dimension': ['Alignment']
    }
    df = pd.DataFrame(data)
    
    _, summary = calculate_fidelity_loss(df)
    
    assert summary['count'] == 0
    assert summary['excluded_count'] == 1
    assert any('missing_human_annotation_Alignment' in r for r in summary['excluded_reasons'])

def test_save_cleaned_data(tmp_path):
    """Test saving the cleaned dataframe."""
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    output_path = tmp_path / "test_output.parquet"
    
    save_cleaned_data(df, str(output_path))
    
    assert output_path.exists()
    loaded = pd.read_parquet(output_path)
    assert len(loaded) == 2

def test_save_summary(tmp_path):
    """Test saving summary JSON."""
    summary = {"mean": 1.5, "count": 10, "excluded_count": 2}
    output_path = tmp_path / "test_summary.json"
    
    save_summary(summary, str(output_path))
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    assert loaded['mean'] == 1.5
    assert loaded['count'] == 10
