"""
Integration tests for plot_sensitivity_overlay.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

import pytest
from analysis.plot_sensitivity_overlay import load_sensitivity_results, plot_sensitivity_overlay


class TestPlotSensitivityOverlay:
    """Test cases for the sensitivity overlay plot functionality."""

    def test_load_sensitivity_results_success(self, tmp_path):
        """Test loading sensitivity results from a valid JSON file."""
        # Create a test JSON file
        test_data = {
            "threshold_results": [
                {
                    "threshold": 2,
                    "accuracies": {"1": 0.95, "2": 0.85, "3": 0.75}
                },
                {
                    "threshold": 3,
                    "accuracies": {"1": 0.94, "2": 0.84, "3": 0.74, "4": 0.64}
                }
            ]
        }
        
        json_file = tmp_path / "test_sensitivity.json"
        with open(json_file, 'w') as f:
            json.dump(test_data, f)
        
        # Load the data
        result = load_sensitivity_results(json_file)
        
        assert result == test_data
        assert "threshold_results" in result
        assert len(result["threshold_results"]) == 2

    def test_load_sensitivity_results_file_not_found(self, tmp_path):
        """Test loading from a non-existent file raises FileNotFoundError."""
        non_existent_file = tmp_path / "non_existent.json"
        
        with pytest.raises(FileNotFoundError):
            load_sensitivity_results(non_existent_file)

    def test_plot_sensitivity_overlay_creates_file(self, tmp_path):
        """Test that the plot function creates the output file."""
        # Create test data
        test_data = {
            "threshold_results": [
                {
                    "threshold": 2,
                    "accuracies": {"1": 0.95, "2": 0.85, "3": 0.75}
                },
                {
                    "threshold": 3,
                    "accuracies": {"1": 0.94, "2": 0.84, "3": 0.74, "4": 0.64}
                }
            ]
        }
        
        output_path = tmp_path / "test_plot.png"
        
        # Generate the plot
        plot_sensitivity_overlay(test_data, output_path)
        
        # Verify the file was created
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_plot_sensitivity_overlay_empty_data(self, tmp_path):
        """Test handling of empty sensitivity data."""
        test_data = {"threshold_results": []}
        
        output_path = tmp_path / "empty_plot.png"
        
        # Generate the plot (should not raise an error)
        plot_sensitivity_overlay(test_data, output_path)
        
        # Verify the file was created (even if it's a placeholder)
        assert output_path.exists()

    def test_plot_sensitivity_overlay_single_threshold(self, tmp_path):
        """Test plotting with a single threshold."""
        test_data = {
            "threshold_results": [
                {
                    "threshold": 2,
                    "accuracies": {"1": 0.95, "2": 0.85, "3": 0.75}
                }
            ]
        }
        
        output_path = tmp_path / "single_threshold_plot.png"
        
        plot_sensitivity_overlay(test_data, output_path)
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0