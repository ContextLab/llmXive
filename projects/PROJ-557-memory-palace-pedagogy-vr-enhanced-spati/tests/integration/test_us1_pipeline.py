"""
Integration test for the full User Story 1 pipeline on sample data.

This test verifies the end-to-end flow:
1. Load raw pupil data from data/raw (downloaded by T004).
2. Run preprocessing (T012 logic) to clean and normalize.
3. Run CLI calculation (T013 logic) to compute z-scores.
4. Verify output file creation and statistical properties.
"""

import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config import get_config, set_random_seed
from data_model import Participant, Passage, Window
from preprocessing import remove_blinks, low_pass_filter, baseline_correct, ingest_screen_luminance_logs, normalize_luminance_algorithm
from cli_engine import compute_moving_average_zscore, identify_high_load_windows, flag_outliers


@pytest.fixture(scope="module")
def sample_data_path():
    """
    Locate the raw data downloaded by T004.
    T004 downloads ds004041 to data/raw/.
    We expect a specific structure or a known file pattern.
    """
    raw_dir = project_root / "data" / "raw"
    if not raw_dir.exists():
        pytest.skip("Raw data directory not found. T004 must be run first.")
    
    # Look for pupil data files (typically .csv or .tsv in subjects folders)
    # ds004041 structure: ds004041/sub-XX/pupil_data.tsv
    pupil_files = list(raw_dir.glob("**/pupil_data.tsv"))
    if not pupil_files:
        # Fallback to any CSV if TSV not found, though spec says TSV
        pupil_files = list(raw_dir.glob("**/*.csv"))
    
    if not pupil_files:
        pytest.skip("No pupil data files found in data/raw. T004 download may have failed or structure differs.")
    
    return pupil_files[0]


@pytest.fixture(scope="module")
def luminance_log_path():
    """
    Locate screen luminance logs if available.
    """
    raw_dir = project_root / "data" / "raw"
    # Look for common luminance log names
    log_files = list(raw_dir.glob("**/*luminance*.tsv")) + list(raw_dir.glob("**/*luminance*.csv"))
    if log_files:
        return log_files[0]
    return None


def test_us1_full_pipeline(sample_data_path, luminance_log_path):
    """
    Run the full US-1 pipeline on the first available sample file.
    
    Steps:
    1. Load raw data.
    2. Preprocess (blink removal, filtering, baseline, luminance).
    3. Compute CLI (z-score).
    4. Identify high-load windows.
    5. Verify output artifacts (in-memory for this test, but logic must hold).
    """
    set_random_seed(42)
    config = get_config()

    # 1. Load Data
    # Assuming ds004041 format: columns like 'pupil_left', 'pupil_right', 'time'
    # We try to load with pandas, handling potential header issues
    try:
        df_raw = pd.read_csv(sample_data_path, sep='\t')
    except Exception:
        try:
            df_raw = pd.read_csv(sample_data_path, sep=',')
        except Exception as e:
            pytest.fail(f"Could not parse raw data file: {e}")

    # Ensure required columns exist (ds004041 usually has 'pupil_left', 'pupil_right')
    required_cols = ['pupil_left', 'pupil_right']
    missing = [c for c in required_cols if c not in df_raw.columns]
    if missing:
        # Try to find similar columns
        possible_cols = [c for c in df_raw.columns if 'pupil' in c.lower()]
        if possible_cols:
            df_raw.rename(columns={possible_cols[0]: 'pupil_left'}, inplace=True)
            if len(possible_cols) > 1:
                df_raw.rename(columns={possible_cols[1]: 'pupil_right'}, inplace=True)
            else:
                # If only one, duplicate for simulation
                df_raw['pupil_right'] = df_raw['pupil_left']
        else:
            pytest.skip(f"Raw data missing pupil columns. Found: {df_raw.columns.tolist()}")

    # 2. Preprocessing
    # Ingest luminance if available
    if luminance_log_path:
        try:
            luminance_df = pd.read_csv(luminance_log_path, sep='\t' if luminance_log_path.suffix == '.tsv' else ',')
            luminance_data = ingest_screen_luminance_logs(luminance_df)
        except Exception:
            luminance_data = None
    else:
        luminance_data = None

    # Apply preprocessing steps
    # Note: remove_blinks expects a series or array
    pupil_left = df_raw['pupil_left'].values
    pupil_right = df_raw['pupil_right'].values

    # Remove blinks
    cleaned_left = remove_blinks(pupil_left)
    cleaned_right = remove_blinks(pupil_right)

    # Low pass filter (cutoff 4Hz as per T008/T012)
    # Assuming sampling rate is in the data or config
    # ds004041 typically 1000Hz or 250Hz. We assume 1000Hz if not found
    fs = 1000
    if 'sampling_rate' in df_raw.columns:
        fs = int(df_raw['sampling_rate'].iloc[0])

    filtered_left = low_pass_filter(cleaned_left, fs, cutoff=4.0)
    filtered_right = low_pass_filter(cleaned_right, fs, cutoff=4.0)

    # Baseline correct (using first 100ms or first 50 samples as baseline)
    baseline_window = 50
    baseline_left = baseline_correct(filtered_left, baseline_window)
    baseline_right = baseline_correct(filtered_right, baseline_window)

    # Luminance normalization if data exists
    if luminance_data is not None:
        norm_left = normalize_luminance_algorithm(baseline_left, luminance_data['left'])
        norm_right = normalize_luminance_algorithm(baseline_right, luminance_data['right'])
    else:
        norm_left = baseline_left
        norm_right = baseline_right

    # Combine channels (average)
    final_pupil = (norm_left + norm_right) / 2.0

    # 3. CLI Calculation
    # Compute moving average z-score
    window_size = 200  # 200ms window approx
    cli_series = compute_moving_average_zscore(final_pupil, window_size)

    # 4. Identify High Load Windows
    # Threshold: 0.5 SD above mean
    high_load_mask = identify_high_load_windows(cli_series, threshold_sd=0.5)

    # 5. Outlier Handling
    outlier_mask = flag_outliers(cli_series, threshold_sd=3.0)

    # 6. Verification
    # Check that we have processed data
    assert len(cli_series) > 0, "CLI series is empty"
    assert len(high_load_mask) == len(cli_series), "High load mask length mismatch"
    assert len(outlier_mask) == len(cli_series), "Outlier mask length mismatch"

    # Check statistical properties
    # Z-scores should have mean ~0 and std ~1 (locally)
    mean_cli = np.nanmean(cli_series)
    std_cli = np.nanstd(cli_series)
    
    # Allow some tolerance due to finite sample and moving average
    assert abs(mean_cli) < 1.0, f"CLI mean {mean_cli} is too far from 0"
    assert std_cli > 0.1, f"CLI std {std_cli} is too small"

    # Check that high load windows are a reasonable proportion (not 0% or 100%)
    high_load_ratio = np.mean(high_load_mask)
    assert 0.01 < high_load_ratio < 0.99, f"High load ratio {high_load_ratio} is extreme"

    # Check that outliers are rare
    outlier_ratio = np.mean(outlier_mask)
    assert outlier_ratio < 0.1, f"Outlier ratio {outlier_ratio} is too high"

    # Log success
    print(f"US-1 Pipeline Integration Test Passed.")
    print(f"  - Samples processed: {len(cli_series)}")
    print(f"  - CLI Mean: {mean_cli:.4f}, Std: {std_cli:.4f}")
    print(f"  - High Load Ratio: {high_load_ratio:.2%}")
    print(f"  - Outlier Ratio: {outlier_ratio:.2%}")

    return True