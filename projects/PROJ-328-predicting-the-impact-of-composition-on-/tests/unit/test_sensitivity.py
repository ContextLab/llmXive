"""
Unit tests for code/evaluation/sensitivity.py
"""
import pytest
import numpy as np
import tempfile
from pathlib import Path
import sys
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from evaluation.sensitivity import run_sensitivity_analysis


class TestSensitivity:
    """Tests for sensitivity analysis."""

    def test_sensitivity_calculation(self):
        """Test sensitivity analysis calculation."""
        # Create synthetic bootstrap R2 values
        np.random.seed(42)
        bootstrap_r2 = np.random.normal(0.6, 0.1, 1000)
        
        thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        
        results = run_sensitivity_analysis(bootstrap_r2, thresholds)
        
        assert len(results) == len(thresholds)
        
        # Check that fraction_exceeding decreases as threshold increases
        for i in range(len(results) - 1):
            assert results[i]['fraction_exceeding'] >= results[i+1]['fraction_exceeding']

    def test_fraction_bounds(self):
        """Test that fractions are within valid bounds."""
        np.random.seed(42)
        bootstrap_r2 = np.random.normal(0.6, 0.1, 1000)
        
        thresholds = [0.0, 0.5, 1.0]
        
        results = run_sensitivity_analysis(bootstrap_r2, thresholds)
        
        for result in results:
            assert 0.0 <= result['fraction_exceeding'] <= 1.0

    def test_threshold_0_and_1(self):
        """Test extreme thresholds."""
        np.random.seed(42)
        bootstrap_r2 = np.random.normal(0.6, 0.1, 1000)
        
        # Threshold 0: all should exceed
        results_0 = run_sensitivity_analysis(bootstrap_r2, [0.0])
        assert results_0[0]['fraction_exceeding'] == 1.0
        
        # Threshold 1: none should exceed (or very few)
        results_1 = run_sensitivity_analysis(bootstrap_r2, [1.0])
        assert results_1[0]['fraction_exceeding'] == 0.0

    def test_save_sensitivity_results(self, tmp_path):
        """Test saving sensitivity results."""
        np.random.seed(42)
        bootstrap_r2 = np.random.normal(0.6, 0.1, 1000)
        thresholds = [0.3, 0.5, 0.7]
        
        results = run_sensitivity_analysis(bootstrap_r2, thresholds)
        
        output_path = tmp_path / "sensitivity_analysis.yaml"
        
        with open(output_path, 'w') as f:
            yaml.dump(results, f)
        
        assert output_path.exists()
        
        # Verify content
        with open(output_path, 'r') as f:
            loaded = yaml.safe_load(f)
        
        assert len(loaded) == len(thresholds)