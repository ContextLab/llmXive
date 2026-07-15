import os
import sys
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from utils.logging import get_logger
try:
    from lempel_ziv import lempel_ziv_complexity
except ImportError:
    # Fallback for if the package name differs or is missing
    lempel_ziv = None
    import warnings
    warnings.warn("lempel_ziv package not found. LZC calculation will fail.")

def load_config(config_path="code/config.yaml"):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def calculate_lzc(signal, window):
    """
    Calculate Lempel-Ziv Complexity.
    """
    if lempel_ziv is None:
        raise ImportError("lempel_ziv package required")
    
    # Binarize signal (median threshold)
    binary = (signal > np.median(signal)).astype(int)
    # Flatten if 2D
    if binary.ndim > 1:
        binary = binary.flatten()
    
    # Calculate LZC
    # Note: lempel_ziv_complexity usually expects a list or array
    return lempel_ziv(binary)

def calculate_permutation_entropy(signal, order, delay):
    """
    Calculate Permutation Entropy.
    """
    # Implementation of permutation entropy
    n = len(signal)
    if n < order + (order - 1) * delay:
        return 0.0
    
    # Generate patterns
    patterns = []
    for i in range(n - (order - 1) * delay):
        pattern = tuple(np.argsort(signal[i:i + order * delay:delay]))
        patterns.append(pattern)
    
    # Count frequencies
    from collections import Counter
    counts = Counter(patterns)
    total = len(patterns)
    
    # Calculate entropy
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * np.log2(p)
    
    # Normalize
    max_entropy = np.log2(np.math.factorial(order))
    if max_entropy > 0:
        entropy /= max_entropy
    
    return entropy

def process_eeg_segments(data, config, logger):
    """
    Process EEG data and calculate metrics.
    """
    lzc_results = []
    pe_results = []
    
    if data.size == 0:
        logger.warning("Input data is empty.")
        return lzc_results, pe_results
    
    # Data shape: (n_channels, n_times)
    n_channels, n_times = data.shape
    window = config['features']['lzc_window']
    pe_order = config['features']['pe_order']
    pe_delay = config['features']['pe_delay']
    
    for ch_idx in range(n_channels):
        signal = data[ch_idx, :]
        
        # Calculate LZC
        try:
            lzc_val = calculate_lzc(signal, window)
            lzc_results.append({'channel': ch_idx, 'lzc': lzc_val})
        except Exception as e:
            logger.error(f"LZC calculation failed for channel {ch_idx}: {e}")
            lzc_results.append({'channel': ch_idx, 'lzc': np.nan})
        
        # Calculate PE
        try:
            pe_val = calculate_permutation_entropy(signal, pe_order, pe_delay)
            pe_results.append({'channel': ch_idx, 'pe': pe_val})
        except Exception as e:
            logger.error(f"PE calculation failed for channel {ch_idx}: {e}")
            pe_results.append({'channel': ch_idx, 'pe': np.nan})
    
    return lzc_results, pe_results

def save_metrics_to_csv(results, output_path, logger):
    """
    Save metrics to CSV.
    """
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved metrics to {output_path}")

def main():
    config = load_config()
    logger = get_logger("features", config)
    logger.info("Starting feature extraction pipeline")
    
    input_file = Path(config['paths']['processed_data']) / "preprocessed_eeg.npy"
    
    if not input_file.exists():
        logger.error(f"Data file not found: {input_file}")
        # Create empty output files to prevent downstream crashes
        Path("data/processed/lzc_metrics.csv").touch()
        Path("data/processed/pe_metrics.csv").touch()
        return

    logger.info(f"Loading preprocessed EEG data from {input_file}")
    data = np.load(input_file)
    
    lzc_results, pe_results = process_eeg_segments(data, config, logger)
    
    save_metrics_to_csv(lzc_results, "data/processed/lzc_metrics.csv", logger)
    save_metrics_to_csv(pe_results, "data/processed/pe_metrics.csv", logger)

if __name__ == "__main__":
    main()
