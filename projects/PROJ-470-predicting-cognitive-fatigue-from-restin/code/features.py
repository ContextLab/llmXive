import os
import sys
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import mne

# Import existing utility functions
from utils.logging import get_logger, log_artifact_rejection

# Import existing model classes if needed
from models.eeg_segment import EEGSegment
from models.complexity_metric import MetricType, ComplexityMetric

def load_config(config_path='code/config.yaml'):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name, log_file='logs/features.log'):
    """Setup logging infrastructure."""
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    return logger

def calculate_lempel_ziv_complexity(signal, sampling_rate=256):
    """
    Calculate Lempel-Ziv Complexity (LZC) for a given signal.
    
    Args:
        signal: 1D numpy array of EEG signal
        sampling_rate: Sampling rate in Hz
        
    Returns:
        float: LZC value
    """
    if len(signal) == 0:
        return 0.0
        
    # Normalize and binarize the signal
    signal = np.asarray(signal, dtype=float)
    if np.std(signal) > 0:
        signal = (signal - np.mean(signal)) / np.std(signal)
    else:
        return 0.0
        
    # Binarize: 1 if above mean, 0 otherwise
    threshold = np.mean(signal)
    binary_signal = (signal > threshold).astype(int)
    
    # LZC calculation
    n = len(binary_signal)
    lzc = 0
    i = 0
    j = 0
    k = 0
    l = 1
    
    while i < n:
        if i == n - 1:
            lzc += 1
            break
            
        if binary_signal[i] == binary_signal[j]:
            if i == j:
                j += 1
                i += 1
            else:
                if i + 1 < n:
                    if binary_signal[i + 1] == binary_signal[j + 1]:
                        j += 1
                        i += 1
                    else:
                        lzc += 1
                        j = 0
                        i += 1
                        l += 1
                else:
                    lzc += 1
                    break
        else:
            j = 0
            i += 1
            l += 1
            
    # Normalized LZC
    if n > 0:
        lzc_normalized = lzc / (n / np.log2(n))
    else:
        lzc_normalized = 0.0
        
    return float(lzc_normalized)

def calculate_permutation_entropy(signal, embedding_dim=3, time_delay=1):
    """
    Calculate Permutation Entropy (PE) for a given signal.
    
    Args:
        signal: 1D numpy array of EEG signal
        embedding_dim: Embedding dimension (m)
        time_delay: Time delay (tau)
        
    Returns:
        float: Permutation Entropy value (normalized to [0, 1])
    """
    if len(signal) < embedding_dim + (embedding_dim - 1) * time_delay:
        return 0.0
        
    signal = np.asarray(signal, dtype=float)
    n = len(signal)
    
    # Create embedded vectors
    n_vectors = n - (embedding_dim - 1) * time_delay
    if n_vectors <= 0:
        return 0.0
        
    # Count permutations
    from collections import Counter
    import math
    
    # Generate all possible permutations of range(embedding_dim)
    from itertools import permutations
    all_perms = list(permutations(range(embedding_dim)))
    perm_map = {p: i for i, p in enumerate(all_perms)}
    
    permutation_counts = Counter()
    
    for i in range(n_vectors):
        # Extract embedded vector
        vector = [signal[i + j * time_delay] for j in range(embedding_dim)]
        
        # Get permutation pattern by sorting indices
        sorted_indices = sorted(range(embedding_dim), key=lambda k: vector[k])
        pattern = tuple(sorted_indices)
        
        # Count this permutation
        permutation_counts[pattern] += 1
    
    # Calculate entropy
    total = sum(permutation_counts.values())
    if total == 0:
        return 0.0
        
    entropy = 0.0
    for count in permutation_counts.values():
        if count > 0:
            p = count / total
            entropy -= p * np.log2(p)
    
    # Normalize by maximum possible entropy (log2(m!))
    max_entropy = np.log2(math.factorial(embedding_dim))
    if max_entropy > 0:
        normalized_entropy = entropy / max_entropy
    else:
        normalized_entropy = 0.0
        
    return float(normalized_entropy)

