import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Add parent directory to path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.analyze.sensitivity_sweep import SensitivityAnalyzer, THRESHOLD_VALUES


class TestSensitivitySweep:
    """
    Tests for the Sensitivity Analysis Sweep (T029).
    
    Verifies that the sweep correctly iterates over threshold values
    and produces consistent statistical outputs.
    """

    def test_threshold_values_defined(self):
        """Verify the specific threshold values from SC-004 are used."""
        assert 0.01 in THRESHOLD_VALUES
        assert 0.05 in THRESHOLD_VALUES
        assert 0.1 in THRESHOLD_VALUES
        assert len(THRESHOLD_VALUES) == 3

    def test_analyzer_initialization(self):
        """Test that the analyzer initializes correctly."""
        analyzer = SensitivityAnalyzer()
        assert analyzer.results["thresholds_tested"] == THRESHOLD_VALUES
        assert analyzer.results["results"] == []

    def test_run_sweep_structure(self):
        """Test that run_sweep produces the expected dictionary structure."""
        analyzer = SensitivityAnalyzer()
        results = analyzer.run_sweep(num_samples=10, seed=42)
        
        assert "thresholds_tested" in results
        assert "results" in results
        assert "summary" in results
        assert len(results["results"]) == 3  # One per threshold

    def test_sweep_results_contain_stats(self):
        """Verify each threshold result contains required statistics."""
        analyzer = SensitivityAnalyzer()
        results = analyzer.run_sweep(num_samples=20, seed=123)
        
        for res in results["results"]:
            assert "threshold" in res
            assert "mean_error_proxy" in res
            assert "std_error_proxy" in res
            assert "trigger_count" in res
            assert "trigger_rate" in res
            
            # Verify types
            assert isinstance(res["threshold"], float)
            assert isinstance(res["trigger_count"], int)
            assert 0.0 <= res["trigger_rate"] <= 1.0

    def test_sweep_reproducibility(self):
        """Test that the sweep is reproducible with the same seed."""
        analyzer1 = SensitivityAnalyzer()
        results1 = analyzer1.run_sweep(num_samples=50, seed=99)
        
        analyzer2 = SensitivityAnalyzer()
        results2 = analyzer2.run_sweep(num_samples=50, seed=99)
        
        # Results should be identical
        assert results1 == results2

    def test_summary_robustness_logic(self):
        """Test that the summary correctly assesses robustness based on variance."""
        analyzer = SensitivityAnalyzer()
        results = analyzer.run_sweep(num_samples=100, seed=42)
        
        assert "robustness_assessment" in results["summary"]
        assert "threshold_variance" in results["summary"]
        
        # The assessment should be either 'stable' or 'sensitive'
        assert results["summary"]["robustness_assessment"] in ["stable", "sensitive"]

    def test_save_results_creates_file(self):
        """Test that save_results writes a valid JSON file."""
        analyzer = SensitivityAnalyzer()
        analyzer.run_sweep(num_samples=10, seed=42)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_sensitivity.json"
            analyzer.save_results(str(output_path))
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded == analyzer.results