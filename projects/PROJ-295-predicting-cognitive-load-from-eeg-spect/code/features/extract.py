import numpy as np
import mne
from typing import Dict, List, Optional, Tuple
import pandas as pd
import os
import sys
import hashlib
import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
EPSILON = 1e-9
THETA_BAND = (4, 7)
ALPHA_BAND = (8, 12)

def load_epochs_chunked(epoch_file_pattern: str, chunk_size: int = 100):
    """
    Load epochs from files in chunks to manage memory.
    This is a helper to ensure memory safety during PSD computation on large datasets.
    """
    files = sorted(glob.glob(epoch_file_pattern))
    if not files:
        raise FileNotFoundError(f"No epoch files found matching pattern: {epoch_file_pattern}")
    
    current_epochs = None
    
    for i in range(0, len(files), chunk_size):
        chunk_files = files[i:i+chunk_size]
        logger.info(f"Loading chunk {i//chunk_size + 1}/{(len(files)+chunk_size-1)//chunk_size}...")
        
        chunk_epochs = []
        for f in chunk_files:
            try:
                epochs = mne.read_epochs(f)
                chunk_epochs.append(epochs)
            except Exception as e:
                logger.warning(f"Failed to load {f}: {e}")
                continue
        
        if chunk_epochs:
            # Concatenate epochs in the chunk
            combined = mne.concatenate_epochs(chunk_epochs)
            if current_epochs is None:
                current_epochs = combined
            else:
                current_epochs = mne.concatenate_epochs([current_epochs, combined])
        
        # Yield processed chunk or accumulate for final return if needed
        # For this task, we assume the caller handles chunking or we return the full accumulated set
        # if memory permits. For T024, we assume the data is already loaded or handled by caller.
        
    return current_epochs

def compute_psd_welch(epochs: mne.Epochs, picks: Optional[List[str]] = None, 
                      fmin: float = 1.0, fmax: float = 45.0, n_fft: int = 256) -> np.ndarray:
    """
    Compute Power Spectral Density using Welch's method for the given epochs.
    
    Args:
        epochs: MNE Epochs object.
        picks: List of channel names to include. If None, uses all data channels.
        fmin: Minimum frequency.
        fmax: Maximum frequency.
        n_fft: FFT window size.
        
    Returns:
        psd: Array of shape (n_epochs, n_channels, n_freqs)
        freqs: Array of frequencies.
    """
    if picks is None:
        picks = mne.pick_types(epochs.info, eeg=True, exclude='bads')
        
    psd, freqs = mne.time_frequency.psd_welch(
        epochs, picks=picks, fmin=fmin, fmax=fmax, n_fft=n_fft, verbose=False
    )
    return psd, freqs

def extract_band_power(psd: np.ndarray, freqs: np.ndarray, band: Tuple[float, float]) -> np.ndarray:
    """
    Extract mean power within a specific frequency band.
    
    Args:
        psd: Power spectral density array.
        freqs: Frequency array.
        band: Tuple (fmin, fmax).
        
    Returns:
        mean_power: Mean power per epoch and channel.
    """
    fmin, fmax = band
    mask = (freqs >= fmin) & (freqs <= fmax)
    if not np.any(mask):
        raise ValueError(f"No frequencies found in band {band} for range {freqs[0]}-{freqs[-1]}")
    
    band_psd = psd[:, :, mask]
    mean_power = np.mean(band_psd, axis=2)
    return mean_power

def compute_theta_alpha_ratio(theta_power: np.ndarray, alpha_power: np.ndarray) -> np.ndarray:
    """
    Compute the Theta/Alpha Ratio (TAR) to handle division-by-zero safely.
    
    This function implements the edge case logic:
    ratio = theta_power / (alpha_power + EPSILON)
    
    Args:
        theta_power: Array of mean theta power (4-7 Hz).
        alpha_power: Array of mean alpha power (8-12 Hz).
        
    Returns:
        tar: Array of Theta/Alpha Ratios.
    """
    if theta_power.shape != alpha_power.shape:
        raise ValueError(f"Shape mismatch: theta_power {theta_power.shape} != alpha_power {alpha_power.shape}")
    
    # Apply the epsilon to prevent division by zero
    # Using EPSILON = 1e-9 as specified in the task
    denominator = alpha_power + EPSILON
    tar = theta_power / denominator
    
    return tar

