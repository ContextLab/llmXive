"""
Feature extraction module for EEG complexity metrics.

Calculates Lempel-Ziv Complexity (LZC) and Permutation Entropy (PE)
for preprocessed EEG segments.
"""
import os
import sys
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, List, Dict, Optional

# Local imports from project structure
try:
    from utils.logging import get_logger
except ImportError:
    # Fallback for direct execution or different import context
    import logging
    def get_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

logger = get_logger(__name__)

def load_config(config_path: str = "code/config.yaml") -> Dict:
    """Load pipeline configuration."""
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def calculate_lzc(signal: np.ndarray, quantization_levels: int = 4) -> float:
    """
    Calculate Lempel-Ziv Complexity for a 1D signal.
    
    Args:
        signal: 1D numpy array of EEG data.
        quantization_levels: Number of discrete levels for binarization.
        
    Returns:
        Normalized Lempel-Ziv complexity value (0.0 to 1.0).
    """
    if len(signal) == 0:
        return 0.0
    
    # Normalize and discretize
    signal = signal - np.mean(signal)
    max_val = np.max(np.abs(signal))
    if max_val == 0:
        return 0.0
    
    # Quantize to binary string based on median split or fixed levels
    # Using a simple median-based binarization for robustness
    median_val = np.median(signal)
    binary_seq = (signal > median_val).astype(int)
    
    # Convert to string for LZ78 algorithm
    s = "".join(str(x) for x in binary_seq)
    n = len(s)
    
    # LZ78 complexity calculation
    lzc_count = 1
    i = 0
    j = 1
    l = 1
    
    while i + l <= n:
        # Find the first substring that hasn't appeared before
        found = False
        for k in range(i):
            if s[k:k+l] == s[i:i+l]:
                # Extend the match
                if i + l + 1 <= n and s[k:k+l+1] == s[i:i+l+1]:
                    l += 1
                else:
                    break
        else:
            # No match found, this is a new pattern
            lzc_count += 1
            i += l
            l = 1
            continue
        
        # If we found a match, we need to handle the extension
        # The logic above is a simplified version; standard LZ78:
        # Find longest prefix of s[i:] that is in the dictionary
        # Add the next character to the dictionary
        # This is O(n^2) worst case but sufficient for typical EEG segments
        
        # Reset for standard LZ78 logic
        break
    
    # Standard LZ78 implementation for accuracy
    # Reset variables
    lzc_count = 1
    i = 0
    l = 1
    while i + l <= n:
        found = False
        for j in range(i):
            if s[j:j+l] == s[i:i+l]:
                # Match found, try to extend
                if i + l + 1 <= n and s[j:j+l+1] == s[i:i+l+1]:
                    l += 1
                else:
                    # Match ends here, new pattern starts
                    lzc_count += 1
                    i += l
                    l = 1
                    found = True
                    break
        if not found:
            # No match found at all, new pattern
            lzc_count += 1
            i += l
            l = 1
    
    # Normalize by log2(n)
    if n == 0:
        return 0.0
    normalized_lzc = lzc_count / (n / np.log2(n))
    return min(normalized_lzc, 1.0)  # Clamp to [0, 1]

def calculate_permutation_entropy(signal: np.ndarray, order: int = 3, delay: int = 1) -> float:
    """
    Calculate Permutation Entropy for a 1D signal.
    
    Args:
        signal: 1D numpy array of EEG data.
        order: Embedding dimension (number of elements in each permutation).
        delay: Time delay between elements.
        
    Returns:
        Normalized permutation entropy value (0.0 to 1.0).
    """
    if len(signal) < order * delay:
        return 0.0
    
    n = len(signal)
    # Generate permutations
    patterns = []
    for i in range(n - (order - 1) * delay):
        # Extract subsequence
        subseq = signal[i : i + order * delay : delay]
        # Get the permutation indices that would sort this subsequence
        pattern = np.argsort(subseq)
        patterns.append(tuple(pattern))
    
    if not patterns:
        return 0.0
    
    # Count frequencies
    from collections import Counter
    counts = Counter(patterns)
    total = len(patterns)
    
    # Calculate entropy
    entropy = 0.0
    for count in counts.values():
        if count > 0:
            p = count / total
            entropy -= p * np.log2(p)
    
    # Normalize by max entropy (log2(order!))
    max_entropy = np.log2(np.math.factorial(order))
    if max_entropy == 0:
        return 0.0
    
    return entropy / max_entropy

