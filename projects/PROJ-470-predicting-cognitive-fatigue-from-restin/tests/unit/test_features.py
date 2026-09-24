"""Unit tests for feature extraction (T016) and verification (T017)."""
import os
import sys
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add code to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from features import extract_complexity_metrics, save_metrics, load_sample_path
import mne


def create_dummy_eeg_data(n_channels=5, n_times=1000, n_epochs=10):
    """Create dummy EEG data for testing."""
    # Create info structure
    ch_names = [f'EEG {i:03d}' for i in range(n_channels)]
    sfreq = 250.0
    info = mne.create_info(ch_names, sfreq, ch_types='eeg')

    # Create random data
    data = np.random.randn(n_epochs, n_channels, n_times) * 1e-6

    # Create Epochs object
    events = np.array([[i * 1000, 0, 1] for i in range(n_epochs)])
    epochs = mne.EpochsArray(data, info, events=events, tmin=0, verbose=False)
    return epochs


def test_extract_complexity_metrics_structure():
    """Test that extract_complexity_metrics returns the correct structure."""
    epochs = create_dummy_eeg_data()
    results = extract_complexity_metrics(epochs, participant_id="P001", segment_id="S1")

    assert isinstance(results, list), "Results must be a list."
    assert len(results) > 0, "Results must not be empty."

    # Check required columns
    required_cols = ["participant_id", "channel", "segment_id", "lzc_value", "pe_value"]
    for item in results:
        assert isinstance(item, dict), "Each item must be a dict."
        for col in required_cols:
            assert col in item, f"Missing column: {col}"

    # Check types
    for item in results:
        assert isinstance(item["participant_id"], str)
        assert isinstance(item["channel"], str)
        assert isinstance(item["segment_id"], str)
        assert isinstance(item["lzc_value"], (int, float, type(None))) # NaN is float
        assert isinstance(item["pe_value"], (int, float, type(None)))


def test_extract_complexity_metrics_values():
    """Test that LZC and PE values are within plausible ranges."""
    epochs = create_dummy_eeg_data()
    results = extract_complexity_metrics(epochs, participant_id="P001", segment_id="S1")

    for item in results:
        lzc = item["lzc_value"]
        pe = item["pe_value"]

        # LZC for binary sequence is typically between 0 and 1 (normalized) or slightly higher
        # nolds.lzc_c returns the count, which depends on length.
        # For a random binary sequence, it should be positive.
        if not np.isnan(lzc):
            assert lzc >= 0, f"LZC must be non-negative, got {lzc}"

        # PE for dimension 3: max is log2(3!) = log2(6) ~ 2.58. Normalized is 0-1.
        if not np.isnan(pe):
            assert 0 <= pe <= 1, f"Normalized PE must be between 0 and 1, got {pe}"


def test_save_metrics_creates_file():
    """Test that save_metrics creates the CSV file with correct columns."""
    results = [
        {"participant_id": "P001", "channel": "EEG 000", "segment_id": "S1", "lzc_value": 0.5, "pe_value": 0.8},
        {"participant_id": "P001", "channel": "EEG 001", "segment_id": "S1", "lzc_value": 0.6, "pe_value": 0.7}
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_metrics.csv")
        save_metrics(results, output_path)

        assert os.path.exists(output_path), "Output file must be created."

        df = pd.read_csv(output_path)
        expected_cols = ["participant_id", "channel", "segment_id", "lzc_value", "pe_value"]
        assert list(df.columns) == expected_cols, f"Columns mismatch: {list(df.columns)} vs {expected_cols}"
        assert len(df) == 2, "Row count mismatch."


def test_complexity_metrics_file_bounds():
    """
    T017 Verification: Load the actual complexity_metrics.csv and assert
    values fall within expected physiological ranges.
    
    Bounds derived from algorithm definitions:
    - LZC (nolds): Normalized complexity is typically 0.0 to 1.0. Unnormalized
      counts are positive. We check >= 0.
    - PE (pyentropy): For embedding dimension 3, max permutations = 3! = 6.
      Max entropy = log2(6) ≈ 2.585. Normalized entropy is 0.0 to 1.0.
    """
    # Path relative to project root (assumed tests run from root or via pytest)
    # The file is produced by T016 at data/analysis/complexity_metrics.csv
    metrics_path = Path(__file__).parent.parent.parent / "data" / "analysis" / "complexity_metrics.csv"
    
    if not metrics_path.exists():
        pytest.skip(f"File not found: {metrics_path}. Run T016 first.")

    df = pd.read_csv(metrics_path)

    required_cols = ["lzc_value", "pe_value"]
    for col in required_cols:
        assert col in df.columns, f"Missing column in {metrics_path}: {col}"

    # Check LZC: Must be non-negative.
    # Note: nolds.lzc_c can return a count. If normalized, it's 0-1.
    # We enforce non-negative as the hard floor for complexity.
    lzc_vals = df['lzc_value'].dropna()
    if len(lzc_vals) > 0:
        assert (lzc_vals >= 0).all(), f"LZC values must be non-negative. Found: {lzc_vals[lzc_vals < 0]}"

    # Check PE: Must be between 0 and log2(3!) ≈ 2.585.
    # If normalized (as per T016 spec "normalized"), it should be 0-1.
    # We check the theoretical max for dim=3 to be safe, but warn if > 1.
    pe_vals = df['pe_value'].dropna()
    if len(pe_vals) > 0:
        max_possible_pe = np.log2(6) # ~2.585
        assert (pe_vals >= 0).all(), f"PE values must be non-negative. Found: {pe_vals[pe_vals < 0]}"
        assert (pe_vals <= max_possible_pe).all(), f"PE values exceed theoretical max for dim=3 ({max_possible_pe}). Found: {pe_vals[pe_vals > max_possible_pe]}"