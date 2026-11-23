"""
Unit tests for statistical analysis functions.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from stats import (
    load_repro_results,
    extract_metric_values,
    run_paired_ttest,
    apply_bonferroni_correction,
    run_all_paired_ttests,
    generate_stat_summary,
    METRICS,
    DEFAULT_ALPHA
)


class TestLoadReproResults(TestCase):
    """Tests for load_repro_results function."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_load_list_format(self):
        """Test loading results in list format."""
        results_path = self.temp_path / "results.json"
        test_data = [
            {"paper_id": "1", "reported_metrics": {"mae": 0.5}, "reproduced_metrics": {"mae": 0.6}},
            {"paper_id": "2", "reported_metrics": {"mae": 0.7}, "reproduced_metrics": {"mae": 0.8}}
        ]
        
        with open(results_path, 'w') as f:
            json.dump(test_data, f)
        
        loaded = load_repro_results(str(results_path))
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["paper_id"], "1")
    
    def test_load_dict_format(self):
        """Test loading results in dictionary format."""
        results_path = self.temp_path / "results.json"
        test_data = {
            "paper_id": "1",
            "reported_metrics": {"mae": 0.5},
            "reproduced_metrics": {"mae": 0.6}
        }
        
        with open(results_path, 'w') as f:
            json.dump(test_data, f)
        
        loaded = load_repro_results(str(results_path))
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["paper_id"], "1")
    
    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with self.assertRaises(FileNotFoundError):
            load_repro_results("/nonexistent/path.json")
    
    def test_invalid_json(self):
        """Test that JSONDecodeError is raised for invalid JSON."""
        results_path = self.temp_path / "invalid.json"
        with open(results_path, 'w') as f:
            f.write("not valid json")
        
        with self.assertRaises(json.JSONDecodeError):
            load_repro_results(str(results_path))


class TestExtractMetricValues(TestCase):
    """Tests for extract_metric_values function."""
    
    def test_extract_mae(self):
        """Test extracting MAE values."""
        results = [
            {
                "paper_id": "1",
                "reported_metrics": {"mae": 0.5, "r2": 0.8},
                "reproduced_metrics": {"mae": 0.6, "r2": 0.75}
            },
            {
                "paper_id": "2",
                "reported_metrics": {"mae": 0.7, "r2": 0.85},
                "reproduced_metrics": {"mae": 0.75, "r2": 0.82}
            }
        ]
        
        reported, reproduced = extract_metric_values(results, "mae")
        
        self.assertEqual(len(reported), 2)
        self.assertEqual(len(reproduced), 2)
        self.assertEqual(reported, [0.5, 0.7])
        self.assertEqual(reproduced, [0.6, 0.75])
    
    def test_skip_missing_values(self):
        """Test that results with missing values are skipped."""
        results = [
            {
                "paper_id": "1",
                "reported_metrics": {"mae": 0.5},
                "reproduced_metrics": {"mae": 0.6}
            },
            {
                "paper_id": "2",
                "reported_metrics": {"mae": 0.7},
                "reproduced_metrics": {}  # Missing reproduced mae
            },
            {
                "paper_id": "3",
                "reported_metrics": {},  # Missing reported mae
                "reproduced_metrics": {"mae": 0.8}
            },
            {
                "paper_id": "4",
                "reported_metrics": {"mae": 0.9},
                "reproduced_metrics": {"mae": 0.95}
            }
        ]
        
        reported, reproduced = extract_metric_values(results, "mae")
        
        # Should only get results 1 and 4
        self.assertEqual(len(reported), 2)
        self.assertEqual(reported, [0.5, 0.9])
        self.assertEqual(reproduced, [0.6, 0.95])
    
    def test_no_valid_values(self):
        """Test that ValueError is raised when no valid values found."""
        results = [
            {
                "paper_id": "1",
                "reported_metrics": {},
                "reproduced_metrics": {}
            }
        ]
        
        with self.assertRaises(ValueError):
            extract_metric_values(results, "mae")

