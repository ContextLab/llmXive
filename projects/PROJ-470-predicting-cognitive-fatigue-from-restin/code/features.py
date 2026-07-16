"""
Feature extraction module for EEG complexity metrics.

Calculates Lempel-Ziv Complexity (LZC) and Permutation Entropy (PE)
per channel for preprocessed EEG segments.
"""
import os
import sys
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

# Add parent directory to path for imports if running as script
if 'code' in os.getcwd():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
else:
    sys.path.insert(0, os.path.join(os.getcwd(), 'code'))
    
from utils.logging import get_logger
from models.complexity_metric import MetricType, ComplexityMetric
from models.eeg_segment import EEGSegment

# Try to import lempel-ziv-complexity package, fallback to manual implementation
try:
    from lempel_ziv_complexity import lempel_ziv_complexity
    HAS_LZC_PKG = True
except ImportError:
    HAS_LZC_PKG = False
    pass  # Will implement manual LZC below

# Try to import npe (Permutation Entropy) package
try:
    from npe import permutation_entropy
    HAS_NPE_PKG = True
except ImportError:
    HAS_NPE_PKG = False
    pass  # Will implement manual PE below

# Add manual implementations if packages are missing
if not HAS_LZC_PKG:
    def lempel_ziv_complexity(sequence, base=2):
        """
        Calculate Lempel-Ziv Complexity for a binary or integer sequence.
        
        Args:
            sequence: Input sequence (will be binarized if not already)
            base: Base for complexity calculation (default 2)
        
        Returns:
            float: Normalized LZC value
        """
        # Convert to string if not already
        if not isinstance(sequence, str):
            # Binarize: 1 if above median, 0 if below or equal
            median_val = np.median(sequence)
            binary_seq = ['1' if x > median_val else '0' for x in sequence]
            sequence = ''.join(binary_seq)
        
        # LZC algorithm
        n = len(sequence)
        lzc = 0
        i = 0
        j = 1
        k = 0
        
        while i + k < n:
            if sequence[i:i+k+1] in sequence[j:i+k+1]:
                k += 1
            else:
                if k == 0:
                    lzc += 1
                    i = j
                    j = i + 1
                    k = 0
                else:
                    lzc += 1
                    j = i + k + 1
                    i = j
                    k = 0
        
        # Normalize
        if n == 0:
            return 0.0
        c_max = n / np.log(base, n) if n > 1 else 1
        return lzc / c_max if c_max > 0 else 0.0

if not HAS_NPE_PKG:
    def permutation_entropy(signal, order=3, delay=1):
        """
        Calculate Permutation Entropy of a time series.
        
        Args:
            signal: Input time series (1D array)
            order: Embedding dimension (default 3)
            delay: Time delay (default 1)
        
        Returns:
            float: Permutation entropy value (0 to log2(order!))
        """
        n = len(signal)
        if n < order + (order - 1) * delay:
            return 0.0
        
        # Count ordinal patterns
        pattern_counts = {}
        num_patterns = 0
        
        for i in range(n - (order - 1) * delay):
            # Extract pattern
            pattern = [signal[i + j * delay] for j in range(order)]
            
            # Get ordinal pattern (ranks)
            # Use argsort to get ranks
            ranks = np.argsort(np.argsort(pattern))
            pattern_tuple = tuple(ranks)
            
            pattern_counts[pattern_tuple] = pattern_counts.get(pattern_tuple, 0) + 1
            num_patterns += 1
        
        if num_patterns == 0:
            return 0.0
        
        # Calculate probabilities
        probs = [count / num_patterns for count in pattern_counts.values()]
        
        # Calculate entropy
        entropy = 0.0
        for p in probs:
            if p > 0:
                entropy -= p * np.log2(p)
        
        return entropy

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def calculate_lzc(signal: np.ndarray, base: int = 2) -> float:
    """
    Calculate Lempel-Ziv Complexity for a signal.
    
    Args:
        signal: 1D numpy array of EEG values
        base: Base for complexity calculation
    
    Returns:
        float: Normalized LZC value
    """
    if len(signal) == 0:
        return 0.0
    
    try:
        return lempel_ziv_complexity(signal, base)
    except Exception as e:
        logger = get_logger(__name__)
        logger.warning(f"Error calculating LZC: {e}")
        return float('nan')

def calculate_permutation_entropy(signal: np.ndarray, order: int = 3, delay: int = 1) -> float:
    """
    Calculate Permutation Entropy for a signal.
    
    Args:
        signal: 1D numpy array of EEG values
        order: Embedding dimension
        delay: Time delay
    
    Returns:
        float: Permutation entropy value
    """
    if len(signal) == 0:
        return 0.0
    
    try:
        return permutation_entropy(signal, order, delay)
    except Exception as e:
        logger = get_logger(__name__)
        logger.warning(f"Error calculating Permutation Entropy: {e}")
        return float('nan')

