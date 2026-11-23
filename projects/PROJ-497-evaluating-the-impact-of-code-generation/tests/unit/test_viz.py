import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt

from viz import load_aggregated_data, prepare_boxplot_data, generate_boxplot

@pytest.fixture
def sample_data_csv(tmp_path):
    """Create a temporary CSV file with sample aggregated data."""
    csv_path = tmp_path / "aggregated_analysis_dataset.csv"
    data = {
        'task_id': ['task1', 'task2', 'task3', 'task4'],
        'source_type': ['LLM', 'Human', 'LLM', 'Human'],
        'mean_vuln_count': [2.5, 1.0, 3.0, 0.5],
        'lines_of_code': [50, 45, 60, 40],
        'benchmark': ['HumanEval', 'HumanEval', 'MBPP', 'MBPP']
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture
def sample_data_empty(tmp_path):
    """Create a temporary CSV file with empty data."""
    csv_path = tmp_path / "empty_dataset.csv"
    data = {
        'task_id': [],
        'source_type': [],
        'mean_vuln_count': [],
        'lines_of_code': []
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path

def test_load_aggregated_data(sample_data_csv):
    """Test loading aggregated data from CSV."""
    df = load_aggregated_data(sample_data_csv)
    assert len(df) == 4
    assert 'source_type' in df.columns
    assert 'mean_vuln_count' in df.columns
    assert df['source_type'].nunique() == 2

def test_load_aggregated_data_missing_file(tmp_path):
    """Test loading data from a non-existent file raises error."""
    missing_path = tmp_path / "non_existent.csv"
    with pytest.raises(FileNotFoundError):
        load_aggregated_data(missing_path)

def test_prepare_boxplot_data(sample_data_csv):
    """Test data preparation for boxplot."""
    df = load_aggregated_data(sample_data_csv)
    plot_df = prepare_boxplot_data(df)
    
    assert len(plot_df) == 4
    assert all(plot_df['source_type'].isin(['LLM', 'Human']))
    assert not plot_df['mean_vuln_count'].isna().any()

def test_prepare_boxplot_data_empty(sample_data_empty):
    """Test data preparation with empty dataset."""
    df = load_aggregated_data(sample_data_empty)
    plot_df = prepare_boxplot_data(df)
    assert plot_df.empty

def test_prepare_boxplot_data_invalid_types(sample_data_csv):
    """Test handling of non-numeric vulnerability counts."""
    df = load_aggregated_data(sample_data_csv)
    # Introduce invalid data
    df.loc[0, 'mean_vuln_count'] = 'invalid'
    plot_df = prepare_boxplot_data(df)
    # Invalid row should be dropped
    assert len(plot_df) == 3

def test_generate_boxplot(sample_data_csv, tmp_path):
    """Test boxplot generation and file creation."""
    df = load_aggregated_data(sample_data_csv)
    plot_df = prepare_boxplot_data(df)
    
    output_path = tmp_path / "test_boxplot.png"
    generate_boxplot(plot_df, output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    
    # Verify no plot is left open
    assert len(plt.get_fignums()) == 0

def test_generate_boxplot_empty_data(tmp_path):
    """Test boxplot generation with empty data."""
    empty_df = pd.DataFrame()
    output_path = tmp_path / "empty_plot.png"
    
    # Should not raise, but log warning
    generate_boxplot(empty_df, output_path)
    
    # File should not be created
    assert not output_path.exists()