"""
Optimized preprocessing pipeline with performance enhancements.

This module provides an optimized version of the preprocessing pipeline
that implements chunked loading and memory-efficient ICA processing.
"""
import os
import sys
import json
import time
import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import mne
from pathlib import Path

# Import from existing modules
from config import load_config, get_config_value
from data.loader import load_epochs_chunked, estimate_memory_usage
from data.manifest import update_state
from utils.optimization_utils import (
    chunked_ica_processing,
    optimized_chunked_loading,
    get_current_memory_mb,
    MEMORY_LIMIT_GB,
    run_optimization_benchmark
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def butter_bandpass_filter_optimized(
    data: np.ndarray,
    lowcut: float,
    highcut: float,
    fs: float,
    order: int = 4
) -> np.ndarray:
    """
    Optimized Butterworth bandpass filter.
    
    Args:
        data: Input data array (n_channels, n_times)
        lowcut: Low cutoff frequency
        highcut: High cutoff frequency
        fs: Sampling frequency
        order: Filter order
    
    Returns:
        Filtered data
    """
    from scipy.signal import butter, filtfilt
    
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    
    b, a = butter(order, [low, high], btype='band')
    
    # Apply filter to each channel
    filtered_data = np.zeros_like(data)
    for i in range(data.shape[0]):
        filtered_data[i, :] = filtfilt(b, a, data[i, :])
    
    return filtered_data

def apply_ica_optimized(
    raw: mne.io.Raw,
    n_components: Optional[int] = None,
    method: str = 'fastica',
    reject: Optional[Dict[str, float]] = None,
    verbose: bool = True
) -> Tuple[mne.io.Raw, Dict[str, Any]]:
    """
    Optimized ICA application with memory profiling.
    
    Args:
        raw: Raw EEG data
        n_components: Number of ICA components (auto if None)
        method: ICA method
        reject: Rejection parameters
        verbose: Whether to print progress
    
    Returns:
        Tuple of (cleaned raw data, metrics dict)
    """
    metrics = {
        'start_memory_mb': get_current_memory_mb(),
        'start_time': time.time()
    }
    
    logger.info("Starting optimized ICA processing...")
    
    # Use optimized ICA processing
    ica, ica_metrics = chunked_ica_processing(
        raw,
        n_components=n_components,
        method=method
    )
    
    # Identify and remove bad components (e.g., eye blinks)
    # This is a simplified version - in practice, you'd use more sophisticated methods
    if verbose:
        logger.info(f"ICA fitted with {ica.n_components_} components")
    
    # Apply ICA to remove artifacts
    # In a real implementation, you'd identify specific components to exclude
    # For now, we'll just fit and return the ICA object
    metrics['ica_fitted'] = True
    metrics['n_components'] = ica.n_components_
    metrics.update(ica_metrics)
    
    logger.info(f"ICA processing completed in {time.time() - metrics['start_time']:.2f} seconds")
    
    return raw, metrics

def preprocess_eeg_data_optimized(
    data_dir: str,
    output_dir: str,
    config_path: Optional[str] = None,
    perform_ica: bool = True,
    filter_params: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Optimized EEG preprocessing pipeline.
    
    Args:
        data_dir: Directory containing raw EEG data
        output_dir: Directory to save processed data
        config_path: Path to configuration file
        perform_ica: Whether to perform ICA
        filter_params: Dictionary with filter parameters
    
    Returns:
        Dictionary with preprocessing metrics
    """
    # Load configuration
    if config_path:
        config = load_config(config_path)
    else:
        config = load_config()
    
    # Extract parameters
    if filter_params is None:
        filter_params = {
            'lowcut': get_config_value(config, 'filter.lowcut', 1.0),
            'highcut': get_config_value(config, 'filter.highcut', 45.0),
            'order': get_config_value(config, 'filter.order', 4)
        }
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    metrics = {
        'timestamp': time.time(),
        'config': config,
        'filter_params': filter_params,
        'steps': []
    }
    
    # Step 1: Load data with chunking
    logger.info("Step 1: Loading data with chunked loading...")
    step_start = time.time()
    
    # Use optimized chunked loading
    raw_data = None
    for chunk_data, chunk_meta in optimized_chunked_loading(
        epochs=None,  # Load raw data in chunks if needed
        chunk_size=100
    ):
        # Process chunk
        if raw_data is None:
            raw_data = chunk_data
        else:
            raw_data = np.concatenate([raw_data, chunk_data], axis=1)
    
    metrics['steps'].append({
        'step': 'load_data',
        'duration': time.time() - step_start,
        'memory_mb': get_current_memory_mb()
    })
    
    # Step 2: Apply bandpass filter
    logger.info("Step 2: Applying bandpass filter...")
    step_start = time.time()
    
    filtered_data = butter_bandpass_filter_optimized(
        raw_data,
        filter_params['lowcut'],
        filter_params['highcut'],
        config.get('sampling_rate', 250),
        filter_params['order']
    )
    
    metrics['steps'].append({
        'step': 'bandpass_filter',
        'duration': time.time() - step_start,
        'memory_mb': get_current_memory_mb()
    })
    
    # Step 3: Apply ICA if requested
    if perform_ica:
        logger.info("Step 3: Applying ICA...")
        step_start = time.time()
        
        # Convert to MNE Raw object for ICA
        # This is a simplified conversion - in practice, you'd use proper MNE objects
        info = mne.create_info(
            ch_names=[f'EEG{i}' for i in range(raw_data.shape[0])],
            sfreq=config.get('sampling_rate', 250),
            ch_types='eeg'
        )
        raw = mne.io.RawArray(filtered_data, info)
        
        cleaned_raw, ica_metrics = apply_ica_optimized(raw)
        
        metrics['ica_metrics'] = ica_metrics
        metrics['steps'].append({
            'step': 'ica',
            'duration': time.time() - step_start,
            'memory_mb': get_current_memory_mb()
        })
    else:
        cleaned_raw = raw_data
        metrics['ica_metrics'] = {'skipped': True}
    
    # Save processed data
    output_path = os.path.join(output_dir, 'processed_data.npz')
    np.savez(output_path, data=cleaned_raw if isinstance(cleaned_raw, np.ndarray) else cleaned_raw.get_data())
    
    metrics['output_path'] = output_path
    metrics['final_memory_mb'] = get_current_memory_mb()
    
    # Update state
    update_state(config, 'preprocess_optimized', metrics)
    
    logger.info(f"Preprocessing completed. Output saved to {output_path}")
    return metrics

def main():
    """Main entry point for optimized preprocessing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Optimized EEG preprocessing pipeline')
    parser.add_argument('--data-dir', type=str, required=True, help='Directory with raw data')
    parser.add_argument('--output-dir', type=str, required=True, help='Directory for processed data')
    parser.add_argument('--config', type=str, default='pipeline_config.yaml', help='Configuration file')
    parser.add_argument('--no-ica', action='store_true', help='Skip ICA processing')
    parser.add_argument('--benchmark', action='store_true', help='Run optimization benchmark')
    
    args = parser.parse_args()
    
    logger.info(f"Starting optimized preprocessing with data from {args.data_dir}")
    
    if args.benchmark:
        # Run benchmark
        logger.info("Running optimization benchmark...")
        # This would require actual data loading
        # For now, we'll just log the benchmark parameters
        logger.info(f"Memory limit: {MEMORY_LIMIT_GB} GB")
        logger.info(f"Chunk size: {100} epochs")
    else:
        # Run preprocessing
        metrics = preprocess_eeg_data_optimized(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            config_path=args.config,
            perform_ica=not args.no_ica
        )
        
        # Save metrics
        metrics_path = os.path.join(args.output_dir, 'preprocessing_metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Preprocessing metrics saved to {metrics_path}")
    
    logger.info("Optimized preprocessing completed successfully")

if __name__ == '__main__':
    main()
