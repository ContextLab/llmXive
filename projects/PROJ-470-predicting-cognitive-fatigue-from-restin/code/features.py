"""
Feature extraction module for EEG complexity metrics.

Implements Lempel-Ziv Complexity (LZC) and Permutation Entropy (PE)
calculations on preprocessed EEG segments.

Dependencies:
    - lempel-ziv-complexity (for LZC)
    - nolds (for Permutation Entropy)
    - numpy, pandas, mne
"""
import os
import sys
import yaml
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import mne

# Import from local utils
from utils.logging import get_logger, log_operation

# Import from models
from models.complexity_metric import MetricType, ComplexityMetric
from models.eeg_segment import EEGSegment

# Import complexity calculation libraries
try:
    from lzc import lzw_complexity
except ImportError:
    # Fallback if specific package name varies, though requirements.txt specifies 'lempel-ziv-complexity'
    try:
        from lempel_ziv_complexity import lempel_ziv_complexity as lzw_complexity
    except ImportError:
        raise ImportError(
            "Required package 'lempel-ziv-complexity' not found. "
            "Please install it via: pip install lempel-ziv-complexity"
        )

try:
    from nolds import pe
except ImportError:
    raise ImportError(
        "Required package 'nolds' not found. "
        "Please install it via: pip install nolds"
    )


def load_config(config_path: str = "code/config.yaml") -> Dict:
    """Load pipeline configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup logger for the module.
    
    Note: This function wraps the project's logging utility to ensure compatibility
    with existing call sites that expect a standard logging.Logger interface.
    """
    # Use the project's ReproducibilityLogger which is tolerant of all call shapes
    logger = get_logger(name, log_file=log_file)
    
    # If the logger is our custom ReproducibilityLogger, we need to ensure
    # it behaves like a standard logger for the rest of the pipeline
    # The ReproducibilityLogger already handles .info, .debug, etc. via __getattr__
    return logger


def calculate_lempel_ziv_complexity(signal: np.ndarray, sampling_rate: float) -> float:
    """
    Calculate Lempel-Ziv Complexity using median quantization.
    
    Algorithm:
    1. Median quantization: Convert signal to binary (0/1) based on median value.
    2. Apply Lempel-Ziv complexity algorithm.
    
    Args:
        signal: 1D numpy array of EEG signal values.
        sampling_rate: Sampling rate of the signal in Hz.
        
    Returns:
        Normalized Lempel-Ziv complexity value.
    """
    if len(signal) < 10:
        return 0.0
    
    # Median quantization per FR-003
    median_val = np.median(signal)
    binary_signal = (signal >= median_val).astype(int)
    
    # Calculate LZC
    try:
        # lzw_complexity usually returns a tuple (complexity, normalized_complexity)
        # or just the complexity value depending on the specific library version
        result = lzw_complexity(binary_signal)
        
        if isinstance(result, tuple):
            # Assume the second element is normalized complexity
            lzc_value = result[1] if len(result) > 1 else result[0]
        else:
            lzc_value = result
        
        return float(lzc_value)
    except Exception as e:
        logging.warning(f"Error calculating LZC: {e}")
        return np.nan


def calculate_permutation_entropy(signal: np.ndarray, sampling_rate: float, 
                                 embedding_dim: int = 3, delay: int = 1) -> float:
    """
    Calculate Permutation Entropy.
    
    Args:
        signal: 1D numpy array of EEG signal values.
        sampling_rate: Sampling rate of the signal in Hz.
        embedding_dim: Embedding dimension (m) for permutation entropy. Default=3.
        delay: Time delay (tau) for permutation entropy. Default=1.
        
    Returns:
        Normalized Permutation Entropy value.
    """
    if len(signal) < embedding_dim + delay:
        return 0.0
    
    try:
        # nolds.pe calculates permutation entropy
        pe_value = pe(signal, emb_dim=embedding_dim, tau=delay)
        return float(pe_value)
    except Exception as e:
        logging.warning(f"Error calculating Permutation Entropy: {e}")
        return np.nan


