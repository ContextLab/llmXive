"""
Unit tests for the visualization module.
Verifies plot generation and file output as per T027.
"""
import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
import matplotlib
# Use non-interactive backend for headless testing
matplotlib.use('Agg') 

# Import the specific functions defined in the API surface
from code.visualization.plots import generate_scatter_plots, generate_importance_plot
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
        # Call the function with real arguments
        generate_scatter_plots(df, 'latency', 'agency_score', output_path)

        # Assert the file was written to disk
        assert os.path.exists(output_path), "Plot file was not created."
        assert os.path.getsize(output_path) > 0, "Plot file is empty."


def test_generate_importance_plot_saves_file():
    """Verify that generate_importance_plot creates a file on disk."""
    # Create mock importance data
    features = ['latency', 'smoothness', 'lead_time']
    importance = [0.4, 0.35, 0.25]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "importance_plot.png")
        generate_importance_plot(features, importance, output_path)

        assert os.path.exists(output_path), "Importance plot file was not created."
        assert os.path.getsize(output_path) > 0, "Importance plot file is empty."


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
        # Note: run_visualization expects feature_cols and target_col
        files = run_visualization(
            input_data_path=input_csv,
            output_dir=output_dir,
            feature_cols=['latency', 'smoothness'],
            target_col='agency_score'
        )

        # Verify outputs: expect scatter plots for each feature
        # The implementation should return a list of created file paths
        assert len(files) >= 2, f"Expected at least 2 plots (one per feature), got {len(files)}"
        
        for f in files:
            assert os.path.exists(f), f"File {f} does not exist."
            assert os.path.getsize(f) > 0, f"File {f} is empty."