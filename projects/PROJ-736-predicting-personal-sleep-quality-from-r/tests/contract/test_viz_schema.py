"""
Contract test for visualization output schema.
Verifies that the brain plot file exists and meets basic schema requirements.
"""
import os
import pytest
from pathlib import Path
import json
from config import get_paths


class TestVizSchema:
    """Tests for visualization output schema compliance."""
    
    def test_plot_file_exists(self):
        """Verify that the brain plot file exists in the expected location."""
        paths = get_paths()
        results_dir = Path(paths['results'])
        plot_path = results_dir / "brain_connectome_plot.png"
        
        assert plot_path.exists(), f"Plot file not found at {plot_path}"
    
    def test_plot_file_not_empty(self):
        """Verify that the plot file is not empty."""
        paths = get_paths()
        results_dir = Path(paths['results'])
        plot_path = results_dir / "brain_connectome_plot.png"
        
        assert plot_path.exists(), f"Plot file not found at {plot_path}"
        assert plot_path.stat().st_size > 0, "Plot file is empty"
    
    def test_plot_file_has_valid_extension(self):
        """Verify that the plot file has a valid image extension."""
        paths = get_paths()
        results_dir = Path(paths['results'])
        plot_path = results_dir / "brain_connectome_plot.png"
        
        assert plot_path.exists(), f"Plot file not found at {plot_path}"
        assert plot_path.suffix.lower() in ['.png', '.svg', '.jpg', '.jpeg'], \
            f"Invalid plot file extension: {plot_path.suffix}"
    
    def test_result_report_updated_with_plot_path(self):
        """Verify that ResultReport.json contains the plot file path."""
        paths = get_paths()
        results_dir = Path(paths['results'])
        report_path = results_dir / "ResultReport.json"
        
        assert report_path.exists(), f"ResultReport.json not found at {report_path}"
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert 'visualization' in report, "ResultReport.json missing 'visualization' section"
        assert 'plot_path' in report['visualization'], \
            "ResultReport.json missing 'plot_path' in visualization section"
        
        # Verify the plot path points to an existing file
        plot_path = Path(report['visualization']['plot_path'])
        assert plot_path.exists(), f"Plot path in report points to non-existent file: {plot_path}"
