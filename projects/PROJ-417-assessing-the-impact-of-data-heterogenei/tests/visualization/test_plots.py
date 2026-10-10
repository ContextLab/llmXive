"""
Simple integration test for the visualization script.

The test runs the ``code.visualization.plots`` module's ``main`` function
and checks that the expected PNG files are created.  It does not verify
the visual content – that would require image comparison which is
unnecessary for the CI's correctness check.
"""

import pathlib
import sys

import pytest

# Ensure the project root is on the import path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from visualization.plots import (
    AGG_METRICS_CSV,
    COVERAGE_PNG,
    BIAS_PNG,
    main,
)

@pytest.fixture(autouse=True)
def cleanup_png_files(tmp_path, monkeypatch):
    """Redirect output files to a temporary directory for isolation."""
    # Patch the output paths used by the script
    monkeypatch.setattr(
        "visualization.plots.OUTPUT_DIR", tmp_path, raising=False
    )
    monkeypatch.setattr(
        "visualization.plots.COVERAGE_PNG", tmp_path / "coverage.png", raising=False
    )
    monkeypatch.setattr(
        "visualization.plots.BIAS_PNG", tmp_path / "bias.png", raising=False
    )
    # Ensure the CSV path points to the real aggregated metrics file
    monkeypatch.setattr(
        "visualization.plots.AGG_METRICS_CSV", AGG_METRICS_CSV, raising=False
    )
    yield
    # Cleanup after test
    for p in [COVERAGE_PNG, BIAS_PNG]:
        if p.exists():
            p.unlink()

def test_plots_are_created():
    """Run the script and assert that both PNG files appear."""
    exit_code = main()
    assert exit_code == 0, "Plot script should exit cleanly"
    assert COVERAGE_PNG.is_file(), "Coverage PNG was not created"
    assert BIAS_PNG.is_file(), "Bias PNG was not created"