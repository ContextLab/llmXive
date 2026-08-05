"""
Feature extraction module for EEG complexity metrics.
Calculates Lempel-Ziv Complexity (LZC) and Permutation Entropy (PE).
"""
import os
import sys
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Tuple, List, Dict, Any

# Import local utilities
from utils.logging import get_logger, save_exclusion_log_csv
from models.eeg_segment import EEGSegment

# Import complexity calculation libraries
try:
    from lempel_ziv_complexity import lempel_ziv_complexity
except ImportError:
    # Fallback implementation if package not found (should be in requirements)
    def lempel_ziv_complexity(sequence):
        """
        Simple LZC implementation.
        """
        sequence = np.array(sequence)
        if len(sequence) == 0:
            return 0.0
        
        # Binarize
        mean_val = np.mean(sequence)
        binary_seq = (sequence > mean_val).astype(int)
        
        # Calculate complexity
        n = len(binary_seq)
        c = 1
        l = 1
        i = 0
        
        while i + l < n:
            if binary_seq[i:i+l] in [binary_seq[j:j+l] for j in range(i+1, i+l+1)]:
                l += 1
            else:
                c += 1
                i += l
                l = 1
                if i >= n:
                    break
        
        return float(c / np.log2(n)) if n > 0 else 0.0

try:
    import nolds
except ImportError:
    nolds = None

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name: str, log_dir: str = "logs") -> logging.Logger:
    """Setup logging infrastructure."""
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # File handler
    fh = logging.FileHandler(os.path.join(log_dir, f"{name}.log"))
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def calculate_lempel_ziv_complexity(signal: np.ndarray) -> float:
    """
    Calculate Lempel-Ziv Complexity for a given signal.
    
    Args:
        signal: 1D numpy array of EEG data.
        
    Returns:
        Normalized LZC value.
    """
    if nolds:
        try:
            return float(nolds.lzc(signal))
        except Exception as e:
            # Fallback to custom implementation
            pass
    
    return lempel_ziv_complexity(signal)

def calculate_permutation_entropy(signal: np.ndarray, embedding_dim: int = 3, time_delay: int = 1) -> float:
    """
    Calculate Permutation Entropy for a given signal.
    
    Args:
        signal: 1D numpy array of EEG data.
        embedding_dim: Dimension of the embedding (m).
        time_delay: Time delay for embedding (tau).
        
    Returns:
        Normalized Permutation Entropy value.
    """
    if nolds:
        try:
            return float(nolds.pe(signal, dim=embedding_dim, tau=time_delay))
        except Exception as e:
            logger = logging.getLogger("features")
            logger.warning(f"nolds.pe failed: {e}, using fallback.")
    
    # Fallback implementation for Permutation Entropy
    return _calculate_permutation_entropy_fallback(signal, embedding_dim, time_delay)

def _calculate_permutation_entropy_fallback(signal: np.ndarray, embedding_dim: int = 3, time_delay: int = 1) -> float:
    """
    Fallback implementation of Permutation Entropy using numpy/scipy.
    """
    n = len(signal)
    if n < embedding_dim + (embedding_dim - 1) * time_delay:
        return 0.0
    
    # Generate permutations
    patterns = []
    for i in range(n - (embedding_dim - 1) * time_delay):
        pattern = [signal[i + j * time_delay] for j in range(embedding_dim)]
        # Get rank order
        rank = sorted(range(embedding_dim), key=lambda k: pattern[k])
        patterns.append(tuple(rank))
    
    if not patterns:
        return 0.0
    
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
    max_entropy = np.log2(np.math.factorial(embedding_dim))
    if max_entropy == 0:
        return 0.0
    
    return float(entropy / max_entropy)

