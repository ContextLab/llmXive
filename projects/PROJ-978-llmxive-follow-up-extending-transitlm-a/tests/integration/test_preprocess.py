"""
Integration tests for data/preprocess.py
Tests the complete preprocessing pipeline on real data.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data.preprocess import (
    filter_cities,
    build_vocabulary,
    apply_vocabulary_filter,
    stratify_routes,
    compute_route_metrics,
    validate_output,
    TARGET_CITIES,
    TOP_N_VOCAB,
    UNKNOWN_TOKEN,
    SHORT_THRESHOLD,
    MEDIUM_THRESHOLD
)


class TestPreprocessIntegration(TestCase):
    """Integration tests for preprocessing functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_routes = [
            {
                "city": "Beijing",
                "stations": ["Beijing West", "Beijing Station", "Dongdan", "Wangfujing"],
                "route_id": "BJ001"
            },
            {
                "city": "Shanghai",
                "stations": ["Shanghai Hongqiao", "Jing'an Temple", "People's Square"],
                "route_id": "SH001"
            },
            {
                "city": "Guangzhou",
                "stations": ["Guangzhou East", "Tianhe", "Zhujiang New Town"],
                "route_id": "GZ001"
            },
            {
                "city": "Shenzhen",
                "stations": ["Shenzhen North", "Futian", "Huaqiangbei"],
                "route_id": "SZ001"
            },
            {
                "city": "Chengdu",  # Should be filtered out
                "stations": ["Chengdu East", "Chunxi Road"],
                "route_id": "CD001"
            },
            # Route for testing stratification
            {
                "city": "Beijing",
                "stations": [f"Station{i}" for i in range(20)],
                "route_id": "BJ002"
            },
            {
                "city": "Shanghai",
                "stations": [f"Station{i}" for i in range(35)],
                "route_id": "SH002"
            }
        ]

    def test_filter_cities(self):
        """Test city filtering."""
        filtered = filter_cities(self.sample_routes, TARGET_CITIES)
        cities_in_result = {r["city"] for r in filtered}
        
        # Should only contain target cities
        self.assertTrue(cities_in_result.issubset(TARGET_CITIES))
        # Should exclude Chengdu
        self.assertNotIn("Chengdu", cities_in_result)
        # Should have 6 routes (4 single + 2 multi)
        self.assertEqual(len(filtered), 6)

    def test_build_vocabulary(self):
        """Test vocabulary building."""
        vocab = build_vocabulary(self.sample_routes, TOP_N_VOCAB)
        
        # Should include UNKNOWN token
        self.assertIn(UNKNOWN_TOKEN, vocab)
        
        # Should have at least as many tokens as unique stations + UNKNOWN
        unique_stations = set()
        for route in self.sample_routes:
            unique_stations.update(route.get("stations", []))
        
        self.assertGreaterEqual(len(vocab), len(unique_stations) + 1)

    def test_apply_vocabulary_filter(self):
        """Test vocabulary filtering."""
        vocab = build_vocabulary(self.sample_routes, TOP_N_VOCAB)
        filtered = apply_vocabulary_filter(self.sample_routes, vocab)
        
        # All stations should be replaced with integer tokens
        for route in filtered:
            stations = route.get("stations", [])
            for station in stations:
                self.assertIsInstance(station, int)
                self.assertIn(station, vocab.values())

    def test_stratify_routes(self):
        """Test route stratification."""
        # Create test routes with known lengths
        test_routes = [
            {"stations": ["A", "B", "C"], "city": "Beijing"},  # 3 (short)
            {"stations": ["A"] * 10, "city": "Beijing"},  # 10 (short)
            {"stations": ["A"] * 15, "city": "Beijing"},  # 15 (medium)
            {"stations": ["A"] * 25, "city": "Beijing"},  # 25 (medium)
            {"stations": ["A"] * 31, "city": "Beijing"},  # 31 (long)
            {"stations": ["A"] * 50, "city": "Beijing"},  # 50 (long)
        ]
        
        strata = stratify_routes(test_routes)
        
        self.assertEqual(len(strata["short"]), 2)
        self.assertEqual(len(strata["medium"]), 2)
        self.assertEqual(len(strata["long"]), 2)

    def test_compute_route_metrics(self):
        """Test route metrics computation."""
        routes = [
            {"stations": ["A", "B", "C"]},
            {"stations": ["A", "B", "C", "D", "E"]},
            {"stations": ["A"]}
        ]
        
        metrics = compute_route_metrics(routes)
        
        self.assertEqual(metrics["total_routes"], 3)
        self.assertEqual(metrics["avg_length"], 3.0)
        self.assertEqual(metrics["min_length"], 1)
        self.assertEqual(metrics["max_length"], 5)

    def test_full_pipeline_structure(self):
        """Test the structure of a full preprocessing run (without actual file I/O)."""
        # Filter cities
        filtered = filter_cities(self.sample_routes, TARGET_CITIES)
        
        # Build vocabulary
        vocab = build_vocabulary(filtered, TOP_N_VOCAB)
        
        # Apply vocabulary filter
        vocab_filtered = apply_vocabulary_filter(filtered, vocab)
        
        # Stratify
        strata = stratify_routes(vocab_filtered)
        
        # Verify structure
        self.assertIn("short", strata)
        self.assertIn("medium", strata)
        self.assertIn("long", strata)
        
        # All routes should have integer station tokens
        for category, routes in strata.items():
            for route in routes:
                self.assertIn("stations", route)
                self.assertIsInstance(route["stations"], list)
                if route["stations"]:
                    self.assertIsInstance(route["stations"][0], int)


def run_tests():
    """Run all tests."""
    import unittest
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPreprocessIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)