class TestRunPairedTtest(TestCase):
    """Tests for run_paired_ttest function."""
    
    def test_basic_ttest(self):
        """Test basic paired t-test execution."""
        reported = [0.5, 0.6, 0.7, 0.8, 0.9]
        reproduced = [0.52, 0.58, 0.72, 0.78, 0.91]
        
        result = run_paired_ttest(reported, reproduced, "mae")
        
        self.assertEqual(result["metric"], "mae")
        self.assertEqual(result["n_samples"], 5)
        self.assertIn("t_statistic", result)
        self.assertIn("p_value", result)
        self.assertIn("mean_reported", result)
        self.assertIn("mean_reproduced", result)
        self.assertEqual(result["test_type"], "paired_ttest")
    
    def test_different_lengths_error(self):
        """Test that ValueError is raised for different length lists."""
        with self.assertRaises(ValueError):
            run_paired_ttest([1, 2, 3], [1, 2], "mae")
    
    def test_insufficient_samples_error(self):
        """Test that ValueError is raised for insufficient samples."""
        with self.assertRaises(ValueError):
            run_paired_ttest([1], [1.1], "mae")
    
    def test_ttest_results(self):
        """Test that t-test produces reasonable results."""
        # Identical values should give p-value = 1.0
        reported = [0.5, 0.6, 0.7, 0.8, 0.9]
        reproduced = [0.5, 0.6, 0.7, 0.8, 0.9]
        
        result = run_paired_ttest(reported, reproduced, "mae")
        
        self.assertAlmostEqual(result["t_statistic"], 0.0, places=5)
        self.assertAlmostEqual(result["p_value"], 1.0, places=5)

class TestApplyBonferroniCorrection(TestCase):
    """Tests for apply_bonferroni_correction function."""
    
    def test_basic_correction(self):
        """Test basic Bonferroni correction."""
        test_results = [
            {"p_value": 0.01, "metric": "mae"},
            {"p_value": 0.03, "metric": "r2"},
            {"p_value": 0.05, "metric": "rho"}
        ]
        
        corrected = apply_bonferroni_correction(test_results, alpha=0.05)
        
        self.assertEqual(len(corrected), 3)
        
        # Check that corrected values are present
        for result in corrected:
            self.assertIn("p_value_corrected", result)
            self.assertIn("is_significant", result)
            self.assertEqual(result["method"], "bonferroni")
            self.assertEqual(result["alpha"], 0.05)
            self.assertEqual(result["n_tests"], 3)
    
    def test_empty_list(self):
        """Test that empty list returns empty list."""
        corrected = apply_bonferroni_correction([], alpha=0.05)
        self.assertEqual(len(corrected), 0)
    
    def test_significance_threshold(self):
        """Test that significance is correctly determined."""
        test_results = [
            {"p_value": 0.01},  # Should be significant after correction
            {"p_value": 0.04},  # May or may not be significant
            {"p_value": 0.06}   # Should not be significant
        ]
        
        corrected = apply_bonferroni_correction(test_results, alpha=0.05)
        
        # First result should be significant (0.01 * 3 = 0.03 < 0.05)
        self.assertTrue(corrected[0]["is_significant"])

