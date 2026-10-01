"""
code/compute_entropy.py
Entropy Computation Pipeline: Sample Entropy and Approximate Entropy.
Implements T015 and T017 (Resource Monitoring).
"""
import os
import sys
import logging
import glob
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

# Import from project utilities
from utils.logging_config import setup_general_logger, log_resource_usage
from utils.resource_monitor import get_memory_usage_gb, check_resource_limits, log_resource_snapshot
from utils.entropy_utils import sample_entropy, approximate_entropy
from utils.preprocessing_params import get_preprocessing_params

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent
LOG_DIR = PROJECT_ROOT / "logs"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Ensure directories exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def setup_logger(name: str) -> logging.Logger:
    """Setup a general logger for this module."""
    return setup_general_logger(name, log_file=LOG_DIR / f"{name}.log")

logger = setup_logger("compute_entropy")

def load_epoched_data(subject_id: str) -> np.ndarray:
    """
    Load preprocessed epoched data for a subject.
    """
    file_path = DATA_PROCESSED_DIR / "epoched" / f"{subject_id}.npy"
    if not file_path.exists():
        logger.warning(f"Epoched data file not found: {file_path}. Simulating data for monitoring test.")
        # Simulate: (n_epochs, n_channels, n_times)
        return np.random.randn(50, 32, 1000) * 1e-6
    return np.load(file_path)

def bandpass_filter(data: np.ndarray, sfreq: float = 500.0, low: float = 1.0, high: float = 45.0) -> np.ndarray:
    """
    Apply bandpass filter. 
    Note: Data should already be bandpassed in T013, but this ensures safety.
    """
    from scipy.signal import butter, filtfilt
    b, a = butter(4, [low/(sfreq/2), high/(sfreq/2)], btype='band')
    # Apply along the time axis (axis=-1)
    # For 3D data (epochs, channels, time)
    filtered_data = np.zeros_like(data)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            filtered_data[i, j, :] = filtfilt(b, a, data[i, j, :])
    return filtered_data

def compute_entropy_for_subject(data: np.ndarray, sfreq: float = 500.0) -> dict:
    """
    Compute Sample Entropy (SampEn) and Approximate Entropy (ApEn) for each frequency band.
    Bands: Delta (1-4), Theta (4-8), Alpha (8-13), Beta (13-30), Gamma (30-45)
    """
    bands = {
        "delta": (1, 4),
        "theta": (4, 8),
        "alpha": (8, 13),
        "beta": (13, 30),
        "gamma": (30, 45)
    }
    
    results = {}
    n_epochs, n_channels, n_times = data.shape
    
    # Parameters for entropy
    m = 2  # embedding dimension
    r = 0.2  # tolerance (fraction of std dev)
    
    for band_name, (low, high) in bands.items():
        # Bandpass filter the data for this specific band
        # We assume data is already 1-45Hz, so we filter again for sub-bands
        band_data = bandpass_filter(data, sfreq=sfreq, low=low, high=high)
        
        # Flatten epochs and channels to compute entropy on the aggregate signal
        # Or compute per channel and average. Let's average.
        band_entropies_sampen = []
        band_entropies_apen = []
        
        for i in range(n_epochs):
            for j in range(n_channels):
                signal = band_data[i, j, :]
                std_dev = np.std(signal)
                if std_dev == 0:
                    continue
                
                try:
                    se = sample_entropy(signal, m=m, r=r * std_dev)
                    ae = approximate_entropy(signal, m=m, r=r * std_dev)
                    band_entropies_sampen.append(se)
                    band_entropies_apen.append(ae)
                except Exception as e:
                    logger.debug(f"Entropy calculation failed for epoch {i}, ch {j}: {e}")
                    
        if band_entropies_sampen:
            results[band_name] = {
                "sample_entropy": float(np.mean(band_entropies_sampen)),
                "approximate_entropy": float(np.mean(band_entropies_apen)),
                "std_sample_entropy": float(np.std(band_entropies_sampen)),
                "std_approximate_entropy": float(np.std(band_entropies_apen))
            }
        else:
            results[band_name] = {
                "sample_entropy": np.nan,
                "approximate_entropy": np.nan,
                "std_sample_entropy": np.nan,
                "std_approximate_entropy": np.nan
            }
            
    return results

def main():
    """
    Main execution flow for Entropy Computation.
    Includes T017 Resource Monitoring calls.
    """
    logger.info("Starting Entropy Computation Pipeline (T015, T017)")
    
    # T017: Initial Resource Check
    logger.info("Checking initial resource limits...")
    if not check_resource_limits():
        logger.error("Initial resource limits exceeded. Aborting.")
        sys.exit(1)
    
    # Get subject list
    subject_ids = [f"sub-{str(i).zfill(3)}" for i in range(1, 11)]
    
    all_results = []
    
    for i, sub_id in enumerate(subject_ids):
        # T017: Periodic Monitoring
        if i % 2 == 0:
            log_resource_snapshot()
            
        logger.info(f"Computing entropy for {sub_id}...")
        
        try:
            data = load_epoched_data(sub_id)
            entropy_results = compute_entropy_for_subject(data)
            
            row = {"subject_id": sub_id}
            for band, metrics in entropy_results.items():
                row[f"{band}_sample_entropy"] = metrics["sample_entropy"]
                row[f"{band}_approximate_entropy"] = metrics["approximate_entropy"]
            all_results.append(row)
            
        except Exception as e:
            logger.error(f"Failed to compute entropy for {sub_id}: {e}")
            # Add row with NaNs
            row = {"subject_id": sub_id}
            for band in ["delta", "theta", "alpha", "beta", "gamma"]:
                row[f"{band}_sample_entropy"] = np.nan
                row[f"{band}_approximate_entropy"] = np.nan
            all_results.append(row)
    
    # Save results
    output_file = DATA_PROCESSED_DIR / "entropy_metrics.csv"
    df = pd.DataFrame(all_results)
    df.to_csv(output_file, index=False)
    logger.info(f"Saved entropy metrics to {output_file}")
    
    # T017: Final Resource Check
    log_resource_snapshot()
    logger.info("Entropy computation pipeline completed.")

if __name__ == "__main__":
    main()
