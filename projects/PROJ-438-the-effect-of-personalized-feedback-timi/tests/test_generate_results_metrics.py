"""
Unit tests for generate_results_metrics.py
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from generate_results_metrics import (
    load_effect_sizes,
    load_sensitivity_stats,
    merge_metrics,
    save_results_metrics
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_effect_sizes(temp_data_dir):
    """Create a sample effect_sizes.csv file."""
    data = {
        'comparison': ['Immediate vs Delayed', 'Immediate vs Variable', 'Delayed vs Variable'],
        'coef': [0.5, 0.2, -0.3],
        'se': [0.1, 0.1, 0.1],
        't_stat': [5.0, 2.0, -3.0],
        'p_value': [0.001, 0.045, 0.003],
        'cohens_d': [0.5, 0.2, -0.3]
    }
    df = pd.DataFrame(data)
    path = temp_data_dir / 'effect_sizes.csv'
    df.to_csv(path, index=False)
    return path

@pytest.fixture
def sample_sensitivity_stats(temp_data_dir):
    """Create a sample sensitivity_results.csv file."""
    data = {
        'boundary_shift': [-0.1, -0.05, 0.0, 0.05, 0.1],
        'significant_count': [150, 152, 155, 148, 151],
        'total_count': [200, 200, 200, 200, 200],
        'stability_rate': [0.75, 0.76, 0.775, 0.74, 0.755]
    }
    df = pd.DataFrame(data)
    path = temp_data_dir / 'sensitivity_results.csv'
    df.to_csv(path, index=False)
    return path

def test_load_effect_sizes(sample_effect_sizes):
    """Test loading effect sizes from CSV."""
    df = load_effect_sizes(sample_effect_sizes)
    assert len(df) == 3
    assert 'comparison' in df.columns
    assert 'cohens_d' in df.columns
    assert df['p_value'].iloc[0] == 0.001

def test_load_sensitivity_stats(sample_sensitivity_stats):
    """Test loading sensitivity stats from CSV."""
    df = load_sensitivity_stats(sample_sensitivity_stats)
    assert len(df) == 5
    assert 'stability_rate' in df.columns
    assert df['stability_rate'].mean() > 0.7

def test_merge_metrics(sample_effect_sizes, sample_sensitivity_stats):
    """Test merging effect sizes and sensitivity stats."""
    effects_df = load_effect_sizes(sample_effect_sizes)
    sensitivity_df = load_sensitivity_stats(sample_sensitivity_stats)
    
    merged_df = merge_metrics(effects_df, sensitivity_df)
    
    # Check that global metrics were added
    assert 'global_stability_rate' in merged_df.columns
    assert 'global_flip_rate' in merged_df.columns
    
    # Check that original columns are preserved
    assert 'comparison' in merged_df.columns
    assert 'effect_size_cohens_d' in merged_df.columns
    
    # Check that the number of rows is preserved
    assert len(merged_df) == 3

def test_save_results_metrics(sample_effect_sizes, sample_sensitivity_stats, temp_data_dir):
    """Test saving results metrics to CSV."""
    effects_df = load_effect_sizes(sample_effect_sizes)
    sensitivity_df = load_sensitivity_stats(sample_sensitivity_stats)
    merged_df = merge_metrics(effects_df, sensitivity_df)
    
    output_path = temp_data_dir / 'results_metrics.csv'
    save_results_metrics(merged_df, output_path)
    
    assert output_path.exists()
    
    # Verify content
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == 3
    assert 'global_stability_rate' in saved_df.columns
    
    # Verify non-empty
    assert saved_df['global_stability_rate'].notna().all()

def test_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        load_effect_sizes(Path("non_existent_file.csv"))
    
    with pytest.raises(FileNotFoundError):
        load_sensitivity_stats(Path("non_existent_file.csv"))