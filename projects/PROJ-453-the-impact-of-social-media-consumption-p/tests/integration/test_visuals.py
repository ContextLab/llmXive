import pytest
from pathlib import Path

def test_plots_generated_correctly():
    """Test that visualization files are generated."""
    # This test assumes the visualization script has been run
    expected_files = [
        "results/figures/regression_plot.png",
        "results/figures/sensitivity_table.png"
    ]
    
    for file in expected_files:
        assert Path(file).exists(), f"Missing expected file: {file}"