def process_eeg_segments(
    eeg_data: np.ndarray,
    metadata: Dict[str, Any],
    config: Dict[str, Any],
    logger: Any
) -> Tuple[List[ComplexityMetric], List[ComplexityMetric]]:
    """
    Process EEG segments to calculate LZC and Permutation Entropy.
    
    Args:
        eeg_data: 2D numpy array (n_channels, n_samples)
        metadata: Dictionary with channel names, participant IDs, etc.
        config: Configuration dictionary
        logger: Logger instance
    
    Returns:
        Tuple of (LZC metrics list, PE metrics list)
    """
    lzc_metrics = []
    pe_metrics = []
    
    # Get parameters from config
    lzc_base = config.get('lzc_base', 2)
    pe_order = config.get('pe_order', 3)
    pe_delay = config.get('pe_delay', 1)
    
    channel_names = metadata.get('channel_names', [f'CH{i}' for i in range(eeg_data.shape[0])])
    participant_id = metadata.get('participant_id', 'unknown')
    session_id = metadata.get('session_id', 'unknown')
    
    for i, channel_name in enumerate(channel_names):
        if i >= eeg_data.shape[0]:
            break
        
        channel_data = eeg_data[i, :]
        
        # Calculate LZC
        lzc_value = calculate_lzc(channel_data, lzc_base)
        lzc_metric = ComplexityMetric(
            participant_id=participant_id,
            session_id=session_id,
            channel=channel_name,
            metric_type=MetricType.LZC,
            value=lzc_value,
            parameters={'base': lzc_base}
        )
        lzc_metrics.append(lzc_metric)
        
        # Calculate Permutation Entropy
        pe_value = calculate_permutation_entropy(channel_data, pe_order, pe_delay)
        pe_metric = ComplexityMetric(
            participant_id=participant_id,
            session_id=session_id,
            channel=channel_name,
            metric_type=MetricType.PE,
            value=pe_value,
            parameters={'order': pe_order, 'delay': pe_delay}
        )
        pe_metrics.append(pe_metric)
        
        logger.info(f"Calculated metrics for {participant_id}/{channel_name}: "
                   f"LZC={lzc_value:.4f}, PE={pe_value:.4f}")
    
    return lzc_metrics, pe_metrics

def save_metrics_to_csv(
    metrics: List[ComplexityMetric],
    output_path: str,
    metric_type: MetricType
) -> bool:
    """
    Save complexity metrics to a CSV file.
    
    Args:
        metrics: List of ComplexityMetric objects
        output_path: Path to output CSV file
        metric_type: Type of metric being saved
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not metrics:
        logger = get_logger(__name__)
        logger.warning(f"No metrics to save for {metric_type}")
        return False
    
    # Create DataFrame
    data = []
    for m in metrics:
        data.append({
            'participant_id': m.participant_id,
            'session_id': m.session_id,
            'channel': m.channel,
            'metric_type': m.metric_type.value,
            'value': m.value,
            **m.parameters
        })
    
    df = pd.DataFrame(data)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    logger = get_logger(__name__)
    logger.info(f"Saved {len(metrics)} {metric_type.value} metrics to {output_path}")
    
    return True

def main():
    """Main entry point for feature extraction pipeline."""
    logger = get_logger(__name__)
    logger.info("Starting feature extraction pipeline")
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
    
    # Input and output paths
    input_path = config.get('preprocessed_eeg_path', 'data/processed/preprocessed_eeg.npy')
    lzc_output_path = config.get('lzc_output_path', 'data/processed/lzc_metrics.csv')
    pe_output_path = config.get('pe_output_path', 'data/processed/pe_metrics.csv')
    metadata_path = config.get('metadata_path', 'data/processed/metadata.json')
    
    logger.info(f"Input: {input_path}")
    logger.info(f"Output LZC: {lzc_output_path}")
    logger.info(f"Output PE: {pe_output_path}")
    
    # Load preprocessed EEG data
    if not os.path.exists(input_path):
        logger.error(f"Data file not found: {input_path}")
        sys.exit(1)
    
    try:
        eeg_data = np.load(input_path, allow_pickle=True)
        # Handle case where data is stored as object array
        if eeg_data.ndim == 0 or (eeg_data.ndim == 1 and isinstance(eeg_data[0], dict)):
            # Try to extract from object array
            if eeg_data.ndim == 0:
                data_obj = eeg_data.item()
                eeg_data = data_obj.get('data')
                metadata = data_obj.get('metadata', {})
            else:
                # Array of dicts
                first_item = eeg_data[0]
                eeg_data = first_item.get('data') if isinstance(first_item, dict) else None
                metadata = first_item.get('metadata', {}) if isinstance(first_item, dict) else {}
        else:
            metadata = {}
    except Exception as e:
        logger.error(f"Failed to load EEG data: {e}")
        sys.exit(1)
    
    if eeg_data is None or eeg_data.size == 0:
        logger.error("No valid EEG data found")
        sys.exit(1)
    
    logger.info(f"Loaded EEG data: shape={eeg_data.shape}")
    
    # Load metadata if available
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                metadata.update(json.load(f))
        except Exception as e:
            logger.warning(f"Failed to load metadata: {e}")
    else:
        logger.info("No metadata file found, using defaults")
    
    # Ensure channel names exist in metadata
    if 'channel_names' not in metadata:
        metadata['channel_names'] = [f'CH{i}' for i in range(eeg_data.shape[0])]
    
    if 'participant_id' not in metadata:
        metadata['participant_id'] = 'unknown'
    
    if 'session_id' not in metadata:
        metadata['session_id'] = 'unknown'
    
    # Process segments
    lzc_metrics, pe_metrics = process_eeg_segments(eeg_data, metadata, config, logger)
    
    # Save results
    if not save_metrics_to_csv(lzc_metrics, lzc_output_path, MetricType.LZC):
        logger.error("Failed to save LZC metrics")
        sys.exit(1)
    
    if not save_metrics_to_csv(pe_metrics, pe_output_path, MetricType.PE):
        logger.error("Failed to save PE metrics")
        sys.exit(1)
    
    logger.info("Feature extraction completed successfully")

if __name__ == "__main__":
    main()
