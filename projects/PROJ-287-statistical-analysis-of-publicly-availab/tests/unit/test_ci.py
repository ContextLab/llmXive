"""
Unit tests for bootstrapped confidence interval computation (T030).

Tests verify:
- Correct bootstrap sampling logic
- CI width constraint (≤ 0.2)
- Proper handling of edge cases
- Integration with divergence calculation
"""

import unittest
import tempfile
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.metrics.ci import (
    bootstrap_divergence,
    compute_all_window_pair_cis,
    load_topic_vectors_for_ci,
    DEFAULT_N_BOOTSTRAP,
    MAX_CI_WIDTH_THRESHOLD
)
from src.models.metrics.divergence import calculate_js_divergence


class TestBootstrapLogic(unittest.TestCase):
    """Test bootstrap sampling and CI computation logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_seed = 42
        np.random.seed(self.test_seed)
        
        # Create mock topic vectors: 10 topics, varying document counts
        self.topic_vectors = {
            "2000-2004": np.random.dirichlet(np.ones(10), size=500).T,  # (10, 500)
            "2005-2009": np.random.dirichlet(np.ones(10), size=600).T,  # (10, 600)
            "2010-2014": np.random.dirichlet(np.ones(10), size=550).T,  # (10, 550)
            "2015-2019": np.random.dirichlet(np.ones(10), size=700).T,  # (10, 700)
            "2020-2024": np.random.dirichlet(np.ones(10), size=650).T   # (10, 650)
        }
        
        self.window_pair = ("2000-2004", "2005-2009")
    
    def test_bootstrap_divergence_returns_valid_structure(self):
        """Test that bootstrap_divergence returns correct tuple structure."""
        point_est, samples, stats = bootstrap_divergence(
            self.topic_vectors,
            self.window_pair,
            n_bootstrap=50,  # Small number for speed
            sample_size=100,
            random_seed=self.test_seed
        )
        
        self.assertIsInstance(point_est, float)
        self.assertIsInstance(samples, np.ndarray)
        self.assertIsInstance(stats, dict)
        
        self.assertEqual(len(samples), 50)
        self.assertIn("point_estimate", stats)
        self.assertIn("ci_lower", stats)
        self.assertIn("ci_upper", stats)
        self.assertIn("ci_width", stats)
    
    def test_ci_bounds_are_ordered(self):
        """Test that CI lower bound is always less than upper bound."""
        point_est, samples, stats = bootstrap_divergence(
            self.topic_vectors,
            self.window_pair,
            n_bootstrap=100,
            sample_size=100,
            random_seed=self.test_seed
        )
        
        self.assertLessEqual(stats["ci_lower"], stats["ci_upper"])
        self.assertLessEqual(stats["ci_lower"], stats["point_estimate"])
        self.assertGreaterEqual(stats["ci_upper"], stats["point_estimate"])
    
    def test_ci_width_within_threshold(self):
        """Test that CI width is within the required threshold (≤ 0.2)."""
        point_est, samples, stats = bootstrap_divergence(
            self.topic_vectors,
            self.window_pair,
            n_bootstrap=100,
            sample_size=100,
            random_seed=self.test_seed
        )
        
        self.assertLessEqual(
            stats["ci_width"],
            MAX_CI_WIDTH_THRESHOLD,
            f"CI width {stats['ci_width']:.4f} exceeds threshold {MAX_CI_WIDTH_THRESHOLD}"
        )
    
    def test_bootstrap_samples_have_reasonable_variance(self):
        """Test that bootstrap samples show reasonable variance (not all identical)."""
        point_est, samples, stats = bootstrap_divergence(
            self.topic_vectors,
            self.window_pair,
            n_bootstrap=100,
            sample_size=100,
            random_seed=self.test_seed
        )
        
        # With random sampling, variance should be > 0
        self.assertGreater(np.std(samples), 0)
    
    def test_deterministic_with_fixed_seed(self):
        """Test that results are deterministic with fixed random seed."""
        seed = 12345
        
        _, _, stats1 = bootstrap_divergence(
            self.topic_vectors,
            self.window_pair,
            n_bootstrap=50,
            sample_size=100,
            random_seed=seed
        )
        
        _, _, stats2 = bootstrap_divergence(
            self.topic_vectors,
            self.window_pair,
            n_bootstrap=50,
            sample_size=100,
            random_seed=seed
        )
        
        self.assertAlmostEqual(
            stats1["point_estimate"],
            stats2["point_estimate"],
            places=10
        )
        self.assertAlmostEqual(
            stats1["ci_lower"],
            stats2["ci_lower"],
            places=10
        )
        self.assertAlmostEqual(
            stats1["ci_upper"],
            stats2["ci_upper"],
            places=10
        )
    
    def test_invalid_window_pair_raises_error(self):
        """Test that non-existent window pairs raise ValueError."""
        with self.assertRaises(ValueError):
            bootstrap_divergence(
                self.topic_vectors,
                ("nonexistent", "2005-2009"),
                n_bootstrap=10,
                sample_size=10
            )
    
    def test_insufficient_documents_raises_error(self):
        """Test that windows with too few documents raise appropriate error."""
        # Create vectors with only 2 documents
        small_vectors = {
            "small1": np.random.dirichlet(np.ones(10), size=2).T,
            "small2": np.random.dirichlet(np.ones(10), size=2).T
        }
        
        # With sample_size=50, this should fail
        with self.assertRaises(ValueError):
            bootstrap_divergence(
                small_vectors,
                ("small1", "small2"),
                n_bootstrap=10,
                sample_size=50
            )

class TestCIFileIO(unittest.TestCase):
    """Test file I/O operations for CI computation."""
    
    def setUp(self):
        """Set up temporary directory and test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.topic_vectors_path = os.path.join(self.temp_dir, "topic_vectors.json")
        self.output_path = os.path.join(self.temp_dir, "ci_results.json")
        
        # Create mock topic vectors
        topic_vectors = {
            "2000-2004": np.random.dirichlet(np.ones(10), size=200).T.tolist(),
            "2005-2009": np.random.dirichlet(np.ones(10), size=200).T.tolist(),
            "2010-2014": np.random.dirichlet(np.ones(10), size=200).T.tolist()
        }
        
        with open(self.topic_vectors_path, 'w') as f:
            json.dump(topic_vectors, f)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_topic_vectors_for_ci(self):
        """Test loading topic vectors from JSON file."""
        vectors = load_topic_vectors_for_ci(self.topic_vectors_path)
        
        self.assertIn("2000-2004", vectors)
        self.assertIn("2005-2009", vectors)
        self.assertIn("2010-2014", vectors)
        
        # Check shapes
        for name, vec in vectors.items():
            self.assertIsInstance(vec, np.ndarray)
            self.assertEqual(vec.shape[0], 10)  # 10 topics
    
    def test_compute_all_window_pair_cis_creates_output(self):
        """Test that compute_all_window_pair_cis creates output file."""
        results = compute_all_window_pair_cis(
            self.topic_vectors_path,
            self.output_path,
            n_bootstrap=20,
            sample_size=50,
            random_seed=42
        )
        
        self.assertTrue(os.path.exists(self.output_path))
        
        # Verify structure
        self.assertIn("metadata", results)
        self.assertIn("window_pairs", results)
        self.assertIn("summary", results)
        
        # Check expected pairs
        expected_pairs = [
            "2000-2004_vs_2005-2009",
            "2005-2009_vs_2010-2014"
        ]
        
        for pair in expected_pairs:
            self.assertIn(pair, results["window_pairs"])
    
    def test_output_file_is_valid_json(self):
        """Test that output file is valid JSON."""
        compute_all_window_pair_cis(
            self.topic_vectors_path,
            self.output_path,
            n_bootstrap=20,
            sample_size=50,
            random_seed=42
        )
        
        with open(self.output_path, 'r') as f:
            data = json.load(f)
        
        self.assertIsInstance(data, dict)
    
    def test_ci_results_contain_required_fields(self):
        """Test that CI results contain all required fields."""
        results = compute_all_window_pair_cis(
            self.topic_vectors_path,
            self.output_path,
            n_bootstrap=20,
            sample_size=50,
            random_seed=42
        )
        
        for pair_key, pair_data in results["window_pairs"].items():
            if "error" not in pair_data:
                required_fields = [
                    "point_estimate", "ci_lower", "ci_upper", "ci_width",
                    "ci_width_within_threshold", "n_bootstrap"
                ]
                
                for field in required_fields:
                    self.assertIn(field, pair_data, f"Missing {field} in {pair_key}")

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""
    
    def test_single_document_per_window(self):
        """Test handling of windows with minimal documents."""
        vectors = {
            "w1": np.random.dirichlet(np.ones(10), size=10).T,
            "w2": np.random.dirichlet(np.ones(10), size=10).T
        }
        
        # Should work with sample_size=10
        point_est, samples, stats = bootstrap_divergence(
            vectors,
            ("w1", "w2"),
            n_bootstrap=10,
            sample_size=10,
            random_seed=42
        )
        
        self.assertIsInstance(stats["point_estimate"], float)
        self.assertTrue(stats["ci_width_within_threshold"])
    
    def test_identical_distributions(self):
        """Test handling of identical topic distributions (JS divergence = 0)."""
        # Create identical distributions
        base = np.random.dirichlet(np.ones(10), size=100).T
        vectors = {
            "w1": base,
            "w2": base.copy()
        }
        
        point_est, samples, stats = bootstrap_divergence(
            vectors,
            ("w1", "w2"),
            n_bootstrap=20,
            sample_size=50,
            random_seed=42
        )
        
        # JS divergence should be near zero
        self.assertLess(point_est, 0.01)
    
    def test_very_different_distributions(self):
        """Test handling of very different topic distributions."""
        # Create very different distributions
        v1 = np.array([0.9] + [0.011] * 9)  # Dominated by topic 0
        v1 = np.tile(v1, (100, 1)).T  # (10, 100)
        
        v2 = np.array([0.011] * 9 + [0.9])  # Dominated by topic 9
        v2 = np.tile(v2, (100, 1)).T  # (10, 100)
        
        vectors = {
            "w1": v1,
            "w2": v2
        }
        
        point_est, samples, stats = bootstrap_divergence(
            vectors,
            ("w1", "w2"),
            n_bootstrap=20,
            sample_size=50,
            random_seed=42
        )
        
        # JS divergence should be high (close to 1 for base=2)
        self.assertGreater(point_est, 0.5)

