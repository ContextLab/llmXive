"""
Test for numerical tolerance (5%) between original and rerun results.
Implements T028: Verify reproducibility package outputs match baseline within 5% tolerance.
"""
import unittest
import json
import csv
import os
import sys
import numpy as np
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class TestReproducibility(unittest.TestCase):
    """Tests numerical tolerance between baseline and rerun results."""

    BASELINE_PATH = project_root / "data" / "analysis_results" / "baseline_results.json"
    RESULTS_CSV_PATH = project_root / "data" / "analysis_results" / "results.csv"
    TOLERANCE_THRESHOLD = 0.05  # 5% tolerance

    def setUp(self):
        """Set up test fixtures."""
        self.baseline_path = self.BASELINE_PATH
        self.results_csv_path = self.RESULTS_CSV_PATH
        self.project_root = project_root

    def test_baseline_file_exists(self):
        """Verify baseline results file exists."""
        self.assertTrue(
            self.baseline_path.exists(),
            f"Baseline file not found at {self.baseline_path}. "
            "Run T030a to generate baseline results first."
        )

    def test_results_csv_exists(self):
        """Verify rerun results CSV exists."""
        self.assertTrue(
            self.results_csv_path.exists(),
            f"Results CSV not found at {self.results_csv_path}. "
            "Run code/analysis/run_statistics.py to generate results first."
        )

    def load_baseline_results(self):
        """Load baseline results from JSON."""
        with open(self.baseline_path, 'r') as f:
            return json.load(f)

    def load_results_csv(self):
        """Load rerun results from CSV."""
        results = []
        with open(self.results_csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(row)
        return results

    def extract_numeric_metrics(self, data_source):
        """
        Extract numeric metrics from baseline or results.
        Returns a dict of metric_name -> value.
        """
        metrics = {}
        if isinstance(data_source, dict):
            # Handle baseline JSON structure
            if 'metrics' in data_source:
                for key, value in data_source['metrics'].items():
                    if isinstance(value, (int, float)):
                        metrics[key] = float(value)
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, (int, float)):
                                metrics[f"{key}_{sub_key}"] = float(sub_value)
        elif isinstance(data_source, list):
            # Handle CSV rows
            for row in data_source:
                for key, value in row.items():
                    try:
                        num_val = float(value)
                        metrics[key] = num_val
                    except (ValueError, TypeError):
                        continue
        return metrics

    def calculate_relative_difference(self, baseline_val, rerun_val):
        """Calculate relative difference between two values."""
        if baseline_val == 0:
            # If baseline is 0, use absolute difference
            return abs(rerun_val)
        return abs(rerun_val - baseline_val) / abs(baseline_val)

    def test_numerical_tolerance(self):
        """
        Test that rerun results match baseline within 5% tolerance.
        This is the core reproducibility test.
        """
        # Load data
        baseline_data = self.load_baseline_results()
        rerun_data = self.load_results_csv()

        # Extract metrics
        baseline_metrics = self.extract_numeric_metrics(baseline_data)
        rerun_metrics = self.extract_numeric_metrics(rerun_data)

        # Check that we have metrics to compare
        self.assertGreater(
            len(baseline_metrics), 0,
            "No numeric metrics found in baseline results"
        )
        self.assertGreater(
            len(rerun_metrics), 0,
            "No numeric metrics found in rerun results"
        )

        # Find common metrics
        common_metrics = set(baseline_metrics.keys()) & set(rerun_metrics.keys())
        self.assertGreater(
            len(common_metrics), 0,
            "No common metrics found between baseline and rerun results"
        )

        # Check tolerance for each common metric
        failed_metrics = []
        for metric_name in common_metrics:
            baseline_val = baseline_metrics[metric_name]
            rerun_val = rerun_metrics[metric_name]

            relative_diff = self.calculate_relative_difference(baseline_val, rerun_val)

            if relative_diff > self.TOLERANCE_THRESHOLD:
                failed_metrics.append({
                    'metric': metric_name,
                    'baseline': baseline_val,
                    'rerun': rerun_val,
                    'relative_diff': relative_diff
                })

        # Assert all metrics pass tolerance check
        self.assertEqual(
            len(failed_metrics), 0,
            f"Numerical tolerance check failed for {len(failed_metrics)} metrics:\n" +
            "\n".join([
                f"  {m['metric']}: baseline={m['baseline']:.6f}, "
                f"rerun={m['rerun']:.6f}, diff={m['relative_diff']:.4f} "
                f"({m['relative_diff']*100:.2f}%)"
                for m in failed_metrics
            ])
        )

    def test_all_baseline_metrics_present(self):
        """Verify all baseline metrics are present in rerun results."""
        baseline_data = self.load_baseline_results()
        rerun_data = self.load_results_csv()

        baseline_metrics = self.extract_numeric_metrics(baseline_data)
        rerun_metrics = self.extract_numeric_metrics(rerun_data)

        missing_metrics = set(baseline_metrics.keys()) - set(rerun_metrics.keys())
        self.assertEqual(
            len(missing_metrics), 0,
            f"Missing metrics in rerun results: {missing_metrics}"
        )

if __name__ == '__main__':
    unittest.main()