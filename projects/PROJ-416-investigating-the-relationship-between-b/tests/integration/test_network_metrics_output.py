"""
Integration test for code/analysis/network.py (Task T019).

Verifies that the network analysis pipeline produces an output CSV
containing all three required metrics (modularity, global_efficiency, local_efficiency)
for each subject processed.

This test assumes:
1. US1 (T017) has completed and produced data/metrics/filtered_subjects.csv.
2. The network analysis script (code/analysis/network.py) has been run.
3. The output file data/metrics/network_metrics.csv exists.
"""

import os
import csv
import pytest
from pathlib import Path
import sys

# Add project root to path if needed (though pytest usually handles this)
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import Config

REQUIRED_METRICS = {
    "modularity",
    "global_efficiency",
    "local_efficiency"
}

REQUIRED_COLUMNS = {"subject_id"} | REQUIRED_METRICS

def test_network_metrics_csv_exists():
    """Test that the network metrics CSV file is created."""
    config = Config()
    output_path = config.METRICS_DIR / "network_metrics.csv"
    
    assert output_path.exists(), f"Output file not found: {output_path}"

def test_network_metrics_csv_has_required_columns():
    """Test that the CSV contains all three required metrics per subject."""
    config = Config()
    output_path = config.METRICS_DIR / "network_metrics.csv"
    
    if not output_path.exists():
        pytest.skip(f"Output file {output_path} does not exist yet. Run code/analysis/network.py first.")
    
    with open(output_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        headers = set(reader.fieldnames) if reader.fieldnames else set()
        
        # Check intersection
        missing = REQUIRED_COLUMNS - headers
        assert not missing, f"Missing required columns in {output_path}: {missing}"

def test_network_metrics_has_data_rows():
    """Test that the CSV contains at least one data row (one subject)."""
    config = Config()
    output_path = config.METRICS_DIR / "network_metrics.csv"
    
    if not output_path.exists():
        pytest.skip(f"Output file {output_path} does not exist yet. Run code/analysis/network.py first.")
    
    row_count = 0
    with open(output_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_count += 1
            # Verify values are present for the required metrics
            for metric in REQUIRED_METRICS:
                val = row.get(metric)
                assert val is not None and val != "", f"Metric '{metric}' is empty for subject {row.get('subject_id', 'UNKNOWN')}"
                # Verify numeric bounds (basic sanity check)
                try:
                    f_val = float(val)
                    # Modularity Q is typically >= 0, Efficiencies >= 0
                    # We allow small negative due to float noise if strictly necessary, but typically >= 0
                    # For this test, we just ensure it's a valid float.
                except ValueError:
                    pytest.fail(f"Metric '{metric}' for subject {row.get('subject_id')} is not a valid float: {val}")
    
    assert row_count > 0, "Network metrics CSV contains no data rows."

def test_metrics_are_finite():
    """Test that metric values are finite numbers (not NaN/Inf)."""
    config = Config()
    output_path = config.METRICS_DIR / "network_metrics.csv"
    
    if not output_path.exists():
        pytest.skip(f"Output file {output_path} does not exist yet. Run code/analysis/network.py first.")
    
    import math
    
    with open(output_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for metric in REQUIRED_METRICS:
                val_str = row.get(metric, "")
                try:
                    val = float(val_str)
                    assert not math.isnan(val), f"Metric '{metric}' is NaN for subject {row['subject_id']}"
                    assert not math.isinf(val), f"Metric '{metric}' is Inf for subject {row['subject_id']}"
                except ValueError:
                    pytest.fail(f"Metric '{metric}' for subject {row['subject_id']} is not a number: {val_str}")