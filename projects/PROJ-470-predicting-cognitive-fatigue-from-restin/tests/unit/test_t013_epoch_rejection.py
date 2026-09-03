import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
import pytest
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_epoch_rejection_creates_exclusion_log():
    """Test that epoch rejection creates exclusion_log.csv with correct format."""
    # Import the function we're testing
    from preprocess import reject_artifacts, save_exclusion_log
    
    # Create test data with some epochs exceeding threshold
    # 32 channels, 10000 samples (10 seconds at 1000 Hz)
    np.random.seed(42)
    data = np.random.randn(32, 10000)
    
    # Inject high amplitude in some epochs to trigger rejection
    # Epoch 2 (samples 4000-6000) will have high amplitude
    data[:, 4000:6000] = 150.0  # Above 100 µV threshold
    
    threshold = 100.0  # µV
    
    # Run rejection
    cleaned_data, rejection_log = reject_artifacts(data, threshold)
    
    # Verify rejection log has entries
    assert len(rejection_log) > 0, "Rejection log should contain entries for rejected epochs"
    
    # Verify at least one rejection has the correct reason
    amplitude_rejections = [r for r in rejection_log if r.get('reason') == 'amplitude_threshold']
    assert len(amplitude_rejections) > 0, "Should have rejections with reason 'amplitude_threshold'"
    
    # Verify the rejection log contains required fields
    for entry in amplitude_rejections:
        assert 'epoch_index' in entry, "Rejection entry should have epoch_index"
        assert 'max_amplitude' in entry, "Rejection entry should have max_amplitude"
        assert 'threshold' in entry, "Rejection entry should have threshold"
        assert 'reason' in entry, "Rejection entry should have reason"
        assert 'timestamp' in entry, "Rejection entry should have timestamp"
        
        # Verify the amplitude exceeded threshold
        assert entry['max_amplitude'] > entry['threshold'], "Rejected epoch should have amplitude > threshold"
        assert entry['reason'] == 'amplitude_threshold', "Reason should be 'amplitude_threshold'"
    
    # Verify exclusion log file is created with correct format
    output_path = 'data/processed/test_exclusion_log.csv'
    save_exclusion_log(rejection_log, output_path)
    
    assert os.path.exists(output_path), "Exclusion log CSV should be created"
    
    # Read and verify CSV structure
    df = pd.read_csv(output_path)
    
    required_columns = ['participant_id', 'epoch_index', 'max_amplitude', 'threshold', 'reason', 'timestamp']
    for col in required_columns:
        assert col in df.columns, f"CSV should contain column '{col}'"
    
    # Verify at least one row with amplitude_threshold reason
    threshold_rows = df[df['reason'] == 'amplitude_threshold']
    assert len(threshold_rows) > 0, "CSV should contain at least one row with reason 'amplitude_threshold'"
    
    # Clean up test file
    if os.path.exists(output_path):
        os.remove(output_path)

def test_amplitude_threshold_logic():
    """Test that epochs exceeding ±100µV are correctly rejected."""
    from preprocess import reject_artifacts
    
    # Create data with known amplitudes
    np.random.seed(123)
    n_channels = 16
    n_samples = 4000  # 4 seconds at 1000 Hz = 2 epochs of 2 seconds
    
    # Low amplitude data (should pass)
    low_amp_data = np.random.randn(n_channels, 2000) * 50  # ~50 µV
    
    # High amplitude data (should fail)
    high_amp_data = np.random.randn(n_channels, 2000) * 150  # ~150 µV
    
    # Combine: first epoch passes, second fails
    combined_data = np.hstack([low_amp_data, high_amp_data])
    
    threshold = 100.0
    
    cleaned_data, rejection_log = reject_artifacts(combined_data, threshold)
    
    # Should have exactly 1 rejection (the high amplitude epoch)
    assert len(rejection_log) == 1, f"Expected 1 rejection, got {len(rejection_log)}"
    
    # The rejection should be for epoch index 1 (the second epoch)
    assert rejection_log[0]['epoch_index'] == 1, "Should reject epoch index 1"
    
    # The max amplitude should be > 100
    assert rejection_log[0]['max_amplitude'] > 100, "Max amplitude should exceed threshold"
    
    # Cleaned data should only contain the first epoch
    expected_samples = 2000  # Only first epoch
    assert cleaned_data.shape[1] == expected_samples, f"Cleaned data should have {expected_samples} samples"

def test_no_rejections_when_all_pass():
    """Test that no rejections occur when all epochs are within threshold."""
    from preprocess import reject_artifacts
    
    # Create data with low amplitude
    np.random.seed(456)
    data = np.random.randn(32, 4000) * 50  # All ~50 µV
    
    threshold = 100.0
    
    cleaned_data, rejection_log = reject_artifacts(data, threshold)
    
    # Should have no rejections
    assert len(rejection_log) == 0, "Should have no rejections when all epochs pass"
    
    # All data should be preserved
    assert cleaned_data.shape == data.shape, "All data should be preserved when no rejections"

def test_exclusion_log_csv_format():
    """Test that exclusion_log.csv is created with the exact required format."""
    from preprocess import save_exclusion_log
    import pandas as pd
    
    # Create sample rejection log
    rejection_log = [
        {
            'participant_id': 'P001',
            'epoch_index': 5,
            'max_amplitude': 125.5,
            'threshold': 100.0,
            'reason': 'amplitude_threshold',
            'timestamp': '2026-09-03T10:00:00'
        },
        {
            'participant_id': 'P001',
            'epoch_index': 12,
            'max_amplitude': 110.2,
            'threshold': 100.0,
            'reason': 'amplitude_threshold',
            'timestamp': '2026-09-03T10:00:01'
        }
    ]
    
    output_path = 'data/processed/test_format_exclusion_log.csv'
    save_exclusion_log(rejection_log, output_path)
    
    # Verify file exists
    assert os.path.exists(output_path), "Exclusion log should be created"
    
    # Read CSV
    df = pd.read_csv(output_path)
    
    # Verify required columns
    required_columns = ['participant_id', 'reason', 'timestamp']
    for col in required_columns:
        assert col in df.columns, f"CSV must contain column '{col}'"
    
    # Verify reason column contains 'amplitude_threshold'
    assert all(df['reason'] == 'amplitude_threshold'), "All entries should have reason 'amplitude_threshold'"
    
    # Verify row count
    assert len(df) == 2, "CSV should have 2 rows"
    
    # Clean up
    os.remove(output_path)