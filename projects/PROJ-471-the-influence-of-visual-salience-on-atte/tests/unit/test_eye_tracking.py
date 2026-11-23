"""
Unit tests for code/processing/eye_tracking.py
Tests parsing of mock fixation files and metric calculation.
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from processing.eye_tracking import (
    EyeTrackingMetrics,
    parse_raw_eye_tracking_file,
    filter_face_roi,
    calculate_metrics,
    process_eye_tracking_data
)

class MockFixationData:
    """Helper to generate mock fixation data for testing."""
    
    @staticmethod
    def generate_mock_csv(filepath: Path, include_face_roi: bool = True) -> None:
        """
        Generate a mock CSV fixation file.
        
        Args:
            filepath: Path to write the CSV
            include_face_roi: If True, include rows with 'Face' ROI
        """
        header = ["trial_id", "fixation_id", "x", "y", "duration", "roi_label"]
        rows = [
            ["T001", "F001", "100", "200", "150", "Face"],
            ["T001", "F002", "110", "210", "200", "Face"],
            ["T001", "F003", "500", "500", "100", "Background"],
            ["T002", "F004", "120", "220", "300", "Face"],
            ["T002", "F005", "600", "600", "50", "Background"],
        ]
        
        if not include_face_roi:
            # Remove Face rows
            rows = [r for r in rows if r[5] != "Face"]

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

    @staticmethod
    def generate_mock_json(filepath: Path) -> None:
        """Generate a mock JSON fixation file."""
        data = [
            {
                "trial_id": "T003",
                "fixations": [
                    {"id": "F006", "x": 150, "y": 250, "duration": 180, "roi": "Face"},
                    {"id": "F007", "x": 550, "y": 550, "duration": 120, "roi": "Background"}
                ]
            }
        ]
        with open(filepath, 'w') as f:
            json.dump(data, f)

class TestEyeTracking(unittest.TestCase):
    """Unit tests for eye tracking parsing and metrics."""

    def setUp(self):
        """Set up temporary directory for test files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_parse_csv_file(self):
        """Test parsing a standard CSV fixation file."""
        csv_file = self.temp_path / "fixations.csv"
        MockFixationData.generate_mock_csv(csv_file)
        
        result = parse_raw_eye_tracking_file(csv_file)
        
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        # Check first row structure
        first_row = result[0]
        self.assertIn("trial_id", first_row)
        self.assertIn("x", first_row)
        self.assertIn("y", first_row)
        self.assertIn("duration", first_row)
        self.assertIn("roi_label", first_row)
        self.assertEqual(first_row["trial_id"], "T001")

    def test_parse_json_file(self):
        """Test parsing a JSON fixation file."""
        json_file = self.temp_path / "fixations.json"
        MockFixationData.generate_mock_json(json_file)
        
        result = parse_raw_eye_tracking_file(json_file)
        
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        # Check structure after flattening
        first_row = result[0]
        self.assertEqual(first_row["trial_id"], "T003")
        self.assertEqual(first_row["roi_label"], "Face")

    def test_parse_invalid_file(self):
        """Test parsing a non-existent file raises error."""
        invalid_file = self.temp_path / "nonexistent.csv"
        
        with self.assertRaises(FileNotFoundError):
            parse_raw_eye_tracking_file(invalid_file)

    def test_filter_face_roi(self):
        """Test filtering fixations for 'Face' ROI."""
        csv_file = self.temp_path / "fixations.csv"
        MockFixationData.generate_mock_csv(csv_file)
        
        all_data = parse_raw_eye_tracking_file(csv_file)
        face_data = filter_face_roi(all_data)
        
        self.assertIsInstance(face_data, list)
        # All rows should have 'Face' label
        for row in face_data:
            self.assertEqual(row["roi_label"], "Face")
        
        # Check we have fewer rows than original (some were Background)
        self.assertLess(len(face_data), len(all_data))

    def test_filter_no_face_roi(self):
        """Test filtering when no Face ROI exists."""
        csv_file = self.temp_path / "no_face.csv"
        MockFixationData.generate_mock_csv(csv_file, include_face_roi=False)
        
        all_data = parse_raw_eye_tracking_file(csv_file)
        face_data = filter_face_roi(all_data)
        
        self.assertEqual(len(face_data), 0)

    def test_calculate_metrics(self):
        """Test calculation of eye tracking metrics."""
        csv_file = self.temp_path / "fixations.csv"
        MockFixationData.generate_mock_csv(csv_file)
        
        all_data = parse_raw_eye_tracking_file(csv_file)
        face_data = filter_face_roi(all_data)
        
        # Group by trial_id
        trials = {}
        for row in face_data:
            tid = row["trial_id"]
            if tid not in trials:
                trials[tid] = []
            trials[tid].append(row)
        
        # Calculate metrics for first trial
        trial_fixations = trials["T001"]
        metrics = calculate_metrics(trial_fixations, total_trials=2)
        
        self.assertIsInstance(metrics, EyeTrackingMetrics)
        self.assertEqual(metrics.trial_id, "T001")
        self.assertGreater(metrics.dwell_time, 0)
        self.assertGreater(metrics.fixation_count, 0)
        # First fixation probability should be 1.0 if first fix is in face
        # (based on our mock data, first fix is in Face)
        self.assertGreaterEqual(metrics.first_fixation_prob, 0.0)
        self.assertLessEqual(metrics.first_fixation_prob, 1.0)

    def test_process_eye_tracking_data(self):
        """Test full pipeline processing of eye tracking data."""
        csv_file = self.temp_path / "fixations.csv"
        MockFixationData.generate_mock_csv(csv_file)
        
        output_file = self.temp_path / "metrics.csv"
        
        # Run full processing
        process_eye_tracking_data(csv_file, output_file)
        
        # Verify output file exists
        self.assertTrue(output_file.exists())
        
        # Verify content
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertGreater(len(rows), 0)
        # Check required columns
        required_cols = ["trial_id", "fixation_count", "dwell_time", "first_fixation_prob", "first_fixation_latency"]
        for col in required_cols:
            self.assertIn(col, rows[0].keys())

    def test_process_empty_face_roi(self):
        """Test processing when no Face ROI exists."""
        csv_file = self.temp_path / "no_face.csv"
        MockFixationData.generate_mock_csv(csv_file, include_face_roi=False)
        
        output_file = self.temp_path / "metrics_empty.csv"
        
        # Should handle gracefully (create file with 0 rows or skip)
        process_eye_tracking_data(csv_file, output_file)
        
        self.assertTrue(output_file.exists())

if __name__ == "__main__":
    unittest.main()