def process_eeg_segments(
    data_path: str,
    output_dir: str,
    config: Dict
) -> Tuple[List[Dict], List[Dict]]:
    """
    Process preprocessed EEG data to calculate complexity metrics.
    
    Args:
        data_path: Path to preprocessed EEG data (NPY format).
        output_dir: Directory to save output CSV files.
        config: Configuration dictionary.
        
    Returns:
        Tuple of (lzc_metrics, pe_metrics) as lists of dictionaries.
    """
    logger.info(f"Loading preprocessed EEG data from {data_path}")
    
    if not os.path.exists(data_path):
        logger.error(f"Preprocessed data not found: {data_path}")
        sys.exit(1)
    
    try:
        # Load preprocessed data
        # Expected shape: (n_channels, n_samples) or (n_segments, n_channels, n_samples)
        eeg_data = np.load(data_path, allow_pickle=True)
        
        # Handle different data structures
        if isinstance(eeg_data, np.ndarray) and eeg_data.ndim == 2:
            # (n_channels, n_samples) - single subject/session
            channels = eeg_data.shape[0]
            samples = eeg_data.shape[1]
            segment_data = [eeg_data]  # Wrap in list for uniform processing
            segment_ids = [f"session_0"]
        elif isinstance(eeg_data, np.ndarray) and eeg_data.ndim == 3:
            # (n_segments, n_channels, n_samples)
            segment_data = list(eeg_data)
            segment_ids = [f"session_{i}" for i in range(len(segment_data))]
        elif isinstance(eeg_data, np.ndarray) and eeg_data.dtype == object:
            # Might be an array of arrays or objects
            # Try to extract as list of segments
            segment_data = []
            segment_ids = []
            for i, seg in enumerate(eeg_data):
                if isinstance(seg, np.ndarray) and seg.ndim == 2:
                    segment_data.append(seg)
                    segment_ids.append(f"session_{i}")
        else:
            logger.error(f"Unexpected data format: {eeg_data.shape}, dtype={eeg_data.dtype}")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Failed to load preprocessed data: {e}")
        sys.exit(1)
    
    lzc_metrics = []
    pe_metrics = []
    
    # Parameters from config
    lzc_levels = config.get('features', {}).get('lzc_quantization_levels', 4)
    pe_order = config.get('features', {}).get('pe_order', 3)
    pe_delay = config.get('features', {}).get('pe_delay', 1)
    
    # Process each segment
    for seg_idx, seg_data in enumerate(segment_data):
        seg_id = segment_ids[seg_idx]
        n_channels, n_samples = seg_data.shape
        
        logger.info(f"Processing segment {seg_id}: {n_channels} channels, {n_samples} samples")
        
        for ch_idx in range(n_channels):
            channel_name = f"ch_{ch_idx}"
            signal = seg_data[ch_idx, :]
            
            # Skip if signal is empty or constant
            if len(signal) == 0 or np.std(signal) < 1e-10:
                continue
            
            # Calculate metrics
            lzc_val = calculate_lzc(signal, lzc_levels)
            pe_val = calculate_permutation_entropy(signal, pe_order, pe_delay)
            
            lzc_metrics.append({
                'segment_id': seg_id,
                'channel': channel_name,
                'metric_type': 'LZC',
                'value': lzc_val,
                'n_samples': n_samples
            })
            
            pe_metrics.append({
                'segment_id': seg_id,
                'channel': channel_name,
                'metric_type': 'PE',
                'value': pe_val,
                'n_samples': n_samples
            })
    
    logger.info(f"Processed {len(lzc_metrics)} LZC metrics and {len(pe_metrics)} PE metrics")
    return lzc_metrics, pe_metrics

def save_metrics_to_csv(metrics: List[Dict], output_path: str):
    """Save metrics to a CSV file."""
    if not metrics:
        logger.warning("No metrics to save")
        # Create empty file with headers
        pd.DataFrame(columns=['segment_id', 'channel', 'metric_type', 'value', 'n_samples']).to_csv(output_path, index=False)
        return
    
    df = pd.DataFrame(metrics)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(metrics)} metrics to {output_path}")

def main():
    """Main entry point for feature extraction."""
    logger.info("Starting feature extraction pipeline")
    
    # Load configuration
    config = load_config()
    
    # Paths
    data_dir = Path(config.get('paths', {}).get('processed_data', 'data/processed'))
    output_dir = Path(config.get('paths', {}).get('processed_data', 'data/processed'))
    input_file = data_dir / "preprocessed_eeg.npy"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process data
    lzc_metrics, pe_metrics = process_eeg_segments(
        data_path=str(input_file),
        output_dir=str(output_dir),
        config=config
    )
    
    # Save results
    lzc_output_path = output_dir / "lzc_metrics.csv"
    pe_output_path = output_dir / "pe_metrics.csv"
    
    save_metrics_to_csv(lzc_metrics, str(lzc_output_path))
    save_metrics_to_csv(pe_metrics, str(pe_output_path))
    
    logger.info("Feature extraction completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
