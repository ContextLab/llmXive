"""Unit tests for ``code.analysis.check_agency_variance``."""

from __future__ import annotations

import pandas as pd
import pytest
from pathlib import Path

# Import the function under test
from analysis.check_agency_variance import check_variance, PipelineError


def _write_csv(tmp_path: Path, values: list[float]) -> Path:
    """Helper to write a minimal agency_scores CSV."""
    df = pd.DataFrame({"session_id": range(len(values)), "agency_score": values})
    csv_path = tmp_path / "agency_scores.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


def test_check_variance_raises_on_zero_variance(tmp_path: Path):
    """A constant score column should trigger a PipelineError."""
    csv_path = _write_csv(tmp_path, [0.5, 0.5, 0.5, 0.5])
    with pytest.raises(PipelineError, match="Variance"):
        check_variance(csv_path, threshold=1e-6)


def test_check_variance_passes_on_nonzero_variance(tmp_path: Path):
    """A variable score column should not raise."""
    csv_path = _write_csv(tmp_path, [0.1, 0.4, 0.7, 0.9])
    # Should complete without raising
    check_variance(csv_path, threshold=1e-6)


def test_check_variance_missing_column(tmp_path: Path):
    """Missing ``agency_score`` column should raise."""
    df = pd.DataFrame({"session_id": [1, 2, 3], "some_other": [0.1, 0.2, 0.3]})
    csv_path = tmp_path / "bad.csv"
    df.to_csv(csv_path, index=False)

    with pytest.raises(PipelineError, match="Missing"):
        check_variance(csv_path, threshold=1e-6)


def test_check_variance_file_not_found(tmp_path: Path):
    """Non‑existent file path should raise."""
    missing_path = tmp_path / "does_not_exist.csv"
    with pytest.raises(PipelineError, match="File not found"):
        check_variance(missing_path, threshold=1e-6)