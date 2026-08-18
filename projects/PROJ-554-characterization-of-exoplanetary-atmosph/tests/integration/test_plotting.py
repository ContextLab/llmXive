import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import json

# Add code directory to path if running standalone
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from plotting import (
    load_retrieval_results,
    load_metadata,
    merge_data,
    plot_water_vs_temperature
)
from config import get_config


class TestPlottingIntegration:
    """
    Integration tests for the plotting module.
    These tests verify that the plot generation works with real data files
    (simulated by creating temporary test files) and produces valid output.
    """

    @pytest.fixture
    def sample_retrieval_data(self, tmp_path):
        """Create a sample retrieval_results.csv for testing."""
        data = {
            "planet_name": ["Planet A", "Planet B", "Planet C", "Planet D"],
            "water_mixing_ratio": [-4.5, -3.2, -5.1, -4.8],
            "uncertainty": [0.3, 0.2, 0.4, 0.3],
            "is_upper_limit": [False, False, True, True],
            "detection_limit": [None, None, -5.0, -4.5],
            "min_detectable_concentration": [None, None, 1e-5, 3e-5]
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "retrieval_results.csv"
        df.to_csv(file_path, index=False)
        return file_path

    @pytest.fixture
    def sample_metadata(self, tmp_path):
        """Create a sample metadata.csv for testing."""
        data = {
            "planet_name": ["Planet A", "Planet B", "Planet C", "Planet D"],
            "temperature": [1500, 1200, 800, 900],
            "metallicity": [0.1, 0.2, -0.1, 0.0],
            "snr": [25, 30, 15, 18],
            "resolution": [100, 100, 50, 50],
            "planet_category": ["Hot Jupiter", "Hot Jupiter", "Super-Earth", "Super-Earth"],
            "instrument": ["HST", "JWST", "HST", "JWST"],
            "wavelength_range": ["0.6-5.0", "0.6-5.0", "1.0-5.0", "0.6-5.0"]
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "metadata.csv"
        df.to_csv(file_path, index=False)
        return file_path

    @pytest.fixture
    def mock_config(self, tmp_path, sample_retrieval_data, sample_metadata):
        """Mock the get_config function to point to temporary files."""
        original_get_config = get_config

        def mock_get_config():
            return {
                "paths": {
                    "processed_dir": tmp_path,
                    "results_dir": tmp_path / "results",
                    "log_dir": tmp_path / "logs"
                }
            }

        # Monkey patch
        import plotting
        plotting.get_config = mock_get_config
        return mock_get_config

    def test_load_retrieval_results(self, sample_retrieval_data, mock_config):
        """Test that retrieval results are loaded correctly."""
        df = load_retrieval_results()
        assert len(df) == 4
        assert "water_mixing_ratio" in df.columns
        assert "is_upper_limit" in df.columns
        assert df["is_upper_limit"].sum() == 2

    def test_load_metadata(self, sample_metadata, mock_config):
        """Test that metadata is loaded correctly."""
        df = load_metadata()
        assert len(df) == 4
        assert "temperature" in df.columns
        assert "planet_name" in df.columns

    def test_merge_data(self, sample_retrieval_data, sample_metadata, mock_config):
        """Test that data merging works correctly."""
        retrieval_df = load_retrieval_results()
        metadata_df = load_metadata()
        merged = merge_data(retrieval_df, metadata_df)

        assert len(merged) == 4
        assert "water_mixing_ratio" in merged.columns
        assert "temperature" in merged.columns
        assert "is_upper_limit" in merged.columns

    def test_plot_generation(self, sample_retrieval_data, sample_metadata, mock_config, tmp_path):
        """Test that the plot is generated and saved as a valid PNG."""
        retrieval_df = load_retrieval_results()
        metadata_df = load_metadata()
        merged = merge_data(retrieval_df, metadata_df)

        output_path = tmp_path / "results" / "plots" / "test_water_vs_temp.png"

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        plot_water_vs_temperature(merged, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify it's a valid image by attempting to open it
        # (This will raise an error if the file is not a valid image)
        try:
            img = plt.imread(output_path)
            assert img.shape[0] > 0
            assert img.shape[1] > 0
        except Exception as e:
            pytest.fail(f"Generated file is not a valid image: {e}")

    def test_plot_handles_upper_limits(self, sample_retrieval_data, sample_metadata, mock_config, tmp_path):
        """Test that the plot correctly handles upper limits."""
        retrieval_df = load_retrieval_results()
        metadata_df = load_metadata()
        merged = merge_data(retrieval_df, metadata_df)

        output_path = tmp_path / "results" / "plots" / "test_upper_limits.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        plot_water_vs_temperature(merged, output_path)

        assert output_path.exists()
        # The test is primarily that it runs without error and produces an image
        # Visual inspection would confirm the specific markers, but programmatically
        # we ensure the function handles the boolean column without crashing.