"""
Integration test for CSV export format (Task T033).

This test verifies that the CSV export logic in `code/visualize.py`
produces a file with the correct schema, data types, and content
as specified in the user story requirements.

It simulates the full export pipeline by:
1. Preparing mock metric result data (simulating output from T030/T032).
2. Calling the export function `export_metric_results_to_csv`.
3. Reading the generated file and validating its structure and content.
"""

import os
import sys
import csv
import tempfile
import pytest
from pathlib import Path

# Ensure the project root is in the path for imports
# Assuming tests are run from the project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.visualize import export_metric_results_to_csv
from code.utils.io import export_csv

# Required columns as per T034 / US4 requirements
REQUIRED_COLUMNS = [
    "SNR_dB",
    "noise_type",
    "metric_name",
    "computed_value",
    "ground_truth_value",
    "error_percent"
]

# Sample data simulating the output of T030 (Error Calculation)
MOCK_METRIC_RESULTS = [
    {
        "SNR_dB": 0,
        "noise_type": "Gaussian",
        "metric_name": "Correlation_Dimension",
        "computed_value": 1.85,
        "ground_truth_value": 2.05,
        "error_percent": 9.76
    },
    {
        "SNR_dB": 0,
        "noise_type": "Gaussian",
        "metric_name": "Lyapunov_Exponent",
        "computed_value": 0.42,
        "ground_truth_value": 0.90,
        "error_percent": 53.33
    },
    {
        "SNR_dB": 0,
        "noise_type": "Gaussian",
        "metric_name": "FNN_Rate",
        "computed_value": 0.15,
        "ground_truth_value": 0.02,
        "error_percent": 650.00
    },
    {
        "SNR_dB": 10,
        "noise_type": "Gaussian",
        "metric_name": "Correlation_Dimension",
        "computed_value": 2.01,
        "ground_truth_value": 2.05,
        "error_percent": 1.95
    },
    {
        "SNR_dB": 10,
        "noise_type": "Gaussian",
        "metric_name": "Lyapunov_Exponent",
        "computed_value": 0.88,
        "ground_truth_value": 0.90,
        "error_percent": 2.22
    },
    {
        "SNR_dB": 10,
        "noise_type": "Gaussian",
        "metric_name": "FNN_Rate",
        "computed_value": 0.03,
        "ground_truth_value": 0.02,
        "error_percent": 50.00
    },
    {
        "SNR_dB": 20,
        "noise_type": "Uniform_Quantization",
        "metric_name": "Correlation_Dimension",
        "computed_value": 2.04,
        "ground_truth_value": 2.05,
        "error_percent": 0.49
    },
    {
        "SNR_dB": 20,
        "noise_type": "Uniform_Quantization",
        "metric_name": "Lyapunov_Exponent",
        "computed_value": 0.89,
        "ground_truth_value": 0.90,
        "error_percent": 1.11
    },
    {
        "SNR_dB": 20,
        "noise_type": "Uniform_Quantization",
        "metric_name": "FNN_Rate",
        "computed_value": 0.02,
        "ground_truth_value": 0.02,
        "error_percent": 0.00
    }
]

def test_export_csv_schema_and_content():
    """
    Verifies that the exported CSV file:
    1. Exists at the specified path.
    2. Contains the exact required columns in the correct order.
    3. Contains the expected number of rows.
    4. Data types are consistent (numeric columns are parseable as float).
    """
    output_dir = PROJECT_ROOT / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "test_export_validation.csv"
    
    # Execute the export logic
    export_metric_results_to_csv(MOCK_METRIC_RESULTS, str(output_file))
    
    # Assert file existence
    assert output_file.exists(), f"Exported file {output_file} was not created."
    
    # Read and validate content
    with open(output_file, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # 1. Validate Header
        header = reader.fieldnames
        assert header is not None, "CSV file is empty or has no header."
        assert list(header) == REQUIRED_COLUMNS, (
            f"Header mismatch. Expected: {REQUIRED_COLUMNS}, Got: {list(header)}"
        )
        
        rows = list(reader)
        
        # 2. Validate Row Count
        assert len(rows) == len(MOCK_METRIC_RESULTS), (
            f"Row count mismatch. Expected: {len(MOCK_METRIC_RESULTS)}, Got: {len(rows)}"
        )
        
        # 3. Validate Data Content and Types
        for i, row in enumerate(rows):
            # Check SNR_dB is numeric
            try:
                snr = float(row['SNR_dB'])
            except ValueError:
                raise AssertionError(f"Row {i}: 'SNR_dB' is not a valid float: {row['SNR_dB']}")
            
            # Check error_percent is numeric
            try:
                error = float(row['error_percent'])
            except ValueError:
                raise AssertionError(f"Row {i}: 'error_percent' is not a valid float: {row['error_percent']}")
            
            # Check specific known values from mock data
            expected_snr = MOCK_METRIC_RESULTS[i]['SNR_dB']
            expected_metric = MOCK_METRIC_RESULTS[i]['metric_name']
            
            assert snr == expected_snr, f"Row {i}: SNR mismatch. Expected {expected_snr}, got {snr}"
            assert row['metric_name'] == expected_metric, f"Row {i}: Metric name mismatch."
            
            # Verify the error calculation logic roughly matches (within floating point tolerance)
            # |computed - ground| / |ground| * 100
            computed = float(row['computed_value'])
            ground = float(row['ground_truth_value'])
            if ground != 0:
                calculated_error = abs(computed - ground) / abs(ground) * 100
                # Allow small floating point drift
                assert abs(calculated_error - error) < 0.01, (
                    f"Row {i}: Error calculation mismatch. "
                    f"Calculated: {calculated_error:.2f}, Exported: {error}"
                )

def test_export_csv_file_format():
    """
    Verifies that the file is a valid CSV and can be read by standard pandas/csv readers.
    """
    output_dir = PROJECT_ROOT / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "test_export_format.csv"
    
    # Execute export
    export_metric_results_to_csv(MOCK_METRIC_RESULTS, str(output_file))
    
    # Try to read with csv module to ensure no weird encoding or formatting issues
    try:
        with open(output_file, 'r', newline='', encoding='utf-8') as f:
            # Attempt to parse all lines
            reader = csv.reader(f)
            lines = list(reader)
            
            # Ensure we have header + data
            assert len(lines) >= 2, "CSV file does not have enough lines."
            
            # Check that no row has a different number of columns than the header
            header_len = len(lines[0])
            for i, line in enumerate(lines[1:], start=2):
                assert len(line) == header_len, (
                    f"Row {i} has {len(line)} columns, expected {header_len}. "
                    "This indicates malformed CSV (e.g., missing commas or extra quotes)."
                )
    except Exception as e:
        pytest.fail(f"Failed to parse CSV file: {e}")