"""
Unit tests for the power analysis module.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.power import perform_power_analysis, estimate_required_sample_size, run_power_analysis

class TestPowerAnalysis:
    def test_perform_power_analysis_high_sample_size(self):
        """Test that a large sample size yields high power."""
        power, passed = perform_power_analysis(
            n_obs=1000,
            effect_size_f2=0.15,
            alpha=0.05
        )
        assert power > 0.80
        assert passed is True

    def test_perform_power_analysis_low_sample_size(self):
        """Test that a very small sample size yields low power."""
        power, passed = perform_power_analysis(
            n_obs=10,
            effect_size_f2=0.15,
            alpha=0.05
        )
        # With N=10, power should be very low
        assert power < 0.50
        assert passed is False

    def test_perform_power_analysis_boundary(self):
        """Test power calculation near the target threshold."""
        # This is a sanity check; exact boundary depends on the solver
        power, passed = perform_power_analysis(
            n_obs=100,
            effect_size_f2=0.15,
            alpha=0.05
        )
        # Just ensure it returns a valid float between 0 and 1
        assert 0.0 <= power <= 1.0

    def test_run_power_analysis_integration(self):
        """Integration test for run_power_analysis with a fake CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "filtered_tasks.csv"
            output_path = Path(tmpdir) / "power_report.json"
            
            # Create a fake dataset
            df = pd.DataFrame({
                "task_id": [f"task_{i}" for i in range(200)],
                "constraint_count": [5] * 200
            })
            df.to_csv(input_path, index=False)
            
            # Run analysis
            report = run_power_analysis(input_path, output_path)
            
            # Verify output file exists
            assert output_path.exists()
            
            # Verify report content
            assert "calculated_power" in report
            assert "effect_size" in report
            assert "pass" in report
            assert report["sample_size"] == 200
            
            # Load and verify JSON structure
            with open(output_path) as f:
                loaded_report = json.load(f)
                assert loaded_report["sample_size"] == 200

    def test_estimate_required_sample_size(self):
        """Test sample size estimation."""
        n = estimate_required_sample_size(
            effect_size=0.15,
            power=0.80
        )
        assert n > 0
        assert isinstance(n, int)

if __name__ == "__main__":
    pytest.main([__file__])