class TestIntegration(unittest.TestCase):
    """Integration tests for CI computation with divergence module."""
    
    def test_ci_point_estimate_matches_direct_divergence(self):
        """Test that CI point estimate matches direct JS divergence calculation."""
        vectors = {
            "w1": np.random.dirichlet(np.ones(10), size=200).T,
            "w2": np.random.dirichlet(np.ones(10), size=200).T
        }
        
        point_est, _, stats = bootstrap_divergence(
            vectors,
            ("w1", "w2"),
            n_bootstrap=10,
            sample_size=100,
            random_seed=42
        )
        
        # Calculate expected point estimate directly
        mean_v1 = np.mean(vectors["w1"], axis=1)
        mean_v2 = np.mean(vectors["w2"], axis=1)
        mean_v1 = mean_v1 / (np.sum(mean_v1) + 1e-10)
        mean_v2 = mean_v2 / (np.sum(mean_v2) + 1e-10)
        
        expected = calculate_js_divergence(mean_v1, mean_v2)
        
        self.assertAlmostEqual(point_est, expected, places=6)
    
    def test_full_pipeline_with_realistic_data(self):
        """Test full CI pipeline with realistic topic vector shapes."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create realistic topic vectors
            n_topics = 10
            n_docs_per_window = 300
            
            topic_vectors = {}
            windows = ["2000-2004", "2005-2009", "2010-2014", "2015-2019", "2020-2024"]
            
            for window in windows:
                # Simulate topic proportions (each document has distribution over topics)
                vectors = np.random.dirichlet(np.ones(n_topics), size=n_docs_per_window).T
                topic_vectors[window] = vectors.tolist()
            
            # Save to file
            input_path = os.path.join(temp_dir, "topic_vectors.json")
            with open(input_path, 'w') as f:
                json.dump(topic_vectors, f)
            
            output_path = os.path.join(temp_dir, "ci_results.json")
            
            # Run full CI computation
            results = compute_all_window_pair_cis(
                input_path,
                output_path,
                n_bootstrap=50,
                sample_size=100,
                random_seed=42
            )
            
            # Verify results
            self.assertEqual(len(results["window_pairs"]), 4)  # 4 consecutive pairs
            self.assertTrue(results["summary"]["all_within_threshold"])
            
            # Check that all pairs have valid CIs
            for pair_key, pair_data in results["window_pairs"].items():
                self.assertNotIn("error", pair_data)
                self.assertLessEqual(pair_data["ci_width"], MAX_CI_WIDTH_THRESHOLD)
        
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    unittest.main()