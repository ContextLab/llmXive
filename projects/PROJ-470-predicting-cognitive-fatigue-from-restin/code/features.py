import os
import sys
import yaml
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import signal as scipy_signal

# Import Lempel-Ziv complexity implementation
try:
    from lempel_ziv import lempel_ziv_complexity
except ImportError:
    # Fallback if the specific package name varies, try common alias
    try:
        from lempel_ziv_complexity import lempel_ziv_complexity
    except ImportError:
        raise ImportError(
            "Required package 'lempel_ziv' or 'lempel_ziv_complexity' not found. "
            "Please ensure it is installed in the virtual environment."
        )

# Import permutation entropy implementation
try:
    import nolds
except ImportError:
    raise ImportError(
        "Required package 'nolds' not found. "
        "Please ensure it is installed in the virtual environment."
    )

def load_config():
    """Load configuration from code/config.yaml."""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name):
    """Setup a basic logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def calculate_lempel_ziv_complexity(signal):
    """
    Calculate Lempel-Ziv complexity for a signal.
    
    Args:
        signal (np.ndarray): 1D array of float values.
        
    Returns:
        float: Normalized Lempel-Ziv complexity.
    """
    if len(signal) < 10:
        return 0.0
    
    # Binarize the signal using median threshold
    median_val = np.median(signal)
    binary_signal = (signal >= median_val).astype(int)
    
    # Calculate LZC
    try:
        lzc = lempel_ziv_complexity(binary_signal)
        # Normalize by length to allow comparison across segments
        n = len(binary_signal)
        normalized_lzc = lzc / (n / np.log2(n))
        return float(normalized_lzc)
    except Exception as e:
        logging.getLogger("features").warning(f"LZC calculation failed for segment: {e}")
        return np.nan

def calculate_permutation_entropy(signal, order=3, delay=1):
    """
    Calculate Permutation Entropy for a signal using nolds.
    
    Args:
        signal (np.ndarray): 1D array of float values.
        order (int): Embedding dimension.
        delay (int): Time delay.
        
    Returns:
        float: Permutation entropy.
    """
    if len(signal) < order + delay:
        return 0.0
    
    try:
        pe = nolds.pe(signal, emb_dim=order, lag=delay)
        return float(pe)
    except Exception as e:
        logging.getLogger("features").warning(f"Permutation entropy calculation failed: {e}")
        return np.nan

def process_eeg_segments(raw_eeg, config):
    """
    Process EEG data to extract complexity metrics per channel.
    
    Args:
        raw_eeg (mne.io.Raw): Loaded MNE raw object.
        config (dict): Configuration dictionary.
        
    Returns:
        list: List of dictionaries containing metrics.
    """
    logger = logging.getLogger("features")
    metrics = []
    
    # Get channel names and data
    ch_names = raw_eeg.ch_names
    data, times = raw_eeg.get_data(return_times=True)
    sfreq = raw_eeg.info['sfreq']
    
    logger.info(f"Processing {len(ch_names)} channels with {data.shape[1]} samples")
    
    # Process each channel
    for idx, ch_name in enumerate(ch_names):
        channel_data = data[idx, :]
        
        # Skip non-EEG channels if any
        if not ch_name[0].isalpha():
            continue
            
        lzc = calculate_lempel_ziv_complexity(channel_data)
        pe = calculate_permutation_entropy(channel_data)
        
        metrics.append({
            "participant_id": raw_eeg.filenames[0].split('/')[-1].split('.')[0] if raw_eeg.filenames else "unknown",
            "channel": ch_name,
            "lzc": lzc,
            "pe": pe,
            "sfreq": sfreq,
            "duration_sec": len(channel_data) / sfreq
        })
        
    return metrics

def save_metrics_to_csv(metrics, output_path):
    """
    Save metrics to a CSV file.
    """
    logger = logging.getLogger("features")
    if not metrics:
        logger.warning("No metrics to save.")
        return
        
    try:
        df = pd.DataFrame(metrics)
        # Ensure numeric columns are properly formatted
        for col in ['lzc', 'pe']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df.to_csv(output_path, index=False)
        logger.info(f"Metrics saved to {output_path} ({len(df)} rows)")
    except Exception as e:
        logger.error(f"Failed to save metrics: {e}")
        raise

def main():
    """Main entry point for feature extraction pipeline."""
    logger = setup_logger("features")
    logger.info("Starting feature extraction pipeline")
    
    config = load_config()
    processed_dir = Path("data/processed")
    analysis_dir = Path("data/analysis")
    analysis_dir.mkdir(parents=True, exist_ok=True)
    
    # Load processed data
    processed_file = processed_dir / "cleaned_eeg.fif"
    if not processed_file.exists():
        logger.error("Processed data not found. Run preprocess.py first.")
        sys.exit(1)
    
    # Load data using MNE
    try:
        import mne
        raw = mne.io.read_raw_fif(processed_file, preload=True)
    except Exception as e:
        logger.error(f"Failed to load {processed_file}: {e}")
        sys.exit(1)
    
    # Extract features
    metrics = process_eeg_segments(raw, config)
    
    if not metrics:
        logger.error("No metrics extracted. Check input data.")
        sys.exit(1)
    
    # Save main metrics
    output_path = analysis_dir / "complexity_metrics.csv"
    save_metrics_to_csv(metrics, output_path)
    
    # Save LZC-only metrics as required by data contract (lzc_metrics.csv)
    lzc_path = analysis_dir / "lzc_metrics.csv"
    lzc_metrics = [
        {
            "participant_id": m["participant_id"],
            "channel": m["channel"],
            "lzc": m["lzc"]
        }
        for m in metrics
    ]
    save_metrics_to_csv(lzc_metrics, lzc_path)
    
    logger.info("Feature extraction complete.")

if __name__ == "__main__":
    main()
