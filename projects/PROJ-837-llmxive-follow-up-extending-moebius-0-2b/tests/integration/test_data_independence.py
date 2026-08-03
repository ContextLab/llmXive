"""
Integration test for User Story 1: Data Independence.

This test verifies that the data generation pipeline (specifically score annotation)
is strictly decoupled from the model inference or mask complexity metrics in CI mode.

Requirement: FR-007 (Avoid Circularity)
- In CI Mode, scores must be generated using random independent values (uniform 1-5).
- Scores must NOT depend on gradient_variance or texture_entropy.
"""
import os
import sys
import csv
import math
import random
from pathlib import Path
from typing import List, Dict, Any
import unittest
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config import set_mode, is_ci_mode
from data.annotator import generate_ci_scores, save_scores, log_validation

class TestDataIndependence(unittest.TestCase):
    
    def setUp(self):
        """Setup temporary directory for test artifacts."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_independence_"))
        self.annotations_dir = self.test_dir / "annotations"
        self.annotations_dir.mkdir()
        
        # Force CI Mode for this test
        set_mode("ci")
        assert is_ci_mode(), "Test requires CI Mode to be active"

    def tearDown(self):
        """Clean up temporary directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_scores_are_random_and_independent_of_metrics(self):
        """
        Test that generated scores are random and show no correlation 
        with synthetic mask metrics (gradient_variance, texture_entropy).
        """
        # Simulate a batch of images with varying metrics
        # In a real scenario, these would come from the mask_generator
        num_samples = 100
        mock_metrics = []
        
        for i in range(num_samples):
            # Generate random mock metrics
            gradient_var = random.uniform(0.1, 10.0)
            texture_ent = random.uniform(0.1, 5.0)
            mock_metrics.append({
                "image_id": f"img_{i:04d}",
                "gradient_variance": gradient_var,
                "texture_entropy": texture_ent
            })

        # Generate CI scores using the actual implementation
        # This should produce random scores independent of the metrics above
        scores = generate_ci_scores(mock_metrics)

        # Save scores to a temporary CSV
        output_csv = self.annotations_dir / "decoupled_scores.csv"
        save_scores(scores, output_csv)

        # Load the saved scores back to verify
        with open(output_csv, 'r', newline='') as f:
            reader = csv.DictReader(f)
            saved_scores = list(reader)

        self.assertEqual(len(saved_scores), num_samples, "Score count mismatch")

        # Perform statistical check for independence
        # Extract metric values and scores
        grad_vars = [float(m["gradient_variance"]) for m in mock_metrics]
        scores_vals = [int(s["score"]) for s in saved_scores]

        # Calculate Pearson Correlation Coefficient manually
        # r = cov(X,Y) / (std(X) * std(Y))
        
        n = len(grad_vars)
        mean_x = sum(grad_vars) / n
        mean_y = sum(scores_vals) / n

        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(grad_vars, scores_vals))
        
        sum_sq_x = sum((x - mean_x) ** 2 for x in grad_vars)
        sum_sq_y = sum((y - mean_y) ** 2 for y in scores_vals)
        
        denominator = math.sqrt(sum_sq_x * sum_sq_y)

        if denominator == 0:
            correlation = 0.0
        else:
            correlation = numerator / denominator

        # In a truly random independent generation, correlation should be close to 0.
        # We allow a small threshold for random chance, but it should be very low.
        # A correlation > 0.3 would be suspicious for random uniform data.
        self.assertLess(abs(correlation), 0.3, 
            f"Scores show suspicious correlation ({correlation:.4f}) with gradient_variance. "
            "Scores must be independent of mask metrics in CI mode."
        )

        # Also verify that scores are within the expected range [1, 5]
        for s in saved_scores:
            score_val = int(s["score"])
            self.assertGreaterEqual(score_val, 1, f"Score {score_val} is below 1")
            self.assertLessEqual(score_val, 5, f"Score {score_val} is above 5")
            self.assertEqual(s["mode"], "ci", f"Mode is not 'ci': {s['mode']}")

    def test_validation_log_exists(self):
        """
        Verify that the validation log is created and contains the required CI Mode message.
        """
        # Run the logging function
        log_path = self.test_dir / "validation_log.txt"
        log_validation("ci_test_run", str(log_path), "ci")
        
        self.assertTrue(log_path.exists(), "Validation log file was not created")
        
        with open(log_path, 'r') as f:
            content = f.read()
        
        self.assertIn("CI Mode: Single-Rater Simulation", content,
            "Validation log must explicitly state 'CI Mode: Single-Rater Simulation'")

if __name__ == "__main__":
    unittest.main()