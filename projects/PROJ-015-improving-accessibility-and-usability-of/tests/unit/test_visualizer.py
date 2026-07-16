import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
from analysis.visualizer import Visualizer

@pytest.fixture
def sample_metrics_df():
    """
    Creates a small, valid DataFrame mimicking the output of T026.
    """
    data = {
        'interface_type': ['Traditional', 'Explainable', 'Traditional', 'Explainable'],
        'completion_time': [120.5, 110.2, 125.0, 108.5],
        'error_count': [5, 3, 6, 2],
        'sus_score': [65.0, 78.5, 62.0, 80.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Creates a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_plot_boxplot_with_error_bars(sample_metrics_df, temp_output_dir):
    """
    Tests that the boxplot function generates a valid image file.
    """
    viz = Visualizer()
    out_path = os.path.join(temp_output_dir, "test_boxplot.png")
    
    # Execute
    viz.plot_boxplot_with_error_bars(
        sample_metrics_df, 
        'interface_type', 
        'completion_time', 
        out_path,
        title="Test Plot"
    )
    
    # Verify file exists and has content
    assert os.path.exists(out_path), f"Output file not created at {out_path}"
    assert os.path.getsize(out_path) > 0, "Output file is empty"

def test_generate_all_plots_missing_metric(sample_metrics_df, temp_output_dir):
    """
    Tests that the function handles missing metrics gracefully (logs warning, skips).
    """
    viz = Visualizer()
    # Remove a column to simulate missing data
    df_missing = sample_metrics_df.drop(columns=['error_count'])
    
    # This should not raise an exception, but log a warning
    viz.generate_all_plots(df_missing, temp_output_dir)
    
    # Check that plots for existing metrics were created
    assert os.path.exists(os.path.join(temp_output_dir, "boxplot_completion_time.png"))
    assert os.path.exists(os.path.join(temp_output_dir, "boxplot_sus_score.png"))
    # Plot for missing metric should not exist
    assert not os.path.exists(os.path.join(temp_output_dir, "boxplot_error_count.png"))

def test_generate_all_plots_comprehensive(sample_metrics_df, temp_output_dir):
    """
    Tests the full generation pipeline with all expected metrics.
    """
    viz = Visualizer()
    viz.generate_all_plots(sample_metrics_df, temp_output_dir)
    
    expected_files = [
        "boxplot_completion_time.png",
        "boxplot_error_count.png",
        "boxplot_sus_score.png"
    ]
    
    for filename in expected_files:
        path = os.path.join(temp_output_dir, filename)
        assert os.path.exists(path), f"Expected plot {filename} was not created"
        assert os.path.getsize(path) > 0, f"Plot {filename} is empty"
