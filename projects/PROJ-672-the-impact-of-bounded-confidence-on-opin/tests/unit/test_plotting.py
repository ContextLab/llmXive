"""
Unit tests for the plotting utilities.

The tests only verify that the functions run without error and that the
output files are created with a non‑zero size.
"""
import os
import sys
import tempfile

# Ensure the project’s `code` directory is on the import path so that
# `utils.plotting` can be imported (the utils package lives under `code/`).
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

from utils.plotting import plot_convergence_loglog, plot_regression_scatter


def test_plot_convergence_loglog_creates_file():
    """A simple log‑log plot should be written to the requested path."""
    data = [
        {"epsilon": 0.05, "convergence_time": 1500},
        {"epsilon": 0.10, "convergence_time": 800},
        {"epsilon": 0.20, "convergence_time": 200},
        {"epsilon": 0.30, "convergence_time": 85},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "convergence.png")
        result_path = plot_convergence_loglog(data, out_path)

        # The function returns an absolute path; ensure it matches the file we expect.
        assert os.path.abspath(out_path) == result_path
        assert os.path.isfile(out_path)
        # File should be larger than a few bytes (a valid PNG is > 1 KB).
        assert os.path.getsize(out_path) > 1024


def test_plot_regression_scatter_creates_file():
    """A scatter plot (with optional regression line) must be saved."""
    x_vals = [0.1, 0.2, 0.35, 0.5, 0.65, 0.8]
    y_vals = [2.1, 2.5, 3.0, 3.6, 4.2, 4.9]

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "scatter.png")
        result_path = plot_regression_scatter(x_vals, y_vals, out_path)

        assert os.path.abspath(out_path) == result_path
        assert os.path.isfile(out_path)
        assert os.path.getsize(out_path) > 1024