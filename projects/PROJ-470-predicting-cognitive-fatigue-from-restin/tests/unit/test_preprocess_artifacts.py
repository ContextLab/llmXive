import os
import pytest
import pandas as pd
from pathlib import Path
import numpy as np
import mne
from datetime import datetime

from preprocess import reject_artifacts, load_config, setup_logger

@pytest.fixture
def sample_raw_data(tmp_path):
    """Create a sample MNE Raw object for testing."""
    # Create synthetic data: 256 Hz, 120 seconds, 5 channels
    sfreq = 256
    duration = 120
    n_channels = 5
    n_samples = int(sfreq * duration)
    
    # Generate white noise data
    data = np.random.randn(n_channels, n_samples) * 1e-6  # Scale to microvolts
    info = mne.create_info(n_channels, sfreq, ch_types='eeg')
    raw = mne.io.RawArray(data, info)
    
    return raw

@pytest.fixture
def logger():
    """Create a test logger."""
    return setup_logger('test_preprocess')

def test_artifact_rejection_amplitude(sample_raw_data, logger):
    """Test that high amplitude signals are rejected."""
    # Create signal with amplitude > 100uV
    high_amp_data = sample_raw_data.copy()
    high_amp_data._data *= 200  # Scale to exceed 100uV threshold
    
    exclusion_reasons = reject_artifacts(
        high_amp_data, 
        amplitude_threshold=100, 
        min_duration=120, 
        logger=logger, 
        participant_id='test_001'
    )[1]
    
    assert len(exclusion_reasons) == 1
    assert exclusion_reasons[0]['participant_id'] == 'test_001'
    assert 'amplitude > 100uV' in exclusion_reasons[0]['reason']
    assert 'timestamp' in exclusion_reasons[0]

def test_artifact_rejection_duration(sample_raw_data, logger):
    """Test that short duration signals are rejected."""
    # Create signal with duration < 120s
    short_data = sample_raw_data.copy()
    # Crop to 60 seconds
    short_data.crop(tmax=60)
    
    exclusion_reasons = reject_artifacts(
        short_data, 
        amplitude_threshold=100, 
        min_duration=120, 
        logger=logger, 
        participant_id='test_002'
    )[1]
    
    assert len(exclusion_reasons) == 1
    assert exclusion_reasons[0]['participant_id'] == 'test_002'
    assert 'segment < 120s' in exclusion_reasons[0]['reason']
    assert 'timestamp' in exclusion_reasons[0]

def test_artifact_rejection_accepts_valid(sample_raw_data, logger):
    """Test that valid signals are accepted."""
    exclusion_reasons = reject_artifacts(
        sample_raw_data, 
        amplitude_threshold=100, 
        min_duration=120, 
        logger=logger, 
        participant_id='test_003'
    )[1]
    
    assert len(exclusion_reasons) == 0

def test_exclusion_log_creation(tmp_path, sample_raw_data, logger):
    """Test that exclusion log is created with correct schema."""
    from utils.logging import save_exclusion_log_csv
    
    # Create test exclusions
    exclusions = [
        {
            'participant_id': 'test_001',
            'reason': 'amplitude > 100uV',
            'timestamp': datetime.now().isoformat()
        },
        {
            'participant_id': 'test_002',
            'reason': 'segment < 120s',
            'timestamp': datetime.now().isoformat()
        }
    ]
    
    log_path = tmp_path / 'exclusion_log.csv'
    save_exclusion_log_csv(exclusions, str(log_path))
    
    assert log_path.exists()
    
    # Verify CSV content
    df = pd.read_csv(log_path)
    assert 'participant_id' in df.columns
    assert 'reason' in df.columns
    assert 'timestamp' in df.columns
    assert len(df) == 2
    
    # Verify valid reasons
    valid_reasons = ['amplitude > 100uV', 'segment < 120s']
    for reason in df['reason']:
        assert reason in valid_reasons