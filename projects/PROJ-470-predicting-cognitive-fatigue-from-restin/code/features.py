import os
import sys
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import mne
from scipy.stats import entropy
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))
from utils.logging import get_logger

def load_config():
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def calculate_lzc(signal):
    """
    Calculate Lempel-Ziv Complexity.
    Uses a simple implementation or library if available.
    """
    try:
        from lempel_ziv_complexity import lempel_ziv_complexity
        # Normalize signal to 0/1 for LZC
        binary_signal = (signal > np.mean(signal)).astype(int)
        lzc, _ = lempel_ziv_complexity(binary_signal)
        return lzc
    except ImportError:
        # Fallback implementation if library not installed
        # Simple LZC calculation
        s = "".join(map(str, (signal > np.mean(signal)).astype(int).tolist()))
        n = len(s)
        lzc = 1
        k = 1
        while k < n:
            found = False
            for i in range(k):
                if s[i:i+k] in s[k:]:
                    found = True
                    break
            if found:
                k += 1
            else:
                lzc += 1
                k += 1
        return lzc / (n / np.log2(n))

def calculate_permutation_entropy(signal, order=3, delay=1):
    """
    Calculate Permutation Entropy.
    """
    n = len(signal)
    if n < order * delay:
        return 0.0
    
    # Create embeddings
    embeddings = []
    for i in range(n - (order - 1) * delay):
        # Extract the segment
        segment = signal[i : i + order * delay : delay]
        # Get the permutation (argsort)
        emb = tuple(np.argsort(segment))
        embeddings.append(emb)
    
    if not embeddings:
        return 0.0

    # Count frequencies
    counts = Counter(embeddings)
    probs = np.array(list(counts.values())) / len(embeddings)
    
    # Avoid log(0)
    probs = probs[probs > 0]
    
    return entropy(probs, base=2)

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
    
    # Determine participant ID from filename if possible, otherwise use generic
    # Assuming the file name might contain participant info, e.g., 'sub-001_cleaned_eeg.fif'
    # For now, we'll extract a generic ID or use 'combined' if not found
    base_name = Path(raw_file).stem
    # Try to extract 'sub-XXX' pattern
    import re
    match = re.search(r'sub-(\w+)', base_name)
    participant_id = match.group(1) if match else "unknown"

    metrics = []
    
    for ch_idx, ch_name in enumerate(ch_names):
        channel_data = data[ch_idx]
        
        # Skip channels that are obviously not EEG (e.g., EOG, EMG if present and labeled)
        # But for now, process all
        
        # Calculate metrics
        lzc_val = calculate_lzc(channel_data)
        pe_val = calculate_permutation_entropy(channel_data)
        
        metrics.append({
            "participant_id": participant_id,
            "channel": ch_name,
            "lzc_value": round(lzc_val, 4),
            "pe_value": round(pe_val, 4)
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
    
    # Process data
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