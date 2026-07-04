"""
Unit tests for Task T032: metrics_summary.csv export functionality.
"""
import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from run_t032 import (
    find_ground_truth_metrics_files,
    find_noisy_metrics_files,
    find_error_results_files,
    load_ground_truth_metrics,
    load_noisy_metrics,
    load_error_results,
    aggregate_results_to_dataframe,
    export_to_csv
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with mock data files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create subdirectories
        processed_dir = Path(tmpdir) / "data" / "processed"
        processed_dir.mkdir(parents=True)

        # Create mock ground truth file
        gt_data = {
            "seed": 42,
            "system": "lorenz",
            "metrics": {
                "correlation_dimension": 2.05,
                "lyapunov_exponent": 0.905,
                "fnn_rate": 0.02
            }
        }
        gt_file = processed_dir / "ground_truth_metrics_42.json"
        with open(gt_file, 'w') as f:
            json.dump(gt_data, f)

        # Create mock noisy metrics file
        noisy_data = {
            "seed": 42,
            "system": "lorenz",
            "snr_db": 10,
            "noise_type": "gaussian",
            "metrics": {
                "correlation_dimension": 1.95,
                "lyapunov_exponent": 0.85,
                "fnn_rate": 0.15
            }
        }
        noisy_file = processed_dir / "noisy_metrics_42_10_gaussian.json"
        with open(noisy_file, 'w') as f:
            json.dump(noisy_data, f)

        # Create mock error results file
        error_data = {
            "seed": 42,
            "system": "lorenz",
            "snr_db": 10,
            "noise_type": "gaussian",
            "metrics": {
                "correlation_dimension": 1.95,
                "lyapunov_exponent": 0.85,
                "fnn_rate": 0.15
            },
            "errors": {
                "correlation_dimension": {
                    "ground_truth_value": 2.05,
                    "error_percent": 4.88
                },
                "lyapunov_exponent": {
                    "ground_truth_value": 0.905,
                    "error_percent": 6.08
                },
                "fnn_rate": {
                    "ground_truth_value": 0.02,
                    "error_percent": 650.0
                }
            }
        }
        error_file = processed_dir / "error_results_42_10_gaussian.json"
        with open(error_file, 'w') as f:
            json.dump(error_data, f)

        yield str(processed_dir)

def test_find_ground_truth_metrics_files(temp_data_dir):
    """Test finding ground truth metrics files."""
    files = find_ground_truth_metrics_files(temp_data_dir)
    assert len(files) == 1
    assert "ground_truth_metrics_42.json" in files[0]

def test_find_noisy_metrics_files(temp_data_dir):
    """Test finding noisy metrics files."""
    files = find_noisy_metrics_files(temp_data_dir)
    assert len(files) == 1
    assert "noisy_metrics_42_10_gaussian.json" in files[0]

def test_find_error_results_files(temp_data_dir):
    """Test finding error results files."""
    files = find_error_results_files(temp_data_dir)
    assert len(files) == 1
    assert "error_results_42_10_gaussian.json" in files[0]

def test_load_ground_truth_metrics(temp_data_dir):
    """Test loading ground truth metrics."""
    gt_file = os.path.join(temp_data_dir, "ground_truth_metrics_42.json")
    data = load_ground_truth_metrics(gt_file)
    assert data["seed"] == 42
    assert "correlation_dimension" in data["metrics"]

def test_load_error_results(temp_data_dir):
    """Test loading error results."""
    error_file = os.path.join(temp_data_dir, "error_results_42_10_gaussian.json")
    data = load_error_results(error_file)
    assert data["snr_db"] == 10
    assert "correlation_dimension" in data["errors"]

def test_aggregate_results_to_dataframe(temp_data_dir):
    """Test aggregating results into a DataFrame."""
    error_files = find_error_results_files(temp_data_dir)
    noisy_files = find_noisy_metrics_files(temp_data_dir)
    gt_files = find_ground_truth_metrics_files(temp_data_dir)

    df = aggregate_results_to_dataframe(error_files, noisy_files, gt_files)

    assert not df.empty
    assert len(df) == 3  # 3 metrics
    assert "SNR_dB" in df.columns
    assert "noise_type" in df.columns
    assert "metric_name" in df.columns
    assert "error_percent" in df.columns

    # Check specific values
    cd_row = df[df["metric_name"] == "correlation_dimension"].iloc[0]
    assert cd_row["SNR_dB"] == 10
    assert cd_row["noise_type"] == "gaussian"
    assert abs(cd_row["error_percent"] - 4.88) < 0.1

def test_export_to_csv(temp_data_dir):
    """Test exporting DataFrame to CSV."""
    error_files = find_error_results_files(temp_data_dir)
    noisy_files = find_noisy_metrics_files(temp_data_dir)
    gt_files = find_ground_truth_metrics_files(temp_data_dir)

    df = aggregate_results_to_dataframe(error_files, noisy_files, gt_files)

    output_path = os.path.join(temp_data_dir, "test_output.csv")
    export_to_csv(df, output_path)

    assert os.path.exists(output_path)

    # Read back and verify
    df_read = pd.read_csv(output_path)
    assert len(df_read) == len(df)
    assert list(df_read.columns) == list(df.columns)