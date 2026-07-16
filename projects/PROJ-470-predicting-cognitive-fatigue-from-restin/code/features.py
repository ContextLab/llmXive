import os
import sys
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Importing local utilities
sys.path.insert(0, str(Path(__file__).parent))
from utils.logging import get_logger
from models.complexity_metric import MetricType, ComplexityMetric

# Try to import lempel-ziv-complexity, fallback to manual implementation if missing
try:
    from lempel_ziv_complexity import lempel_ziv_complexity
    HAS_LZC_PKG = True
except ImportError:
    HAS_LZC_PKG = False
    # Manual implementation of Lempel-Ziv Complexity for binary sequences
    def calculate_lzc_manual(binary_seq: List[int]) -> float:
        """
        Calculates the Lempel-Ziv complexity of a binary sequence.
        This is a fallback if the 'lempel-ziv-complexity' package is not installed.
        """
        if not binary_seq:
            return 0.0
        
        # Normalize complexity by length
        n = len(binary_seq)
        if n == 0:
            return 0.0
        
        # LZ76 algorithm implementation
        c = 1
        l = 1
        i = 0
        j = 0
        
        # Convert to string for easier slicing if not already
        s = "".join(str(x) for x in binary_seq)
        
        while i + j + 1 < n:
            # Check if s[i:i+j+1] is in s[0:i+j]
            sub = s[i:i+j+1]
            if sub in s[0:i+j]:
                j += 1
            else:
                c += 1
                i = i + j + 1
                j = 0
        
        # Handle the last part
        if j > 0:
            c += 1
        
        # Normalization factor
        # For binary sequences, the normalization factor is n / log2(n)
        # However, standard LZC often uses a slightly different normalization
        # to bound it between 0 and 1.
        # Standard formula: LZC = c / (n / log2(n))
        
        if n <= 1:
            return 0.0
            
        norm_factor = n / np.log2(n)
        return c / norm_factor

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def calculate_lzc(signal: np.ndarray, threshold: float = None) -> float:
    """
    Calculate Lempel-Ziv Complexity for a given signal.
    
    Args:
        signal: 1D numpy array of EEG data.
        threshold: Threshold for binarization. If None, uses median.
    
    Returns:
        Normalized Lempel-Ziv complexity value.
    """
    if len(signal) == 0:
        return 0.0
    
    # Binarize the signal
    if threshold is None:
        threshold = np.median(signal)
    
    binary_seq = (signal > threshold).astype(int).tolist()
    
    if HAS_LZC_PKG:
        # Use the library function if available
        # lempel_ziv_complexity returns a tuple (complexity, normalized_complexity)
        # depending on version, but usually we want the normalized one
        try:
            lzc_val = lempel_ziv_complexity(binary_seq)
            # The library might return a tuple or a single float depending on version
            if isinstance(lzc_val, tuple):
                return float(lzc_val[1]) # Return normalized
            return float(lzc_val)
        except Exception:
            # Fallback to manual if library fails
            return calculate_lzc_manual(binary_seq)
    else:
        return calculate_lzc_manual(binary_seq)

def calculate_permutation_entropy(signal: np.ndarray, order: int = 3, delay: int = 1) -> float:
    """
    Calculate Permutation Entropy for a given signal.
    
    Args:
        signal: 1D numpy array of EEG data.
        order: Order of permutation (number of elements in each pattern).
        delay: Time delay between elements.
    
    Returns:
        Permutation entropy value.
    """
    if len(signal) < order * delay:
        return 0.0
    
    n = len(signal)
    # Number of patterns
    num_patterns = n - (order - 1) * delay
    
    if num_patterns <= 0:
        return 0.0
    
    # Extract patterns
    patterns = []
    for i in range(num_patterns):
        pattern = [signal[i + j * delay] for j in range(order)]
        # Get the rank order (permutation)
        rank = sorted(range(order), key=lambda k: pattern[k])
        patterns.append(tuple(rank))
    
    # Count frequencies
    from collections import Counter
    counts = Counter(patterns)
    total = sum(counts.values())
    
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

