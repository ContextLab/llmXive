"""
Unit tests for log_extreme_cases module.
"""

import os
import json
import csv
import tempfile
from pathlib import Path
from unittest import TestCase

# Add code directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from compliance.log_extreme_cases import (
    load_compliance_data,
    is_extreme_case,
    identify_extreme_cases,
    write_extreme_cases_log,
    run_extreme_case_logging
)

class TestExtremeCaseLogging(TestCase):
    
    def setUp(self):
        """Create temporary directory structure for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)
        self.compliance_csv = self.data_dir / "compliance_scores.csv"
        self.output_json = self.data_dir / "extreme_cases.json"

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_compliance_csv(self, rows):
        """Helper to write test CSV data."""
        with open(self.compliance_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['participant_id', 'date', 'minutes_social_media', 'minutes_news', 'minutes_other', 'total_minutes'])
            writer.writeheader()
            writer.writerows(rows)

    def test_is_extreme_case_zero_usage_all_days(self):
        """Test detection of a participant with 0 minutes for all 7 days."""
        logs = [
            {'participant_id': 'P001', 'date': '2023-10-01', 'total_minutes': 0},
            {'participant_id': 'P001', 'date': '2023-10-02', 'total_minutes': 0},
            {'participant_id': 'P001', 'date': '2023-10-03', 'total_minutes': 0},
            {'participant_id': 'P001', 'date': '2023-10-04', 'total_minutes': 0},
            {'participant_id': 'P001', 'date': '2023-10-05', 'total_minutes': 0},
            {'participant_id': 'P001', 'date': '2023-10-06', 'total_minutes': 0},
            {'participant_id': 'P001', 'date': '2023-10-07', 'total_minutes': 0},
        ]
        self.assertTrue(is_extreme_case(logs, threshold=1.0))

    def test_is_extreme_case_below_threshold(self):
        """Test detection of a participant with low usage (0.5 mins) for all 7 days."""
        logs = [
            {'participant_id': 'P002', 'date': '2023-10-01', 'total_minutes': 0.5},
            {'participant_id': 'P002', 'date': '2023-10-02', 'total_minutes': 0.5},
            {'participant_id': 'P002', 'date': '2023-10-03', 'total_minutes': 0.5},
            {'participant_id': 'P002', 'date': '2023-10-04', 'total_minutes': 0.5},
            {'participant_id': 'P002', 'date': '2023-10-05', 'total_minutes': 0.5},
            {'participant_id': 'P002', 'date': '2023-10-06', 'total_minutes': 0.5},
            {'participant_id': 'P002', 'date': '2023-10-07', 'total_minutes': 0.5},
        ]
        self.assertTrue(is_extreme_case(logs, threshold=1.0))

    def test_is_extreme_case_one_day_above_threshold(self):
        """Test that a participant is NOT an extreme case if one day exceeds threshold."""
        logs = [
            {'participant_id': 'P003', 'date': '2023-10-01', 'total_minutes': 0},
            {'participant_id': 'P003', 'date': '2023-10-02', 'total_minutes': 0},
            {'participant_id': 'P003', 'date': '2023-10-03', 'total_minutes': 0},
            {'participant_id': 'P003', 'date': '2023-10-04', 'total_minutes': 0},
            {'participant_id': 'P003', 'date': '2023-10-05', 'total_minutes': 0},
            {'participant_id': 'P003', 'date': '2023-10-06', 'total_minutes': 0},
            {'participant_id': 'P003', 'date': '2023-10-07', 'total_minutes': 5}, # Exceeds threshold
        ]
        self.assertFalse(is_extreme_case(logs, threshold=1.0))

    def test_is_extreme_case_missing_days(self):
        """Test that a participant with only 6 days of logs is NOT an extreme case."""
        logs = [
            {'participant_id': 'P004', 'date': '2023-10-01', 'total_minutes': 0},
            {'participant_id': 'P004', 'date': '2023-10-02', 'total_minutes': 0},
            {'participant_id': 'P004', 'date': '2023-10-03', 'total_minutes': 0},
            {'participant_id': 'P004', 'date': '2023-10-04', 'total_minutes': 0},
            {'participant_id': 'P004', 'date': '2023-10-05', 'total_minutes': 0},
            {'participant_id': 'P004', 'date': '2023-10-06', 'total_minutes': 0},
            # Missing day 7
        ]
        self.assertFalse(is_extreme_case(logs, threshold=1.0))

    def test_identify_extreme_cases_pipeline(self):
        """Test the full identification pipeline with mixed data."""
        self._create_compliance_csv([
            # Extreme Case: P001 (0 mins all 7 days)
            {'participant_id': 'P001', 'date': '2023-10-01', 'total_minutes': 0},
            {'participant_id': 'P001', 'date': '2023-10-02', 'total_minutes': 0},
            {'participant_id': 'P001', 'date': '2023-10-03', 'total_minutes': 0},
            {'participant_id': 'P001', 'date': '2023-10-04', 'total_minutes': 0},
            {'participant_id': 'P001', 'date': '2023-10-05', 'total_minutes': 0},
            {'participant_id': 'P001', 'date': '2023-10-06', 'total_minutes': 0},
            {'participant_id': 'P001', 'date': '2023-10-07', 'total_minutes': 0},
            
            # Normal Case: P002 (has some usage)
            {'participant_id': 'P002', 'date': '2023-10-01', 'total_minutes': 30},
            {'participant_id': 'P002', 'date': '2023-10-02', 'total_minutes': 30},
            {'participant_id': 'P002', 'date': '2023-10-03', 'total_minutes': 30},
            {'participant_id': 'P002', 'date': '2023-10-04', 'total_minutes': 30},
            {'participant_id': 'P002', 'date': '2023-10-05', 'total_minutes': 30},
            {'participant_id': 'P002', 'date': '2023-10-06', 'total_minutes': 30},
            {'participant_id': 'P002', 'date': '2023-10-07', 'total_minutes': 30},

            # Edge Case: P003 (6 days zero, 1 day normal)
            {'participant_id': 'P003', 'date': '2023-10-01', 'total_minutes': 0},
            {'participant_id': 'P003', 'date': '2023-10-02', 'total_minutes': 0},
            {'participant_id': 'P003', 'date': '2023-10-03', 'total_minutes': 0},
            {'participant_id': 'P003', 'date': '2023-10-04', 'total_minutes': 0},
            {'participant_id': 'P003', 'date': '2023-10-05', 'total_minutes': 0},
            {'participant_id': 'P003', 'date': '2023-10-06', 'total_minutes': 0},
            {'participant_id': 'P003', 'date': '2023-10-07', 'total_minutes': 10},
        ])

        data = load_compliance_data(self.compliance_csv)
        extreme = identify_extreme_cases(data, threshold=1.0)

        self.assertEqual(len(extreme), 1)
        self.assertEqual(extreme[0]['participant_id'], 'P001')
        self.assertEqual(extreme[0]['total_weekly_minutes'], 0)

    def test_write_extreme_cases_log(self):
        """Test writing results to JSON."""
        extreme_cases = [
            {
                'participant_id': 'P001',
                'days_logged': 7,
                'total_weekly_minutes': 0,
                'avg_daily_minutes': 0.0,
                'threshold_minutes': 1.0,
                'classification': 'extreme_zero_usage',
                'reason': 'Reported <= 1.0 minutes of digital use for all 7 days.'
            }
        ]

        path = write_extreme_cases_log(extreme_cases, self.output_json)

        self.assertTrue(path.exists())
        with open(path, 'r') as f:
            content = json.load(f)
        
        self.assertEqual(content['metadata']['total_extreme_cases'], 1)
        self.assertEqual(len(content['cases']), 1)
        self.assertEqual(content['cases'][0]['participant_id'], 'P001')

    def test_run_extreme_case_logging_integration(self):
        """Integration test: create CSV, run pipeline, verify output."""
        self._create_compliance_csv([
            {'participant_id': 'P001', 'date': '2023-10-01', 'total_minutes': 0},
            {'participant_id': 'P001', 'date': '2023-10-02', 'total_minutes': 0},
            {'participant_id': 'P001', 'date': '2023-10-03', 'total_minutes': 0},
            {'participant_id': 'P001', 'date': '2023-10-04', 'total_minutes': 0},
            {'participant_id': 'P001', 'date': '2023-10-05', 'total_minutes': 0},
            {'participant_id': 'P001', 'date': '2023-10-06', 'total_minutes': 0},
            {'participant_id': 'P001', 'date': '2023-10-07', 'total_minutes': 0},
            {'participant_id': 'P002', 'date': '2023-10-01', 'total_minutes': 50},
            {'participant_id': 'P002', 'date': '2023-10-02', 'total_minutes': 50},
            {'participant_id': 'P002', 'date': '2023-10-03', 'total_minutes': 50},
            {'participant_id': 'P002', 'date': '2023-10-04', 'total_minutes': 50},
            {'participant_id': 'P002', 'date': '2023-10-05', 'total_minutes': 50},
            {'participant_id': 'P002', 'date': '2023-10-06', 'total_minutes': 50},
            {'participant_id': 'P002', 'date': '2023-10-07', 'total_minutes': 50},
        ])

        count, path = run_extreme_case_logging(self.compliance_csv, self.output_json, threshold=1.0)

        self.assertEqual(count, 1)
        self.assertTrue(path.exists())
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data['metadata']['total_extreme_cases'], 1)
        self.assertEqual(data['cases'][0]['participant_id'], 'P001')
        self.assertTrue(data['cases'][0]['reason'].startswith('Reported <= 1.0 minutes'))
        
        # Verify P002 is NOT in the list
        ids = [c['participant_id'] for c in data['cases']]
        self.assertNotIn('P002', ids)