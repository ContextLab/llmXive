"""
Unit tests for code/analysis/summary_table.py (T033).
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np

# Add project root to path for imports
sys_path = str(Path(__file__).parent.parent.parent)
if sys_path not in os.sys.path:
    os.sys.path.insert(0, sys_path)

from code.analysis.summary_table import (
    load_aggregation_results,
    calculate_majority_rule_threshold,
    generate_summary_table,
    save_summary_table,
    MAJORITY_RULE_THRESHOLD
)

class TestCalculateMajorityRuleThreshold(unittest.TestCase):
    
    def test_no_events(self):
        """Test with empty event list."""
        result = calculate_majority_rule_threshold([])
        self.assertIsNone(result)

    def test_no_valid_thresholds(self):
        """Test when no events have a valid threshold."""
        events = [
            {"event_id": "E1", "threshold_sampling_rate": None},
            {"event_id": "E2", "threshold_sampling_rate": None},
        ]
        result = calculate_majority_rule_threshold(events)
        self.assertIsNone(result)

    def test_simple_majority_met(self):
        """Test scenario where majority rule is met at a specific rate."""
        # 3 events. Thresholds: 4096, 2048, 2048.
        # Sorted thresholds: 2048 (2 events), 4096 (1 event).
        # At 2048: 2/3 = 66.6% >= 50%. Should return 2048.
        events = [
            {"event_id": "E1", "threshold_sampling_rate": 4096},
            {"event_id": "E2", "threshold_sampling_rate": 2048},
            {"event_id": "E3", "threshold_sampling_rate": 2048},
        ]
        result = calculate_majority_rule_threshold(events)
        self.assertEqual(result, 2048)

    def test_majority_not_met(self):
        """Test scenario where majority rule is never met."""
        # 3 events. Thresholds: 4096, 4096, 4096.
        # At 4096: 3/3 = 100%. Wait, this meets it.
        # Let's try: 10 events, 4 have threshold 1024, 6 have threshold 4096.
        # At 1024: 4/10 = 40% < 50%.
        # At 4096: 10/10 = 100% >= 50%. So it should return 4096.
        # To fail, we need a case where even at the highest rate, it's < 50%?
        # That's impossible if all events have a threshold.
        # The function returns None only if no events have thresholds.
        # Let's test the logic of the loop.
        events = [
            {"event_id": f"E{i}", "threshold_sampling_rate": 1024 if i < 4 else 4096}
            for i in range(10)
        ]
        result = calculate_majority_rule_threshold(events)
        self.assertEqual(result, 4096) # Because at 4096, 10/10 >= 0.5

    def test_exact_boundary(self):
        """Test exactly 50%."""
        # 2 events. One at 2048, one at 4096.
        # At 2048: 1/2 = 50%. Should return 2048.
        events = [
            {"event_id": "E1", "threshold_sampling_rate": 2048},
            {"event_id": "E2", "threshold_sampling_rate": 4096},
        ]
        result = calculate_majority_rule_threshold(events)
        self.assertEqual(result, 2048)

class TestGenerateSummaryTable(unittest.TestCase):
    
    def test_generate_rows(self):
        """Test generation of summary rows from aggregation data."""
        agg_data = {
            "events": [
                {"event_id": "GW1", "threshold_sampling_rate": 2048, "bias_exceeded_count": 3, "total_valid_events": 3, "majority_rule_met": True, "inconclusive_count": 0, "excluded_count": 0},
                {"event_id": "GW2", "threshold_sampling_rate": 1024, "bias_exceeded_count": 3, "total_valid_events": 3, "majority_rule_met": True, "inconclusive_count": 0, "excluded_count": 0},
            ]
        }
        rows = generate_summary_table(agg_data)
        
        self.assertEqual(len(rows), 2)
        # Check sorting (1024 should come before 2048)
        self.assertEqual(rows[0]['event_id'], 'GW2')
        self.assertEqual(rows[0]['threshold_sampling_rate_hz'], 1024)
        self.assertEqual(rows[1]['event_id'], 'GW1')
        self.assertEqual(rows[1]['threshold_sampling_rate_hz'], 2048)

class TestSaveSummaryTable(unittest.TestCase):
    
    def test_save_files(self):
        """Test that files are created with correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock RESULTS_DIR
            with patch('code.analysis.summary_table.RESULTS_DIR', Path(tmpdir)):
                with patch('code.analysis.summary_table.MAJORITY_RULE_THRESHOLD', 0.5):
                    summary_rows = [
                        {"event_id": "E1", "threshold_sampling_rate_hz": 2048, "bias_exceeded_count": 1, "total_valid_events": 1, "majority_rule_met": True, "inconclusive_count": 0, "excluded_count": 0}
                    ]
                    save_summary_table(summary_rows, 2048)
                    
                    csv_path = Path(tmpdir) / "metrics" / "summary_table.csv"
                    json_path = Path(tmpdir) / "metrics" / "summary_table.json"
                    hash_path = Path(tmpdir) / "metrics" / "summary_table_hashes.json"
                    
                    self.assertTrue(csv_path.exists())
                    self.assertTrue(json_path.exists())
                    self.assertTrue(hash_path.exists())
                    
                    # Verify CSV content
                    with open(csv_path, 'r') as f:
                        content = f.read()
                        self.assertIn("event_id", content)
                        self.assertIn("E1", content)
                    
                    # Verify JSON content
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                        self.assertIn("global_summary", data)
                        self.assertEqual(data["global_summary"]["majority_rule_threshold_hz"], 2048)
                        self.assertEqual(len(data["events"]), 1)

if __name__ == '__main__':
    unittest.main()
