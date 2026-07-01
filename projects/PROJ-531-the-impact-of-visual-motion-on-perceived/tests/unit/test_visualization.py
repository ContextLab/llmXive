"""
Unit tests for the visualization module.
"""
import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from code.visualization.plots import generate_scatter_plots
from code.visualization import run_visualization


def test_generate_scatter_plots_saves_file():
    """Verify that generate_scatter_plots creates a file on disk."""
    # Create a mock dataframe
    data = {
        'latency': [0.1, 0.2, 0.3, 0.4, 0.5],
        'agency_score': [1.0, 2.0, 3.0, 4.0, 5.0]
    }
    df = pd.DataFrame(data)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_plot.png")
        generate_scatter_plots(df, 'latency', 'agency_score', output_path)

        assert os.path.exists(output_path), "Plot file was not created."
        assert os.path.getsize(output_path) > 0, "Plot file is empty."


def test_run_visualization_integration():
    """Test the full visualization pipeline with a temporary CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup input data
        input_csv = os.path.join(tmpdir, "cleaned_data.csv")
        df = pd.DataFrame({
            'latency': [0.1, 0.2, 0.3, 0.4, 0.5],
            'smoothness': [0.8, 0.7, 0.6, 0.5, 0.4],
            'lead_time': [0.2, 0.3, 0.4, 0.5, 0.6],
            'agency_score': [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        df.to_csv(input_csv, index=False)

        output_dir = os.path.join(tmpdir, "plots")

        # Run the visualization function
        files = run_visualization(
            input_data_path=input_csv,
            output_dir=output_dir,
            feature_cols=['latency', 'smoothness'],
            target_col='agency_score'
        )

        # Verify outputs
        assert len(files) == 2, f"Expected 2 plots, got {len(files)}"
        for f in files:
            assert os.path.exists(f), f"File {f} does not exist."
            assert os.path.getsize(f) > 0, f"File {f} is empty."