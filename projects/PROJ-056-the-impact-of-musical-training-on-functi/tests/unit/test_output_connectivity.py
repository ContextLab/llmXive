import os
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from analysis.output_connectivity_results import load_processed_connectivity_data, compute_group_statistics, write_connectivity_results

def test_load_processed_connectivity_data(tmp_path):
    """Test loading of network metrics CSV"""
    # Create a mock network_metrics.csv
    mock_data = pd.DataFrame({
        'subject_id': [1, 2, 3, 4],
        'connection_id': ['A', 'A', 'B', 'B'],
        'group': ['musician', 'non_musician', 'musician', 'non_musician'],
        'value': [0.5, 0.3, 0.6, 0.4]
    })
    input_file = tmp_path / "network_metrics.csv"
    mock_data.to_csv(input_file, index=False)
    
    df = load_processed_connectivity_data(str(input_file))
    assert 'connection_id' in df.columns
    assert 'group' in df.columns
    assert 'value' in df.columns
    assert len(df) == 4

def test_compute_group_statistics(tmp_path):
    """Test statistical computation"""
    # Create mock data with enough samples for stats
    np.random.seed(42)
    n_musicians = 50
    n_non = 50
    
    musician_vals = np.random.normal(0.5, 0.1, n_musicians)
    non_musician_vals = np.random.normal(0.4, 0.1, n_non)
    
    mock_data = pd.DataFrame({
        'connection_id': ['conn_A'] * n_musicians + ['conn_A'] * n_non,
        'group': ['musician'] * n_musicians + ['non_musician'] * n_non,
        'value': list(musician_vals) + list(non_musician_vals)
    })
    
    # Save to temp file
    input_file = tmp_path / "network_metrics.csv"
    mock_data.to_csv(input_file, index=False)
    
    df = load_processed_connectivity_data(str(input_file))
    stats_df = compute_group_statistics(df)
    
    assert 'connection_id' in stats_df.columns
    assert 't_stat' in stats_df.columns
    assert 'p_value' in stats_df.columns
    assert 'q_value' in stats_df.columns
    assert 'effect_size' in stats_df.columns
    assert 'ci_lower' in stats_df.columns
    assert 'ci_upper' in stats_df.columns
    assert len(stats_df) == 1

def test_write_connectivity_results(tmp_path):
    """Test writing results to CSV"""
    output_file = tmp_path / "connectivity_results.csv"
    
    # Create a valid stats dataframe
    stats_df = pd.DataFrame({
        'connection_id': ['conn_A'],
        't_stat': [2.5],
        'p_value': [0.01],
        'q_value': [0.02],
        'effect_size': [0.8],
        'ci_lower': [0.2],
        'ci_upper': [1.5]
    })
    
    write_connectivity_results(stats_df, str(output_file))
    
    assert output_file.exists()
    result_df = pd.read_csv(output_file)
    assert list(result_df.columns) == ['connection_id', 't_stat', 'p_value', 'q_value', 'effect_size', 'ci_lower', 'ci_upper']
    assert len(result_df) == 1
