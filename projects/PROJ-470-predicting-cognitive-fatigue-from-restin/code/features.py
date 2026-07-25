import os
import sys
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import List, Tuple, Optional
import mne

# Import logging utilities from the project's utils
from utils.logging import get_logger, save_exclusion_log_csv

def load_config(config_path: str = "code/config.yaml") -> dict:
    """Load pipeline configuration from YAML."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name: str, log_file: str) -> logging.Logger:
    """Set up a logger that writes to a file and stdout."""
    logger = get_logger(name)
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    fh = logging.FileHandler(log_file, mode='a')
    fh.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)
    return logger

def calculate_permutation_entropy(signal: np.ndarray, order: int = 3, delay: int = 1) -> float:
    """
    Calculate Permutation Entropy (PE) for a 1D signal.
    
    Parameters:
    -----------
    signal : np.ndarray
        1D array of EEG data.
    order : int
        Embedding dimension (default 3).
    delay : int
        Time delay (default 1).
        
    Returns:
    --------
    float
        Permutation entropy value.
    """
    n = len(signal)
    if n <= order * delay:
        return np.nan
    
    # Generate all permutations of range(order)
    from itertools import permutations
    perms = list(permutations(range(order)))
    perm_map = {p: i for i, p in enumerate(perms)}
    
    # Count occurrences of each permutation pattern
    counts = np.zeros(len(perms))
    total_patterns = n - (order - 1) * delay
    
    for i in range(total_patterns):
        # Extract the subsequence
        subseq = signal[i : i + order * delay : delay]
        # Get the rank order (permutation index)
        # argsort gives the indices that would sort the array
        rank_indices = np.argsort(subseq)
        # Convert rank indices to the permutation pattern
        # We need the permutation that transforms (0, 1, ..., order-1) to rank_indices
        # Actually, we need the permutation that represents the order of values
        # If subseq is [0.5, 0.1, 0.9], ranks are [1, 0, 2] (0.1 is smallest, 0.5 middle, 0.9 largest)
        # The permutation pattern is the tuple of ranks: (1, 0, 2)
        pattern = tuple(rank_indices)
        if pattern in perm_map:
            counts[perm_map[pattern]] += 1
    
    # Normalize counts to probabilities
    probs = counts / total_patterns
    probs = probs[probs > 0]  # Remove zeros to avoid log(0)
    
    # Calculate entropy: -sum(p * log(p))
    entropy = -np.sum(probs * np.log(probs))
    
    # Normalize by max entropy (log(order!))
    max_entropy = np.log(np.math.factorial(order))
    if max_entropy == 0:
        return 0.0
    
    return entropy / max_entropy

def process_eeg_segments(raw_data: mne.io.BaseRaw, participant_id: str, 
                         config: dict, logger: logging.Logger) -> List[Tuple[str, str, float]]:
    """
    Process EEG segments for a single participant and calculate PE per channel.
    
    Parameters:
    -----------
    raw_data : mne.io.BaseRaw
        Preprocessed EEG data object.
    participant_id : str
        Participant identifier.
    config : dict
        Configuration dictionary.
    logger : logging.Logger
        Logger instance.
        
    Returns:
    --------
    List[Tuple[str, str, float]]
        List of (participant_id, channel, pe_value) tuples.
    """
    results = []
    channels = raw_data.ch_names
    sfreq = raw_data.info['sfreq']
    
    # Get segment length from config (default 120 seconds)
    segment_length = config.get('segment_length', 120)
    sample_length = int(segment_length * sfreq)
    
    # Get embedding parameters from config
    order = config.get('pe_order', 3)
    delay = config.get('pe_delay', 1)
    
    for ch_idx, ch_name in enumerate(channels):
        # Extract channel data
        data, _ = raw_data.get_data(picks=[ch_idx], start=0, stop=sample_length)
        if data.size == 0:
            logger.warning(f"No data for channel {ch_name} in participant {participant_id}")
            continue
        
        signal = data[0]
        
        # Calculate Permutation Entropy
        pe_value = calculate_permutation_entropy(signal, order=order, delay=delay)
        
        if np.isnan(pe_value):
            logger.warning(f"NaN PE value for channel {ch_name} in participant {participant_id}")
            continue
            
        results.append((participant_id, ch_name, pe_value))
        
    return results

def save_metrics_to_csv(results: List[Tuple[str, str, float]], output_path: str, logger: logging.Logger):
    """
    Save permutation entropy metrics to CSV.
    
    Parameters:
    -----------
    results : List[Tuple[str, str, float]]
        List of (participant_id, channel, pe_value) tuples.
    output_path : str
        Path to output CSV file.
    logger : logging.Logger
        Logger instance.
    """
    if not results:
        logger.error("No results to save.")
        return
    
    df = pd.DataFrame(results, columns=['participant_id', 'channel', 'pe_value'])
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} PE metrics to {output_path}")

def main():
    """Main entry point for Permutation Entropy feature extraction."""
    config = load_config()
    
    # Setup logging
    log_dir = config.get('log_dir', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    logger = setup_logger('features', os.path.join(log_dir, 'features.log'))
    
    logger.info("Starting Permutation Entropy calculation pipeline")
    
    # Define paths
    processed_dir = Path(config.get('processed_dir', 'data/processed'))
    output_path = processed_dir / 'pe_metrics.csv'
    
    if not processed_dir.exists():
        logger.error(f"Processed data directory not found: {processed_dir}")
        sys.exit(1)
    
    # Find all cleaned EEG files
    eeg_files = list(processed_dir.glob('cleaned_eeg*.fif'))
    if not eeg_files:
        logger.error("No cleaned EEG files found in data/processed/")
        sys.exit(1)
    
    logger.info(f"Found {len(eeg_files)} cleaned EEG files")
    
    all_results = []
    
    for eeg_file in eeg_files:
        participant_id = eeg_file.stem.replace('cleaned_eeg_', '')
        try:
            logger.info(f"Processing participant: {participant_id}")
            raw = mne.io.read_raw_fif(eeg_file, preload=False)
            
            # Process segments
            results = process_eeg_segments(raw, participant_id, config, logger)
            all_results.extend(results)
            
        except Exception as e:
            logger.error(f"Failed to process {eeg_file}: {str(e)}")
            continue
    
    if all_results:
        save_metrics_to_csv(all_results, str(output_path), logger)
        logger.info("Permutation Entropy pipeline completed successfully")
    else:
        logger.error("No valid PE metrics were calculated.")
        sys.exit(1)

if __name__ == "__main__":
    main()