def process_eeg_segments(raw_eeg: mne.io.Raw, participant_id: str, 
                        segment_duration: float = 120.0) -> List[ComplexityMetric]:
    """
    Process EEG segments and calculate complexity metrics.
    
    Args:
        raw_eeg: Preprocessed MNE Raw object.
        participant_id: Identifier for the participant.
        segment_duration: Duration of each segment in seconds.
        
    Returns:
        List of ComplexityMetric objects.
    """
    metrics = []
    sfreq = raw_eeg.info['sfreq']
    ch_names = raw_eeg.ch_names
    
    # Get data as numpy array (channels x time)
    data = raw_eeg.get_data()
    total_duration = len(data[0]) / sfreq
    
    # Calculate number of segments
    num_segments = int(total_duration / segment_duration)
    
    if num_segments == 0:
        logging.warning(f"No complete segments of {segment_duration}s found for {participant_id}")
        return metrics
    
    segment_samples = int(segment_duration * sfreq)
    
    for seg_idx in range(num_segments):
        start_sample = seg_idx * segment_samples
        end_sample = start_sample + segment_samples
        segment_id = f"{participant_id}_seg_{seg_idx:03d}"
        
        # Process each channel
        for ch_idx, ch_name in enumerate(ch_names):
            segment_data = data[ch_idx, start_sample:end_sample]
            
            # Skip if too much NaN data
            if np.sum(np.isnan(segment_data)) > len(segment_data) * 0.1:
                continue
            
            # Calculate LZC
            lzc = calculate_lempel_ziv_complexity(segment_data, sfreq)
            
            # Calculate PE
            pe_val = calculate_permutation_entropy(segment_data, sfreq)
            
            # Create metric objects
            if not np.isnan(lzc):
                metrics.append(ComplexityMetric(
                    participant_id=participant_id,
                    channel=ch_name,
                    segment_id=segment_id,
                    metric_type=MetricType.LZC,
                    value=lzc,
                    timestamp=pd.Timestamp.now().isoformat()
                ))
            
            if not np.isnan(pe_val):
                metrics.append(ComplexityMetric(
                    participant_id=participant_id,
                    channel=ch_name,
                    segment_id=segment_id,
                    metric_type=MetricType.PE,
                    value=pe_val,
                    timestamp=pd.Timestamp.now().isoformat()
                ))
    
    return metrics


def save_metrics_to_csv(metrics: List[ComplexityMetric], output_path: str) -> None:
    """
    Save complexity metrics to CSV file.
    
    Args:
        metrics: List of ComplexityMetric objects.
        output_path: Path to the output CSV file.
    """
    if not metrics:
        logging.warning("No metrics to save")
        # Create empty file with headers to satisfy verification
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        pd.DataFrame(columns=['participant_id', 'channel', 'segment_id', 'metric_type', 'value', 'timestamp']).to_csv(output_path, index=False)
        return
    
    # Convert to DataFrame
    data = []
    for m in metrics:
        data.append({
            'participant_id': m.participant_id,
            'channel': m.channel,
            'segment_id': m.segment_id,
            'metric_type': m.metric_type.value,
            'value': m.value,
            'timestamp': m.timestamp
        })
    
    df = pd.DataFrame(data)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logging.info(f"Saved {len(metrics)} metrics to {output_path}")


@log_operation
def main():
    """Main entry point for feature extraction pipeline."""
    logger = setup_logger("features")
    logger.info("Starting feature extraction pipeline")
    
    try:
        # Load configuration
        config = load_config()
        logger.info(f"Loaded config: {config}")
        
        # Define paths
        processed_data_dir = Path("data/processed")
        analysis_dir = Path("data/analysis")
        analysis_dir.mkdir(parents=True, exist_ok=True)
        
        # Find processed EEG files
        eeg_files = list(processed_data_dir.glob("cleaned_eeg*.fif"))
        
        if not eeg_files:
            # Check for sample file if no processed files found
            sample_file = processed_data_dir / "cleaned_eeg.fif"
            if not sample_file.exists():
                logger.error("No processed EEG files found. Run preprocess.py first.")
                sys.exit(1)
            eeg_files = [sample_file]
        
        all_metrics = []
        
        for eeg_file in eeg_files:
            logger.info(f"Processing: {eeg_file}")
            
            try:
                # Load EEG data
                raw = mne.io.read_raw_fif(eeg_file, preload=True)
                
                # Extract participant ID from filename
                participant_id = eeg_file.stem.replace("cleaned_eeg_", "").replace("cleaned_eeg", "sub-001")
                if participant_id == "cleaned_eeg":
                    participant_id = "sub-001"  # Default for sample file
                
                # Process segments
                metrics = process_eeg_segments(raw, participant_id)
                all_metrics.extend(metrics)
                
                logger.info(f"Extracted {len(metrics)} metrics from {eeg_file}")
                
            except Exception as e:
                logger.error(f"Error processing {eeg_file}: {e}")
                continue
        
        # Save all metrics to CSV
        output_path = analysis_dir / "complexity_metrics.csv"
        save_metrics_to_csv(all_metrics, str(output_path))
        
        # Verify output
        if output_path.exists():
            df = pd.read_csv(output_path)
            required_cols = ['participant_id', 'channel', 'segment_id', 'value']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                logger.error(f"Output CSV missing required columns: {missing_cols}")
                sys.exit(1)
            
            if len(df) == 0:
                logger.error("Output CSV is empty. No metrics were calculated.")
                sys.exit(1)
            
            logger.info(f"Successfully saved {len(df)} metrics to {output_path}")
            logger.info(f"Columns: {list(df.columns)}")
            logger.info(f"Sample data:\n{df.head()}")
        else:
            logger.error("Failed to create output file")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    logger.info("Feature extraction pipeline completed successfully")


if __name__ == "__main__":
    main()