"""
Integration test for CSV export format (Task T033).

This test verifies that the `export_metric_results_to_csv` function in
`code.visualize` correctly writes metric results to a CSV file with the
expected schema and format.

It validates:
1. The output file is created at the expected path.
2. The CSV headers match the required columns.
3. The data types and values in the rows are consistent with the input data.
"""

import os
import csv
import tempfile
import pytest
from pathlib import Path

# Import the function under test
from code.visualize import export_metric_results_to_csv


class TestCSVExportFormat:
    """Integration tests for CSV export functionality."""

    def test_export_creates_file_with_correct_headers(self, tmp_path):
        """Test that the exported CSV has the correct column headers."""
        # Arrange
        output_file = tmp_path / "metrics_summary.csv"
        
        # Sample metric results matching the expected schema
        metric_results = [
            {
                "snr_db": 10.0,
                "noise_type": "gaussian",
                "metric_name": "correlation_dimension",
                "computed_value": 2.05,
                "ground_truth_value": 2.06,
                "error_percent": 0.485
            },
            {
                "snr_db": 10.0,
                "noise_type": "gaussian",
                "metric_name": "lyapunov_exponent",
                "computed_value": 0.90,
                "ground_truth_value": 0.91,
                "error_percent": 1.099
            },
            {
                "snr_db": 10.0,
                "noise_type": "gaussian",
                "metric_name": "fnn_rate",
                "computed_value": 0.02,
                "ground_truth_value": 0.01,
                "error_percent": 100.0
            }
        ]

        expected_headers = [
            "snr_db",
            "noise_type",
            "metric_name",
            "computed_value",
            "ground_truth_value",
            "error_percent"
        ]

        # Act
        export_metric_results_to_csv(metric_results, str(output_file))

        # Assert
        assert output_file.exists(), "CSV file was not created"

        with open(output_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            assert headers is not None, "CSV file is empty or has no headers"
            assert set(headers) == set(expected_headers), (
                f"Headers mismatch. Expected {expected_headers}, got {headers}"
            )

            # Verify row count
            rows = list(reader)
            assert len(rows) == len(metric_results), (
                f"Row count mismatch. Expected {len(metric_results)}, got {len(rows)}"
            )

    def test_export_writes_data_correctly(self, tmp_path):
        """Test that the exported CSV contains the correct data values."""
        # Arrange
        output_file = tmp_path / "metrics_test_data.csv"
        
        metric_results = [
            {
                "snr_db": 0.0,
                "noise_type": "quantization",
                "metric_name": "correlation_dimension",
                "computed_value": 1.95,
                "ground_truth_value": 2.06,
                "error_percent": 5.34
            }
        ]

        # Act
        export_metric_results_to_csv(metric_results, str(output_file))

        # Assert
        with open(output_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            assert len(rows) == 1
            row = rows[0]

            assert float(row['snr_db']) == 0.0
            assert row['noise_type'] == "quantization"
            assert row['metric_name'] == "correlation_dimension"
            assert abs(float(row['computed_value']) - 1.95) < 1e-5
            assert abs(float(row['ground_truth_value']) - 2.06) < 1e-5
            assert abs(float(row['error_percent']) - 5.34) < 1e-3

    def test_export_handles_empty_list(self, tmp_path):
        """Test that an empty list produces a valid CSV with only headers."""
        # Arrange
        output_file = tmp_path / "empty_metrics.csv"
        expected_headers = [
            "snr_db", "noise_type", "metric_name", 
            "computed_value", "ground_truth_value", "error_percent"
        ]

        # Act
        export_metric_results_to_csv([], str(output_file))

        # Assert
        assert output_file.exists()
        
        with open(output_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            rows = list(reader)

            assert set(headers) == set(expected_headers)
            assert len(rows) == 0

    def test_export_numeric_precision(self, tmp_path):
        """Test that numeric values are written with reasonable precision."""
        # Arrange
        output_file = tmp_path / "precision_test.csv"
        
        metric_results = [
            {
                "snr_db": 15.123456789,
                "noise_type": "gaussian",
                "metric_name": "lyapunov_exponent",
                "computed_value": 0.123456789012,
                "ground_truth_value": 0.123456789013,
                "error_percent": 0.0000000001
            }
        ]

        # Act
        export_metric_results_to_csv(metric_results, str(output_file))

        # Assert
        with open(output_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            assert len(rows) == 1
            row = rows[0]
            
            # Verify that high precision numbers are preserved in CSV
            assert float(row['snr_db']) == 15.123456789
            assert float(row['computed_value']) == 0.123456789012
            assert float(row['ground_truth_value']) == 0.123456789013
            assert float(row['error_percent']) == 0.0000000001