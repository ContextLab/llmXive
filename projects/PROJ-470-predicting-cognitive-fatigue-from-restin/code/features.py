import os
import sys
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import mne

# Import Lempel-Ziv complexity implementation
try:
    from lempel_ziv import lzw_complexity
except ImportError:
    # Fallback to a simple implementation if the package is not available
    # This ensures the script runs even if the specific package version varies
    def lzw_complexity(binary_sequence):
        """
        Calculates the Lempel-Ziv complexity of a binary sequence.
        This is a standard implementation used when external packages are unavailable.
        """
        if not isinstance(binary_sequence, (list, np.ndarray)):
            binary_sequence = list(binary_sequence)
        
        n = len(binary_sequence)
        if n == 0:
            return 0.0
        
        lzw = 0
        current_substring = ""
        current_set = set()
        current_set.add("")
        
        for i, bit in enumerate(binary_sequence):
            current_substring += str(bit)
            if current_substring not in current_set:
                lzw += 1
                current_set.add(current_substring)
                # Reset current substring to the last character to start new pattern
                current_substring = str(bit)
                current_set.add(current_substring)
        
        # Normalize by length
        if n == 0:
            return 0.0
        # Standard normalization for LZ76/78
        c = lzw
        return c / (n / np.log2(n + 1)) if n > 1 else 0.0

def load_config(config_path="code/config.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name, log_file=None, level=logging.INFO):
    """Set up a logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def calculate_lempel_ziv_complexity(signal, threshold=0.5):
    """
    Calculate Lempel-Ziv Complexity for a continuous signal.
    
    Args:
        signal: 1D numpy array of EEG data.
        threshold: Threshold for binarization (default: median).
    
    Returns:
        float: Normalized Lempel-Ziv complexity value.
    """
    if len(signal) == 0:
        return 0.0
    
    # Binarize the signal (0 if below threshold, 1 if above)
    # Using median as the threshold is common for EEG
    if threshold is None:
        threshold = np.median(signal)
    
    binary_signal = (signal > threshold).astype(int)
    
    # Calculate LZC
    try:
        # Try to use the external package if available
        from lempel_ziv import lzw_complexity
        lzc = lzw_complexity(binary_signal)
    except ImportError:
        # Use local implementation
        lzc = lzw_complexity(binary_signal)
    
    return float(lzc)

def process_eeg_segments(raw_data, config, logger):
    """
    Process EEG segments to calculate LZC per channel per participant.
    
    Args:
        raw_data: List of mne.io.Raw objects or a single Raw object.
        config: Configuration dictionary.
        logger: Logger instance.
    
    Returns:
        list: List of dictionaries containing participant_id, channel, lzc_value.
    """
    results = []
    
    # Ensure raw_data is a list
    if not isinstance(raw_data, list):
        raw_data = [raw_data]
    
    for idx, raw in enumerate(raw_data):
        # Determine participant ID
        # Try to extract from filename or use index
        if hasattr(raw, 'info') and 'meas_date' in raw.info:
            # If we have metadata, we might map this to a participant
            # For now, we'll use a generic ID based on index if not found
            participant_id = f"participant_{idx:04d}"
        else:
            participant_id = f"participant_{idx:04d}"
        
        # Get channel names
        ch_names = raw.ch_names
        sfreq = raw.info['sfreq']
        
        logger.info(f"Processing participant: {participant_id}, Channels: {len(ch_names)}")
        
        # Iterate over each channel
        for ch_name in ch_names:
            # Extract data for this channel
            data, _ = raw[:, ch_name]
            data = data.flatten()
            
            # Filter out NaNs and Inf
            valid_mask = np.isfinite(data)
            if np.sum(valid_mask) < 100: # Need enough data points
                logger.warning(f"Skipping channel {ch_name} for {participant_id}: insufficient valid data.")
                continue
            
            valid_data = data[valid_mask]
            
            # Calculate LZC
            lzc_value = calculate_lempel_ziv_complexity(valid_data, threshold=None)
            
            results.append({
                'participant_id': participant_id,
                'channel': ch_name,
                'lzc_value': lzc_value
            })
    
    return results

def save_metrics_to_csv(metrics, output_path):
    """
    Save metrics to a CSV file.
    
    Args:
        metrics: List of dictionaries with metrics.
        output_path: Path to the output CSV file.
    """
    if not metrics:
        raise ValueError("No metrics to save.")
    
    df = pd.DataFrame(metrics)
    # Ensure correct column order
    df = df[['participant_id', 'channel', 'lzc_value']]
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logging.info(f"Saved metrics to {output_path}")

def main():
    """Main entry point for feature extraction."""
    logger = setup_logger('features', 'logs/features.log')
    logger.info("Starting Permutation Entropy and LZC calculation pipeline")
    
    config = load_config()
    
    input_file = Path("data/processed/cleaned_eeg.fif")
    output_file = Path("data/processed/lzc_metrics.csv")
    
    # Check if input file exists
    if not input_file.exists():
        logger.error(f"Processed data directory not found: {input_file.parent}")
        logger.error(f"Missing file: {input_file}")
        sys.exit(1)
    
    try:
        # Load the preprocessed data
        # The file might contain multiple subjects or a single subject
        # We assume it's a single concatenated file or we need to split it
        # For MNE, we usually load a Raw object
        raw = mne.io.read_raw_fif(input_file, preload=False)
        
        # If the file contains multiple subjects, we might need to split them
        # For this implementation, we assume the file contains one continuous recording
        # or we process it as a single unit.
        # If the file has multiple subjects, the naming convention in the filename
        # or metadata should indicate this. We'll process the loaded raw object.
        
        # If the file is a list of files (not typical for .fif), we would iterate.
        # Assuming raw is a single Raw object here.
        
        logger.info(f"Loaded EEG data: {input_file}")
        logger.info(f"Channels: {raw.ch_names}")
        logger.info(f"Duration: {raw.times[-1]:.2f}s")
        
        # Process segments
        metrics = process_eeg_segments(raw, config, logger)
        
        # Save to CSV
        save_metrics_to_csv(metrics, output_file)
        
        logger.info(f"Successfully calculated LZC for {len(metrics)} channel-participant pairs.")
        
    except Exception as e:
        logger.error(f"Error during feature extraction: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
