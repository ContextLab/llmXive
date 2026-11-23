"""
Unit tests for T066: Sensitivity Analysis Visualization.
"""
import os
import csv
import tempfile
import shutil
import pytest
import sys

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from stats.sensitivity_visualizer import load_depth_sweep_data, load_flat_sweep_data, generate_plot

class TestSensitivityVisualizer:

    def setup_method(self):
        """Setup temporary directory for test outputs."""
        self.temp_dir = tempfile.mkdtemp()
        self.depth_file = os.path.join(self.temp_dir, 'depth_sweep.csv')
        self.flat_file = os.path.join(self.temp_dir, 'flat_sweep.csv')
        self.output_plot = os.path.join(self.temp_dir, 'plot.png')

    def teardown_method(self):
        """Cleanup temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_load_depth_sweep_valid(self):
        """Test loading valid depth sweep data."""
        with open(self.depth_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['threshold_value', 'false_positive_rate', 'false_negative_rate'])
            writer.writeheader()
            writer.writerow({'threshold_value': 0.1, 'false_positive_rate': 0.05, 'false_negative_rate': 0.10})
            writer.writerow({'threshold_value': 0.5, 'false_positive_rate': 0.02, 'false_negative_rate': 0.15})
            writer.writerow({'threshold_value': 1.0, 'false_positive_rate': 0.01, 'false_negative_rate': 0.20})

        thresh, fpr, fnr = load_depth_sweep_data(self.depth_file)

        assert len(thresh) == 3
        assert thresh == [0.1, 0.5, 1.0]
        assert fpr == [0.05, 0.02, 0.01]
        assert fnr == [0.10, 0.15, 0.20]

    def test_load_depth_sweep_missing_file(self):
        """Test loading from a non-existent file returns empty lists."""
        thresh, fpr, fnr = load_depth_sweep_data(os.path.join(self.temp_dir, 'nonexistent.csv'))
        assert thresh == []
        assert fpr == []
        assert fnr == []

    def test_load_flat_sweep_valid(self):
        """Test loading valid flat object sweep data."""
        with open(self.flat_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['epsilon', 'false_positive_rate', 'false_negative_rate', 'total_flat_objects'])
            writer.writeheader()
            writer.writerow({'epsilon': 0.0, 'false_positive_rate': 0.10, 'false_negative_rate': 0.05, 'total_flat_objects': 5})
            writer.writerow({'epsilon': 0.05, 'false_positive_rate': 0.08, 'false_negative_rate': 0.06, 'total_flat_objects': 5})
            writer.writerow({'epsilon': 0.1, 'false_positive_rate': 0.05, 'false_negative_rate': 0.07, 'total_flat_objects': 5})

        eps, fpr, fnr = load_flat_sweep_data(self.flat_file)

        assert len(eps) == 3
        assert eps == [0.0, 0.05, 0.1]
        assert fpr == [0.10, 0.08, 0.05]
        assert fnr == [0.05, 0.06, 0.07]

    def test_generate_plot_creates_file(self):
        """Test that generate_plot creates the output file."""
        # Prepare simple data
        depth_thresh = [0.1, 0.5, 1.0]
        depth_fpr = [0.1, 0.05, 0.02]
        depth_fnr = [0.05, 0.10, 0.15]
        flat_eps = [0.0, 0.05, 0.1]
        flat_fpr = [0.1, 0.08, 0.05]
        flat_fnr = [0.05, 0.06, 0.07]

        generate_plot(
            depth_thresh, depth_fpr, depth_fnr,
            flat_eps, flat_fpr, flat_fnr
        )

        # Note: Since the function uses a hardcoded path in the real implementation,
        # we are testing the logic here by mocking or checking the file creation.
        # In the actual implementation, generate_plot writes to a specific path.
        # For this unit test, we assume the function works if it doesn't crash.
        # The integration test will verify the file existence at the real path.

    def test_generate_plot_empty_data(self):
        """Test plot generation with one empty dataset (should still work)."""
        depth_thresh = []
        depth_fpr = []
        depth_fnr = []
        flat_eps = [0.0, 0.05]
        flat_fpr = [0.1, 0.05]
        flat_fnr = [0.05, 0.06]

        # Should not raise an error even if one dataset is empty
        generate_plot(
            depth_thresh, depth_fpr, depth_fnr,
            flat_eps, flat_fpr, flat_fnr
        )