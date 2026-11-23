"""
Integration test for sensitivity analysis pipeline (T031, T032).
Verifies the full sensitivity analysis pipeline against the stability threshold.
"""
import os
import json
import csv
import tempfile
import shutil
import pytest
from pathlib import Path

# Import the functions to test
# We need to mock the file paths to use a temporary directory
from validation.sensitivity import (
    load_baseline_shifts,
    load_rf_rmse,
    calculate_stability_metrics,
    save_stability_metrics
)

# We will also need to import the main logic to simulate the sweep
# Since the main function in sensitivity.py orchestrates T031 and T032,
# we will test the components directly with mock data.

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def mock_baseline_shifts(temp_dir):
    """
    Create a mock baseline_shifts.csv that produces a stability_metric > 0.5.
    We need the classification rate to vary significantly across the 0.45-0.55 range.
    To achieve high std (and thus high stability_metric), we'll create data where
    the threshold crossing happens abruptly within the range.
    """
    file_path = os.path.join(temp_dir, "baseline_shifts.csv")
    
    # Create data where baseline_shift values are clustered such that
    # a small change in threshold causes a large jump in classification rate.
    # Example: 50% of data has shift=0.46, 50% has shift=0.54.
    # Threshold 0.45 -> both pass (rate=1.0)
    # Threshold 0.47 -> only 0.54 passes (rate=0.5)
    # Threshold 0.53 -> only 0.54 passes (rate=0.5)
    # Threshold 0.55 -> none pass (rate=0.0)
    # This creates a high variance.
    
    rows = []
    # 10 rows with shift 0.46
    for i in range(10):
        rows.append({
            "host_id": "Cu",
            "solute_id": "Ni",
            "activation_energy": 1.5,
            "pure_host_baseline": 1.04,
            "baseline_shift": 0.46
        })
    # 10 rows with shift 0.54
    for i in range(10):
        rows.append({
            "host_id": "Cu",
            "solute_id": "Zn",
            "activation_energy": 1.58,
            "pure_host_baseline": 1.04,
            "baseline_shift": 0.54
        })

    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["host_id", "solute_id", "activation_energy", "pure_host_baseline", "baseline_shift"])
        writer.writeheader()
        writer.writerows(rows)
    
    return file_path

@pytest.fixture
def mock_sweep_data(temp_dir):
    """
    Create a mock sensitivity_sweep.csv with known values that produce a high stability metric.
    We manually construct the CSV to ensure the calculated stability_metric > 0.5.
    """
    file_path = os.path.join(temp_dir, "sensitivity_sweep.csv")
    
    # Thresholds from 0.45 to 0.55 in 0.01 steps
    # We want high variance in classification rates.
    # Let's say:
    # 0.45 -> 1.0
    # 0.46 -> 1.0
    # 0.47 -> 0.5 (drop because 0.46 < 0.47)
    # ...
    # 0.53 -> 0.5
    # 0.54 -> 0.5
    # 0.55 -> 0.0 (drop because 0.54 < 0.55)
    
    data = [
        {"threshold_eV": 0.45, "classification_rate": 1.0},
        {"threshold_eV": 0.46, "classification_rate": 1.0},
        {"threshold_eV": 0.47, "classification_rate": 0.5},
        {"threshold_eV": 0.48, "classification_rate": 0.5},
        {"threshold_eV": 0.49, "classification_rate": 0.5},
        {"threshold_eV": 0.50, "classification_rate": 0.5},
        {"threshold_eV": 0.51, "classification_rate": 0.5},
        {"threshold_eV": 0.52, "classification_rate": 0.5},
        {"threshold_eV": 0.53, "classification_rate": 0.5},
        {"threshold_eV": 0.54, "classification_rate": 0.5},
        {"threshold_eV": 0.55, "classification_rate": 0.0},
    ]
    
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["threshold_eV", "classification_rate"])
        writer.writeheader()
        writer.writerows(data)
        
    return file_path

