import os
import sys
import tempfile
import json
import pytest
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from visualize import (
    pin_random_seed,
    is_seed_pinned,
    get_current_seed,
    load_residue_data,
    plot_bar_frequencies,
    plot_residual_qq,
    annotate_theoretical_bounds,
    generate_visualization_report
)
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing
import matplotlib.pyplot as plt
import numpy as np


class TestPlotGeneration:
    """Unit tests for plot generation functionality in visualize.py"""

    @pytest.fixture
    def sample_residue_data(self, tmp_path):
        """Create sample residue data file for testing"""
        # Create a temporary directory for test data
        data_dir = tmp_path / "data" / "raw"
        data_dir.mkdir(parents=True)

        # Create sample residue counts data
        sample_data = {
            "prime": 5,
            "N": 1000,
            "residue_counts": {0: 198, 1: 205, 2: 195, 3: 202, 4: 200},
            "total_count": 1000
        }

        # Save to file
        file_path = data_dir / "residues_5_1000.json"
        with open(file_path, 'w') as f:
            json.dump(sample_data, f)

        return file_path

    @pytest.fixture
    def sample_stats_data(self, tmp_path):
        """Create sample statistical results for testing"""
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True)

        sample_stats = {
            "prime": 5,
            "N": 1000,
            "chi_squared_statistic": 1.2,
            "p_value": 0.878,
            "block_bootstrap_p_value": 0.85,
            "pass_flag": True,
            "bonferroni_pass_flag": True,
            "theoretical_bounds": {
                "lebowitz_lockard": 50.0,
                "pollack_roy": 45.0
            }
        }

        file_path = data_dir / "stats_5_1000.json"
        with open(file_path, 'w') as f:
            json.dump(sample_stats, f)

        return file_path

    def test_plot_bar_frequencies_creates_file(self, sample_residue_data, tmp_path):
        """Test that plot_bar_frequencies creates a valid image file"""
        output_dir = tmp_path / "results" / "plots"
        output_dir.mkdir(parents=True)

        output_path = output_dir / "bar_frequencies_5_1000.png"

        # Call the function
        plot_bar_frequencies(
            residue_counts=sample_residue_data.parent.parent / "raw" / "residues_5_1000.json",
            prime=5,
            output_path=str(output_path)
        )

        # Verify file was created
        assert output_path.exists(), f"Output file {output_path} was not created"
        assert output_path.stat().st_size > 0, f"Output file {output_path} is empty"

        # Verify it's a valid PNG file (check magic bytes)
        with open(output_path, 'rb') as f:
            magic = f.read(8)
            assert magic[:8] == b'\x89PNG\r\n\x1a\n', "File is not a valid PNG"

        # Clean up
        plt.close('all')

    def test_plot_bar_frequencies_dimensions(self, sample_residue_data, tmp_path):
        """Test that generated plots have expected dimensions"""
        output_dir = tmp_path / "results" / "plots"
        output_dir.mkdir(parents=True)

        output_path = output_dir / "bar_frequencies_5_1000.png"

        plot_bar_frequencies(
            residue_counts=sample_residue_data.parent.parent / "raw" / "residues_5_1000.json",
            prime=5,
            output_path=str(output_path),
            figsize=(10, 6),
            dpi=100
        )

        # Load the image and check dimensions
        from PIL import Image
        img = Image.open(output_path)
        width, height = img.size

        # Allow some tolerance for margins
        assert 950 <= width <= 1050, f"Width {width} not within expected range"
        assert 550 <= height <= 650, f"Height {height} not within expected range"

        plt.close('all')

    def test_plot_residual_qq_creates_file(self, sample_residue_data, sample_stats_data, tmp_path):
        """Test that plot_residual_qq creates a valid image file"""
        output_dir = tmp_path / "results" / "plots"
        output_dir.mkdir(parents=True)

        output_path = output_dir / "residual_qq_5_1000.png"

        plot_residual_qq(
            residue_data_path=str(sample_residue_data),
            stats_data_path=str(sample_stats_data),
            output_path=str(output_path)
        )

        assert output_path.exists(), f"Output file {output_path} was not created"
        assert output_path.stat().st_size > 0, f"Output file {output_path} is empty"

        plt.close('all')

    def test_annotate_theoretical_bounds_integration(self, sample_residue_data, sample_stats_data, tmp_path):
        """Test that theoretical bounds annotation works correctly"""
        output_dir = tmp_path / "results" / "plots"
        output_dir.mkdir(parents=True)

        output_path = output_dir / "annotated_plot_5_1000.png"

        # This should not raise an error and should create a file
        annotate_theoretical_bounds(
            residue_data_path=str(sample_residue_data),
            stats_data_path=str(sample_stats_data),
            output_path=str(output_path)
        )

        assert output_path.exists(), "Annotated plot file was not created"
        assert output_path.stat().st_size > 0, "Annotated plot file is empty"

        plt.close('all')

    def test_generate_visualization_report_creates_all_files(self, sample_residue_data, sample_stats_data, tmp_path):
        """Test that the full report generation creates all expected files"""
        output_dir = tmp_path / "results" / "plots"
        output_dir.mkdir(parents=True)

        report_dir = tmp_path / "results" / "reports"
        report_dir.mkdir(parents=True)

        # Generate full report
        generate_visualization_report(
            residue_data_path=str(sample_residue_data),
            stats_data_path=str(sample_stats_data),
            output_plots_dir=str(output_dir),
            output_reports_dir=str(report_dir)
        )

        # Check that all expected files were created
        expected_plots = [
            "bar_frequencies_5_1000.png",
            "residual_qq_5_1000.png",
            "annotated_bounds_5_1000.png"
        ]

        for plot_name in expected_plots:
            plot_path = output_dir / plot_name
            assert plot_path.exists(), f"Expected plot {plot_name} was not created"
            assert plot_path.stat().st_size > 0, f"Plot {plot_name} is empty"

        plt.close('all')

    def test_load_residue_data_functionality(self, sample_residue_data):
        """Test that load_residue_data correctly loads the data"""
        data = load_residue_data(str(sample_residue_data))

        assert data is not None, "Data loading returned None"
        assert 'prime' in data, "Missing 'prime' key in loaded data"
        assert 'N' in data, "Missing 'N' key in loaded data"
        assert 'residue_counts' in data, "Missing 'residue_counts' key in loaded data"
        assert data['prime'] == 5, f"Expected prime=5, got {data['prime']}"
        assert data['N'] == 1000, f"Expected N=1000, got {data['N']}"

    def test_seed_pinning_in_visualization(self):
        """Test that seed pinning works correctly in visualization module"""
        # Reset seed state
        pin_random_seed(42)

        assert is_seed_pinned(), "Seed should be pinned after pin_random_seed call"
        assert get_current_seed() == 42, f"Expected seed 42, got {get_current_seed()}"

        # Test that random operations are deterministic
        random.seed(42)
        val1 = np.random.rand()

        pin_random_seed(42)
        val2 = np.random.rand()

        assert val1 == val2, "Random operations should be deterministic with pinned seed"

    def test_error_handling_missing_data_file(self, tmp_path):
        """Test that appropriate errors are raised for missing data files"""
        output_dir = tmp_path / "results" / "plots"
        output_dir.mkdir(parents=True)

        output_path = output_dir / "error_test.png"

        # Should raise FileNotFoundError for missing data
        with pytest.raises(FileNotFoundError):
            plot_bar_frequencies(
                residue_counts="/nonexistent/path/residues_5_1000.json",
                prime=5,
                output_path=str(output_path)
            )

    def test_edge_case_small_prime(self, tmp_path):
        """Test plot generation with small prime (p=3)"""
        data_dir = tmp_path / "data" / "raw"
        data_dir.mkdir(parents=True)

        small_prime_data = {
            "prime": 3,
            "N": 100,
            "residue_counts": {0: 33, 1: 34, 2: 33},
            "total_count": 100
        }

        file_path = data_dir / "residues_3_100.json"
        with open(file_path, 'w') as f:
            json.dump(small_prime_data, f)

        output_dir = tmp_path / "results" / "plots"
        output_dir.mkdir(parents=True)
        output_path = output_dir / "bar_frequencies_3_100.png"

        plot_bar_frequencies(
            residue_counts=str(file_path),
            prime=3,
            output_path=str(output_path)
        )

        assert output_path.exists(), "Plot for small prime was not created"
        assert output_path.stat().st_size > 0, "Plot for small prime is empty"

        plt.close('all')