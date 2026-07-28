"""
Tests for T024: Dimensional Fidelity Loss Calculation.
"""
import os
import tempfile
import json
import pandas as pd
import numpy as np
import pytest

# Import the functions from the module
# Note: We assume the module is in code/fidelity_loss.py
# Adjust import path if necessary based on project structure
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from fidelity_loss import calculate_fidelity_loss, load_raw_data, save_cleaned_data

@pytest.fixture
def sample_raw_data():
    """Create a sample dataframe mimicking the output of T012/T013/T014."""
    data = [
        {
            "sample_id": "1",
            "prompt": "Sample 1",
            "image_url": "url1",
            "teacher_scores": {"Alignment": 0.9, "Realism": 0.8, "Aesthetics": 0.7, "Plausibility": 0.6},
            "student_scalar": 0.85,
            "human_annotations": {"Alignment": 0.9, "Realism": 0.8, "Aesthetics": 0.7, "Plausibility": 0.6},
            "primary_dimension": "Alignment"
        },
        {
            "sample_id": "2",
            "prompt": "Sample 2",
            "image_url": "url2",
            "teacher_scores": {"Alignment": 0.5, "Realism": 0.4, "Aesthetics": 0.3, "Plausibility": 0.2},
            "student_scalar": 0.3,
            "human_annotations": {"Alignment": 0.5, "Realism": 0.4, "Aesthetics": 0.3, "Plausibility": 0.2},
            "primary_dimension": "Realism"
        },
        {
            "sample_id": "3",
            "prompt": "Sample 3 (Missing Primary)",
            "image_url": "url3",
            "teacher_scores": {"Alignment": 0.1, "Realism": 0.1, "Aesthetics": 0.1, "Plausibility": 0.1},
            "student_scalar": 0.1,
            "human_annotations": {"Alignment": 0.1, "Realism": 0.1, "Aesthetics": 0.1, "Plausibility": 0.1},
            "primary_dimension": None  # Should be excluded
        },
        {
            "sample_id": "4",
            "prompt": "Sample 4 (Missing Student)",
            "image_url": "url4",
            "teacher_scores": {"Alignment": 0.2, "Realism": 0.2, "Aesthetics": 0.2, "Plausibility": 0.2},
            "student_scalar": np.nan,  # Should be excluded
            "human_annotations": {"Alignment": 0.2, "Realism": 0.2, "Aesthetics": 0.2, "Plausibility": 0.2},
            "primary_dimension": "Alignment"
        },
        {
            "sample_id": "5",
            "prompt": "Sample 5 (Missing Human Ann)",
            "image_url": "url5",
            "teacher_scores": {"Alignment": 0.3, "Realism": 0.3, "Aesthetics": 0.3, "Plausibility": 0.3},
            "student_scalar": 0.3,
            "human_annotations": None,  # Should be excluded
            "primary_dimension": "Aesthetics"
        },
        {
            "sample_id": "6",
            "prompt": "Sample 6 (Human Ann Missing Key)",
            "image_url": "url6",
            "teacher_scores": {"Alignment": 0.4, "Realism": 0.4, "Aesthetics": 0.4, "Plausibility": 0.4},
            "student_scalar": 0.4,
            "human_annotations": {"Alignment": 0.4},  # Missing 'Plausibility' which is primary
            "primary_dimension": "Plausibility"
        }
    ]
    return pd.DataFrame(data)

def test_calculate_fidelity_loss_filters_and_computes(sample_raw_data):
    """Test that calculate_fidelity_loss correctly filters and computes MAE."""
    result_df = calculate_fidelity_loss(sample_raw_data)

    # Expected: Only samples 1 and 2 should remain
    # Sample 1: |0.85 - 0.9| = 0.05
    # Sample 2: |0.3 - 0.4| = 0.1
    assert len(result_df) == 2, f"Expected 2 rows, got {len(result_df)}"

    # Check sample IDs
    assert set(result_df['sample_id'].tolist()) == {'1', '2'}

    # Check fidelity loss values
    row1 = result_df[result_df['sample_id'] == '1'].iloc[0]
    assert np.isclose(row1['fidelity_loss'], 0.05), f"Expected 0.05, got {row1['fidelity_loss']}"

    row2 = result_df[result_df['sample_id'] == '2'].iloc[0]
    assert np.isclose(row2['fidelity_loss'], 0.1), f"Expected 0.1, got {row2['fidelity_loss']}"

def test_save_and_load_cleaned_data(sample_raw_data):
    """Test saving to parquet and loading back."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "cleaned.parquet")
        clean_df = calculate_fidelity_loss(sample_raw_data)
        save_cleaned_data(clean_df, output_path)

        assert os.path.exists(output_path)

        loaded_df = load_raw_data(output_path)
        assert len(loaded_df) == 2
        assert 'fidelity_loss' in loaded_df.columns

def test_empty_dataframe():
    """Test behavior with empty dataframe."""
    empty_df = pd.DataFrame(columns=['sample_id', 'primary_dimension', 'student_scalar', 'human_annotations'])
    result = calculate_fidelity_loss(empty_df)
    assert len(result) == 0
    assert 'fidelity_loss' in result.columns