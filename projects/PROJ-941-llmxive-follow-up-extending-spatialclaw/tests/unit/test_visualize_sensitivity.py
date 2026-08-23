"""
Unit tests for T066: Sensitivity Analysis Visualization.
"""
import os
import tempfile
import csv
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
from code.stats.visualize_sensitivity import load_sensitivity_csv, plot_sensitivity_analysis

class TestLoadSensitivityCsv:
    def test_load_valid_depth_csv(self, tmp_path):
        """Test loading a valid depth threshold CSV."""
        csv_path = tmp_path / "depth_sweep.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['threshold_value', 'false_positive_rate', 'false_negative_rate'])
            writer.writeheader()
            writer.writerow({'threshold_value': '0.1', 'false_positive_rate': '0.05', 'false_negative_rate': '0.02'})
            writer.writerow({'threshold_value': '0.5', 'false_positive_rate': '0.03', 'false_negative_rate': '0.04'})
        
        data = load_sensitivity_csv(str(csv_path))
        
        assert data is not None
        assert len(data['threshold']) == 2
        assert data['threshold'] == [0.1, 0.5]
        assert data['fpr'] == [0.05, 0.03]
        assert data['fnr'] == [0.02, 0.04]

    def test_load_valid_flat_csv(self, tmp_path):
        """Test loading a valid flat object epsilon CSV."""
        csv_path = tmp_path / "flat_sweep.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['epsilon', 'false_positive_rate', 'false_negative_rate'])
            writer.writeheader()
            writer.writerow({'epsilon': '0.0', 'false_positive_rate': '0.1', 'false_negative_rate': '0.0'})
            writer.writerow({'epsilon': '0.05', 'false_positive_rate': '0.08', 'false_negative_rate': '0.02'})
        
        data = load_sensitivity_csv(str(csv_path))
        
        assert data is not None
        assert len(data['threshold']) == 2
        assert data['threshold'] == [0.0, 0.05]

    def test_load_missing_file(self, tmp_path):
        """Test behavior when file does not exist."""
        data = load_sensitivity_csv(str(tmp_path / "nonexistent.csv"))
        assert data is None

    def test_load_invalid_values(self, tmp_path):
        """Test handling of invalid numeric values."""
        csv_path = tmp_path / "bad.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['threshold_value', 'false_positive_rate', 'false_negative_rate'])
            writer.writeheader()
            writer.writerow({'threshold_value': 'invalid', 'false_positive_rate': '0.05', 'false_negative_rate': '0.02'})
            writer.writerow({'threshold_value': '0.1', 'false_positive_rate': '0.05', 'false_negative_rate': '0.02'})
        
        data = load_sensitivity_csv(str(csv_path))
        
        # Should skip the bad row and load the good one
        assert data is not None
        assert len(data['threshold']) == 1
        assert data['threshold'] == [0.1]

class TestPlotSensitivityAnalysis:
    def test_plot_with_both_datasets(self, tmp_path):
        """Test plotting with both depth and flat data present."""
        depth_data = {
            'threshold': [0.1, 0.5, 1.0],
            'fpr': [0.05, 0.03, 0.02],
            'fnr': [0.02, 0.04, 0.06]
        }
        flat_data = {
            'threshold': [0.0, 0.05, 0.1],
            'fpr': [0.1, 0.08, 0.07],
            'fnr': [0.0, 0.02, 0.03]
        }
        
        output_path = str(tmp_path / "plot.png")
        
        # This should not raise an exception
        plot_sensitivity_analysis(depth_data, flat_data, output_path)
        
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

    def test_plot_with_only_depth_data(self, tmp_path):
        """Test plotting when only depth data is available."""
        depth_data = {
            'threshold': [0.1, 0.5],
            'fpr': [0.05, 0.03],
            'fnr': [0.02, 0.04]
        }
        
        output_path = str(tmp_path / "plot.png")
        plot_sensitivity_analysis(depth_data, None, output_path)
        
        assert os.path.exists(output_path)

    def test_plot_with_only_flat_data(self, tmp_path):
        """Test plotting when only flat data is available."""
        flat_data = {
            'threshold': [0.0, 0.05],
            'fpr': [0.1, 0.08],
            'fnr': [0.0, 0.02]
        }
        
        output_path = str(tmp_path / "plot.png")
        plot_sensitivity_analysis(None, flat_data, output_path)
        
        assert os.path.exists(output_path)

    def test_plot_with_no_data(self, tmp_path):
        """Test plotting when no data is provided."""
        output_path = str(tmp_path / "plot.png")
        # Should still create a file, but with "No Data" messages
        plot_sensitivity_analysis(None, None, output_path)
        assert os.path.exists(output_path)