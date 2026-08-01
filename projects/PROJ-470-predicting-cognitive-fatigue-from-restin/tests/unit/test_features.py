import pytest
import numpy as np
import os
import sys
from pathlib import Path

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from features import calculate_lzc, calculate_permutation_entropy, save_metrics_to_csv

def test_lzc_known_signal():
    """
    Unit test for LZC calculation on a synthetic white noise signal.
    Per T015 verification:
    - Generate synthetic signal (white noise, seed=42, amplitude=1, 256 Hz, 120s)
    - Assert output is a valid numeric float, positive, and not NaN.
    """
    # Generate synthetic signal
    np.random.seed(42)
    duration = 120  # seconds
    sampling_rate = 256  # Hz
    n_samples = duration * sampling_rate
    signal = np.random.normal(loc=0, scale=1, size=n_samples)
    
    # Calculate LZC
    lzc_value = calculate_lzc(signal)
    
    # Assertions
    assert isinstance(lzc_value, float), "LZC value must be a float"
    assert not np.isnan(lzc_value), "LZC value must not be NaN"
    assert lzc_value >= 0, "LZC value must be non-negative"
    # White noise should have high complexity, typically > 0.5 normalized
    # We don't assert a specific value as LZC can vary, but it must be valid.

def test_pe_known_signal():
    """
    Unit test for Permutation Entropy on a synthetic white noise signal.
    Per T016 verification (relevant for features.py):
    - Generate synthetic signal (white noise, seed=42, amplitude=1, 256 Hz, 120s, order=3, delay=1)
    - Assert output is a valid numeric float, positive, and not NaN.
    """
    # Generate synthetic signal
    np.random.seed(42)
    duration = 120  # seconds
    sampling_rate = 256  # Hz
    n_samples = duration * sampling_rate
    signal = np.random.normal(loc=0, scale=1, size=n_samples)
    
    # Calculate PE
    pe_value = calculate_permutation_entropy(signal, order=3, delay=1)
    
    # Assertions
    assert isinstance(pe_value, float), "PE value must be a float"
    assert not np.isnan(pe_value), "PE value must not be NaN"
    assert pe_value >= 0, "PE value must be non-negative"
    # Normalized PE should be between 0 and 1
    assert pe_value <= 1.0, "Normalized PE value must be <= 1.0"

def test_save_metrics_to_csv():
    """
    Unit test for saving metrics to CSV.
    """
    import tempfile
    import pandas as pd

    # Mock results
    results = [
        {'participant_id': 'P001', 'channel': 'Fz', 'metric_type': 'LZC', 'value': 0.65},
        {'participant_id': 'P001', 'channel': 'Cz', 'metric_type': 'LZC', 'value': 0.62},
        {'participant_id': 'P002', 'channel': 'Fz', 'metric_type': 'LZC', 'value': 0.68},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_lzc_metrics.csv')
        save_metrics_to_csv(results, output_path, metric_type='LZC')
        
        # Verify file exists
        assert os.path.exists(output_path), "CSV file should be created"
        
        # Verify content
        df = pd.read_csv(output_path)
        assert 'participant_id' in df.columns, "CSV must contain 'participant_id' column"
        assert 'channel' in df.columns, "CSV must contain 'channel' column"
        assert 'lzc_value' in df.columns, "CSV must contain 'lzc_value' column"
        assert len(df) == 3, "CSV should contain 3 rows"
        assert df['lzc_value'].dtype in [np.float64, np.float32], "lzc_value should be numeric"