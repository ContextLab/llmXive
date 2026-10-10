"""
Minimal unit test to ensure that the plotting script runs without error
and creates the expected PNG files.

The test uses the real aggregated_metrics.csv already present in the
repository, so no synthetic data is introduced.
"""

import os
from pathlib import Path

import pytest

# Import the script as a module to call its main() directly
import importlib.util

PLOTS_SCRIPT = Path("code/visualization/plots.py")
COVERAGE_PNG = Path("data/results/coverage_vs_tau2.png")
BIAS_PNG = Path("data/results/mean_bias_vs_tau2.png")

@pytest.fixture
def clean_output():
    """Remove any pre‑existing PNG files before the test runs."""
    for p in (COVERAGE_PNG, BIAS_PNG):
        if p.is_file():
            p.unlink()
    yield
    # Clean up after test
    for p in (COVERAGE_PNG, BIAS_PNG):
        if p.is_file():
            p.unlink()

def load_module():
    spec = importlib.util.spec_from_file_location("plots", str(PLOTS_SCRIPT))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_plots_generate_files(clean_output):
    """Run the script and verify PNG files are created."""
    assert not COVERAGE_PNG.is_file()
    assert not BIAS_PNG.is_file()

    module = load_module()
    # The script defines a main() function
    module.main()

    assert COVERAGE_PNG.is_file(), "Coverage plot PNG was not created"
    assert BIAS_PNG.is_file(), "Mean bias plot PNG was not created"

    # Basic sanity checks on file size (non‑empty)
    assert COVERAGE_PNG.stat().st_size > 0
    assert BIAS_PNG.stat().st_size > 0