class TestRunAllPairedTtests(TestCase):
    """Tests for run_all_paired_ttests function."""
    
    def test_all_metrics(self):
        """Test that all metrics are tested."""
        results = [
            {
                "paper_id": f"paper_{i}",
                "reported_metrics": {"mae": 0.5 + i*0.1, "r2": 0.8 - i*0.05, "rho": 0.9 - i*0.05},
                "reproduced_metrics": {"mae": 0.52 + i*0.1, "r2": 0.78 - i*0.05, "rho": 0.88 - i*0.05}
            }
            for i in range(10)
        ]
        
        summary = run_all_paired_ttests(results, alpha=0.05)
        
        self.assertEqual(summary["n_papers"], 10)
        self.assertEqual(summary["n_tests_performed"], 3)
        self.assertEqual(summary["correction_method"], "bonferroni")
        self.assertEqual(summary["alpha"], 0.05)
        
        # Check that all metrics are present
        metrics_tested = [test["metric"] for test in summary["tests"]]
        self.assertEqual(set(metrics_tested), set(METRICS))
    
    def test_skip_invalid_metrics(self):
        """Test that invalid metrics are skipped with warning."""
        results = [
            {
                "paper_id": "1",
                "reported_metrics": {"mae": 0.5},  # Missing r2 and rho
                "reproduced_metrics": {"mae": 0.6}
            }
        ]
        
        # Should not raise error, just skip missing metrics
        summary = run_all_paired_ttests(results, alpha=0.05)
        
        self.assertEqual(summary["n_papers"], 1)
        # Only mae should be tested
        metrics_tested = [test["metric"] for test in summary["tests"]]
        self.assertEqual(len(metrics_tested), 1)
        self.assertEqual(metrics_tested[0], "mae")

class TestGenerateStatSummary(TestCase):
    """Tests for generate_stat_summary function."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_save_to_file(self):
        """Test that summary is saved to file."""
        results = [
            {
                "paper_id": f"paper_{i}",
                "reported_metrics": {"mae": 0.5 + i*0.1, "r2": 0.8 - i*0.05, "rho": 0.9 - i*0.05},
                "reproduced_metrics": {"mae": 0.52 + i*0.1, "r2": 0.78 - i*0.05, "rho": 0.88 - i*0.05}
            }
            for i in range(5)
        ]
        
        output_path = self.temp_path / "stat_summary.json"
        summary = generate_stat_summary(results, str(output_path), alpha=0.05)
        
        self.assertTrue(output_path.exists())
        
        # Verify file content
        with open(output_path, 'r') as f:
            saved_summary = json.load(f)
        
        self.assertEqual(saved_summary["n_papers"], 5)
        self.assertEqual(saved_summary["n_tests_performed"], 3)
    
    def test_creates_directory(self):
        """Test that output directory is created if it doesn't exist."""
        results = [
            {
                "paper_id": "1",
                "reported_metrics": {"mae": 0.5, "r2": 0.8, "rho": 0.9},
                "reproduced_metrics": {"mae": 0.52, "r2": 0.78, "rho": 0.88}
            }
        ]
        
        output_path = self.temp_path / "nested" / "dir" / "stat_summary.json"
        summary = generate_stat_summary(results, str(output_path), alpha=0.05)
        
        self.assertTrue(output_path.exists())

class TestIntegration(TestCase):
    """Integration tests for the stats module."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_full_pipeline(self):
        """Test the complete pipeline from results to summary."""
        # Create realistic test data
        results = [
            {
                "paper_id": f"paper_{i}",
                "reported_metrics": {
                    "mae": 0.5 + np.random.normal(0, 0.1),
                    "r2": 0.8 + np.random.normal(0, 0.05),
                    "rho": 0.9 + np.random.normal(0, 0.05)
                },
                "reproduced_metrics": {
                    "mae": 0.52 + np.random.normal(0, 0.1),
                    "r2": 0.78 + np.random.normal(0, 0.05),
                    "rho": 0.88 + np.random.normal(0, 0.05)
                }
            }
            for i in range(20)
        ]
        
        results_path = self.temp_path / "repro_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f)
        
        output_path = self.temp_path / "stat_summary.json"
        
        # Run the full pipeline
        summary = generate_stat_summary(
            load_repro_results(str(results_path)),
            str(output_path),
            alpha=0.05
        )
        
        # Verify results
        self.assertTrue(output_path.exists())
        self.assertEqual(summary["n_papers"], 20)
        self.assertEqual(summary["n_tests_performed"], 3)
        self.assertEqual(len(summary["tests"]), 3)
        
        # Each test should have corrected p-value
        for test in summary["tests"]:
            self.assertIn("p_value_corrected", test)
            self.assertIn("is_significant", test)
            self.assertGreater(test["p_value_corrected"], 0)
            self.assertLessEqual(test["p_value_corrected"], 1)