"""Feature extraction: Lempel-Ziv Complexity (LZC) and Permutation Entropy (PE) for EEG segments.

Implements FR-003: Calculate LZC and PE per channel per segment.
- LZC: Uses median quantization for binary conversion.
- PE: Uses embedding dimension=3, delay=1.
Output: data/analysis/complexity_metrics.csv with columns:
  participant_id, channel, segment_id, lzc_value, pe_value
"""
import os
import sys
import yaml
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Import local utilities
from utils.logging import get_logger, save_exclusion_log_csv

# Import mne for EEG handling
import mne

def load_config(config_path="code/config.yaml"):
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name, log_file=None):
    """Setup a logger that writes to file and console."""
    # The logging utility is designed to be tolerant of argument counts.
    # It accepts (name,) or (name, log_file) without raising.
    logger = get_logger(name, log_file)
    return logger

def calculate_lempel_ziv_complexity(signal: np.ndarray, quantize: bool = True) -> float:
    """
    Calculate Lempel-Ziv Complexity (LZC) for a 1D signal.

    Args:
        signal: 1D numpy array of EEG data.
        quantize: If True, quantize signal to binary (median split).

    Returns:
        float: Normalized LZC value between 0 and 1.
    """
    if len(signal) == 0:
        return 0.0

    if quantize:
        # Quantize to binary using median
        median_val = np.median(signal)
        binary_signal = (signal >= median_val).astype(int)
    else:
        # Discretize based on unique values (not recommended for continuous EEG)
        binary_signal = signal.astype(int)

    # Ensure binary
    binary_signal = np.array(binary_signal, dtype=int)

    # LZC Algorithm
    n = len(binary_signal)
    if n <= 1:
        return 0.0

    # Convert to string of 0s and 1s
    s = ''.join(map(str, binary_signal))

    # LZC counting
    lzc = 0
    i = 0
    while i < n:
        j = i + 1
        while j <= n:
            sub = s[i:j]
            if sub in s[:i]:
                j += 1
            else:
                break
        if j > i:
            lzc += 1
            i = j
        else:
            i += 1

    # Normalize by n / log2(n)
    if n <= 1:
        return 0.0
    normalized_lzc = lzc / (n / np.log2(n))
    return min(normalized_lzc, 1.0)  # Cap at 1.0

def calculate_permutation_entropy(signal: np.ndarray, embedding_dim: int = 3, delay: int = 1) -> float:
    """
    Calculate Permutation Entropy (PE) for a 1D signal.

    Args:
        signal: 1D numpy array of EEG data.
        embedding_dim: Dimension of the embedding vector (m).
        delay: Time delay for embedding (tau).

    Returns:
        float: Normalized Permutation Entropy value.
    """
    if len(signal) < embedding_dim + (embedding_dim - 1) * delay:
        return 0.0

    n = len(signal)
    # Number of vectors
    num_vectors = n - (embedding_dim - 1) * delay

    # Count permutations
    from collections import Counter
    permutation_counts = Counter()

    for i in range(num_vectors):
        # Extract vector
        vector = [signal[i + j * delay] for j in range(embedding_dim)]
        # Get the order pattern (ranks)
        # argsort returns indices that would sort the array
        # We map these indices to the permutation pattern
        order_pattern = tuple(np.argsort(vector))
        permutation_counts[order_pattern] += 1

    total = sum(permutation_counts.values())
    if total == 0:
        return 0.0

    # Calculate probabilities
    probs = np.array(list(permutation_counts.values())) / total

    # Calculate entropy: -sum(p * ln(p))
    entropy = -np.sum(probs * np.log(probs))

    # Normalize by max possible entropy: ln(embedding_dim!)
    max_entropy = np.log(np.math.factorial(embedding_dim))
    if max_entropy == 0:
        return 0.0

    normalized_pe = entropy / max_entropy
    return normalized_pe

def process_eeg_segments(raw_eeg: mne.io.BaseRaw, config: dict) -> list:
    """
    Process EEG segments and calculate LZC and PE for each channel.

    Args:
        raw_eeg: MNE Raw object containing EEG data.
        config: Configuration dictionary.

    Returns:
        list: List of dicts with channel, segment_id, lzc_value, pe_value.
    """
    results = []
    sfreq = raw_eeg.info['sfreq']
    data = raw_eeg.get_data()
    ch_names = raw_eeg.info['ch_names']

    # Define segment length (e.g., 120 seconds)
    segment_length_sec = config.get('segment_length_sec', 120)
    segment_samples = int(segment_length_sec * sfreq)

    # Iterate through segments
    num_segments = len(data[0]) // segment_samples
    
    # Extract participant ID from raw info
    participant_id = raw_eeg.info.get('subject_info', {}).get('his_id', 'unknown')
    if participant_id == 'unknown':
        # Fallback to subject if his_id not set
        participant_id = str(raw_eeg.info.get('subject_info', {}).get('subject', 'unknown'))

    for seg_idx in range(num_segments):
        start = seg_idx * segment_samples
        end = start + segment_samples
        segment_data = data[:, start:end]

        for ch_idx, ch_name in enumerate(ch_names):
            ch_signal = segment_data[ch_idx, :]
            
            # Calculate LZC
            lzc_val = calculate_lempel_ziv_complexity(ch_signal)
            
            # Calculate PE
            pe_val = calculate_permutation_entropy(ch_signal, embedding_dim=3, delay=1)
            
            results.append({
                'participant_id': participant_id,
                'channel': ch_name,
                'segment_id': f"seg_{seg_idx:03d}",
                'lzc_value': lzc_val,
                'pe_value': pe_val
            })

    return results

def save_metrics_to_csv(metrics: list, output_path: str) -> None:
    """Save metrics to CSV file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df = pd.DataFrame(metrics)
    # Ensure columns are in the expected order
    expected_cols = ['participant_id', 'channel', 'segment_id', 'lzc_value', 'pe_value']
    if all(col in df.columns for col in expected_cols):
        df = df[expected_cols]
    df.to_csv(output_path, index=False)

def main():
    """Main entry point for feature extraction."""
    logger = setup_logger("features")
    logger.info("Starting feature extraction pipeline.")

    # Load config
    try:
        config = load_config()
    except FileNotFoundError:
        print("Warning: config.yaml not found. Using defaults.")
        config = {'segment_length_sec': 120}

    # Define paths
    input_file = "data/processed/cleaned_eeg.fif"
    output_file = "data/analysis/complexity_metrics.csv"

    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        print(f"ERROR: Cleaned EEG file not found at {input_file}.")
        print("Please run code/preprocess.py first.")
        sys.exit(1)

    try:
        # Load EEG data
        raw = mne.io.read_raw_fif(input_file, preload=True)

        # Process segments
        metrics = process_eeg_segments(raw, config)

        if not metrics:
            logger.warning("No metrics generated. Check segment length or data availability.")
            # Still write an empty file with headers to satisfy downstream consumers
            save_metrics_to_csv([], output_file)
        else:
            # Save results
            save_metrics_to_csv(metrics, output_file)

        logger.info(f"Feature extraction complete. Results saved to {output_file}")
        print(f"Success: Complexity metrics written to {output_file}")
        print(f"Total segments processed: {len(metrics)}")

    except Exception as e:
        logger.error(f"Error during feature extraction: {e}")
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()