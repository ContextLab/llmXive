"""
Unit tests for the plotting utilities.
"""
import os
import tempfile
from pathlib import Path

# Import plotting functions from the project's utils package
from code.utils.plotting import (
    plot_convergence_loglog,
    plot_regression_scatter,
)


def test_plot_convergence_loglog_creates_file():
    # Minimal data for the log‑log plot
    data = [{"epsilon": 0.1, "convergence_time": 25}]

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "convergence.png"
        returned_path = plot_convergence_loglog(data, str(out_path))

        # The function should return the absolute path
        assert Path(returned_path) == out_path.resolve()
        # The file must exist and be non‑empty
        assert out_path.is_file()
        assert out_path.stat().st_size > 0


def test_plot_regression_scatter_creates_file():
    x_vals = [0.1, 0.2, 0.3, 0.4]
    y_vals = [10, 20, 30, 40]

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "regression.png"
        returned_path = plot_regression_scatter(x_vals, y_vals, str(out_path))

        assert Path(returned_path) == out_path.resolve()
        assert out_path.is_file()
        assert out_path.stat().st_size > 0