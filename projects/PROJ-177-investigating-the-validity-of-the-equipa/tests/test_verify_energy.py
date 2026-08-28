"""
Unit tests for the energy verification module (T012a).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import os
import sys

# Add code to path if not already
sys.path.insert(0, 'code')

from verify_energy_implementation import generate_synthetic_ground_truth, run_verification

class TestEnergyVerification:
    
    def test_generate_synthetic_ground_truth_creates_file(self, tmp_path):
        """Test that the ground truth generator creates the CSV file."""
        output_path = tmp_path / "manual_baseline.csv"
        df = generate_synthetic_ground_truth(output_path)
        
        assert output_path.exists(), "Output CSV file was not created"
        assert df is not None, "DataFrame was not returned"
        assert 'E_trans_expected' in df.columns, "Expected column missing"
        assert 'E_rot_expected' in df.columns, "Expected column missing"
        assert 'E_pot_expected' in df.columns, "Expected column missing"
        assert 'E_vib_expected' in df.columns, "Expected column missing"

    def test_energy_values_are_correct(self, tmp_path):
        """Test that the calculated ground truth values match manual physics."""
        output_path = tmp_path / "manual_baseline.csv"
        df = generate_synthetic_ground_truth(output_path)
        
        # Constants used in generation
        mass = 1.0
        radius = 0.05
        g = 9.81
        
        # v = [1, 2, 3] -> v^2 = 1+4+9 = 14
        # E_trans = 0.5 * 1 * 14 = 7.0
        assert np.isclose(df['E_trans_expected'].iloc[0], 7.0), "E_trans calculation incorrect"
        
        # I = 0.4 * 1 * 0.05^2 = 0.001
        # omega = [0.1, 0.2, 0.3] -> omega^2 = 0.01+0.04+0.09 = 0.14
        # E_rot = 0.5 * 0.001 * 0.14 = 0.00007
        expected_rot = 0.5 * (0.4 * mass * radius**2) * (0.1**2 + 0.2**2 + 0.3**2)
        assert np.isclose(df['E_rot_expected'].iloc[0], expected_rot), "E_rot calculation incorrect"
        
        # E_pot = 1 * 9.81 * 1.0 = 9.81
        assert np.isclose(df['E_pot_expected'].iloc[0], 9.81), "E_pot calculation incorrect"
        
        # E_vib = 0 (constant velocity)
        assert np.isclose(df['E_vib_expected'].iloc[0], 0.0), "E_vib calculation incorrect"

    def test_verification_report_structure(self, tmp_path, monkeypatch):
        """Test that the verification report is generated with correct structure."""
        # Mock the artifacts directory
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        
        # Patch the Path calls to use tmp_path
        import verify_energy_implementation
        original_path = verify_energy_implementation.Path
        
        def mock_path(path_str):
            if path_str == "artifacts":
                return artifacts_dir
            return original_path(path_str)
        
        monkeypatch.setattr(verify_energy_implementation, 'Path', mock_path)
        
        # Run verification
        # We need to mock compute_energy to return a known result
        def mock_compute_energy(df, dt=0.01):
            # Return a copy with expected columns added
            res = df.copy()
            res['E_trans'] = res['E_trans_expected']
            res['E_rot'] = res['E_rot_expected']
            res['E_pot'] = res['E_pot_expected']
            res['E_vib'] = res['E_vib_expected']
            return res
        
        monkeypatch.setattr(verify_energy_implementation, 'compute_energy', mock_compute_energy)
        
        run_verification()
        
        report_path = artifacts_dir / "energy_verification_report.json"
        assert report_path.exists(), "Verification report not created"
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert "status" in report
        assert "max_absolute_error" in report
        assert "repair_needed" in report
        assert report["status"] == "success"
        assert report["repair_needed"] == False # Since errors are 0
        assert report["max_absolute_error"] == 0.0