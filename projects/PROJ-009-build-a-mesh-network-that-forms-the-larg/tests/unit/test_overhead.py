"""
Unit tests for the Coordination Overhead Calculator.
"""

import csv
import os
import tempfile
from pathlib import Path
from unittest import TestCase

from code.analysis.overhead import CoordinationOverheadCalculator, OverheadMetrics


class TestCoordinationOverheadCalculator(TestCase):
    """Tests for the CoordinationOverheadCalculator class."""

    def setUp(self):
        """Set up temporary files for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_path = Path(self.temp_dir.name) / "execution_logs.csv"
        self.output_path = Path(self.temp_dir.name) / "overhead_results.csv"

        # Create a mock input CSV with known values
        # We will use the formula: handshake = total - (total * cpu/100)
        # Row 1: total=100, cpu=80 -> compute=80, handshake=20, ratio=0.2
        # Row 2: total=50, cpu=50 -> compute=25, handshake=25, ratio=0.5
        # Row 3: total=10, cpu=100 -> compute=10, handshake=0, ratio=0.0
        # Row 4: total=20, cpu=0 -> compute=0, handshake=20, ratio=1.0
        mock_data = [
            {
                "task_id": "task_001",
                "node_id": "node_A",
                "wall_clock_time": "100.0",
                "cpu_utilization_pct": "80.0",
                "granularity": "fine",
                "timestamp": "2023-01-01T00:00:00"
            },
            {
                "task_id": "task_002",
                "node_id": "node_B",
                "wall_clock_time": "50.0",
                "cpu_utilization_pct": "50.0",
                "granularity": "medium",
                "timestamp": "2023-01-01T00:01:00"
            },
            {
                "task_id": "task_003",
                "node_id": "node_C",
                "wall_clock_time": "10.0",
                "cpu_utilization_pct": "100.0",
                "granularity": "coarse",
                "timestamp": "2023-01-01T00:02:00"
            },
            {
                "task_id": "task_004",
                "node_id": "node_D",
                "wall_clock_time": "20.0",
                "cpu_utilization_pct": "0.0",
                "granularity": "fine",
                "timestamp": "2023-01-01T00:03:00"
            }
        ]

        with open(self.input_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=mock_data[0].keys())
            writer.writeheader()
            writer.writerows(mock_data)

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def test_process_calculates_correctly(self):
        """Test that the calculator processes rows and calculates overhead correctly."""
        calculator = CoordinationOverheadCalculator(str(self.input_path), str(self.output_path))
        results = calculator.process()

        self.assertEqual(len(results), 4)

        # Check Row 1: total=100, cpu=80 -> handshake=20, ratio=0.2
        r1 = results[0]
        self.assertAlmostEqual(r1.handshake_time, 20.0, places=5)
        self.assertAlmostEqual(r1.overhead_ratio, 0.2, places=5)
        self.assertAlmostEqual(r1.compute_time, 80.0, places=5)

        # Check Row 2: total=50, cpu=50 -> handshake=25, ratio=0.5
        r2 = results[1]
        self.assertAlmostEqual(r2.handshake_time, 25.0, places=5)
        self.assertAlmostEqual(r2.overhead_ratio, 0.5, places=5)

        # Check Row 3: total=10, cpu=100 -> handshake=0, ratio=0.0
        r3 = results[2]
        self.assertAlmostEqual(r3.handshake_time, 0.0, places=5)
        self.assertAlmostEqual(r3.overhead_ratio, 0.0, places=5)

        # Check Row 4: total=20, cpu=0 -> handshake=20, ratio=1.0
        r4 = results[3]
        self.assertAlmostEqual(r4.handshake_time, 20.0, places=5)
        self.assertAlmostEqual(r4.overhead_ratio, 1.0, places=5)

    def test_write_results_creates_file(self):
        """Test that write_results creates the output file with correct content."""
        calculator = CoordinationOverheadCalculator(str(self.input_path), str(self.output_path))
        calculator.process()
        calculator.write_results()

        self.assertTrue(self.output_path.exists())

        with open(self.output_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 4)
        # Verify headers
        expected_headers = ['task_id', 'node_id', 'total_time', 'handshake_time', 'compute_time', 'overhead_ratio', 'granularity', 'timestamp']
        self.assertEqual(list(rows[0].keys()), expected_headers)

    def test_empty_input_handles_gracefully(self):
        """Test behavior when input file is empty (only headers)."""
        empty_path = Path(self.temp_dir.name) / "empty_logs.csv"
        with open(empty_path, mode='w', newline='', encoding='utf-8') as f:
            f.write("task_id,node_id,wall_clock_time,cpu_utilization_pct,granularity,timestamp\n")

        calculator = CoordinationOverheadCalculator(str(empty_path), str(self.output_path))
        results = calculator.process()

        self.assertEqual(len(results), 0)
        calculator.write_results()
        self.assertTrue(self.output_path.exists())

        with open(self.output_path, mode='r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("task_id", content) # Headers should exist

    def test_invalid_rows_skipped(self):
        """Test that rows with missing or invalid data are skipped."""
        invalid_data = [
            {
                "task_id": "task_001",
                "node_id": "node_A",
                "wall_clock_time": "100.0",
                "cpu_utilization_pct": "80.0",
                "granularity": "fine",
                "timestamp": "2023-01-01T00:00:00"
            },
            {
                "task_id": "task_002",
                "node_id": "node_B",
                "wall_clock_time": "invalid_float", # Should be skipped
                "cpu_utilization_pct": "50.0",
                "granularity": "medium",
                "timestamp": "2023-01-01T00:01:00"
            },
            {
                "task_id": "task_003",
                "node_id": "", # Missing node_id
                "wall_clock_time": "10.0",
                "cpu_utilization_pct": "100.0",
                "granularity": "coarse",
                "timestamp": "2023-01-01T00:02:00"
            }
        ]

        invalid_path = Path(self.temp_dir.name) / "invalid_logs.csv"
        with open(invalid_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=invalid_data[0].keys())
            writer.writeheader()
            writer.writerows(invalid_data)

        calculator = CoordinationOverheadCalculator(str(invalid_path), str(self.output_path))
        results = calculator.process()

        # Only the first valid row should be processed
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].task_id, "task_001")

    def test_summary_statistics(self):
        """Test the calculation of summary statistics."""
        calculator = CoordinationOverheadCalculator(str(self.input_path), str(self.output_path))
        calculator.process()
        summary = calculator.get_summary_statistics()

        self.assertEqual(summary['total_tasks'], 4)
        # Mean of 0.2, 0.5, 0.0, 1.0 = 1.7 / 4 = 0.425
        self.assertAlmostEqual(summary['mean_overhead_ratio'], 0.425, places=5)
        self.assertAlmostEqual(summary['min_overhead_ratio'], 0.0, places=5)
        self.assertAlmostEqual(summary['max_overhead_ratio'], 1.0, places=5)

    def test_file_not_found_raises_error(self):
        """Test that FileNotFoundError is raised if input file does not exist."""
        non_existent_path = Path(self.temp_dir.name) / "does_not_exist.csv"
        calculator = CoordinationOverheadCalculator(str(non_existent_path), str(self.output_path))

        with self.assertRaises(FileNotFoundError):
            calculator.process()