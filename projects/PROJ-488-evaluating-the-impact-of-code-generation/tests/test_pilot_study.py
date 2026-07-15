"""
Tests for pilot_study.py
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.pilot_study import (
    compute_pearson_r, 
    generate_markdown_report,
    TITLE_OVERLAP_THRESHOLD,
    PEARSON_R_THRESHOLD
)

class TestPilotStudy(unittest.TestCase):

    def test_compute_pearson_r_valid_data(self):
        """Test Pearson r computation with valid data."""
        effort = [1.0, 2.0, 3.0, 4.0, 5.0]
        metrics = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        r, p = compute_pearson_r(effort, metrics, MagicMock())
        
        self.assertIsNotNone(r)
        self.assertEqual(r, 1.0) # Perfect correlation
        self.assertIsNotNone(p)

    def test_compute_pearson_r_insufficient_data(self):
        """Test Pearson r with insufficient data."""
        effort = [1.0]
        metrics = [1.0]
        
        r, p = compute_pearson_r(effort, metrics, MagicMock())
        
        self.assertIsNone(r)
        self.assertIsNone(p)

    def test_generate_markdown_report_method_a_passed(self):
        """Test report generation for Method A passed."""
        result = {
            "method": "A",
            "status": "passed",
            "reason": "Pearson r (0.6) >= threshold (0.5)",
            "details": {
                "dataset": "test_dataset",
                "samples": 100,
                "pearson_r": 0.6,
                "p_value": 0.01,
                "threshold_met": True
            }
        }
        
        report = generate_markdown_report(result, MagicMock())
        
        self.assertIn("Method A", report)
        self.assertIn("PASSED", report)
        self.assertIn("0.6", report)

    def test_generate_markdown_report_method_b_passed(self):
        """Test report generation for Method B passed."""
        result = {
            "method": "B",
            "status": "passed",
            "reason": "Title overlap (0.8) >= threshold (0.7)",
            "details": {
                "citation": "Test Citation",
                "topic_keywords": ["code", "review"],
                "overlap_score": 0.8,
                "threshold_met": True
            }
        }
        
        report = generate_markdown_report(result, MagicMock())
        
        self.assertIn("Method B", report)
        self.assertIn("PASSED", report)
        self.assertIn("0.8", report)

    def test_threshold_constants(self):
        """Test that thresholds are defined correctly."""
        self.assertEqual(PEARSON_R_THRESHOLD, 0.5)
        self.assertEqual(TITLE_OVERLAP_THRESHOLD, 0.7)

if __name__ == '__main__':
    unittest.main()
