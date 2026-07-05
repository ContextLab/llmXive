import os
import sys
import yaml
import pandas as pd
import numpy as np
from pathlib import Path

# Import from local models if available, otherwise handle gracefully
try:
    from models.complexity_metric import MetricType, ComplexityMetric
except ImportError:
    MetricType = None
    ComplexityMetric = None

# Import logging utilities
try:
    from utils.logging import get_logger, log_artifact_rejection
except ImportError:
    def get_logger(name):
        import logging
        return logging.getLogger(name)
    def log_artifact_rejection(*args, **kwargs):
        pass

def load_config(config_path="code/config.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def calculate_lzc(signal, order=2):
    """
    Calculate Lempel-Ziv Complexity for a 1D signal.
    
    Parameters:
    -----------
    signal : np.ndarray
        1D array of signal values
    order : int
        Thresholding order (1 = median, 2 = mean)
        
    Returns:
    --------
    float
        Normalized LZ complexity value
    """
    if len(signal) < 10:
        return 0.0
        
    # Binarize signal
    if order == 1:
        threshold = np.median(signal)
    else:
        threshold = np.mean(signal)
        
    binary_signal = (signal > threshold).astype(int)
    
    # LZ76 complexity calculation
    n = len(binary_signal)
    lzc = 0
    i = 0
    while i < n:
        lzc += 1
        j = i + 1
        k = 0
        while j < n and k <= (j - i):
            if binary_signal[i + k] != binary_signal[j]:
                break
            k += 1
        if k > (j - i):
            i = j
        else:
            i += 1
            
    # Normalize by n / log2(n)
    if n > 1:
        return lzc / (n / np.log2(n))
    return 0.0

def calculate_permutation_entropy(signal, order=3, delay=1, n_samples=10000):
    """
    Calculate Permutation Entropy for a 1D signal.
    
    Parameters:
    -----------
    signal : np.ndarray
        1D array of signal values
    order : int
        Embedding dimension (number of elements in each pattern)
    delay : int
        Time delay between elements in the pattern
    n_samples : int
        Number of samples to use for calculation (for large signals)
        
    Returns:
    --------
    float
        Permutation entropy value (normalized to [0, 1])
    """
    if len(signal) < order * delay:
        return 0.0
        
    # Limit samples for performance on large datasets
    if len(signal) > n_samples:
        indices = np.random.choice(len(signal), n_samples, replace=False)
        signal = signal[np.sort(indices)]
        
    n = len(signal)
    n_patterns = n - (order - 1) * delay
    
    if n_patterns <= 0:
        return 0.0
        
    # Extract ordinal patterns
    patterns = []
    for i in range(n_patterns):
        pattern = signal[i:i + order * delay:delay]
        # Get the rank order of the pattern
        rank = np.argsort(pattern)
        patterns.append(tuple(rank))
        
    # Calculate probability distribution
    from collections import Counter
    pattern_counts = Counter(patterns)
    total_patterns = sum(pattern_counts.values())
    
    if total_patterns == 0:
        return 0.0
        
    # Calculate entropy
    entropy = 0.0
    max_entropy = np.log2(np.math.factorial(order))
    
    for count in pattern_counts.values():
        if count > 0:
            p = count / total_patterns
            entropy -= p * np.log2(p)
            
    # Normalize to [0, 1]
    if max_entropy > 0:
        return entropy / max_entropy
    return 0.0

def main():
    """
    Main function to calculate Permutation Entropy for all channels
    in the preprocessed data and save to data/processed/pe_metrics.csv.
    """
    logger = get_logger("features")
    logger.info("Starting Permutation Entropy calculation")
    
    config = load_config()
    
    # Paths
    base_dir = Path(config.get("paths", {}).get("base", "."))
    processed_dir = base_dir / config.get("paths", {}).get("processed", "data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Input file from preprocessing step
    input_file = processed_dir / "preprocessed_data.csv"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
        
    # Load preprocessed data
    try:
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} rows from {input_file}")
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        print(f"Error loading input file: {e}")
        sys.exit(1)
        
    # Expected columns
    required_cols = ['participant_id', 'session', 'channel', 'data']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        print(f"Error: Missing required columns: {missing_cols}")
        sys.exit(1)
        
    # Configuration for PE calculation
    pe_config = config.get("features", {}).get("permutation_entropy", {})
    order = pe_config.get("order", 3)
    delay = pe_config.get("delay", 1)
    
    logger.info(f"Calculating PE with order={order}, delay={delay}")
    
    # Results storage
    results = []
    
    # Process each row
    for idx, row in df.iterrows():
        participant_id = row['participant_id']
        session = row['session']
        channel = row['channel']
        
        # Parse signal data
        try:
            if isinstance(row['data'], str):
                signal = np.array([float(x) for x in row['data'].split(',')])
            else:
                signal = np.array(row['data'])
                
            if len(signal) < order * delay:
                logger.warning(f"Skipping {participant_id}-{session}-{channel}: signal too short ({len(signal)})")
                continue
                
            # Calculate Permutation Entropy
            pe_value = calculate_permutation_entropy(signal, order=order, delay=delay)
            
            results.append({
                'participant_id': participant_id,
                'session': session,
                'channel': channel,
                'permutation_entropy': pe_value,
                'order': order,
                'delay': delay,
                'signal_length': len(signal)
            })
            
        except Exception as e:
            logger.warning(f"Error processing {participant_id}-{session}-{channel}: {e}")
            continue
            
    # Save results
    if results:
        output_df = pd.DataFrame(results)
        output_file = processed_dir / "pe_metrics.csv"
        output_df.to_csv(output_file, index=False)
        logger.info(f"Saved {len(results)} PE metrics to {output_file}")
        print(f"Success: Saved {len(results)} PE metrics to {output_file}")
    else:
        logger.warning("No PE metrics calculated")
        print("Warning: No PE metrics calculated")
        
if __name__ == "__main__":
    main()