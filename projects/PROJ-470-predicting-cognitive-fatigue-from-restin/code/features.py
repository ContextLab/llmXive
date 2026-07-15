import os
import sys
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import entropy
from scipy.signal import detrend

# Importing from sibling modules as per API surface
from utils.logging import get_logger

logger = get_logger(__name__)

def load_config(config_path='code/config.yaml'):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def calculate_lzc(signal):
    """
    Calculate Lempel-Ziv Complexity for a given signal.
    
    Args:
        signal: 1D numpy array of EEG data
        
    Returns:
        float: LZC value normalized by sequence length
    """
    if len(signal) == 0:
        return 0.0
        
    # Binarize signal (median threshold)
    median_val = np.median(signal)
    binary_seq = (signal > median_val).astype(int)
    
    # LZC calculation
    n = len(binary_seq)
    c = 0
    l = 1
    i = 0
    j = 0
    
    while i < n - l:
        k = 0
        while i + l + k < n:
            if np.array_equal(binary_seq[i:i+l], binary_seq[i+l+k:i+l+k+l]):
                k += 1
            else:
                break
        
        if k == 0:
            c += 1
            i += 1
            l = 1
        else:
            i += l + k
            l = 1
            c += 1
            
    # Normalize
    c = c / (n / np.log2(n))
    return c

def calculate_permutation_entropy(signal, order=3, delay=1):
    """
    Calculate Permutation Entropy for a given signal.
    
    Args:
        signal: 1D numpy array of EEG data
        order: Order of permutation (number of elements in each pattern)
        delay: Delay between elements in the pattern
        
    Returns:
        float: Permutation Entropy value
    """
    if len(signal) < order * delay:
        logger.warning(f"Signal length {len(signal)} too short for order {order} and delay {delay}")
        return 0.0
        
    # Detrend signal to remove linear trends
    detrended_signal = detrend(signal)
    
    # Create embedded vectors
    n_vectors = len(detrended_signal) - (order - 1) * delay
    if n_vectors <= 0:
        return 0.0
        
    # Extract patterns and determine their ordinal rankings
    patterns = []
    for i in range(n_vectors):
        vector = detrended_signal[i:i + order * delay:delay]
        # Get the permutation that would sort the vector
        pattern = np.argsort(vector)
        patterns.append(tuple(pattern))
    
    # Calculate probability distribution of patterns
    unique_patterns, counts = np.unique(patterns, return_counts=True)
    probabilities = counts / len(patterns)
    
    # Calculate Shannon entropy
    pe = entropy(probabilities, base=2)
    
    # Normalize by max possible entropy (log2(order!))
    max_entropy = np.log2(np.math.factorial(order))
    if max_entropy > 0:
        pe = pe / max_entropy
        
    return pe

def process_eeg_segments(eeg_data, config):
    """
    Process EEG segments to calculate complexity metrics.
    
    Args:
        eeg_data: Dictionary with channel names as keys and 1D arrays as values
        config: Configuration dictionary
        
    Returns:
        DataFrame with complexity metrics per channel
    """
    results = []
    
    # Get parameters from config
    lzc_enabled = config.get('features', {}).get('lzc_enabled', True)
    pe_enabled = config.get('features', {}).get('pe_enabled', True)
    pe_order = config.get('features', {}).get('pe_order', 3)
    pe_delay = config.get('features', {}).get('pe_delay', 1)
    
    for channel, signal in eeg_data.items():
        # Skip if signal is too short
        if len(signal) < 10:
            logger.warning(f"Skipping channel {channel} due to short signal length")
            continue
            
        row = {'channel': channel, 'duration': len(signal)}
        
        if lzc_enabled:
            lzc_val = calculate_lzc(signal)
            row['lzc'] = lzc_val
            logger.debug(f"Calculated LZC for {channel}: {lzc_val:.4f}")
            
        if pe_enabled:
            pe_val = calculate_permutation_entropy(signal, order=pe_order, delay=pe_delay)
            row['pe'] = pe_val
            logger.debug(f"Calculated PE for {channel}: {pe_val:.4f}")
            
        results.append(row)
        
    return pd.DataFrame(results)

def save_metrics_to_csv(metrics_df, output_path):
    """
    Save complexity metrics to CSV file.
    
    Args:
        metrics_df: DataFrame with metrics
        output_path: Path to output CSV file
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(output_path, index=False)
    logger.info(f"Saved metrics to {output_path}")

def main():
    """Main function to run feature extraction pipeline."""
    config = load_config()
    
    # Define input and output paths based on config
    processed_dir = Path(config.get('paths', {}).get('processed_data', 'data/processed'))
    lzc_output = processed_dir / 'lzc_metrics.csv'
    pe_output = processed_dir / 'pe_metrics.csv'
    
    # Load preprocessed EEG data (assumed to be in a standard format)
    # This function would need to be implemented based on the actual data format
    # For now, we assume the data is available in a specific location
    eeg_data_path = config.get('paths', {}).get('preprocessed_eeg', 'data/processed/preprocessed_eeg.npy')
    
    if not os.path.exists(eeg_data_path):
        logger.error(f"Preprocessed EEG data not found at {eeg_data_path}")
        sys.exit(1)
        
    # Load EEG data
    eeg_data = np.load(eeg_data_path, allow_pickle=True).item()
    
    # Process segments
    metrics_df = process_eeg_segments(eeg_data, config)
    
    # Split metrics by type if needed
    if 'lzc' in metrics_df.columns:
        lzc_df = metrics_df[['channel', 'duration', 'lzc']]
        save_metrics_to_csv(lzc_df, lzc_output)
        
    if 'pe' in metrics_df.columns:
        pe_df = metrics_df[['channel', 'duration', 'pe']]
        save_metrics_to_csv(pe_df, pe_output)
        
    logger.info("Feature extraction completed successfully")

if __name__ == '__main__':
    main()