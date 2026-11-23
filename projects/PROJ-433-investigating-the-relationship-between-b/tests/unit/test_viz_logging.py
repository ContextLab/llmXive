"""
Unit test for Task T069: ensure that generated plot files are recorded in
``data/analysis_log.txt``.
"""

import os
from pathlib import Path

import pytest

# Import the main function to trigger plot generation
from viz import main as viz_main

ANALYSIS_LOG = Path("data/analysis_log.txt")
PLOT_PATH = Path("data/results/plot_transition_count_DSAT_score.png")

@pytest.fixture(autouse=True)
def clean_environment(tmp_path_factory):
    """
    Ensure a clean state before each test run:
    - Remove any existing analysis log.
    - Remove any existing plot file.
    """
    # Remove log if present
    if ANALYSIS_LOG.is_file():
        ANALYSIS_LOG.unlink()
    # Remove plot if present
    if PLOT_PATH.is_file():
        PLOT_PATH.unlink()
    yield
    # Cleanup after test
    if ANALYSIS_LOG.is_file():
        ANALYSIS_LOG.unlink()
    if PLOT_PATH.is_file():
        PLOT_PATH.unlink()

def test_plot_path_logged(tmp_path):
    """
    Run the viz main routine and verify that:
    1. The plot PNG file is created.
    2. The analysis log contains a line mentioning the plot path.
    """
    # Execute the visualization script
    viz_main()

    # Check that the plot file exists and is non‑empty
    assert PLOT_PATH.is_file(), "Plot file was not created"
    assert PLOT_PATH.stat().st_size > 0, "Plot file is empty"

    # Verify that the analysis log now exists and contains the expected entry
    assert ANALYSIS_LOG.is_file(), "Analysis log file was not created"
    log_content = ANALYSIS_LOG.read_text(encoding="utf-8")
    expected_line = f"Plot generated: {PLOT_PATH}"
    assert expected_line in log_content, f"Log does not contain expected entry: {expected_line}"