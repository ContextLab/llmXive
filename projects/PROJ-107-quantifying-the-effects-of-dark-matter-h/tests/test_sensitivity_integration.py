"""
Integration tests for sensitivity analysis (T030).
Tests the full flow of sensitivity analysis script.
"""
import pytest
import os
import sys
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.sensitivity import run_sensitivity_analysis, calculate_variance, recompute_bin_assignments

class TestSensitivityIntegration:
    @pytest.fixture
    def temp_project_structure(self):
        """Create a temporary project structure with mock data."""
        temp_dir = tempfile.mkdtemp()
        root = Path(temp_dir)
        
        # Create directory structure
        code_dir = root / "code"
        data_dir = root / "data"
        processed_dir = data_dir / "processed"
        
        code_dir.mkdir(parents=True)
        data_dir.mkdir(parents=True)
        processed_dir.mkdir(parents=True)
        
        # Create mock data files
        # 1. halo_shapes.csv with raw data
        halo_data = {
            'halo_id': range(100),
            'c_a_ratio': np.random.uniform(0.1, 1.0, 100),
            'b_a_ratio': np.random.uniform(0.1, 1.0, 100),
            'SFR': np.random.uniform(0.1, 10.0, 100)
        }
        halo_df = pd.DataFrame(halo_data)
        halo_df.to_csv(processed_dir / "halo_shapes.csv", index=False)
        
        # 2. statistical_results.csv (mock summary)
        stat_data = {
            'metric': ['SFR'],
            'test': ['Kruskal-Wallis'],
            'p_value': [0.05],
            'significance': ['not_significant']
        }
        stat_df = pd.DataFrame(stat_data)
        stat_df.to_csv(processed_dir / "statistical_results.csv", index=False)
        
        # 3. metadata.yaml
        metadata_content = """
        project:
          name: "test-project"
        success_criteria:
          SC-003: "Pending"
        """
        (data_dir / "metadata.yaml").write_text(metadata_content)
        
        # Mock config functions to use temp_dir
        def mock_get_project_root():
            return root
        
        def mock_get_data_processed_path():
            return processed_dir
        
        def mock_get_output_path():
            return root / "outputs"
        
        return root, mock_get_project_root, mock_get_data_processed_path, mock_get_output_path

    @patch('analysis.sensitivity.get_project_root')
    @patch('analysis.sensitivity.get_data_processed_path')
    @patch('analysis.sensitivity.get_output_path')
    def test_sensitivity_analysis_runs(self, mock_out, mock_proc, mock_root, temp_project_structure):
        """Test that the sensitivity analysis script runs without crashing."""
        root, mock_get_root, mock_get_proc, mock_get_out = temp_project_structure
        
        mock_root.return_value = root
        mock_proc.return_value = root / "data" / "processed"
        mock_out.return_value = root / "outputs"
        
        # Run the analysis
        df_output, variance, passed = run_sensitivity_analysis()
        
        # Assertions
        assert df_output is not None
        assert 'p_value' in df_output.columns
        assert 'threshold_low' in df_output.columns
        assert 'threshold_high' in df_output.columns
        
        # Check that output file was created
        output_file = root / "data" / "processed" / "sensitivity_report.csv"
        assert output_file.exists()
        
        # Check variance calculation
        assert isinstance(variance, float)

    def test_recompute_bin_assignments(self):
        """Test the bin reassignment logic."""
        df = pd.DataFrame({
            'c_a_ratio': [0.3, 0.5, 0.8, 0.9, 0.45, 0.75]
        })
        
        # Test with standard thresholds (0.5, 0.8)
        bins = recompute_bin_assignments(df, 0.5, 0.8)
        expected = ['prolate', 'triaxial', 'spherical', 'spherical', 'prolate', 'triaxial']
        assert bins.tolist() == expected
        
        # Test with varied thresholds (0.4, 0.7)
        bins2 = recompute_bin_assignments(df, 0.4, 0.7)
        expected2 = ['prolate', 'triaxial', 'spherical', 'spherical', 'triaxial', 'spherical']
        assert bins2.tolist() == expected2

    def test_variance_calculation(self):
        """Test variance calculation function."""
        # Normal case
        p_vals = [0.01, 0.02, 0.03]
        var = calculate_variance(p_vals)
        assert abs(var - 0.0000666) < 1e-6
        
        # With NaNs
        p_vals_nan = [0.01, np.nan, 0.03]
        var_nan = calculate_variance(p_vals_nan)
        assert abs(var_nan - 0.0001) < 1e-6
        
        # Insufficient data
        p_vals_one = [0.01]
        var_one = calculate_variance(p_vals_one)
        assert np.isnan(var_one)

    @patch('analysis.sensitivity.get_project_root')
    @patch('analysis.sensitivity.get_data_processed_path')
    @patch('analysis.sensitivity.get_output_path')
    def test_metadata_update(self, mock_out, mock_proc, mock_root, temp_project_structure):
        """Test that metadata is updated with SC-003 status."""
        root, mock_get_root, mock_get_proc, mock_get_out = temp_project_structure
        
        mock_root.return_value = root
        mock_proc.return_value = root / "data" / "processed"
        mock_out.return_value = root / "outputs"
        
        # Run analysis
        run_sensitivity_analysis()
        
        # Check metadata file
        metadata_file = root / "data" / "metadata.yaml"
        assert metadata_file.exists()
        
        content = metadata_file.read_text()
        assert 'SC-003' in content
        assert 'status' in content
        assert 'variance' in content