def process_eeg_segments(data_path: str, config: Dict[str, Any], logger) -> List[ComplexityMetric]:
    """
    Process EEG segments from a preprocessed data file.
    
    Args:
        data_path: Path to the preprocessed EEG data file (.npy).
        config: Configuration dictionary.
        logger: Logger instance.
    
    Returns:
        List of ComplexityMetric objects.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Preprocessed data file not found: {data_path}")
    
    logger.info(f"Loading preprocessed EEG data from {data_path}")
    data = np.load(data_path, allow_pickle=True)
    
    # Expected format: dictionary or structured array with keys:
    # 'data': (n_epochs, n_channels, n_samples)
    # 'info': metadata (ch_names, sfreq, etc.)
    # 'metadata': participant IDs, etc.
    
    if isinstance(data, dict):
        eeg_data = data.get('data')
        ch_names = data.get('ch_names', [f'CH{i}' for i in range(eeg_data.shape[1])])
        sfreq = data.get('sfreq', 250.0)
        metadata = data.get('metadata', {})
    else:
        # Fallback for simple numpy array
        raise ValueError("Data must be a dictionary with 'data', 'ch_names', 'sfreq' keys.")
    
    if eeg_data is None:
        raise ValueError("No EEG data found in the file.")
    
    logger.info(f"Processing {eeg_data.shape[0]} epochs with {eeg_data.shape[1]} channels")
    
    metrics = []
    lzc_order = config.get('features', {}).get('lzc_threshold', None)
    pe_order = config.get('features', {}).get('pe_order', 3)
    pe_delay = config.get('features', {}).get('pe_delay', 1)
    
    for epoch_idx in range(eeg_data.shape[0]):
        epoch_data = eeg_data[epoch_idx] # (n_channels, n_samples)
        
        # Determine participant ID for this epoch
        # Assuming metadata is a list of dicts or similar
        if isinstance(metadata, list) and epoch_idx < len(metadata):
            pid = metadata[epoch_idx].get('participant_id', f'S{epoch_idx}')
        else:
            pid = f'S{epoch_idx}'
        
        for ch_idx, ch_name in enumerate(ch_names):
            signal = epoch_data[ch_idx]
            
            # Calculate LZC
            lzc_val = calculate_lzc(signal, threshold=lzc_order)
            metrics.append(ComplexityMetric(
                participant_id=pid,
                channel=ch_name,
                epoch=epoch_idx,
                metric_type=MetricType.LZC,
                value=lzc_val
            ))
            
            # Calculate PE
            pe_val = calculate_permutation_entropy(signal, order=pe_order, delay=pe_delay)
            metrics.append(ComplexityMetric(
                participant_id=pid,
                channel=ch_name,
                epoch=epoch_idx,
                metric_type=MetricType.PE,
                value=pe_val
            ))
    
    logger.info(f"Generated {len(metrics)} complexity metrics")
    return metrics

def save_metrics_to_csv(metrics: List[ComplexityMetric], output_path: str, metric_type: MetricType):
    """
    Save a list of ComplexityMetrics to a CSV file.
    
    Args:
        metrics: List of ComplexityMetric objects.
        output_path: Path to the output CSV file.
        metric_type: Type of metric to filter (LZC or PE).
    """
    filtered_metrics = [m for m in metrics if m.metric_type == metric_type]
    
    if not filtered_metrics:
        raise ValueError(f"No metrics of type {metric_type} found to save.")
    
    data = {
        'participant_id': [m.participant_id for m in filtered_metrics],
        'channel': [m.channel for m in filtered_metrics],
        'epoch': [m.epoch for m in filtered_metrics],
        'value': [m.value for m in filtered_metrics]
    }
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(filtered_metrics)} {metric_type.value} metrics to {output_path}")

def main():
    """Main entry point for feature extraction."""
    config = load_config()
    logger = get_logger("features")
    
    input_path = config.get('paths', {}).get('preprocessed_data', 'data/processed/preprocessed_eeg.npy')
    lzc_output = config.get('paths', {}).get('lzc_metrics', 'data/processed/lzc_metrics.csv')
    pe_output = config.get('paths', {}).get('pe_metrics', 'data/processed/pe_metrics.csv')
    
    logger.info("Starting feature extraction pipeline")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output LZC: {lzc_output}")
    logger.info(f"Output PE: {pe_output}")
    
    try:
        metrics = process_eeg_segments(input_path, config, logger)
        
        # Save LZC metrics
        save_metrics_to_csv(metrics, lzc_output, MetricType.LZC)
        
        # Save PE metrics
        save_metrics_to_csv(metrics, pe_output, MetricType.PE)
        
        logger.info("Feature extraction completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during feature extraction: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()