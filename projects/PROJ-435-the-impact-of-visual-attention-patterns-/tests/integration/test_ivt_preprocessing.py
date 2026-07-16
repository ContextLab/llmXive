"""
Integration test for I-VT algorithm on sample noisy data.

This test verifies that the I-VT fixation detection logic in 
`code/utils/fixation_detection.py` correctly processes noisy gaze data,
identifies fixations based on velocity thresholds, and handles edge cases
such as missing data or outliers.

It depends on the implementation of T006 (fixation_detection.py).
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Add the project root to the path to allow imports from code/
# Assuming this test runs from the project root or tests/ directory
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.fixation_detection import (
    load_fixation_config,
    calculate_velocity,
    detect_fixations_ivt,
    process_gaze_data
)
from utils.logging_config import setup_logging

# Setup logging for the test run
setup_logging()
logger = logging.getLogger(__name__)


@pytest.fixture
def sample_noisy_gaze_data():
    """
    Generates a synthetic but realistic sample of noisy eye-tracking data.
    This is NOT a dataset for analysis, but a controlled input for testing the I-VT logic.
    """
    np.random.seed(42)
    n_points = 500
    
    # Simulate a fixation on a target (x=300, y=200) with some jitter
    x_base = 300.0
    y_base = 200.0
    jitter = 2.0  # pixels of micro-saccade/noise
    
    # Create a fixation burst in the middle of the sequence
    data = []
    for i in range(n_points):
        timestamp = i * 16.67  # ~60Hz sampling
        
        if 100 <= i <= 200:
            # Fixation period
            x = x_base + np.random.normal(0, jitter)
            y = y_base + np.random.normal(0, jitter)
        elif i < 100:
            # Saccade approach (moving towards target)
            x = x_base - 100 + (i * (100 / 100)) + np.random.normal(0, jitter)
            y = y_base + np.random.normal(0, jitter)
        else:
            # Saccade away
            x = x_base + 100 - ((n_points - i) * (100 / (n_points - 200))) + np.random.normal(0, jitter)
            y = y_base + np.random.normal(0, jitter)
        
        # Add some random noise spikes (outliers)
        if np.random.random() < 0.01:
            x += np.random.normal(0, 50) # Large spike
            y += np.random.normal(0, 50)
        
        data.append({
            "participant_id": "P001",
            "trial_id": "T01",
            "timestamp": timestamp,
            "x": x,
            "y": y,
            "valid": True
        })
    
    # Inject a few missing values to test robustness
    data[50]["valid"] = False
    data[150]["x"] = np.nan
    
    return pd.DataFrame(data)


@pytest.fixture
def ivt_config():
    """
    Returns the default I-VT configuration parameters.
    """
    return {
        "ivt_velocity_threshold": 30.0,  # deg/s
        "ivt_min_duration": 60.0,        # ms
        "sampling_rate": 60.0            # Hz
    }


def test_calculate_velocity(sample_noisy_gaze_data, ivt_config):
    """
    Test that velocity calculation correctly computes speed between points.
    """
    # Filter to a known segment where we can estimate velocity
    # Saccade approach: moving ~100px in 100 frames (1.67s) -> ~60 px/s
    # We need to convert to deg/s, but let's just check the relative logic first.
    # For this test, we assume 100px = 10 degrees (arbitrary scaling for test)
    
    # Run velocity calculation
    df_with_vel = calculate_velocity(sample_noisy_gaze_data.copy(), ivt_config)
    
    assert "velocity" in df_with_vel.columns
    assert len(df_with_vel) == len(sample_noisy_gaze_data)
    
    # Check that velocity is 0 for the first point (no previous point)
    assert pd.isna(df_with_vel.iloc[0]["velocity"])
    
    # Check that velocities in the fixation period are generally low
    fixation_mask = (df_with_vel["timestamp"] >= 1667) & (df_with_vel["timestamp"] <= 3334)
    fixation_velocities = df_with_vel.loc[fixation_mask, "velocity"].dropna()
    
    # The majority of fixation velocities should be below the threshold (30 deg/s)
    # Allow some noise, but mean should be low
    if len(fixation_velocities) > 0:
        assert fixation_velocities.mean() < ivt_config["ivt_velocity_threshold"]


def test_detect_fixations_ivt_integration(sample_noisy_gaze_data, ivt_config):
    """
    Integration test: Run the full I-VT detection pipeline on noisy data.
    Verifies that fixations are detected in the expected time window.
    """
    # Run detection
    fixations = detect_fixations_ivt(sample_noisy_gaze_data, ivt_config)
    
    # Assertions
    assert isinstance(fixations, pd.DataFrame)
    assert "start_time" in fixations.columns
    assert "end_time" in fixations.columns
    assert "duration" in fixations.columns
    assert "avg_x" in fixations.columns
    assert "avg_y" in fixations.columns
    
    # We expect at least one fixation in the 100-200 frame range (approx 1667ms - 3334ms)
    # The I-VT algorithm should have identified this cluster.
    if len(fixations) > 0:
        # Check if any fixation overlaps with our known fixation period
        fixation_period_start = 1667 # ms
        fixation_period_end = 3334   # ms
        
        found_fixation = False
        for _, fix in fixations.iterrows():
            # Check for overlap
            if (fix["start_time"] <= fixation_period_end) and (fix["end_time"] >= fixation_period_start):
                found_fixation = True
                # Check that the center of the fixation is roughly where we put it (300, 200)
                assert 250 <= fix["avg_x"] <= 350, f"Fixation center X {fix['avg_x']} out of expected range"
                assert 150 <= fix["avg_y"] <= 250, f"Fixation center Y {fix['avg_y']} out of expected range"
                break
        
        assert found_fixation, "No fixation detected in the expected time window (1667ms - 3334ms)"
    else:
        # If no fixations found, it might be due to noise being too high or threshold too strict
        # In a real test, we might want to check why, but for now we assert that the logic ran
        pytest.fail("I-VT algorithm failed to detect any fixations in the sample data.")


def test_process_gaze_data_pipeline(sample_noisy_gaze_data, ivt_config, tmp_path):
    """
    End-to-end test of the process_gaze_data function.
    Verifies that the function reads input, processes it, and writes output correctly.
    """
    # Save input to a temp CSV
    input_path = tmp_path / "input_gaze.csv"
    sample_noisy_gaze_data.to_csv(input_path, index=False)
    
    # Define output path
    output_path = tmp_path / "output_fixations.csv"
    
    # Run the pipeline function
    # Note: process_gaze_data expects a list of files or a single file path
    # We adapt the call to pass a single file path
    result = process_gaze_data(
        input_files=[str(input_path)],
        output_dir=str(tmp_path),
        config=ivt_config
    )
    
    # Verify output file exists
    assert output_path.exists(), f"Output file {output_path} was not created."
    
    # Verify content
    output_df = pd.read_csv(output_path)
    assert len(output_df) > 0, "Output file is empty."
    assert "duration" in output_df.columns
    
    # Check that the output contains the expected fixation
    # (Similar logic to test_detect_fixations_ivt_integration)
    fixation_period_start = 1667
    fixation_period_end = 3334
    
    found = False
    for _, row in output_df.iterrows():
        if (row["start_time"] <= fixation_period_end) and (row["end_time"] >= fixation_period_start):
            found = True
            break
    
    assert found, "Processed output does not contain the expected fixation."


def test_ivt_handles_nan_and_invalid(sample_noisy_gaze_data, ivt_config):
    """
    Test that the I-VT algorithm handles NaN and invalid flags gracefully.
    """
    # Ensure the sample data has NaN/Invalid values (set up in fixture)
    assert sample_noisy_gaze_data["valid"].sum() < len(sample_noisy_gaze_data)
    assert sample_noisy_gaze_data["x"].isna().sum() > 0
    
    # Run detection
    fixations = detect_fixations_ivt(sample_noisy_gaze_data, ivt_config)
    
    # The algorithm should not crash and should produce valid fixations
    assert isinstance(fixations, pd.DataFrame)
    # We expect at least one fixation despite the noise/missing data
    assert len(fixations) > 0, "I-VT failed to detect fixations when handling missing data."
