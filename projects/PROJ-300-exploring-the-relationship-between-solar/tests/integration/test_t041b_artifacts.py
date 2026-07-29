"""
Integration test for T041b: Verify results directory contains all expected artifacts.
"""
import os
import sys
import json
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

class TestT041bArtifacts:
    """Test suite to verify all required artifacts exist after pipeline execution."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure directories exist before testing."""
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    def test_us1_correlation_json_exists(self):
        """Verify us1_correlation.json exists in results directory."""
        file_path = RESULTS_DIR / "us1_correlation.json"
        assert file_path.exists(), f"File {file_path} does not exist"

    def test_us1_correlation_json_schema(self):
        """Verify us1_correlation.json contains required keys."""
        file_path = RESULTS_DIR / "us1_correlation.json"
        assert file_path.exists(), f"File {file_path} does not exist"

        with open(file_path, 'r') as f:
            data = json.load(f)

        required_keys = ["pearson", "spearman", "optimal_lag", "lag_correlation_value"]
        for key in required_keys:
            assert key in data, f"Missing required key: {key}"

    def test_plot_scatter_png_exists(self):
        """Verify plot_scatter.png exists in results directory."""
        file_path = RESULTS_DIR / "plot_scatter.png"
        assert file_path.exists(), f"File {file_path} does not exist"

    def test_plot_timeseries_png_exists(self):
        """Verify plot_timeseries.png exists in results directory."""
        file_path = RESULTS_DIR / "plot_timeseries.png"
        assert file_path.exists(), f"File {file_path} does not exist"

    def test_quality_log_json_exists(self):
        """Verify quality_log.json exists in data/processed directory."""
        file_path = DATA_PROCESSED_DIR / "quality_log.json"
        assert file_path.exists(), f"File {file_path} does not exist"

    def test_quality_log_json_valid(self):
        """Verify quality_log.json is valid JSON."""
        file_path = DATA_PROCESSED_DIR / "quality_log.json"
        assert file_path.exists(), f"File {file_path} does not exist"

        try:
            with open(file_path, 'r') as f:
                json.load(f)
        except json.JSONDecodeError:
            pytest.fail(f"File {file_path} is not valid JSON")

    def test_all_expected_artifacts_present(self):
        """Verify all expected artifacts are present."""
        expected_files = {
            "results": [
                "us1_correlation.json",
                "plot_scatter.png",
                "plot_timeseries.png",
            ],
            "data/processed": [
                "quality_log.json",
            ]
        }

        missing_files = []
        for directory, files in expected_files.items():
            base_path = RESULTS_DIR if directory == "results" else DATA_PROCESSED_DIR
            for filename in files:
                file_path = base_path / filename
                if not file_path.exists():
                    missing_files.append(str(file_path))

        assert not missing_files, f"Missing artifacts: {missing_files}"