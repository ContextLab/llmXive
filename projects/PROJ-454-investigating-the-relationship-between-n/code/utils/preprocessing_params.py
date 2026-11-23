"""
Preprocessing parameters for EEG pipeline.

This module provides default parameters for EEG preprocessing steps.
These can be overridden via environment variables or config files.
"""
from typing import Dict, List
import os

DEFAULT_PREPROCESSING_PARAMS: Dict = {
    'l_freq': 1.0,
    'h_freq': 45.0,
    'notch_freqs': [50.0, 60.0],
    'bad_channel_threshold': 3.0,
    'n_ica_components': 20,
    'epoch_duration': 2.0,
}

DEFAULT_DATA_QUALITY_THRESHOLDS: Dict = {
    'min_valid_eeg_seconds': 60,
    'max_corrupted_segments_percent': 20,
    'min_snr_db': 5,
}

def get_preprocessing_params() -> Dict:
    """Get preprocessing parameters from environment or defaults."""
    params = DEFAULT_PREPROCESSING_PARAMS.copy()
    
    # Override with environment variables if present
    if os.getenv('PREPROCESS_L_FREQ'):
        params['l_freq'] = float(os.getenv('PREPROCESS_L_FREQ'))
    if os.getenv('PREPROCESS_H_FREQ'):
        params['h_freq'] = float(os.getenv('PREPROCESS_H_FREQ'))
    if os.getenv('PREPROCESS_NOTCH_FREQS'):
        params['notch_freqs'] = [float(x) for x in os.getenv('PREPROCESS_NOTCH_FREQS').split(',')]
    if os.getenv('PREPROCESS_BAD_THRESHOLD'):
        params['bad_channel_threshold'] = float(os.getenv('PREPROCESS_BAD_THRESHOLD'))
    if os.getenv('PREPROCESS_N_ICA'):
        params['n_ica_components'] = int(os.getenv('PREPROCESS_N_ICA'))
    if os.getenv('PREPROCESS_EPOCH_DURATION'):
        params['epoch_duration'] = float(os.getenv('PREPROCESS_EPOCH_DURATION'))
    
    return params

def get_data_quality_thresholds() -> Dict:
    """Get data quality thresholds from environment or defaults."""
    thresholds = DEFAULT_DATA_QUALITY_THRESHOLDS.copy()
    
    if os.getenv('MIN_VALID_EEG_SECONDS'):
        thresholds['min_valid_eeg_seconds'] = int(os.getenv('MIN_VALID_EEG_SECONDS'))
    if os.getenv('MAX_CORRUPTED_PERCENT'):
        thresholds['max_corrupted_segments_percent'] = float(os.getenv('MAX_CORRUPTED_PERCENT'))
    if os.getenv('MIN_SNR_DB'):
        thresholds['min_snr_db'] = float(os.getenv('MIN_SNR_DB'))
    
    return thresholds
