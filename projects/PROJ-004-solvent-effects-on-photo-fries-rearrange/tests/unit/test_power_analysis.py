"""
Unit tests for the Unified Power Analysis module (T059).
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.power import (
    calculate_effect_size,
    estimate_mdes,
    calculate_post_hoc_power,
    analyze_kinetic_power,
    analyze_correlation_power,
    write_power_report,
    PowerAnalysisError
)

class TestPowerCalculations(TestCase):
    
    def test_calculate_effect_size(self):
        """Test Cohen's d calculation."""
        # Standard case
        d = calculate_effect_size(mean_diff=0.5, std_dev=1.0)
        self.assertAlmostEqual(d, 0.5)
        
        # Zero std dev
        d = calculate_effect_size(mean_diff=0.5, std_dev=0.0)
        self.assertEqual(d, 0.0)

    def test_estimate_mdes(self):
        """Test Minimum Detectable Effect Size estimation."""
        # Large N should yield smaller MDES
        mdes_large = estimate_mdes(n=100, alpha=0.05, power=0.8, std_dev=1.0)
        # Small N should yield larger MDES
        mdes_small = estimate_mdes(n=3, alpha=0.05, power=0.8, std_dev=1.0)
        
        self.assertGreater(mdes_small, mdes_large)
        self.assertGreater(mdes_small, 0)

    def test_calculate_post_hoc_power(self):
        """Test post-hoc power calculation."""
        # With large effect and N, power should be high
        power_high = calculate_post_hoc_power(n=50, effect_size=1.0, alpha=0.05)
        self.assertGreater(power_high, 0.8)
        
        # With small effect and small N, power should be low
        power_low = calculate_post_hoc_power(n=3, effect_size=0.2, alpha=0.05)
        self.assertLess(power_low, 0.5)

class TestAnalysisFunctions(TestCase):
    
    def test_analyze_kinetic_power_structure(self):
        """Test that kinetic power analysis returns expected keys."""
        results = analyze_kinetic_power(n_replicates=3)
        
        required_keys = [
            "n_replicates", "assumed_std_dev_ns", "alpha", "target_power",
            "mdes_ns", "power_for_medium_effect", "interpretation"
        ]
        
        for key in required_keys:
            self.assertIn(key, results)
        
        self.assertIsInstance(results["mdes_ns"], float)
        self.assertGreater(results["mdes_ns"], 0)

    def test_analyze_correlation_power_structure(self):
        """Test that correlation power analysis returns expected keys."""
        results = analyze_correlation_power(n_solvents=5)
        
        required_keys = [
            "n_solvents", "n_replicates_per_solvent", "effective_N", "alpha",
            "assumed_correlation", "critical_r", "power_to_detect_assumed_r", "interpretation"
        ]
        
        for key in required_keys:
            self.assertIn(key, results)
        
        self.assertIsInstance(results["power_to_detect_assumed_r"], float)
        self.assertLessEqual(results["power_to_detect_assumed_r"], 1.0)

class TestWritePowerReport(TestCase):
    
    def test_write_power_report_creates_file(self):
        """Test that the report is written to disk correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_power_analysis.json"
            
            kinetic = {"mdes_ns": 0.1}
            correlation = {"power_to_detect_assumed_r": 0.2}
            
            write_power_report(kinetic, correlation, output_path)
            
            self.assertTrue(output_path.exists())
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            self.assertIn("metadata", data)
            self.assertIn("kinetic_analysis", data)
            self.assertIn("correlation_analysis", data)
            self.assertIn("unified_conclusion", data)
            self.assertEqual(data["kinetic_analysis"]["mdes_ns"], 0.1)

if __name__ == "__main__":
    import unittest
    unittest.main()