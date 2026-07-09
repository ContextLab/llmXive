"""
Unit tests for the literature review module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase

# Ensure code/ is in path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from literature_review import extract_feature_importance, aggregate_importance_vectors, construct_literature_vector, REVIEW_PAPERS

class TestLiteratureReview(TestCase):
    
    def test_extract_feature_importance_ranking(self):
        """Test that extraction assigns correct 1/rank scores."""
        paper = {
            "title": "Test Paper",
            "doi": "10.1000/test",
            "features": ["A", "B", "C"]
        }
        result = extract_feature_importance(paper)
        
        # Rank 1 (A) -> 1.0
        self.assertEqual(result["A"], 1.0)
        # Rank 2 (B) -> 0.5
        self.assertEqual(result["B"], 0.5)
        # Rank 3 (C) -> 0.333...
        self.assertAlmostEqual(result["C"], 1.0/3.0)
    
    def test_aggregate_importance_vectors(self):
        """Test aggregation logic and normalization."""
        # Two papers with overlapping features
        papers = [
            {"title": "P1", "doi": "1", "features": ["Fe", "Cr"]},
            {"title": "P2", "doi": "2", "features": ["Cr", "Ni"]}
        ]
        
        result = aggregate_importance_vectors(papers)
        
        # Check that all features are present
        self.assertIn("Fe", result)
        self.assertIn("Cr", result)
        self.assertIn("Ni", result)
        
        # Check normalization (max value should be 1.0)
        max_val = max(result.values())
        self.assertAlmostEqual(max_val, 1.0)
        
        # Check sorting (descending)
        values = list(result.values())
        self.assertEqual(values, sorted(values, reverse=True))
    
    def test_construct_literature_vector_writes_file(self):
        """Test that the full pipeline writes a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_vector.json"
            
            result = construct_literature_vector(output_path)
            
            # Check file exists
            self.assertTrue(output_path.exists())
            
            # Check JSON content
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            self.assertEqual(data["source"], "Literature Review")
            self.assertEqual(data["papers_count"], 5)
            self.assertIn("vector", data)
            self.assertTrue(data["normalized"])
            
            # Verify the vector has the expected keys from REVIEW_PAPERS
            expected_features = set()
            for p in REVIEW_PAPERS:
                expected_features.update(p["features"])
            
            self.assertEqual(set(data["vector"].keys()), expected_features)

if __name__ == "__main__":
    import unittest
    unittest.main()