import os
import sys
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import mne
from scipy import signal
import logging
from datetime import datetime
import time
from typing import List, Dict, Tuple, Optional, Iterator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/features.log')
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_path: str = "code/config.yaml") -> Dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML config: {e}")
        sys.exit(1)

def calculate_lzc(signal_data: np.ndarray, sampling_rate: float) -> float:
    """
    Calculate Lempel-Ziv Complexity for a given signal.
    
    Args:
        signal_data: 1D numpy array of signal values
        sampling_rate: Sampling rate in Hz
        
    Returns:
        Normalized LZC value between 0 and 1
    """
    # Discretize the signal to binary (0 or 1)
    median_val = np.median(signal_data)
    binary_signal = (signal_data > median_val).astype(int)
    
    # Convert to string of '0's and '1's
    binary_str = ''.join(map(str, binary_signal))
    
    # Calculate LZC
    n = len(binary_str)
    if n == 0:
        return 0.0
        
    c = 1  # Start with first symbol
    i = 0
    j = 1
    k = 0
    
    while i + j <= n:
        if binary_str[i:i+j] in binary_str[:i+j-k]:
            k += 1
            if i + j == n:
                c += 1
            j += 1
        else:
            if k == 0:
                k = 1
            c += 1
            i += j
            j = 1
            k = 0
            
    # Normalize by the maximum possible complexity
    max_c = n / np.log2(n) if n > 1 else 1
    lzc_normalized = c / max_c
    
    return float(np.clip(lzc_normalized, 0, 1))

def calculate_permutation_entropy(
    signal_data: np.ndarray, 
    sampling_rate: float, 
    embedding_dim: int = 3, 
    time_delay: int = 1
) -> float:
    """
    Calculate Permutation Entropy for a given signal.
    
    Args:
        signal_data: 1D numpy array of signal values
        sampling_rate: Sampling rate in Hz
        embedding_dim: Dimension of embedding (m)
        time_delay: Time delay for embedding (tau)
        
    Returns:
        Normalized PE value between 0 and 1
    """
    n = len(signal_data)
    
    # Ensure we have enough data points
    if n < embedding_dim + (embedding_dim - 1) * time_delay:
        logger.warning(f"Signal length {n} too short for embedding_dim={embedding_dim}")
        return 0.0
        
    # Create embedded vectors
    num_vectors = n - (embedding_dim - 1) * time_delay
    if num_vectors <= 0:
        return 0.0
        
    # Extract patterns and their ranks
    patterns = []
    for i in range(num_vectors):
        vector = signal_data[i:i + embedding_dim * time_delay:time_delay]
        # Get the rank order of the vector
        rank = np.argsort(np.argsort(vector))
        patterns.append(tuple(rank))
        
    # Count frequency of each pattern
    from collections import Counter
    pattern_counts = Counter(patterns)
    total_patterns = len(patterns)
    
    # Calculate probabilities
    probabilities = np.array(list(pattern_counts.values())) / total_patterns
    
    # Calculate entropy
    # Avoid log(0) by filtering out zero probabilities
    probs_nonzero = probabilities[probabilities > 0]
    if len(probs_nonzero) == 0:
        return 0.0
        
    entropy = -np.sum(probs_nonzero * np.log2(probs_nonzero))
    
    # Normalize by maximum possible entropy (log2 of factorial of embedding_dim)
    max_entropy = np.log2(np.math.factorial(embedding_dim))
    
    if max_entropy == 0:
        return 0.0
        
    pe_normalized = entropy / max_entropy
    
    return float(np.clip(pe_normalized, 0, 1))

def process_eeg_segments(
    eeg_data: np.ndarray,
    sfreq: float,
    channels: List[str],
    segment_duration: float = 120.0
) -> Iterator[Tuple[str, str, np.ndarray]]:
    """
    Generator to yield EEG segments for processing.
    
    Args:
        eeg_data: 2D numpy array (n_channels, n_samples)
        sfreq: Sampling frequency
        channels: List of channel names
        segment_duration: Duration of each segment in seconds
        
    Yields:
        Tuples of (participant_id, channel_name, segment_data)
    """
    segment_samples = int(segment_duration * sfreq)
    n_channels, n_samples = eeg_data.shape
    
    # Assume participant_id is derived from the filename or context
    # For now, we'll use a generic ID
    participant_id = "participant_001"
    
    # Process each channel
    for i, channel in enumerate(channels):
        channel_data = eeg_data[i, :]
        
        # Split into segments if data is long enough
        num_segments = n_samples // segment_samples
        
        for seg_idx in range(num_segments):
            start_idx = seg_idx * segment_samples
            end_idx = start_idx + segment_samples
            segment = channel_data[start_idx:end_idx]
            
            yield participant_id, channel, segment

