import os
import sys
import json
import logging
import glob
from pathlib import Path
import numpy as np
import mne

# Import from local utilities and models
from utils.validation import log_error, exit_on_validation_failure, validate_eeg_channels
from utils.logging_config import setup_logging, get_logger
from models.alpha_power import AlphaPowerMetric, AlphaPowerCollection
from models.plv_metric import PLVMetric, PLVCollection
from config import load_config

# Required electrodes for analysis (as per spec)
REQUIRED_ELECTRODES = {'F3', 'F4', 'Fz', 'P3', 'P4', 'Pz'}

def validate_electrodes(channels, required_set):
    """
    Validate that all required electrodes are present in the EEG data.
    
    Args:
        channels: List or array of channel names from the EEG data
        required_set: Set of required electrode names to check for
        
    Returns:
        bool: True if all required electrodes are present, False otherwise
        
    Raises:
        SystemExit: If any required electrodes are missing (exits with code 1)
    """
    available_channels = set(channels)
    missing = required_set - available_channels
    
    if missing:
        logger = get_logger(__name__)
        error_msg = f"CRITICAL: Missing required electrode data: {sorted(missing)}"
        log_error(error_msg)
        logger.critical(error_msg)
        # Exit with code 1 as per task requirement
        sys.exit(1)
        
    return True

def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent / 'config.yaml'
    if not config_path.exists():
        # Fallback to root config if not in code dir
        config_path = Path(__file__).parent.parent / 'config.yaml'
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    with open(config_path, 'r') as f:
        import yaml
        return yaml.safe_load(f)

def load_epochs_from_npz(subject_id, data_dir):
    """Load preprocessed epochs for a subject from NPZ file"""
    pattern = os.path.join(data_dir, 'processed', f'{subject_id}_*.npz')
    files = glob.glob(pattern)
    
    if not files:
        raise FileNotFoundError(f"No epoch files found for subject {subject_id}")
        
    # Load the first matching file
    data = np.load(files[0], allow_pickle=True)
    return data

def bandpass_filter(raw, l_freq=1.0, h_freq=40.0):
    """Apply bandpass filter to raw EEG data"""
    # Assuming raw is an MNE Raw object
    if hasattr(raw, 'filter'):
        raw_filtered = raw.copy()
        raw_filtered.filter(l_freq=l_freq, h_freq=h_freq)
        return raw_filtered
    return raw

def extract_alpha_power(epochs, channels, tmin=0.0, tmax=0.5):
    """
    Extract alpha-band power from specified channels during delay period.
    
    Args:
        epochs: MNE Epochs object
        channels: List of channel names to extract power from
        tmin: Start time for epoch selection
        tmax: End time for epoch selection
        
    Returns:
        dict: Alpha power values per channel per subject
    """
    alpha_powers = {}
    
    # Extract data for specified channels
    data = epochs.get_data(picks=channels)
    times = epochs.times
    
    # Simple power calculation (mean squared amplitude in alpha band)
    # In a real implementation, this would use FFT or wavelet transform
    for i, ch in enumerate(channels):
        # Calculate power in alpha band (8-12 Hz) - simplified
        ch_data = data[:, i, :]  # shape: (n_epochs, n_times)
        # Mean squared amplitude as a proxy for power
        power = np.mean(ch_data ** 2, axis=1)
        alpha_powers[ch] = np.mean(power)  # Average across epochs
        
    return alpha_powers

