"""
Integration test for src/utils/plotting.py.

This test verifies that all plotting functions generate valid output files
without errors and save them to the correct directory.

Dependencies:
- T062: src/utils/plotting.py implementation
- T061: src/evaluation/final_report.py (provides sample data)

Execution:
pytest tests/integration/test_plotting.py -v
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.plotting import (
    plot_success_rate_vs_k,
    plot_text_weight_correlation,
    plot_latency_breakdown,
    main
)
from src.utils.config import ensure_directories


class TestPlottingIntegration:
    """Integration tests for plotting module."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up temporary directories and sample data for testing."""
        # Create temporary directories for test outputs
        self.test_output_dir = Path(tempfile.mkdtemp())
        self.plots_dir = self.test_output_dir / "plots"
        self.results_dir = self.test_output_dir / "results"
        
        # Ensure directories exist
        ensure_directories([self.plots_dir, self.results_dir])
        
        # Create sample data files that the plotting functions expect
        self._create_sample_data()
        
        yield
        
        # Cleanup after test
        shutil.rmtree(self.test_output_dir)

    def _create_sample_data(self):
        """Create sample data files for plotting tests."""
        # 1. Sensitivity data (for plot_success_rate_vs_k)
        sensitivity_data = {
            "k_values": [1, 3, 5, 10],
            "success_rates": [0.45, 0.52, 0.58, 0.55],
            "variance": [0.02, 0.015, 0.012, 0.018],
            "robustness_score": 0.48
        }
        with open(self.results_dir / "sensitivity.yaml", "w") as f:
            import yaml
            yaml.dump(sensitivity_data, f)
        
        # 2. Linearity data (for plot_text_weight_correlation)
        linearity_data = {
            "correlation_coefficient": 0.78,
            "text_distances": [0.1, 0.2, 0.3, 0.4, 0.5],
            "weight_distances": [0.12, 0.21, 0.35, 0.42, 0.51]
        }
        with open(self.results_dir / "linearity_validation.json", "w") as f:
            json.dump(linearity_data, f)
        
        # 3. Latency data (for plot_latency_breakdown)
        latency_data = {
            "embedding_latency_ms": 15.2,
            "retrieval_latency_ms": 8.7,
            "interpolation_latency_ms": 3.1,
            "total_skill_selection_latency_ms": 27.0,
            "baseline_latency_ms": 150.0,
            "computational_savings_ms": 123.0
        }
        with open(self.results_dir / "latency_metrics.json", "w") as f:
            json.dump(latency_data, f)

    def test_plot_success_rate_vs_k(self):
        """Test that plot_success_rate_vs_k generates a valid plot file."""
        output_file = self.plots_dir / "success_rate_vs_k.png"
        
        # Call the plotting function
        plot_success_rate_vs_k(
            sensitivity_data_path=self.results_dir / "sensitivity.yaml",
            output_path=str(output_file)
        )
        
        # Verify file was created
        assert output_file.exists(), f"Plot file not created: {output_file}"
        
        # Verify file has content (not empty)
        assert output_file.stat().st_size > 0, "Plot file is empty"
        
        # Verify it's a valid PNG (first 8 bytes are PNG signature)
        with open(output_file, "rb") as f:
            header = f.read(8)
            assert header[:8] == b'\x89PNG\r\n\x1a\n', "Invalid PNG header"

    def test_plot_text_weight_correlation(self):
        """Test that plot_text_weight_correlation generates a valid plot file."""
        output_file = self.plots_dir / "text_weight_correlation.png"
        
        # Call the plotting function
        plot_text_weight_correlation(
            linearity_data_path=self.results_dir / "linearity_validation.json",
            output_path=str(output_file)
        )
        
        # Verify file was created
        assert output_file.exists(), f"Plot file not created: {output_file}"
        
        # Verify file has content
        assert output_file.stat().st_size > 0, "Plot file is empty"
        
        # Verify it's a valid PNG
        with open(output_file, "rb") as f:
            header = f.read(8)
            assert header[:8] == b'\x89PNG\r\n\x1a\n', "Invalid PNG header"

    def test_plot_latency_breakdown(self):
        """Test that plot_latency_breakdown generates a valid plot file."""
        output_file = self.plots_dir / "latency_breakdown.png"
        
        # Call the plotting function
        plot_latency_breakdown(
            latency_data_path=self.results_dir / "latency_metrics.json",
            output_path=str(output_file)
        )
        
        # Verify file was created
        assert output_file.exists(), f"Plot file not created: {output_file}"
        
        # Verify file has content
        assert output_file.stat().st_size > 0, "Plot file is empty"
        
        # Verify it's a valid PNG
        with open(output_file, "rb") as f:
            header = f.read(8)
            assert header[:8] == b'\x89PNG\r\n\x1a\n', "Invalid PNG header"

    def test_main_function_generates_all_plots(self):
        """Test that the main function generates all expected plots."""
        # Create a combined results directory with all necessary files
        combined_results = self.test_output_dir / "combined_results"
        ensure_directories([combined_results])
        
        # Copy sample data
        import yaml
        sensitivity_data = {
            "k_values": [1, 3, 5, 10],
            "success_rates": [0.45, 0.52, 0.58, 0.55],
            "variance": [0.02, 0.015, 0.012, 0.018],
            "robustness_score": 0.48
        }
        with open(combined_results / "sensitivity.yaml", "w") as f:
            yaml.dump(sensitivity_data, f)
        
        linearity_data = {
            "correlation_coefficient": 0.78,
            "text_distances": [0.1, 0.2, 0.3, 0.4, 0.5],
            "weight_distances": [0.12, 0.21, 0.35, 0.42, 0.51]
        }
        with open(combined_results / "linearity_validation.json", "w") as f:
            json.dump(linearity_data, f)
        
        latency_data = {
            "embedding_latency_ms": 15.2,
            "retrieval_latency_ms": 8.7,
            "interpolation_latency_ms": 3.1,
            "total_skill_selection_latency_ms": 27.0,
            "baseline_latency_ms": 150.0,
            "computational_savings_ms": 123.0
        }
        with open(combined_results / "latency_metrics.json", "w") as f:
            json.dump(latency_data, f)
        
        # Call main function
        plots_output = self.test_output_dir / "final_plots"
        ensure_directories([plots_output])
        
        main(
            results_dir=str(combined_results),
            output_dir=str(plots_output)
        )
        
        # Verify all expected plot files exist
        expected_plots = [
            "success_rate_vs_k.png",
            "text_weight_correlation.png",
            "latency_breakdown.png"
        ]
        
        for plot_name in expected_plots:
            plot_path = plots_output / plot_name
            assert plot_path.exists(), f"Missing plot: {plot_name}"
            assert plot_path.stat().st_size > 0, f"Empty plot: {plot_name}"

    def test_plotting_with_missing_data_graceful_failure(self):
        """Test that plotting functions handle missing data files gracefully."""
        output_file = self.plots_dir / "test_missing.png"
        
        # Try to plot with non-existent data file
        with pytest.raises((FileNotFoundError, ValueError)) as exc_info:
            plot_success_rate_vs_k(
                sensitivity_data_path=self.results_dir / "nonexistent.yaml",
                output_path=str(output_file)
            )
        
        # Verify error message is informative
        assert "not found" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()

    def test_plotting_with_invalid_data_format(self):
        """Test that plotting functions handle invalid data format gracefully."""
        # Create a file with invalid JSON/YAML
        invalid_data_file = self.results_dir / "invalid_data.json"
        with open(invalid_data_file, "w") as f:
            f.write("not valid json {{{")
        
        output_file = self.plots_dir / "test_invalid.png"
        
        # Try to plot with invalid data
        with pytest.raises((json.JSONDecodeError, yaml.YAMLError, ValueError)) as exc_info:
            plot_text_weight_correlation(
                linearity_data_path=invalid_data_file,
                output_path=str(output_file)
            )

    def test_plot_dimensions_and_quality(self):
        """Test that generated plots have reasonable dimensions and quality."""
        output_file = self.plots_dir / "quality_test.png"
        
        plot_success_rate_vs_k(
            sensitivity_data_path=self.results_dir / "sensitivity.yaml",
            output_path=str(output_file),
            figsize=(10, 6),  # Explicit dimensions
            dpi=150  # High resolution
        )
        
        # Verify file size indicates reasonable quality (not too small)
        file_size = output_file.stat().st_size
        assert file_size > 10000, f"Plot file too small ({file_size} bytes), likely low quality"
        
        # Verify it's a valid PNG with dimensions
        with open(output_file, "rb") as f:
            # Skip PNG signature and IHDR chunk
            f.read(24)  # 8 (sig) + 4 (length) + 4 (type) + 4 (length)
            width_bytes = f.read(4)
            height_bytes = f.read(4)
            width = int.from_bytes(width_bytes, 'big')
            height = int.from_bytes(height_bytes, 'big')
            
            assert width >= 600, f"Plot width too small: {width}"
            assert height >= 400, f"Plot height too small: {height}"