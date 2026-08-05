import pytest
import os
import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from features import main as features_main
from features import calculate_permutation_entropy, calculate_lempel_ziv_complexity

def test_pe_integration():
    """
    Integration test for Permutation Entropy calculation.
    This test verifies that the feature extraction pipeline can run
    and produce valid output files when given proper input data.
    """
    # This is a basic integration test that verifies the functions work
    # together correctly. A full integration test would require the actual
    # preprocessed EEG data from T011.
    
    # Test with synthetic data that mimics the structure of real EEG
    np.random.seed(42)
    sampling_rate = 256
    duration = 120
    n_samples = sampling_rate * duration
    
    # Simulate multi-channel EEG data (10 channels)
    n_channels = 10
    eeg_data = np.random.normal(0, 1e-5, (n_channels, n_samples))
    
    # Calculate PE for each channel
    pe_values = []
    for i in range(n_channels):
        pe = calculate_permutation_entropy(eeg_data[i])
        pe_values.append(pe)
        assert isinstance(pe, float), f"PE for channel {i} should be a float"
        assert not np.isnan(pe), f"PE for channel {i} should not be NaN"
        assert 0 <= pe <= 1, f"PE for channel {i} should be in [0, 1]"
    
    # Verify that PE values are reasonably consistent for white noise
    mean_pe = np.mean(pe_values)
    std_pe = np.std(pe_values)
    
    # For white noise, PE should be high and relatively consistent
    assert mean_pe > 0.5, "Mean PE for white noise should be > 0.5"
    assert std_pe < 0.1, "PE values for white noise should be relatively consistent"
    
    print(f"Integration test passed. Mean PE: {mean_pe:.4f}, Std PE: {std_pe:.4f}")

def test_lzc_integration():
    """
    Integration test for LZC calculation.
    Similar to PE integration test.
    """
    np.random.seed(42)
    sampling_rate = 256
    duration = 120
    n_samples = sampling_rate * duration
    
    # Simulate multi-channel EEG data
    n_channels = 10
    eeg_data = np.random.normal(0, 1e-5, (n_channels, n_samples))
    
    # Calculate LZC for each channel
    lzc_values = []
    for i in range(n_channels):
        lzc = calculate_lempel_ziv_complexity(eeg_data[i], sampling_rate)
        lzc_values.append(lzc)
        assert isinstance(lzc, float), f"LZC for channel {i} should be a float"
        assert not np.isnan(lzc), f"LZC for channel {i} should not be NaN"
        assert lzc >= 0, f"LZC for channel {i} should be non-negative"
    
    # Verify consistency
    mean_lzc = np.mean(lzc_values)
    std_lzc = np.std(lzc_values)
    
    assert mean_lzc > 0, "Mean LZC should be > 0"
    assert std_lzc < 0.1, "LZC values should be relatively consistent"
    
    print(f"LZC integration test passed. Mean LZC: {mean_lzc:.4f}, Std LZC: {std_lzc:.4f}")

@pytest.mark.skipif(not Path('data/processed/cleaned_eeg.fif').exists(), 
                   reason="Preprocessed EEG data not available")
def test_features_pipeline_end_to_end():
    """
    End-to-end test of the features pipeline.
    This test requires the preprocessed EEG data from T011.
    """
    # Run the main function
    # Note: This will create both lzc_metrics.csv and pe_metrics.csv
    features_main()
    
    # Verify output files exist
    lzc_path = Path('data/processed/lzc_metrics.csv')
    pe_path = Path('data/processed/pe_metrics.csv')
    
    assert lzc_path.exists(), "LZC metrics file should exist"
    assert pe_path.exists(), "PE metrics file should exist"
    
    # Verify file contents
    lzc_df = pd.read_csv(lzc_path)
    pe_df = pd.read_csv(pe_path)
    
    # Check schema
    assert list(lzc_df.columns) == ['participant_id', 'channel', 'lzc_value'], \
        "LZC metrics should have correct columns"
    assert list(pe_df.columns) == ['participant_id', 'channel', 'pe_value'], \
        "PE metrics should have correct columns"
    
    # Check non-empty
    assert len(lzc_df) > 0, "LZC metrics file should not be empty"
    assert len(pe_df) > 0, "PE metrics file should not be empty"
    
    # Check for valid values
    assert not lzc_df['lzc_value'].isna().any(), "LZC values should not contain NaN"
    assert not pe_df['pe_value'].isna().any(), "PE values should not contain NaN"
    
    print("End-to-end features pipeline test passed.")
    print(f"LZC metrics: {len(lzc_df)} rows")
    print(f"PE metrics: {len(pe_df)} rows")