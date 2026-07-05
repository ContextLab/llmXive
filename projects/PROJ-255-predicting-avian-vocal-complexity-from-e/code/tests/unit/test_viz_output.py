import os
import sys
import tempfile
import pytest
from pathlib import Path

# Ensure the project root is in the path so we can import src modules
# This mimics how tests would be run from the project root
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.analysis.viz import (
    generate_scatter_plot,
    generate_regional_heatmap,
    generate_residual_plots
)
from src.utils.config import get_figures_dir, get_project_root


class TestVizOutput:
    """Unit tests for plot generation logic (file existence)."""

    @pytest.fixture
    def temp_figures_dir(self):
        """Create a temporary directory for figure outputs."""
        temp_dir = tempfile.mkdtemp()
        return temp_dir

    def test_scatter_plot_generates_file(self, temp_figures_dir):
        """Verify that generate_scatter_plot creates the expected output file."""
        output_path = Path(temp_figures_dir) / "scatter_noise_complexity.png"
        
        # Create a minimal dummy dataset for testing
        # In a real scenario, this would come from data/processed/final_dataset.csv
        dummy_data = [
            {"noise_level_db": 30.0, "syllable_count": 5, "location": "A"},
            {"noise_level_db": 40.0, "syllable_count": 8, "location": "B"},
            {"noise_level_db": 50.0, "syllable_count": 3, "location": "C"},
            {"noise_level_db": 60.0, "syllable_count": 2, "location": "D"},
        ]
        
        # Call the function
        generate_scatter_plot(dummy_data, str(output_path))
        
        # Assert the file exists
        assert output_path.exists(), f"Scatter plot file not created at {output_path}"
        assert output_path.stat().st_size > 0, "Scatter plot file is empty"

    def test_regional_heatmap_generates_file(self, temp_figures_dir):
        """Verify that generate_regional_heatmap creates the expected output file."""
        output_path = Path(temp_figures_dir) / "regional_heatmap.png"
        
        # Create a minimal dummy dataset for testing
        dummy_data = [
            {"noise_level_db": 30.0, "syllable_count": 5, "location": "Urban"},
            {"noise_level_db": 40.0, "syllable_count": 8, "location": "Rural"},
            {"noise_level_db": 50.0, "syllable_count": 3, "location": "Wild"},
            {"noise_level_db": 60.0, "syllable_count": 2, "location": "Urban"},
            {"noise_level_db": 35.0, "syllable_count": 7, "location": "Rural"},
        ]
        
        # Call the function
        generate_regional_heatmap(dummy_data, str(output_path))
        
        # Assert the file exists
        assert output_path.exists(), f"Heatmap file not created at {output_path}"
        assert output_path.stat().st_size > 0, "Heatmap file is empty"

    def test_residual_plots_generate_files(self, temp_figures_dir):
        """Verify that generate_residual_plots creates the expected output files."""
        # Define expected output filenames based on implementation
        qq_plot_path = Path(temp_figures_dir) / "residual_qq_plot.png"
        res_vs_fit_path = Path(temp_figures_dir) / "residual_vs_fitted.png"
        
        # Create a minimal dummy dataset for testing
        dummy_residuals = [1.2, -0.5, 0.8, -1.1, 0.3, -0.2, 1.5, -0.9]
        dummy_fitted = [10.0, 12.5, 11.2, 13.1, 10.8, 11.5, 14.0, 12.2]
        
        # Call the function
        generate_residual_plots(dummy_residuals, dummy_fitted, temp_figures_dir)
        
        # Assert the files exist
        assert qq_plot_path.exists(), f"Q-Q plot file not created at {qq_plot_path}"
        assert res_vs_fit_path.exists(), f"Residual vs fitted file not created at {res_vs_fit_path}"
        
        # Assert files are not empty
        assert qq_plot_path.stat().st_size > 0, "Q-Q plot file is empty"
        assert res_vs_fit_path.stat().st_size > 0, "Residual vs fitted file is empty"

    def test_plot_files_in_standard_figures_dir(self):
        """Verify plots can be generated in the project's standard figures directory."""
        figures_dir = get_figures_dir()
        
        # Ensure the directory exists
        figures_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a minimal dummy dataset
        dummy_data = [
            {"noise_level_db": 30.0, "syllable_count": 5, "location": "A"},
            {"noise_level_db": 40.0, "syllable_count": 8, "location": "B"},
            {"noise_level_db": 50.0, "syllable_count": 3, "location": "C"},
            {"noise_level_db": 60.0, "syllable_count": 2, "location": "D"},
        ]
        
        # Generate a test plot in the standard directory
        test_plot_path = figures_dir / "test_viz_output_check.png"
        generate_scatter_plot(dummy_data, str(test_plot_path))
        
        # Verify file existence
        assert test_plot_path.exists(), f"Test plot not created in standard figures dir at {test_plot_path}"
        
        # Clean up
        if test_plot_path.exists():
            test_plot_path.unlink()