"""
Unit test for the exploratory scatter‑plot generation.
The test runs the module and checks that the expected PNG file is created.
"""

import os
from pathlib import Path

import pytest

# Import the function directly to avoid executing the full pipeline.
from analysis.exploratory import generate_exploratory_plots, PLOT_PATH


@pytest.mark.usefixtures("tmp_path_factory")
def test_scatter_plot_is_created(tmp_path):
    # Run the plot generation; it will write to the project data directory.
    generate_exploratory_plots()

    # Verify that the file exists and is a non‑empty PNG.
    assert PLOT_PATH.is_file(), f"Expected plot at {PLOT_PATH}"
    assert PLOT_PATH.stat().st_size > 0, "Plot file is empty"

    # Clean up after test to keep the repository tidy.
    try:
        os.remove(PLOT_PATH)
    except OSError:
        pass