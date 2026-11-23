"""
Integration tests for output_connectivity_results module.

These tests verify that the connectivity results pipeline:
1. Correctly loads processed data
2. Computes accurate statistics
3. Writes valid output files
"""
import os
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.output_connectivity_results import (
    load_processed_connectivity_data,
    compute_group_statistics,
    write_connectivity_results
)

@pytest.fixture
def sample_data():
    """Create sample connectivity and subject data for testing."""
    # Create sample connectivity data (10 subjects, 5 connections)
    np.random.seed(42)
    n_subjects = 10
    n_connections = 5
    
    connectivity_data = {
        'subject_id': [f'sub_{i:03d}' for i in range(n_subjects)],
        'conn_1': np.random.randn(n_subjects),
        'conn_2': np.random.randn(n_subjects),
        'conn_3': np.random.randn(n_subjects),
        'conn_4': np.random.randn(n_subjects),
        'conn_5': np.random.randn(n_subjects),
    }
    connectivity_df = pd.DataFrame(connectivity_data)
    
    # Create sample subject data with groups
    subject_data = {
        'subject_id': [f'sub_{i:03d}' for i in range(n_subjects)],
        'group': ['musician'] * 5 + ['non_musician'] * 5,
        'years_of_training': [2.5, 3.0, 1.5, 4.0, 2.0, 0.0, 0.5, 0.0, 0.2, 0.0],
    }
    subject_df = pd.DataFrame(subject_data)
    
    return connectivity_df, subject_df

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_processed_connectivity_data(sample_data):
    """Test loading of connectivity and subject data."""
    connectivity_df, subject_df = sample_data
    
    # Save to temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        conn_path = Path(tmpdir) / "connectivity.csv"
        subj_path = Path(tmpdir) / "subjects.csv"
        
        connectivity_df.to_csv(conn_path, index=False)
        subject_df.to_csv(subj_path, index=False)
        
        # Load data
        loaded_conn, loaded_subj = load_processed_connectivity_data(
            str(conn_path),
            str(subj_path)
        )
        
        # Verify data loaded correctly
        assert len(loaded_conn) == len(connectivity_df)
        assert len(loaded_subj) == len(subject_df)
        assert list(loaded_conn.columns) == list(connectivity_df.columns)
        assert list(loaded_subj.columns) == list(subject_df.columns)

def test_compute_group_statistics(sample_data):
    """Test computation of group statistics."""
    connectivity_df, subject_df = sample_data
    
    # Compute statistics
    results_df = compute_group_statistics(connectivity_df, subject_df)
    
    # Verify results structure
    expected_columns = ['connection_id', 't_stat', 'p_value', 'q_value', 'effect_size', 'ci_lower', 'ci_upper']
    assert list(results_df.columns) == expected_columns
    
    # Verify we have results for all connections
    assert len(results_df) == 5  # 5 connections
    
    # Verify statistical values are reasonable
    assert all(results_df['t_stat'] != 0)  # t-stats should be non-zero
    assert all((results_df['p_value'] >= 0) & (results_df['p_value'] <= 1))  # p-values in [0, 1]
    assert all((results_df['q_value'] >= 0) & (results_df['q_value'] <= 1))  # q-values in [0, 1]

def test_write_connectivity_results(sample_data, temp_output_dir):
    """Test writing of connectivity results to CSV."""
    connectivity_df, subject_df = sample_data
    
    # Compute statistics
    results_df = compute_group_statistics(connectivity_df, subject_df)
    
    # Write results
    output_path = temp_output_dir / "connectivity_results.csv"
    write_connectivity_results(results_df, str(output_path))
    
    # Verify file exists
    assert os.path.exists(output_path)
    
    # Verify file contents
    loaded_results = pd.read_csv(output_path)
    assert len(loaded_results) == len(results_df)
    assert list(loaded_results.columns) == list(results_df.columns)

def test_full_pipeline(sample_data, temp_output_dir):
    """Test the full pipeline from data loading to file writing."""
    connectivity_df, subject_df = sample_data
    
    # Save to temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        conn_path = Path(tmpdir) / "connectivity.csv"
        subj_path = Path(tmpdir) / "subjects.csv"
        
        connectivity_df.to_csv(conn_path, index=False)
        subject_df.to_csv(subj_path, index=False)
        
        # Load data
        loaded_conn, loaded_subj = load_processed_connectivity_data(
            str(conn_path),
            str(subj_path)
        )
        
        # Compute statistics
        results_df = compute_group_statistics(loaded_conn, loaded_subj)
        
        # Write results
        output_path = Path(temp_output_dir) / "connectivity_results.csv"
        write_connectivity_results(results_df, str(output_path))
        
        # Verify final output
        assert os.path.exists(output_path)
        final_results = pd.read_csv(output_path)
        
        # Verify expected columns
        expected_columns = ['connection_id', 't_stat', 'p_value', 'q_value', 'effect_size', 'ci_lower', 'ci_upper']
        assert list(final_results.columns) == expected_columns
        
        # Verify data integrity
        assert len(final_results) == 5  # 5 connections
        assert all(final_results['p_value'] >= 0)
        assert all(final_results['q_value'] >= 0)
