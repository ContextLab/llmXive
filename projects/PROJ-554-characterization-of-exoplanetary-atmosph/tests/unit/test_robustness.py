"""
Unit tests for T026: robustness.py
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from robustness import (
    compute_ci_width,
    determine_threshold_met,
    load_retrieval_results,
    save_robustness_report,
)


class TestLoadRetrievalResults:
    def test_load_existing_file(self, tmp_path):
        """Test loading an existing retrieval results file."""
        # Create a mock retrieval results file
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()
        results_file = processed_dir / "retrieval_results.csv"

        mock_data = {
            "planet_name": ["p1", "p2", "p3"],
            "water_mixing_ratio": [-3.5, -4.2, -3.8],
            "uncertainty": [0.1, 0.2, 0.15],
        }
        df = pd.DataFrame(mock_data)
        df.to_csv(results_file, index=False)

        config = {"paths": {"processed": str(processed_dir)}}

        loaded_df = load_retrieval_results(config)

        assert len(loaded_df) == 3
        assert "water_mixing_ratio" in loaded_df.columns
        assert loaded_df["water_mixing_ratio"].mean() == pytest.approx(-3.833, rel=0.01)

    def test_missing_file_raises_error(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()

        config = {"paths": {"processed": str(processed_dir)}}

        with pytest.raises(FileNotFoundError, match="Retrieval results file not found"):
            load_retrieval_results(config)


class TestComputeCiWidth:
    def test_compute_ci_width_valid_data(self):
        """Test CI width computation with valid data."""
        values = [-3.5, -4.2, -3.8, -3.9, -4.0]
        df = pd.DataFrame({"water_mixing_ratio": values})

        ci_width = compute_ci_width(df, column="water_mixing_ratio", ci_level=0.95)

        assert ci_width is not None
        assert ci_width > 0
        # With 5 samples, CI width should be roughly 2 * 2.776 * std / sqrt(n)
        # std ~ 0.27, sqrt(5) ~ 2.23, so width ~ 2 * 2.776 * 0.27 / 2.23 ~ 0.67
        assert ci_width < 1.0

    def test_compute_ci_width_insufficient_data(self):
        """Test CI width computation with insufficient data."""
        df = pd.DataFrame({"water_mixing_ratio": [-3.5]})

        ci_width = compute_ci_width(df, column="water_mixing_ratio", ci_level=0.95)

        assert ci_width is None

    def test_compute_ci_width_with_nan(self):
        """Test CI width computation with NaN values."""
        values = [-3.5, np.nan, -3.8, -4.0]
        df = pd.DataFrame({"water_mixing_ratio": values})

        ci_width = compute_ci_width(df, column="water_mixing_ratio", ci_level=0.95)

        assert ci_width is not None
        assert ci_width > 0

    def test_compute_ci_width_missing_column(self):
        """Test CI width computation with missing column."""
        df = pd.DataFrame({"other_column": [-3.5, -4.0]})

        with pytest.raises(ValueError, match="Column 'water_mixing_ratio' not found"):
            compute_ci_width(df, column="water_mixing_ratio", ci_level=0.95)


class TestDetermineThresholdMet:
    def test_threshold_met(self):
        """Test threshold determination when CI width is below threshold."""
        assert determine_threshold_met(ci_width=0.3, threshold=0.5) is True
        assert determine_threshold_met(ci_width=0.5, threshold=0.5) is True

    def test_threshold_not_met(self):
        """Test threshold determination when CI width exceeds threshold."""
        assert determine_threshold_met(ci_width=0.6, threshold=0.5) is False

    def test_threshold_with_none(self):
        """Test threshold determination when CI width is None."""
        assert determine_threshold_met(ci_width=None, threshold=0.5) is False


class TestSaveRobustnessReport:
    def test_save_report(self, tmp_path):
        """Test saving the robustness report."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        config = {"paths": {"results": str(results_dir)}}

        report_path = save_robustness_report(
            config=config,
            ci_width=0.45,
            threshold_met=True,
            ci_lower=-4.1,
            ci_upper=-3.65,
            n_samples=100,
        )

        assert report_path.exists()

        with open(report_path, "r") as f:
            report = json.load(f)

        assert report["ci_width"] == 0.45
        assert report["threshold_met"] is True
        assert report["ci_lower"] == -4.1
        assert report["ci_upper"] == -3.65
        assert report["n_samples"] == 100
        assert "description" in report