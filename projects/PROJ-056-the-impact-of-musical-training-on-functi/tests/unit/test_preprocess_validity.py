import os
import pandas as pd
import pytest
from pathlib import Path
import sys

# Add code to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.preprocess import calculate_dataset_validity, write_validity_report, main
from data.synthetic_generator import generate_synthetic_dataset

def test_calculate_dataset_validity():
    """
    Test that calculate_dataset_validity correctly computes the percentage
    of subjects with valid years_of_training labels.
    """
    # Create a mock dataframe
    data = {
        'subject_id': [f'sub_{i}' for i in range(10)],
        'group': ['musician'] * 5 + ['non_musician'] * 5,
        'years_of_training': [2.0, 3.0, 1.5, 0.5, 4.0, 0.0, 0.0, 0.0, 0.0, 0.0], # All valid numbers
        'age': [15] * 10,
        'sex': ['M'] * 5 + ['F'] * 5,
        'motion_score': [0.1] * 10,
        'ses_score': [50] * 10
    }
    df = pd.DataFrame(data)

    metrics = calculate_dataset_validity(df)

    assert 'valid_subjects_percentage' in metrics
    assert 'total_subjects' in metrics
    assert 'valid_subjects' in metrics
    
    # All 10 have valid training years (not NaN)
    assert metrics['total_subjects'] == 10
    assert metrics['valid_subjects'] == 10
    assert metrics['valid_subjects_percentage'] == 100.0

def test_calculate_dataset_validity_with_missing():
    """
    Test validity calculation when some years_of_training are missing (NaN).
    """
    data = {
        'subject_id': [f'sub_{i}' for i in range(10)],
        'group': ['musician'] * 5 + ['non_musician'] * 5,
        'years_of_training': [2.0, 3.0, None, 0.5, 4.0, 0.0, 0.0, 0.0, 0.0, 0.0], # One NaN
        'age': [15] * 10,
        'sex': ['M'] * 5 + ['F'] * 5,
        'motion_score': [0.1] * 10,
        'ses_score': [50] * 10
    }
    df = pd.DataFrame(data)

    metrics = calculate_dataset_validity(df)

    assert metrics['total_subjects'] == 10
    assert metrics['valid_subjects'] == 9
    assert abs(metrics['valid_subjects_percentage'] - 90.0) < 1e-6

def test_write_validity_report(tmp_path):
    """
    Test that write_validity_report creates the CSV file with correct columns.
    """
    metrics = {
        'valid_subjects_percentage': 95.5,
        'total_subjects': 100,
        'valid_subjects': 95
    }
    output_path = tmp_path / "dataset_validity_report.csv"
    
    write_validity_report(metrics, output_path)
    
    assert output_path.exists()
    
    df = pd.read_csv(output_path)
    assert 'metric' in df.columns
    assert 'value' in df.columns
    
    # Check specific values
    metric_row = df[df['metric'] == 'valid_subjects_percentage']
    assert len(metric_row) == 1
    assert metric_row.iloc[0]['value'] == 95.5

def test_full_preprocess_pipeline_validity_output(tmp_path):
    """
    Integration test: Run the main function logic to ensure the file is written.
    """
    # Generate synthetic data
    df = generate_synthetic_dataset(n_subjects=20, n_timepoints=50, n_rois=10)
    
    # Save to temp CSV
    input_csv = tmp_path / "input.csv"
    df.to_csv(input_csv, index=False)
    
    output_dir = tmp_path / "processed"
    output_dir.mkdir()
    
    # Mock the main logic
    from data.preprocess import calculate_dataset_validity, write_validity_report, preprocess_subjects
    
    df_cleaned = preprocess_subjects(df, 'verification')
    metrics = calculate_dataset_validity(df_cleaned)
    validity_path = output_dir / "dataset_validity_report.csv"
    write_validity_report(metrics, validity_path)
    
    assert validity_path.exists()
    result_df = pd.read_csv(validity_path)
    assert 'metric' in result_df.columns
    assert 'value' in result_df.columns
    assert 'valid_subjects_percentage' in result_df['metric'].values