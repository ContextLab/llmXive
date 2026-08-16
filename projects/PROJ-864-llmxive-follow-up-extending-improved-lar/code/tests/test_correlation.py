"""
Integration tests for correlation calculation between generalization gap and HumanEval.

Verifies that the correlation analysis correctly computes metrics and validates thresholds.
This test ensures that the pipeline correctly loads training logs, maps seeds to HumanEval
scores, computes gap slopes, and calculates the Pearson correlation coefficient.
"""
import json
import sys
import unittest
from pathlib import Path
from typing import Dict, List, Any
import tempfile
import csv

# Ensure imports work
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

import numpy as np
from analysis.compute_metrics import (
    compute_gap_correlation,
    load_training_logs,
    load_human_eval_results,
    compute_gap_slope,
    map_seed_to_human_eval_score
)


class TestCorrelation(unittest.TestCase):
    """Integration test for HumanEval correlation calculation."""

    def setUp(self):
        """Set up temporary files for integration testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create sample training logs CSV
        self.logs_path = self.temp_path / "training_logs.csv"
        self._create_sample_logs()
        
        # Create sample HumanEval results JSON
        self.human_eval_path = self.temp_path / "human_eval_results.json"
        self._create_sample_human_eval()

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def _create_sample_logs(self):
        """Create realistic sample training logs."""
        # Simulate 5 seeds for AR and Diffusion models over 10 epochs
        # with increasing generalization gap (val_loss - train_loss)
        with open(self.logs_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["epoch", "train_loss", "val_loss", "seed_id", "model_type"])
            
            epochs = 10
            seeds = 5
            models = ["ar", "diffusion"]
            
            for model in models:
                for seed in range(seeds):
                    for epoch in range(1, epochs + 1):
                        # Simulate training loss decreasing
                        train_loss = 2.0 - (epoch * 0.15) + (seed * 0.02)
                        # Simulate validation loss decreasing slower (creating gap)
                        val_loss = 2.1 - (epoch * 0.10) + (seed * 0.03) + (epoch * 0.01 * seed)
                        writer.writerow([epoch, f"{train_loss:.4f}", f"{val_loss:.4f}", seed, model])

    def _create_sample_human_eval(self):
        """Create sample HumanEval results matching the seeds."""
        # Simulate HumanEval pass@1 scores for 5 seeds per model
        # AR model: generally higher scores
        # Diffusion: generally lower scores (to create negative correlation with gap)
        human_eval_data = {
            "ar": [0.82, 0.79, 0.75, 0.71, 0.68],  # Seeds 0-4
            "diffusion": [0.76, 0.72, 0.68, 0.64, 0.60]  # Seeds 0-4
        }
        with open(self.human_eval_path, "w") as f:
            json.dump(human_eval_data, f, indent=2)

    def test_load_training_logs_integration(self):
        """Test loading training logs from CSV file."""
        logs = load_training_logs(self.logs_path)
        
        self.assertIsInstance(logs, dict)
        self.assertIn("ar", logs)
        self.assertIn("diffusion", logs)
        
        # Check AR model data
        ar_data = logs["ar"]
        self.assertIsInstance(ar_data, list)
        self.assertEqual(len(ar_data), 5)  # 5 seeds
        
        # Check each seed has 10 epochs
        for seed_data in ar_data:
            self.assertIn("seed_id", seed_data)
            self.assertIn("epochs", seed_data)
            self.assertEqual(len(seed_data["epochs"]), 10)

    def test_load_human_eval_results_integration(self):
        """Test loading HumanEval results from JSON file."""
        results = load_human_eval_results(self.human_eval_path)
        
        self.assertIsInstance(results, dict)
        self.assertIn("ar", results)
        self.assertIn("diffusion", results)
        
        self.assertEqual(len(results["ar"]), 5)
        self.assertEqual(len(results["diffusion"]), 5)

    def test_map_seed_to_human_eval_score(self):
        """Test mapping seed IDs to HumanEval scores."""
        human_eval = load_human_eval_results(self.human_eval_path)
        
        # Test AR model mapping
        ar_scores = [map_seed_to_human_eval_score(human_eval, "ar", seed) for seed in range(5)]
        self.assertEqual(ar_scores, human_eval["ar"])
        
        # Test Diffusion model mapping
        diff_scores = [map_seed_to_human_eval_score(human_eval, "diffusion", seed) for seed in range(5)]
        self.assertEqual(diff_scores, human_eval["diffusion"])

    def test_compute_gap_slope(self):
        """Test computing generalization gap slope from training logs."""
        logs = load_training_logs(self.logs_path)
        
        # Test AR model, seed 0
        gap_slope = compute_gap_slope(logs["ar"][0]["epochs"])
        
        # Gap should be positive (val_loss > train_loss) and increasing
        self.assertGreater(gap_slope, 0, "Gap slope should be positive for increasing gap")
        
        # Verify slope calculation manually for seed 0
        epochs = logs["ar"][0]["epochs"]
        gaps = [e["val_loss"] - e["train_loss"] for e in epochs]
        expected_slope = np.polyfit(range(len(gaps)), gaps, 1)[0]
        self.assertAlmostEqual(gap_slope, expected_slope, places=6)

    def test_compute_gap_correlation_integration(self):
        """Integration test for full correlation calculation pipeline."""
        # This is the main integration test that verifies the complete pipeline
        correlation, ar_correlation, diff_correlation, metadata = compute_gap_correlation(
            self.logs_path,
            self.human_eval_path
        )
        
        # Verify correlation is computed
        self.assertIsInstance(correlation, float)
        self.assertTrue(np.isfinite(correlation))
        
        # Verify we have per-model correlations
        self.assertIsInstance(ar_correlation, float)
        self.assertIsInstance(diff_correlation, float)
        
        # Verify metadata is populated
        self.assertIn("num_seeds", metadata)
        self.assertIn("threshold", metadata)
        self.assertIn("threshold_met", metadata)
        
        # With our synthetic data (gap increasing, scores decreasing),
        # we expect a negative correlation
        self.assertLess(correlation, 0, "Expected negative correlation with synthetic data")
        
        # Verify threshold check (|r| >= 0.5)
        # Our synthetic data should produce a strong correlation
        self.assertTrue(metadata["threshold_met"], "Expected |r| >= 0.5 with synthetic data")

    def test_correlation_threshold_validation(self):
        """Test that threshold validation works correctly."""
        correlation, _, _, metadata = compute_gap_correlation(
            self.logs_path,
            self.human_eval_path
        )
        
        # Verify threshold logic
        expected_met = abs(correlation) >= 0.5
        self.assertEqual(metadata["threshold_met"], expected_met)

    def test_correlation_with_incomplete_data(self):
        """Test handling of incomplete seed data."""
        # Create HumanEval results missing one seed
        incomplete_human_eval = self.temp_path / "human_eval_incomplete.json"
        with open(incomplete_human_eval, "w") as f:
            json.dump({
                "ar": [0.82, 0.79, 0.75],  # Only 3 seeds
                "diffusion": [0.76, 0.72, 0.68]  # Only 3 seeds
            }, f)
        
        # Should still compute correlation with available data
        correlation, _, _, _ = compute_gap_correlation(
            self.logs_path,
            incomplete_human_eval
        )
        
        self.assertIsInstance(correlation, float)
        self.assertTrue(np.isfinite(correlation))


def run_tests():
    """Run all tests in this module."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCorrelation)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)