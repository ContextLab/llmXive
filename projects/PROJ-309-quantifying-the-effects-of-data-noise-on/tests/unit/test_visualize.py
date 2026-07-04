"""
Unit tests for the visualize module (T034).
"""
import pytest
import tempfile
import os
from pathlib import Path
import csv
from code.visualize import export_metric_results_to_csv

def test_export_metric_results_to_csv():
    """Test that export_metric_results_to_csv creates a valid CSV with correct columns."""
    # Sample data matching the task requirements
    mock_results = [
        {
            'SNR_dB': 30.0,
            'noise_type': 'gaussian',
            'metric_name': 'correlation_dimension',
            'computed_value': 2.05,
            'ground_truth_value': 2.06,
            'error_percent': 0.49
        },
        {
            'SNR_dB': 20.0,
            'noise_type': 'gaussian',
            'metric_name': 'lyapunov_exponent',
            'computed_value': 0.90,
            'ground_truth_value': 0.91,
            'error_percent': 1.10
        },
        {
            'SNR_dB': 10.0,
            'noise_type': 'quantization',
            'metric_name': 'fnn',
            'computed_value': 0.55,
            'ground_truth_value': 0.02,
            'error_percent': 2650.0
        }
    ]

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "test_metrics.csv"
        
        # Execute the function
        result_path = export_metric_results_to_csv(mock_results, output_path)
        
        # Verify file exists
        assert result_path.exists()
        assert result_path == output_path

        # Verify content
        with open(result_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Check row count
            assert len(rows) == 3

            # Check columns
            expected_columns = [
                'SNR_dB', 'noise_type', 'metric_name', 
                'computed_value', 'ground_truth_value', 'error_percent'
            ]
            assert list(rows[0].keys()) == expected_columns

            # Check specific values
            assert float(rows[0]['SNR_dB']) == 30.0
            assert rows[0]['noise_type'] == 'gaussian'
            assert float(rows[2]['error_percent']) == 2650.0

def test_export_empty_results():
    """Test that exporting empty results raises a ValueError."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "empty.csv"
        
        with pytest.raises(ValueError, match="The results list is empty"):
            export_metric_results_to_csv([], output_path)