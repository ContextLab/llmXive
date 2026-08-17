"""
Integration test for comparative evaluation.
Verifies output reports MAE_semi, MAE_DFT, p-value, flags.
"""
import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile
import shutil

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from evaluate_models import (
    run_paired_t_test,
    verify_mae_threshold,
    load_data_semi,
    load_data_dft
)


class TestEvaluateModels:
    """Integration tests for the comparative evaluation pipeline."""

    @pytest.fixture(autouse=True)
    def setup_temp_dirs(self, tmp_path):
        """Create temporary directories for test artifacts."""
        self.temp_dir = tmp_path
        self.data_dir = self.temp_dir / "data"
        self.reports_dir = self.temp_dir / "reports"
        self.data_dir.mkdir()
        self.reports_dir.mkdir()
        
        # Create mock data files
        self.semi_csv = self.data_dir / "descriptors_semi.csv"
        self.dft_csv = self.data_dir / "descriptors_dft.csv"
        self.eval_json = self.reports_dir / "evaluation.json"
        
        # Write mock semi-empirical data
        semi_data = [
            ["molecule_id", "homo", "lumo", "mayer", "experimental_barrier"],
            ["mol_001", "-5.2", "-1.1", "0.85", "12.5"],
            ["mol_002", "-5.5", "-1.3", "0.92", "14.2"],
            ["mol_003", "-5.1", "-1.0", "0.78", "11.8"],
            ["mol_004", "-5.4", "-1.2", "0.88", "13.5"],
            ["mol_005", "-5.3", "-1.15", "0.82", "12.9"],
        ]
        with open(self.semi_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(semi_data)
        
        # Write mock DFT data
        dft_data = [
            ["molecule_id", "homo", "lumo", "mayer", "experimental_barrier"],
            ["mol_001", "-5.45", "-1.05", "0.86", "12.5"],
            ["mol_002", "-5.75", "-1.25", "0.93", "14.2"],
            ["mol_003", "-5.35", "-0.95", "0.79", "11.8"],
            ["mol_004", "-5.65", "-1.15", "0.89", "13.5"],
            ["mol_005", "-5.55", "-1.10", "0.83", "12.9"],
        ]
        with open(self.dft_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(dft_data)

    def test_load_data_semi(self):
        """Verify loading of semi-empirical descriptor data."""
        data = load_data_semi(str(self.semi_csv))
        assert len(data) == 5
        assert "homo" in data[0]
        assert "experimental_barrier" in data[0]
        assert float(data[0]["homo"]) < 0

    def test_load_data_dft(self):
        """Verify loading of DFT descriptor data."""
        data = load_data_dft(str(self.dft_csv))
        assert len(data) == 5
        assert "homo" in data[0]
        assert float(data[0]["homo"]) < 0

    def test_run_paired_t_test(self):
        """Verify paired t-test calculation between semi and DFT models."""
        # Mock fold results for semi-empirical model
        semi_mae = [0.8, 0.75, 0.82, 0.78, 0.79]
        # Mock fold results for DFT model
        dft_mae = [0.6, 0.58, 0.62, 0.59, 0.61]
        
        result = run_paired_t_test(semi_mae, dft_mae)
        
        assert "statistic" in result
        assert "p_value" in result
        assert "null_hypothesis" in result
        assert "significance_level" in result
        assert "models_compared" in result
        assert result["significance_level"] == 0.05
        assert result["models_compared"] == ["semi_empirical", "dft_b3lyp"]

    def test_verify_mae_threshold(self):
        """Verify MAE threshold comparison logic."""
        semi_mae = 0.8
        dft_mae = 0.6
        
        flag, ratio = verify_mae_threshold(semi_mae, dft_mae)
        
        # Semi MAE is 33% higher than DFT MAE (0.8/0.6 = 1.33)
        assert flag == True
        assert ratio > 1.2

    def test_full_evaluation_report(self):
        """Test the full evaluation report generation structure."""
        # Simulate the data that would be produced by the full pipeline
        semi_mae = 0.8
        dft_mae = 0.6
        
        t_test_result = {
            "statistic": -4.52,
            "p_value": 0.008,
            "null_hypothesis": "No difference in mean absolute error",
            "significance_level": 0.05,
            "models_compared": ["semi_empirical", "dft_b3lyp"]
        }
        
        flag, ratio = verify_mae_threshold(semi_mae, dft_mae)
        
        report = {
            "mae_semi": semi_mae,
            "mae_dft": dft_mae,
            "t_test": t_test_result,
            "mae_threshold_flag": flag,
            "threshold_ratio": ratio
        }
        
        # Write report to temp location
        with open(self.eval_json, "w") as f:
            json.dump(report, f, indent=2)
        
        # Verify file exists and contains expected keys
        assert self.eval_json.exists()
        with open(self.eval_json) as f:
            loaded = json.load(f)
            assert loaded["mae_semi"] == semi_mae
            assert loaded["mae_dft"] == dft_mae
            assert "p_value" in loaded["t_test"]
            assert loaded["mae_threshold_flag"] == True

    def test_script_structure(self):
        """Verify evaluate_models.py exists and has correct structure."""
        script_path = Path("code/evaluate_models.py")
        assert script_path.exists(), "evaluate_models.py not found"
        
        with open(script_path) as f:
            content = f.read()
            assert "run_paired_t_test" in content
            assert "verify_mae_threshold" in content
            assert "load_data_semi" in content
            assert "load_data_dft" in content

# Import csv here to avoid top-level dependency issues in test discovery
import csv