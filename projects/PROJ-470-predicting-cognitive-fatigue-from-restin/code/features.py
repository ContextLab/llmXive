import os
import sys
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import mne
from scipy.stats import entropy
from collections import Counter
import re
import math

sys.path.insert(0, str(Path(__file__).parent))
from utils.logging import get_logger

def load_config():
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def calculate_lzc(signal):
    """
    Calculate Lempel-Ziv Complexity.
    Uses a robust implementation.
    """
    # Normalize signal to binary (0/1) based on median
    median_val = np.median(signal)
    binary_signal = (signal > median_val).astype(int)
    
    # Convert to string for algorithm
    s = "".join(map(str, binary_signal.tolist()))
    n = len(s)
    
    if n == 0:
        return 0.0

    # Robust LZC algorithm
    lzc = 1
    k = 1
    len_k = 1
    
    while k <= n:
        sub = s[:k]
        if sub in s[k:]:
            k += 1
            len_k += 1
        else:
            lzc += 1
            if k == n:
                break
            if k > len_k:
                len_k = k
            k += 1
            len_k = 1
    
    # Normalization: C(n) ~ n / log2(n)
    if n / np.log2(n) == 0:
        return 0.0
    
    return lzc / (n / np.log2(n))

def calculate_permutation_entropy(signal, order=3, delay=1):
    """
    Calculate Normalized Permutation Entropy.
    Returns value in range [0, 1].
    For white noise, the value should be close to 1.0.
    """
    n = len(signal)
    if n < order * delay:
        return 0.0
    
    # Create embeddings
    embeddings = []
    for i in range(n - (order - 1) * delay):
        segment = signal[i : i + order * delay : delay]
        # argsort returns indices that would sort the array
        emb = tuple(np.argsort(segment))
        embeddings.append(emb)
    
    if not embeddings:
        return 0.0

    # Count frequencies
    counts = Counter(embeddings)
    probs = np.array(list(counts.values())) / len(embeddings)
    
    # Avoid log(0)
    probs = probs[probs > 0]
    
    # Calculate raw entropy
    raw_entropy = entropy(probs, base=2)
    
    # Normalize by max possible entropy (log2(order!))
    max_entropy = np.log2(math.factorial(order))
    if max_entropy == 0:
        return 0.0
    
    return raw_entropy / max_entropy

def process_eeg_segments(raw_file):
    logger = get_logger("features")
    logger.info(f"Loading preprocessed EEG data from {raw_file}")
    
    if not os.path.exists(raw_file):
        logger.error(f"Data file not found: {raw_file}")
        sys.exit(1)
    
    try:
        raw = mne.io.read_raw_fif(raw_file, preload=True)
    except Exception as e:
        logger.error(f"Failed to load FIF file: {e}")
        sys.exit(1)
    
    data = raw.get_data()
    sfreq = raw.info['sfreq']
    ch_names = raw.ch_names
    
    base_name = Path(raw_file).stem
    match = re.search(r'sub-(\w+)', base_name)
    participant_id = match.group(1) if match else "unknown"

    metrics = []
    
    for ch_idx, ch_name in enumerate(ch_names):
        channel_data = data[ch_idx]
        
        lzc_val = calculate_lzc(channel_data)
        pe_val = calculate_permutation_entropy(channel_data)
        
        metrics.append({
            "participant_id": participant_id,
            "channel": ch_name,
            "lzc_value": round(float(lzc_val), 4),
            "pe_value": round(float(pe_val), 4)
        })
    
    return metrics

def save_metrics_to_csv(metrics, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df = pd.DataFrame(metrics)
    df.to_csv(output_path, index=False)
    print(f"Saved metrics to {output_path}")

def main():
    logger = get_logger("features")
    logger.info("Starting feature extraction pipeline")
    
    config = load_config()
    input_file = "data/processed/cleaned_eeg.fif"
    lzc_output = "data/processed/lzc_metrics.csv"
    pe_output = "data/processed/pe_metrics.csv"
    
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    metrics = process_eeg_segments(input_file)
    
    if not metrics:
        logger.error("No metrics calculated.")
        sys.exit(1)
    
    # Save to separate files as per schema
    lzc_df = pd.DataFrame(metrics)[["participant_id", "channel", "lzc_value"]]
    lzc_df.to_csv(lzc_output, index=False)
    logger.info(f"LZC metrics saved to {lzc_output}")
    
    pe_df = pd.DataFrame(metrics)[["participant_id", "channel", "pe_value"]]
    pe_df.to_csv(pe_output, index=False)
    logger.info(f"PE metrics saved to {pe_output}")
    
    logger.info("Feature extraction complete.")

if __name__ == "__main__":
    main()