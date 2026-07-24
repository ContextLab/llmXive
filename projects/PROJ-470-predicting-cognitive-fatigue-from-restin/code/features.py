import os
import sys
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import mne
from scipy.stats import pearsonr, spearmanr

# Import from utils.logging as per API surface
from utils.logging import get_logger, save_exclusion_log_csv

def load_config(config_path='code/config.yaml'):
    """Load pipeline configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name, log_file='logs/pipeline.log', level=logging.INFO):
    """Set up a logger that writes to both console and file."""
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(log_file, mode='a')
    fh.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

def calculate_lzc(signal):
    """
    Calculate Lempel-Ziv Complexity for a 1D signal.
    Normalizes signal to [0, 1] and discretizes to binary.
    """
    if len(signal) == 0:
        return 0.0
    
    # Normalize to [0, 1]
    min_val, max_val = np.min(signal), np.max(signal)
    if max_val - min_val < 1e-10:
        return 0.0
    
    norm_signal = (signal - min_val) / (max_val - min_val)
    
    # Discretize to binary (0 if below mean, 1 otherwise)
    threshold = np.mean(norm_signal)
    binary_signal = (norm_signal > threshold).astype(int)
    
    # LZC algorithm
    n = len(binary_signal)
    c = 0
    l = 1
    i = 0
    while i < n - l:
        pattern = tuple(binary_signal[i:i+l])
        found = False
        for j in range(0, i):
            if tuple(binary_signal[j:j+l]) == pattern:
                found = True
                break
        if not found:
            c += 1
            i += l
            l = 1
        else:
            l += 1
            if i + l >= n:
                c += 1
                break
    
    # Normalize by n / log2(n)
    if n <= 1:
        return 0.0
    return c / (n / np.log2(n))

def calculate_permutation_entropy(signal, embedding_dim=3, time_delay=1):
    """
    Calculate Permutation Entropy for a 1D signal.
    
    Parameters:
    -----------
    signal : array-like
        The input time series.
    embedding_dim : int
        The dimension of the embedding (order of the permutation).
    time_delay : int
        The time delay for the embedding.
        
    Returns:
    --------
    float
        The permutation entropy value.
    """
    if len(signal) < embedding_dim + (embedding_dim - 1) * time_delay:
        return 0.0
    
    n = len(signal)
    # Create embedded vectors
    # We need to form vectors of length 'embedding_dim' with 'time_delay' spacing
    # Number of such vectors we can form
    num_vectors = n - (embedding_dim - 1) * time_delay
    
    if num_vectors <= 0:
        return 0.0
    
    # Count permutations
    from collections import Counter
    permutation_counts = Counter()
    
    for i in range(num_vectors):
        # Extract the embedded vector
        vector = [signal[i + j * time_delay] for j in range(embedding_dim)]
        
        # Determine the permutation pattern by ranking
        # argsort gives the indices that would sort the array
        # We want the permutation of ranks
        sorted_indices = np.argsort(vector)
        # Create a tuple representing the permutation pattern
        # We map the original indices to their rank positions
        # Actually, we need the inverse: for each position j in the vector,
        # what is the rank of vector[j]?
        # If we sort, sorted_indices[k] is the index of the k-th smallest element.
        # So the rank of element at index i is the position j such that sorted_indices[j] == i.
        # We can compute this by:
        permutation = np.empty(embedding_dim, dtype=int)
        for rank, idx in enumerate(sorted_indices):
            permutation[idx] = rank
        
        pattern = tuple(permutation)
        permutation_counts[pattern] += 1
    
    total = sum(permutation_counts.values())
    if total == 0:
        return 0.0
    
    # Calculate entropy
    entropy = 0.0
    for count in permutation_counts.values():
        p = count / total
        if p > 0:
            entropy -= p * np.log(p)
    
    # Normalize by max entropy (log2(embedding_dim!))
    max_entropy = np.log(np.math.factorial(embedding_dim))
    if max_entropy == 0:
        return 0.0
    
    return entropy / max_entropy

def process_eeg_segments(data_dir, config, logger):
    """
    Process EEG segments from preprocessed data.
    Reads cleaned_eeg.fif and calculates LZC and PE per participant/channel.
    """
    # Determine input file path
    input_file = os.path.join(data_dir, 'processed', 'cleaned_eeg.fif')
    if not os.path.exists(input_file):
        # Try alternative path if data_dir is project root
        input_file = os.path.join('data', 'processed', 'cleaned_eeg.fif')
    
    if not os.path.exists(input_file):
        logger.error(f"Preprocessed EEG file not found: {input_file}")
        return None, None
    
    logger.info(f"Loading preprocessed EEG from {input_file}")
    
    # Load data using MNE
    # Assuming the file is in FIF format
    raw = mne.read_raw_fif(input_file, preload=False)
    
    # Get data and info
    data = raw.get_data()  # shape: (n_channels, n_times)
    info = raw.info
    channel_names = info['ch_names']
    sfreq = info['sfreq']
    
    logger.info(f"Loaded EEG data: {data.shape[0]} channels, {data.shape[1]} samples")
    
    # Get embedding parameters from config
    embedding_dim = config.get('embedding_dim', 3)
    time_delay = config.get('time_delay', 1)
    
    lzc_results = []
    pe_results = []
    
    # Iterate over participants (assuming single participant per file for now,
    # or we need to handle multiple segments)
    # For simplicity, we assume the file contains one continuous recording per participant
    # and we process it as a single segment per channel.
    # If there are multiple participants, we would need to segment by participant_id.
    # For now, we'll assume the file has one participant and process all channels.
    
    # If the data has multiple segments (e.g., by participant), we need to handle that.
    # Since we don't have participant IDs in the FIF file directly, we'll assume
    # the file is for one participant and use a placeholder ID or extract from filename.
    participant_id = os.path.splitext(os.path.basename(input_file))[0]
    
    logger.info(f"Processing participant: {participant_id}")
    
    for ch_idx, ch_name in enumerate(channel_names):
        signal = data[ch_idx, :]
        
        # Calculate LZC
        lzc_val = calculate_lzc(signal)
        lzc_results.append({
            'participant_id': participant_id,
            'channel': ch_name,
            'lzc_value': lzc_val
        })
        
        # Calculate PE
        pe_val = calculate_permutation_entropy(signal, embedding_dim, time_delay)
        pe_results.append({
            'participant_id': participant_id,
            'channel': ch_name,
            'pe_value': pe_val
        })
        
        logger.debug(f"Channel {ch_name}: LZC={lzc_val:.4f}, PE={pe_val:.4f}")
    
    return lzc_results, pe_results

def save_metrics_to_csv(results, output_path, columns):
    """Save metrics to CSV file."""
    if not results:
        logging.error("No results to save")
        return
    
    df = pd.DataFrame(results)
    # Ensure columns are in the correct order
    df = df[columns]
    df.to_csv(output_path, index=False)
    logging.info(f"Saved metrics to {output_path}")

def main():
    """Main entry point for feature extraction."""
    # Load config
    config = load_config()
    
    # Set up logger
    logger = setup_logger('features', 'logs/features.log')
    logger.info("Starting feature extraction pipeline")
    
    try:
        # Process EEG segments
        lzc_results, pe_results = process_eeg_segments('data', config, logger)
        
        if lzc_results is None or pe_results is None:
            logger.error("Failed to process EEG segments")
            sys.exit(1)
        
        # Save LZC metrics
        lzc_output = os.path.join('data', 'processed', 'lzc_metrics.csv')
        save_metrics_to_csv(lzc_results, lzc_output, ['participant_id', 'channel', 'lzc_value'])
        
        # Save PE metrics
        pe_output = os.path.join('data', 'processed', 'pe_metrics.csv')
        save_metrics_to_csv(pe_results, pe_output, ['participant_id', 'channel', 'pe_value'])
        
        logger.info("Feature extraction completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