def save_metrics_to_csv(
    metrics: List[Dict],
    output_path: str,
    columns: List[str]
) -> None:
    """
    Save metrics to a CSV file.
    
    Args:
        metrics: List of dictionaries containing metrics
        output_path: Path to output CSV file
        columns: List of column names in order
    """
    if not metrics:
        logger.warning("No metrics to save.")
        # Create an empty file with headers
        df = pd.DataFrame(columns=columns)
    else:
        df = pd.DataFrame(metrics, columns=columns)
        
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Metrics saved to {output_path} with {len(df)} rows")

def main():
    """Main function to run the feature extraction pipeline."""
    logger.info("Starting feature extraction pipeline")
    
    # Load configuration
    config = load_config()
    
    # Define paths
    input_path = Path("data/processed/cleaned_eeg.fif")
    lzc_output_path = Path("data/processed/lzc_metrics.csv")
    pe_output_path = Path("data/processed/pe_metrics.csv")
    
    # Check if input file exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run preprocessing first to generate cleaned_eeg.fif")
        sys.exit(1)
        
    # Load EEG data
    logger.info(f"Loading EEG data from {input_path}")
    try:
        raw = mne.io.read_raw_fif(input_path, preload=False)
        eeg_data = raw.get_data()  # Shape: (n_channels, n_samples)
        sfreq = raw.info['sfreq']
        channels = raw.ch_names
        logger.info(f"Loaded data: {eeg_data.shape}, sampling rate: {sfreq} Hz, channels: {len(channels)}")
    except Exception as e:
        logger.error(f"Failed to load EEG data: {e}")
        sys.exit(1)
        
    # Parameters
    embedding_dim = config.get('embedding_dim', 3)
    segment_duration = 120.0  # seconds
    
    # Lists to store metrics
    lzc_metrics = []
    pe_metrics = []
    
    # Process each channel
    logger.info("Processing EEG segments for complexity metrics...")
    start_time = time.time()
    
    for participant_id, channel, segment in process_eeg_segments(
        eeg_data, sfreq, channels, segment_duration
    ):
        # Calculate LZC
        lzc_val = calculate_lzc(segment, sfreq)
        lzc_metrics.append({
            'participant_id': participant_id,
            'channel': channel,
            'lzc_value': lzc_val
        })
        
        # Calculate Permutation Entropy
        pe_val = calculate_permutation_entropy(segment, sfreq, embedding_dim)
        pe_metrics.append({
            'participant_id': participant_id,
            'channel': channel,
            'pe_value': pe_val
        })
        
    elapsed_time = time.time() - start_time
    logger.info(f"Feature extraction completed in {elapsed_time:.2f} seconds")
    
    # Define column order
    lzc_columns = ['participant_id', 'channel', 'lzc_value']
    pe_columns = ['participant_id', 'channel', 'pe_value']
    
    # Save LZC metrics
    save_metrics_to_csv(lzc_metrics, str(lzc_output_path), lzc_columns)
    
    # Save PE metrics
    save_metrics_to_csv(pe_metrics, str(pe_output_path), pe_columns)
    
    # Verification: Run on synthetic signal
    logger.info("Running verification on synthetic signal...")
    try:
        # Generate synthetic white noise
        n_samples = int(256 * 120)  # 256 Hz * 120 seconds
        np.random.seed(42)
        synthetic_signal = np.random.randn(n_samples)
        
        # Calculate LZC
        synthetic_lzc = calculate_lzc(synthetic_signal, 256)
        logger.info(f"Synthetic LZC (white noise): {synthetic_lzc:.4f}")
        
        # Calculate PE
        synthetic_pe = calculate_permutation_entropy(synthetic_signal, 256, embedding_dim=3)
        logger.info(f"Synthetic PE (white noise): {synthetic_pe:.4f}")
        
        # Verify ranges
        assert 0 <= synthetic_lzc <= 1, f"LZC {synthetic_lzc} out of range [0, 1]"
        assert 0 <= synthetic_pe <= 1, f"PE {synthetic_pe} out of range [0, 1]"
        
        logger.info("Verification passed: Synthetic signal metrics are within theoretical range [0, 1]")
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)
        
    logger.info("Feature extraction pipeline completed successfully")

if __name__ == "__main__":
    main()