def process_eeg_segments(eeg_data, config, logger):
    """
    Process EEG data to calculate complexity metrics for each participant and channel.
    
    Args:
        eeg_data: MNE Raw object containing preprocessed EEG
        config: Configuration dictionary
        logger: Logger instance
        
    Returns:
        list: List of dictionaries containing metrics
    """
    metrics = []
    participant_id = eeg_data.info.get('subject_info', {}).get('his_id', 'unknown')
    if participant_id == 'unknown':
        # Try to extract from filename or other metadata
        participant_id = 'participant_001'
        
    channels = eeg_data.ch_names
    sampling_rate = eeg_data.info['sfreq']
    
    logger.info(f"Processing participant: {participant_id}, channels: {len(channels)}")
    
    for channel in channels:
        try:
            # Extract channel data
            channel_data, _ = eeg_data.get_data(picks=[channel])
            channel_signal = channel_data[0]
            
            # Calculate LZC
            lzc_value = calculate_lempel_ziv_complexity(channel_signal, sampling_rate)
            metrics.append({
                'participant_id': participant_id,
                'channel': channel,
                'lzc_value': lzc_value,
                'metric_type': 'LZC'
            })
            
            # Calculate Permutation Entropy
            pe_value = calculate_permutation_entropy(
                channel_signal, 
                embedding_dim=config.get('embedding_dim', 3),
                time_delay=config.get('time_delay', 1)
            )
            metrics.append({
                'participant_id': participant_id,
                'channel': channel,
                'pe_value': pe_value,
                'metric_type': 'PE'
            })
            
        except Exception as e:
            logger.warning(f"Error processing channel {channel}: {str(e)}")
            continue
            
    return metrics

def save_metrics_to_csv(metrics, output_path, metric_type):
    """
    Save complexity metrics to CSV file.
    
    Args:
        metrics: List of metric dictionaries
        output_path: Path to output CSV file
        metric_type: Type of metric ('LZC' or 'PE')
    """
    if not metrics:
        raise ValueError(f"No metrics to save for {metric_type}")
        
    # Filter metrics for the specific type
    filtered_metrics = [m for m in metrics if m.get('metric_type') == metric_type]
    
    if not filtered_metrics:
        raise ValueError(f"No {metric_type} metrics found to save")
        
    # Create DataFrame with correct schema
    if metric_type == 'LZC':
        df = pd.DataFrame(filtered_metrics, columns=['participant_id', 'channel', 'lzc_value'])
    elif metric_type == 'PE':
        df = pd.DataFrame(filtered_metrics, columns=['participant_id', 'channel', 'pe_value'])
    else:
        raise ValueError(f"Unknown metric type: {metric_type}")
        
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    return len(df)

def main():
    """Main function to run the feature extraction pipeline."""
    logger = setup_logger('features')
    logger.info("Starting Permutation Entropy and LZC calculation pipeline")
    
    try:
        # Load configuration
        config = load_config()
        logger.info(f"Configuration loaded: {config}")
        
        # Check for preprocessed data
        processed_dir = Path('data/processed')
        if not processed_dir.exists():
            logger.error("Processed data directory not found: data/processed")
            sys.exit(1)
            
        cleaned_eeg_path = processed_dir / 'cleaned_eeg.fif'
        if not cleaned_eeg_path.exists():
            logger.error(f"Missing file: {cleaned_eeg_path}")
            sys.exit(1)
            
        logger.info(f"Loading preprocessed EEG from: {cleaned_eeg_path}")
        
        # Load EEG data
        eeg_data = mne.io.read_raw_fif(str(cleaned_eeg_path), preload=False)
        
        # Process data and calculate metrics
        all_metrics = process_eeg_segments(eeg_data, config, logger)
        
        # Save LZC metrics
        lzc_output_path = 'data/processed/lzc_metrics.csv'
        lzc_count = save_metrics_to_csv(all_metrics, lzc_output_path, 'LZC')
        logger.info(f"Saved {lzc_count} LZC metrics to {lzc_output_path}")
        
        # Save PE metrics
        pe_output_path = 'data/processed/pe_metrics.csv'
        pe_count = save_metrics_to_csv(all_metrics, pe_output_path, 'PE')
        logger.info(f"Saved {pe_count} PE metrics to {pe_output_path}")
        
        logger.info("Feature extraction pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