def test_sensitivity_sweep_generation(mock_baseline_shifts, temp_dir):
    """
    Test that the sweep generation logic (T031) produces the correct 11 points.
    We simulate the logic here since we can't easily import the internal loop without
    refactoring the main function to be more testable. Instead, we verify the
    expected behavior by running the calculation logic manually.
    """
    # Load the mock data
    df = load_baseline_shifts(mock_baseline_shifts)
    
    # Manually perform the sweep to verify logic
    thresholds = [0.45 + i * 0.01 for i in range(11)]
    rates = []
    
    for thresh in thresholds:
        # Count rows where baseline_shift > threshold
        count = sum(1 for _, row in df.iterrows() if row['baseline_shift'] > thresh)
        rate = count / len(df)
        rates.append(rate)
    
    # Expected rates based on our mock data (10 at 0.46, 10 at 0.54, total 20)
    # 0.45: 0.46>0.45 (yes), 0.54>0.45 (yes) -> 20/20 = 1.0
    # 0.46: 0.46>0.46 (no), 0.54>0.46 (yes) -> 10/20 = 0.5
    # ...
    # 0.54: 0.46>0.54 (no), 0.54>0.54 (no) -> 0/20 = 0.0
    # Wait, my mock data logic above was slightly off for 0.46.
    # 0.46 > 0.46 is False. So at 0.46, rate is 0.5.
    # At 0.45, rate is 1.0.
    # At 0.54, 0.54 > 0.54 is False. So rate is 0.0.
    # At 0.53, 0.54 > 0.53 is True. Rate is 0.5.
    
    expected_rates = [
        1.0, # 0.45
        0.5, # 0.46
        0.5, # 0.47
        0.5, # 0.48
        0.5, # 0.49
        0.5, # 0.50
        0.5, # 0.51
        0.5, # 0.52
        0.5, # 0.53
        0.5, # 0.54
        0.0  # 0.55
    ]
    
    assert len(rates) == 11
    for i, (actual, expected) in enumerate(zip(rates, expected_rates)):
        assert abs(actual - expected) < 1e-6, f"Mismatch at index {i}: {actual} != {expected}"

def test_stability_metric_calculation(mock_sweep_data, temp_dir):
    """
    Test that the stability metric is calculated correctly and the threshold check works.
    """
    # Load the sweep data
    # Note: The function calculate_stability_metrics expects the path to the CSV
    # and optionally the RF RMSE (which we don't need for this specific metric calculation)
    # We need to read the CSV manually to pass to the calculation logic or mock it.
    # Let's read the CSV and calculate manually to verify the function's logic.
    
    df = pd.read_csv(mock_sweep_data)
    rates = df['classification_rate'].values
    min_thresh = df['threshold_eV'].min()
    max_thresh = df['threshold_eV'].max()
    
    # Calculate std
    std_val = np.std(rates)
    # Calculate stability metric: std / (max - min)
    stability_metric = std_val / (max_thresh - min_thresh)
    
    # Expected values
    # rates = [1.0, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.0]
    # mean = (1 + 9*0.5 + 0) / 11 = 5.5 / 11 = 0.5
    # variance = sum((x - 0.5)^2) / 11
    # (1-0.5)^2 = 0.25
    # (0.5-0.5)^2 = 0 (9 times)
    # (0-0.5)^2 = 0.25
    # sum = 0.5
    # var = 0.5 / 11 ≈ 0.04545
    # std = sqrt(0.04545) ≈ 0.2132
    # range = 0.55 - 0.45 = 0.1
    # stability_metric = 0.2132 / 0.1 = 2.132
    
    expected_stability = 2.132 # Approximate
    
    assert abs(stability_metric - expected_stability) < 0.1, f"Calculated stability metric {stability_metric} does not match expected {expected_stability}"
    
    # Now test the function save_stability_metrics
    output_path = os.path.join(temp_dir, "stability_metrics.json")
    
    # We need to call the function that does the calculation and saving.
    # Since the main function in sensitivity.py does the whole pipeline,
    # let's call calculate_stability_metrics and save_stability_metrics directly.
    # But calculate_stability_metrics expects the CSV path and returns the metrics.
    
    metrics = calculate_stability_metrics(mock_sweep_data)
    
    assert "stability_metric" in metrics
    assert "mean_classification_rate" in metrics
    assert "threshold_check" in metrics
    
    assert metrics["stability_metric"] > 0.5, "Stability metric should be > 0.5 for this mock data"
    assert metrics["threshold_check"] == "fail", "Threshold check should be 'fail' for stability_metric > 0.5"

def test_full_pipeline_integration(mock_baseline_shifts, temp_dir):
    """
    Test the full integration: generate sweep, calculate stability, save results.
    This simulates running T031 and T032.
    """
    # Step 1: Generate sweep (T031 logic)
    # We'll do this manually to avoid dependencies on the main function's file I/O
    df = load_baseline_shifts(mock_baseline_shifts)
    thresholds = [0.45 + i * 0.01 for i in range(11)]
    sweep_data = []
    
    for thresh in thresholds:
        count = sum(1 for _, row in df.iterrows() if row['baseline_shift'] > thresh)
        rate = count / len(df)
        sweep_data.append({"threshold_eV": thresh, "classification_rate": rate})
    
    sweep_path = os.path.join(temp_dir, "sensitivity_sweep.csv")
    with open(sweep_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["threshold_eV", "classification_rate"])
        writer.writeheader()
        writer.writerows(sweep_data)
    
    # Step 2: Calculate stability (T032 logic)
    metrics = calculate_stability_metrics(sweep_path)
    
    # Step 3: Save metrics
    output_path = os.path.join(temp_dir, "stability_metrics.json")
    save_stability_metrics(metrics, output_path)
    
    # Step 4: Verify output
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        saved_metrics = json.load(f)
    
    assert saved_metrics["stability_metric"] > 0.5
    assert saved_metrics["threshold_check"] == "fail"
    assert len(sweep_data) == 11

import pandas as pd
import numpy as np