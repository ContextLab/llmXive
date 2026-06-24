"""Tests for ``code.analysis.validate_variance``."""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

import pytest

# Import the function from the module we just created
from analysis.validate_variance import (
    _read_rmse_values,
    validate_rmse_variance,
)


def _write_metrics_csv(path: Path, rmse_values: list[float]) -> None:
    """Utility to write a minimal ``metrics.csv`` file."""
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Seed", "RMSE"])
        for idx, val in enumerate(rmse_values):
            writer.writerow([idx, f"{val:.6f}"])


def test_read_rmse_values(tmp_path: Path) -> None:
    csv_path = tmp_path / "metrics.csv"
    _write_metrics_csv(csv_path, [0.5, 0.6, 0.55])
    values = _read_rmse_values(csv_path)
    assert values == [0.5, 0.6, 0.55]


def test_validate_rmse_variance_success(tmp_path: Path) -> None:
    """Coefficient of variation < 10 % should succeed."""
    csv_path = tmp_path / "metrics.csv"
    # Values with low spread
    _write_metrics_csv(csv_path, [0.50, 0.51, 0.49, 0.505, 0.495])
    assert validate_rmse_variance(metrics_path=csv_path, threshold=0.10) is True


def test_validate_rmse_variance_failure(tmp_path: Path) -> None:
    """Coefficient of variation > 10 % should fail."""
    csv_path = tmp_path / "metrics.csv"
    # Values with higher spread
    _write_metrics_csv(csv_path, [0.40, 0.60, 0.55, 0.45, 0.70])
    assert validate_rmse_variance(metrics_path=csv_path, threshold=0.10) is False


def test_missing_file(tmp_path: Path) -> None:
    """Missing CSV should result in a False return."""
    missing_path = tmp_path / "nonexistent.csv"
    assert validate_rmse_variance(metrics_path=missing_path) is False


def test_invalid_header(tmp_path: Path) -> None:
    """CSV without an RMSE column should result in a False return."""
    path = tmp_path / "bad.csv"
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Seed", "MAE"])
        writer.writerow([0, 0.1])
    assert validate_rmse_variance(metrics_path=path) is False