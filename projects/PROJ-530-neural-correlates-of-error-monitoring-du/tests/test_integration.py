"""
Integration tests for the preprocessing pipeline.

This module verifies that the full preprocessing pipeline runs successfully
on a synthetic subset of data and produces the expected artifacts.
"""

import os
import sys
import yaml
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.preprocess import process_eeg_data, save_preprocessing_log
from code.utils import set_global_seed
from code.logging_config import initialize_logging

# Set random seed for reproducibility
set_global_seed(42)

# Constants for test
TEST_N_PARTICIPANTS = 5
TEST_OUTPUT_DIR = project_root / "data" / "processed"
TEST_LOG_FILE = project_root / "data" / "preprocessing.yaml"

def generate_synthetic_eeg_data(n_participants: int = 5, n_channels: int = 32, 
                                n_samples: int = 2500, fs: int = 250):
    """
    Generate synthetic EEG data for testing purposes.
    
    This creates a minimal dataset that mimics the structure of real EEG data
    without requiring external downloads.
    
    Args:
        n_participants: Number of synthetic participants
        n_channels: Number of EEG channels
        n_samples: Number of time samples per trial
        fs: Sampling frequency in Hz
    
    Returns:
        Dictionary containing synthetic EEG data
    """
    import numpy as np
    
    data = {
        'participants': [],
        'fs': fs,
        'channels': [f'EEG{i:03d}' for i in range(n_channels)],
        'events': []
    }
    
    for p_id in range(n_participants):
        participant_data = {
            'id': f'sub-{p_id:03d}',
            'epochs': [],
            'error_events': []
        }
        
        # Generate synthetic epochs (2 seconds of data at 250Hz = 500 samples)
        n_epochs = 50
        for epoch_idx in range(n_epochs):
            # Simulate EEG signal with some noise and a potential MFN component
            time_axis = np.linspace(-0.5, 1.5, n_samples)  # -500ms to 1500ms
            signal = np.random.randn(n_channels, n_samples) * 10  # Baseline noise
            
            # Add a simulated MFN component for some epochs (error trials)
            if epoch_idx % 2 == 0:  # Every other epoch is an "error" trial
                # MFN: negative deflection around 250-300ms
                mf_time = time_axis - 0.25  # Shift to center at 250ms
                mf_component = np.exp(-0.5 * (mf_time / 0.1) ** 2)  # Gaussian kernel
                # Apply to central channels (simulated FCz, Cz, Fz)
                central_indices = [8, 16, 24]  # Approximate central channel indices
                for ch_idx in central_indices:
                    if ch_idx < n_channels:
                        signal[ch_idx, :] -= 5 * mf_component  # Negative deflection
            
            participant_data['epochs'].append({
                'epoch_id': f'epoch_{epoch_idx:03d}',
                'data': signal.tolist(),
                'time': time_axis.tolist(),
                'is_error': epoch_idx % 2 == 0,
                'error_magnitude': abs(np.random.randn() * 15) if epoch_idx % 2 == 0 else 0
            })
            
            # Add error event metadata
            if epoch_idx % 2 == 0:
                participant_data['error_events'].append({
                    'epoch_id': f'epoch_{epoch_idx:03d}',
                    'error_magnitude': participant_data['epochs'][-1]['error_magnitude'],
                    'timestamp': epoch_idx * 2.0  # Approximate timestamp in seconds
                })
        
        data['participants'].append(participant_data)
    
    return data

def test_full_preprocessing_pipeline_subset():
    """
    Run the full preprocessing pipeline on a synthetic subset (N=5) and verify:
    1. data/processed/ contains epoch files
    2. data/preprocessing.yaml is populated with filter/ICA parameters
    
    This is an integration test that exercises the entire preprocessing workflow.
    """
    # Initialize logging
    initialize_logging(project_root / "data" / "logs", "test_preprocessing")
    
    # Generate synthetic data
    print("Generating synthetic EEG data...")
    synthetic_data = generate_synthetic_eeg_data(n_participants=TEST_N_PARTICIPANTS)
    
    # Ensure output directories exist
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (project_root / "data" / "logs").mkdir(parents=True, exist_ok=True)
    
    # Run preprocessing pipeline
    print("Running preprocessing pipeline...")
    processed_results = process_eeg_data(
        raw_data=synthetic_data,
        output_dir=TEST_OUTPUT_DIR,
        log_file=TEST_LOG_FILE,
        filter_config={
            'lowcut': 1.0,
            'highcut': 40.0,
            'notch_freq': 60.0
        },
        ica_config={
            'n_components': 15,
            'random_state': 42
        }
    )
    
    # Verify results
    assert processed_results is not None, "Preprocessing pipeline returned None"
    assert 'participants' in processed_results, "Processed results missing 'participants' key"
    assert len(processed_results['participants']) == TEST_N_PARTICIPANTS, \
        f"Expected {TEST_N_PARTICIPANTS} participants, got {len(processed_results['participants'])}"
    
    # Verify output files exist
    assert TEST_OUTPUT_DIR.exists(), "Output directory does not exist"
    
    # Check for epoch files
    epoch_files = list(TEST_OUTPUT_DIR.glob("*.csv"))
    assert len(epoch_files) > 0, "No epoch files found in output directory"
    
    # Verify preprocessing log file exists and contains expected parameters
    assert TEST_LOG_FILE.exists(), "Preprocessing log file does not exist"
    
    with open(TEST_LOG_FILE, 'r') as f:
        log_data = yaml.safe_load(f)
    
    assert log_data is not None, "Preprocessing log is empty"
    assert 'filter_parameters' in log_data, "Filter parameters missing from log"
    assert 'ica_parameters' in log_data, "ICA parameters missing from log"
    assert 'components_removed' in log_data, "Removed components not logged"
    
    # Verify specific parameters are logged
    assert log_data['filter_parameters']['lowcut'] == 1.0
    assert log_data['filter_parameters']['highcut'] == 40.0
    assert log_data['filter_parameters']['notch_freq'] == 60.0
    
    # Verify ICA parameters
    assert log_data['ica_parameters']['n_components'] == 15
    assert log_data['ica_parameters']['random_state'] == 42
    
    # Verify components were logged (even if empty list)
    assert isinstance(log_data['components_removed'], list)
    
    print(f"✓ Successfully processed {TEST_N_PARTICIPANTS} participants")
    print(f"✓ Found {len(epoch_files)} epoch files in {TEST_OUTPUT_DIR}")
    print(f"✓ Preprocessing log saved to {TEST_LOG_FILE}")
    print("✓ All integration tests passed!")
    
    return True

if __name__ == "__main__":
    test_full_preprocessing_pipeline_subset()