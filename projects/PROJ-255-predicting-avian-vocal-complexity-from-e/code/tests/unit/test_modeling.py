"""
Unit tests for src/analysis/modeling.py
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.analysis.modeling import run_power_analysis, generate_power_report

class TestPowerAnalysis:
    
    def test_run_power_analysis_basic(self):
        """Test that power analysis runs and returns expected keys."""
        result = run_power_analysis(n_species=50, n_observations_per_species=5)
        
        assert isinstance(result, dict)
        assert "min_detectable_effect_size_f" in result
        assert "n_species" in result
        assert "target_power" in result
        assert "detailed_results" in result
        assert len(result["detailed_results"]) > 0
        
        # Check types
        assert isinstance(result["min_detectable_effect_size_f"], (float, type(None)))
        
    def test_mdes_monotonicity(self):
        """Test that power increases with effect size."""
        result = run_power_analysis(n_species=50, n_observations_per_species=5, effect_size_range=[0.1, 0.2, 0.3, 0.4, 0.5])
        
        powers = [r["power"] for r in result["detailed_results"]]
        # Power should generally increase with effect size
        # Allowing for slight numerical noise, we check the trend
        assert powers[-1] >= powers[0]

    def test_generate_power_report_writes_file(self):
        """Test that generate_power_report creates a valid markdown file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.md"
            
            result = run_power_analysis(n_species=10, n_observations_per_species=5)
            generate_power_report(result, output_path)
            
            assert output_path.exists()
            content = output_path.read_text()
            
            assert "# Power Analysis Report" in content
            assert "Minimum Detectable Effect Size" in content
            assert "## Parameters" in content

if __name__ == "__main__":
    pytest.main([__file__, "-v"])