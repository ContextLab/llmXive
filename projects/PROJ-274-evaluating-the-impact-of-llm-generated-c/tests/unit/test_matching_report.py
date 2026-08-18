import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from run_matching_report import calculate_baseline_stats, evaluate_matching_quality

class TestMatchingReportLogic(unittest.TestCase):

    def test_calculate_baseline_stats_empty(self):
        """Test baseline calculation with empty list."""
        baseline = calculate_baseline_stats([])
        self.assertEqual(baseline["loc_mean"], 0.0)
        self.assertEqual(baseline["cc_mean"], 0.0)

    def test_calculate_baseline_stats_valid(self):
        """Test baseline calculation with valid data."""
        data = [
            {"loc": 100, "cc": 10},
            {"loc": 200, "cc": 20}
        ]
        baseline = calculate_baseline_stats(data)
        self.assertEqual(baseline["loc_mean"], 150.0)
        self.assertEqual(baseline["cc_mean"], 15.0)

    def test_evaluate_matching_quality_within_tolerance(self):
        """Test evaluation when all repos are within 15% tolerance."""
        baseline = {"loc_mean": 100.0, "cc_mean": 10.0}
        data = [
            {"loc": 100, "cc": 10}, # 0% diff
            {"loc": 110, "cc": 11}, # 10% diff
            {"loc": 90, "cc": 9}    # 10% diff
        ]
        result = evaluate_matching_quality(data, baseline, tolerance_pct=15.0)
        
        self.assertEqual(result["total_repos_analyzed"], 3)
        self.assertEqual(result["repos_within_loc_tolerance_pct"], 100.0)
        self.assertEqual(result["repos_within_cc_tolerance_pct"], 100.0)
        self.assertIn("note", result) # Verify the ANCOVA note is present

    def test_evaluate_matching_quality_outside_tolerance(self):
        """Test evaluation when some repos are outside 15% tolerance."""
        baseline = {"loc_mean": 100.0, "cc_mean": 10.0}
        data = [
            {"loc": 100, "cc": 10},
            {"loc": 200, "cc": 20}  # 100% diff
        ]
        result = evaluate_matching_quality(data, baseline, tolerance_pct=15.0)
        
        self.assertEqual(result["total_repos_analyzed"], 2)
        # One is 0% diff, one is 100% diff. Only one within 15%.
        self.assertEqual(result["repos_within_loc_tolerance_pct"], 50.0)
        
        # Verify mean difference calculation
        # Mean diff = (0 + 100) / 2 = 50
        self.assertAlmostEqual(result["mean_loc_difference_pct"], 50.0, places=1)

    def test_output_structure(self):
        """Verify the output structure matches the task requirements."""
        baseline = {"loc_mean": 100.0, "cc_mean": 10.0}
        data = [{"loc": 100, "cc": 10}]
        result = evaluate_matching_quality(data, baseline)
        
        required_keys = [
            "baseline",
            "tolerance_threshold_pct",
            "total_repos_analyzed",
            "mean_loc_difference_pct",
            "mean_cc_difference_pct",
            "repos_within_loc_tolerance_pct",
            "repos_within_cc_tolerance_pct",
            "individual_differences",
            "note"
        ]
        for key in required_keys:
            self.assertIn(key, result, f"Missing key: {key}")

if __name__ == "__main__":
    unittest.main()