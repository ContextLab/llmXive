"""
Unit tests for code/analysis/viz.py
"""
import os
import sys
import tempfile
import pandas as pd
import pytest
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.analysis.viz import (
    load_metrics_data,
    calculate_pareto_frontier,
    plot_pareto_frontier,
    plot_alignment_by_density
)

@pytest.fixture
def sample_data():
    """Create sample simulation data for testing."""
    data = {
        'alignment_score': [0.8, 0.9, 0.85, 0.95, 0.7, 0.88, 0.92],
        'total_latency_ms': [100, 200, 150, 300, 50, 250, 280],
        'density_level': [1, 3, 1, 5, 1, 3, 5]
    }
    return pd.DataFrame(data)

def test_load_metrics_data(tmp_path, sample_data):
    """Test loading metrics data from CSV."""
    input_file = tmp_path / "test_results.csv"
    sample_data.to_csv(input_file, index=False)
    
    loaded_df = load_metrics_data(str(input_file))
    
    assert len(loaded_df) == len(sample_data)
    assert 'alignment_score' in loaded_df.columns
    assert 'total_latency_ms' in loaded_df.columns
    assert 'density_level' in loaded_df.columns

def test_load_metrics_data_missing_file(tmp_path):
    """Test loading from non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_metrics_data(str(tmp_path / "nonexistent.csv"))

def test_calculate_pareto_frontier(sample_data):
    """Test Pareto frontier calculation."""
    frontier = calculate_pareto_frontier(sample_data)
    
    # Verify that all frontier points are actually in the original data
    assert len(frontier) <= len(sample_data)
    
    # Verify no point in frontier is dominated by another in frontier
    # (Simplified check: ensure frontier is not empty for this data)
    assert len(frontier) > 0
    
    # Verify the logic: for each point in frontier, there is no other point
    # with lower latency AND higher/equal alignment
    for _, p in frontier.iterrows():
        for _, other in sample_data.iterrows():
            if other['total_latency_ms'] < p['total_latency_ms'] and other['alignment_score'] >= p['alignment_score']:
                # This point should not be in frontier
                assert False, f"Point {p} dominated by {other}"

def test_plot_pareto_frontier(tmp_path, sample_data):
    """Test generating Pareto plot."""
    frontier = calculate_pareto_frontier(sample_data)
    output_file = tmp_path / "pareto.png"
    
    plot_pareto_frontier(sample_data, frontier, str(output_file))
    
    assert output_file.exists()
    assert output_file.stat().st_size > 0

def test_plot_alignment_by_density(tmp_path, sample_data):
    """Test generating density plot."""
    output_file = tmp_path / "density.png"
    
    plot_alignment_by_density(sample_data, str(output_file))
    
    assert output_file.exists()
    assert output_file.stat().st_size > 0

def test_empty_dataframe():
    """Test handling of empty dataframe."""
    empty_df = pd.DataFrame(columns=['alignment_score', 'total_latency_ms', 'density_level'])
    frontier = calculate_pareto_frontier(empty_df)
    assert len(frontier) == 0