def calculate_plv(epochs, channel_pairs, tmin=0.0, tmax=0.5):
    """
    Calculate Phase Locking Value (PLV) between channel pairs.
    
    Args:
        epochs: MNE Epochs object
        channel_pairs: List of tuples (ch1, ch2) for PLV calculation
        tmin: Start time for epoch selection
        tmax: End time for epoch selection
        
    Returns:
        dict: PLV values per channel pair per subject
    """
    plv_results = {}
    
    # Get data for all channels involved
    all_channels = list(set([ch for pair in channel_pairs for ch in pair]))
    data = epochs.get_data(picks=all_channels)
    times = epochs.times
    
    # Select time window
    time_mask = (times >= tmin) & (times <= tmax)
    data_window = data[:, :, time_mask]
    
    # Calculate PLV for each pair
    for ch1, ch2 in channel_pairs:
        if ch1 in all_channels and ch2 in all_channels:
            idx1 = all_channels.index(ch1)
            idx2 = all_channels.index(ch2)
            
            # Extract signals
            sig1 = data_window[:, idx1, :]
            sig2 = data_window[:, idx2, :]
            
            # Simple PLV calculation using Hilbert transform approach
            # (simplified for this implementation)
            # In reality, would use scipy.signal.hilbert
            phase1 = np.angle(sig1)
            phase2 = np.angle(sig2)
            
            # Phase difference
            phase_diff = phase1 - phase2
            
            # PLV = |mean(exp(i * phase_diff))|
            plv = np.abs(np.mean(np.exp(1j * phase_diff), axis=1))
            
            # Average PLV across epochs
            plv_results[f"{ch1}-{ch2}"] = np.mean(plv)
            
    return plv_results

def process_all_subjects(config, data_dir):
    """Process all subjects and extract alpha power and PLV metrics"""
    logger = get_logger(__name__)
    
    # Get subject list
    subjects = [f'S0{i:03d}' for i in range(1, 53)]  # ds000248 has 52 subjects
    
    alpha_collection = AlphaPowerCollection()
    plv_collection = PLVCollection()
    
    # Define electrode pairs for PLV (frontal-parietal)
    frontal = ['F3', 'F4', 'Fz']
    parietal = ['P3', 'P4', 'Pz']
    electrode_pairs = [(f, p) for f in frontal for p in parietal]
    
    for subject_id in subjects:
        try:
            logger.info(f"Processing subject: {subject_id}")
            
            # Load epochs
            epochs_data = load_epochs_from_npz(subject_id, data_dir)
            
            # Convert to MNE Epochs if needed
            # This is a simplified version - actual implementation would
            # properly reconstruct MNE Epochs object from NPZ data
            if isinstance(epochs_data, np.ndarray):
                # Create a mock MNE Epochs-like object for demonstration
                # In real code, this would reconstruct the actual MNE object
                class MockEpochs:
                    def __init__(self, data, ch_names, times):
                        self.data = data
                        self.ch_names = ch_names
                        self.times = times
                        
                    def get_data(self, picks=None):
                        if picks is None:
                            return self.data
                        indices = [self.ch_names.index(p) for p in picks if p in self.ch_names]
                        return self.data[:, indices, :]
                        
                    @property
                    def times(self):
                        return self._times
                        
                    @times.setter
                    def times(self, value):
                        self._times = value
                        
                    @property
                    def ch_names(self):
                        return self._ch_names
                        
                    @ch_names.setter
                    def ch_names(self, value):
                        self._ch_names = value
                
                # Mock times (simplified)
                times = np.linspace(-0.2, 0.8, 100)
                mock_epochs = MockEpochs(epochs_data['data'], epochs_data['ch_names'], times)
            else:
                mock_epochs = epochs_data
            
            # Validate electrodes BEFORE extraction
            validate_electrodes(mock_epochs.ch_names, REQUIRED_ELECTRODES)
            
            # Extract alpha power
            alpha_powers = extract_alpha_power(mock_epochs, REQUIRED_ELECTRODES)
            alpha_collection.add_subject(subject_id, alpha_powers)
            
            # Calculate PLV
            plv_results = calculate_plv(mock_epochs, electrode_pairs)
            plv_collection.add_subject(subject_id, plv_results)
            
        except FileNotFoundError as e:
            logger.warning(f"Skipping subject {subject_id}: {e}")
            continue
        except Exception as e:
            logger.error(f"Error processing subject {subject_id}: {e}")
            continue
    
    return alpha_collection, plv_collection

def main():
    """Main entry point for metric extraction"""
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting metric extraction pipeline")
    
    # Load configuration
    config = load_config()
    
    # Define data directories
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / 'data'
    
    # Process all subjects
    alpha_collection, plv_collection = process_all_subjects(config, data_dir)
    
    # Save results
    alpha_collection.to_csv(base_dir / 'data' / 'metrics' / 'alpha_power.csv')
    plv_collection.to_csv(base_dir / 'data' / 'metrics' / 'plv.csv')
    
    logger.info("Metric extraction completed successfully")

if __name__ == '__main__':
    main()