def extract_features(epochs: mne.Epochs, picks: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Extract spectral features (Theta, Alpha, TAR) for all epochs and channels.
    
    Args:
        epochs: MNE Epochs object.
        picks: List of channel names.
        
    Returns:
        df: DataFrame with columns: epoch_id, channel, theta_power, alpha_power, tar
    """
    psd, freqs = compute_psd_welch(epochs, picks=picks)
    
    theta_power = extract_band_power(psd, freqs, THETA_BAND)
    alpha_power = extract_band_power(psd, freqs, ALPHA_BAND)
    
    tar = compute_theta_alpha_ratio(theta_power, alpha_power)
    
    n_epochs, n_channels, _ = psd.shape
    channel_names = [epochs.ch_names[i] for i in mne.pick_types(epochs.info, eeg=True, exclude='bads') if picks is None or epochs.ch_names[i] in picks]
    
    records = []
    for ep_idx in range(n_epochs):
        for ch_idx in range(n_channels):
            records.append({
                'epoch_id': ep_idx,
                'channel': channel_names[ch_idx],
                'theta_power': float(theta_power[ep_idx, ch_idx]),
                'alpha_power': float(alpha_power[ep_idx, ch_idx]),
                'tar': float(tar[ep_idx, ch_idx])
            })
    
    return pd.DataFrame(records)

def calculate_file_checksum(filepath: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_checksums(output_path: str, state_file: str = "state/pipeline_state.yaml"):
    """
    Update the pipeline state file with the checksum of the output artifact.
    """
    import yaml
    
    if not os.path.exists(state_file):
        logger.warning(f"State file {state_file} not found. Skipping update.")
        return

    checksum = calculate_file_checksum(output_path)
    
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)
        
    if 'artifacts' not in state:
        state['artifacts'] = {}
        
    state['artifacts']['feature_extraction'] = {
        'path': output_path,
        'checksum': checksum,
        'updated_at': datetime.datetime.now().isoformat()
    }
    
    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    logger.info(f"Updated state file with checksum for {output_path}")

def main():
    """
    Main entry point for feature extraction.
    Expects preprocessed epochs to be available in data/processed/
    """
    import glob
    
    # Configuration paths (adjust based on project structure)
    epoch_pattern = "data/processed/clean_epochs/*.fif"
    output_path = "data/processed/feature_matrix.csv"
    
    if not os.path.exists("data/processed/clean_epochs"):
        logger.error("Preprocessed epochs directory not found. Please run preprocessing first.")
        sys.exit(1)
        
    files = glob.glob(epoch_pattern)
    if not files:
        logger.error(f"No epoch files found at {epoch_pattern}")
        sys.exit(1)
        
    logger.info(f"Found {len(files)} epoch files.")
    
    # Load and process
    # Note: In a real scenario, we might process chunk by chunk if memory is tight.
    # For this implementation, we assume the dataset fits in memory or is small enough for the demo.
    # If memory is an issue, the load_epochs_chunked function should be integrated here.
    
    try:
        all_epochs = mne.read_epochs(files[0]) # Load first to check structure
        # Concatenate all if needed, or process one by one
        if len(files) > 1:
            for f in files[1:]:
                all_epochs = mne.concatenate_epochs([all_epochs, mne.read_epochs(f)])
        
        logger.info(f"Loaded {len(all_epochs)} epochs.")
        
        df = extract_features(all_epochs)
        
        # Save to CSV
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Features saved to {output_path}")
        
        # Update state
        update_state_checksums(output_path)
        
    except Exception as e:
        logger.error(f"Error during feature extraction: {e}")
        raise

if __name__ == "__main__":
    main()