def process_eeg_segments(raw_data_path: str, config: Dict[str, Any], logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Process EEG segments from the preprocessed FIF file.
    
    Args:
        raw_data_path: Path to the cleaned_eeg.fif file.
        config: Configuration dictionary.
        logger: Logger instance.
        
    Returns:
        List of dictionaries containing metrics.
    """
    import mne
    
    if not os.path.exists(raw_data_path):
        raise FileNotFoundError(f"Processed data file not found: {raw_data_path}")
    
    # Load the FIF file
    raw = mne.read_raw_fif(raw_data_path, preload=True)
    
    # Extract channel names
    channel_names = raw.ch_names
    sfreq = raw.info['sfreq']
    
    # Get participant ID from filename or info
    # Assuming filename format: data/processed/participant_{id}_cleaned.fif or similar
    # If the file contains multiple subjects, we need to handle that.
    # For now, assuming single subject per file or a concatenated file with events.
    # Based on T010/T011, we expect a single cleaned file per run, potentially concatenated.
    # Let's assume the file represents one participant for simplicity, or we extract from filename.
    participant_id = Path(raw_data_path).stem.replace("cleaned_eeg_", "").replace("cleaned_", "")
    if participant_id == "cleaned_eeg":
        participant_id = "unknown" # Fallback
    
    metrics = []
    
    # If the file contains multiple segments (epochs), we might need to average or process per epoch.
    # For this task, we process the continuous data per channel.
    
    logger.info(f"Processing {len(channel_names)} channels for participant {participant_id}")
    
    for ch_name in channel_names:
        # Get data for the channel
        data, times = raw[ch_name]
        signal = data[0]
        
        # Skip if signal is too short
        if len(signal) < 100:
            logger.warning(f"Skipping channel {ch_name}: signal too short ({len(signal)} samples)")
            continue
        
        # Calculate LZC
        lzc_val = calculate_lempel_ziv_complexity(signal)
        
        # Calculate PE
        embedding_dim = config.get('embedding_dim', 3)
        time_delay = config.get('time_delay', 1)
        pe_val = calculate_permutation_entropy(signal, embedding_dim, time_delay)
        
        metrics.append({
            'participant_id': participant_id,
            'channel': ch_name,
            'lzc_value': lzc_val,
            'pe_value': pe_val
        })
    
    return metrics

def save_metrics_to_csv(metrics: List[Dict[str, Any]], output_path: str, metric_type: str = "combined"):
    """
    Save calculated metrics to a CSV file.
    
    Args:
        metrics: List of metric dictionaries.
        output_path: Path to the output CSV file.
        metric_type: Type of metrics ('lzc', 'pe', or 'combined').
    """
    if not metrics:
        logger = logging.getLogger("features")
        logger.warning("No metrics to save.")
        # Create empty file with headers
        df = pd.DataFrame(columns=['participant_id', 'channel', f'{metric_type}_value'])
        df.to_csv(output_path, index=False)
        return
    
    df = pd.DataFrame(metrics)
    
    # Ensure columns are in correct order and named correctly based on task
    if metric_type == "lzc":
        df = df[['participant_id', 'channel', 'lzc_value']]
        df.to_csv(output_path, index=False)
    elif metric_type == "pe":
        df = df[['participant_id', 'channel', 'pe_value']]
        df.to_csv(output_path, index=False)
    else:
        # Combined: save both if needed, but task T016 specifically asks for pe_metrics.csv
        # We will save the specific file requested by the calling function
        df.to_csv(output_path, index=False)
    
    logger = logging.getLogger("features")
    logger.info(f"Saved {len(metrics)} metrics to {output_path}")

def main():
    """Main entry point for feature extraction."""
    logger = setup_logger("features")
    logger.info("Starting Permutation Entropy and LZC calculation pipeline")
    
    # Load config
    try:
        config = load_config()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Define paths
    processed_dir = Path("data/processed")
    if not processed_dir.exists():
        logger.error(f"Processed data directory not found: {processed_dir}")
        sys.exit(1)
    
    # Input file for T011 output
    input_file = processed_dir / "cleaned_eeg.fif"
    
    if not input_file.exists():
        logger.error(f"Missing file: {input_file}")
        sys.exit(1)
    
    # Output paths
    lzc_output = processed_dir / "lzc_metrics.csv"
    pe_output = processed_dir / "pe_metrics.csv"
    
    try:
        # Process data
        metrics = process_eeg_segments(str(input_file), config, logger)
        
        if not metrics:
            logger.error("No metrics were calculated.")
            sys.exit(1)
        
        # Save LZC metrics (for T015)
        lzc_only = [m for m in metrics if 'lzc_value' in m]
        if lzc_only:
            save_metrics_to_csv(lzc_only, str(lzc_output), metric_type="lzc")
        else:
            # Fallback: save all if lzc_only is empty but data exists
            pd.DataFrame(metrics)[['participant_id', 'channel', 'lzc_value']].to_csv(lzc_output, index=False)
        
        # Save PE metrics (for T016)
        pe_only = [m for m in metrics if 'pe_value' in m]
        if pe_only:
            save_metrics_to_csv(pe_only, str(pe_output), metric_type="pe")
        else:
            # Fallback
            pd.DataFrame(metrics)[['participant_id', 'channel', 'pe_value']].to_csv(pe_output, index=False)
        
        logger.info("Feature extraction completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during feature extraction: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
