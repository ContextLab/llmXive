import os
import sys
import logging
import glob
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

# Import from local utils
sys.path.insert(0, str(Path(__file__).parent))
from utils.logging_config import setup_resource_logger, get_logger, log_resource_usage
from utils.resource_monitor import check_resource_limits, log_resource_snapshot, enforce_resource_limits
from utils.entropy_utils import sample_entropy, approximate_entropy, compute_entropy_metrics

def setup_logger(name: str) -> logging.Logger:
    """Setup a logger for the entropy computation module."""
    logger = get_logger(name)
    return logger

def load_epoched_data(data_dir: str) -> List[Dict[str, Any]]:
    """
    Load epoched EEG data from processed directory.
    Returns a list of dictionaries containing subject data.
    """
    logger = get_logger("compute_entropy")
    subject_files = glob.glob(os.path.join(data_dir, "*.npy"))
    
    if not subject_files:
        logger.warning(f"No epoched data found in {data_dir}")
        return []

    data_list = []
    for f_path in subject_files:
        try:
            data = np.load(f_path, allow_pickle=True).item()
            data_list.append(data)
        except Exception as e:
            logger.error(f"Failed to load {f_path}: {e}")
    
    return data_list

def bandpass_filter(data: np.ndarray, fs: float, lowcut: float, highcut: float) -> np.ndarray:
    """
    Simple bandpass filter using FFT (placeholder for real filter implementation).
    In production, use scipy.signal or mne.filter.
    """
    n = len(data)
    fft_vals = np.fft.fft(data)
    freqs = np.fft.fftfreq(n, 1/fs)
    
    # Zero out frequencies outside the band
    mask = (np.abs(freqs) >= lowcut) & (np.abs(freqs) <= highcut)
    fft_filtered = fft_vals * mask
    
    return np.fft.ifft(fft_filtered).real

def compute_entropy_for_subject(subject_data: Dict[str, Any], logger: logging.Logger) -> Dict[str, float]:
    """
    Compute Sample Entropy and Approximate Entropy for all frequency bands.
    Bands: Delta (1-4Hz), Theta (4-8Hz), Alpha (8-13Hz), Beta (13-30Hz), Gamma (30-45Hz)
    """
    signal = subject_data.get('data', [])
    fs = subject_data.get('fs', 250.0)
    subj_id = subject_data.get('subject_id', 'unknown')
    
    if len(signal) == 0:
        return {}

    bands = {
        'delta': (1, 4),
        'theta': (4, 8),
        'alpha': (8, 13),
        'beta': (13, 30),
        'gamma': (30, 45)
    }

    results = {}
    for band_name, (low, high) in bands.items():
        try:
            # Filter signal
            filtered_signal = bandpass_filter(np.array(signal), fs, low, high)
            
            # Compute entropy metrics
            se = sample_entropy(filtered_signal, m=2, r=0.2 * np.std(filtered_signal))
            ae = approximate_entropy(filtered_signal, m=2, r=0.2 * np.std(filtered_signal))
            
            results[f"{subj_id}_{band_name}_sample_entropy"] = se
            results[f"{subj_id}_{band_name}_approx_entropy"] = ae
            
        except Exception as e:
            logger.error(f"Failed to compute entropy for {subj_id} {band_name}: {e}")
            results[f"{subj_id}_{band_name}_sample_entropy"] = np.nan
            results[f"{subj_id}_{band_name}_approx_entropy"] = np.nan

    return results

def main():
    """Main entry point for entropy computation with resource monitoring."""
    logger = setup_logger("compute_entropy")
    logger.info("Starting Entropy Computation Pipeline")
    
    # Resource monitoring setup
    resource_logger = setup_resource_logger()
    log_resource_snapshot(resource_logger, "start")
    
    # Check resources at start
    try:
        enforce_resource_limits(resource_logger)
    except RuntimeError as e:
        logger.critical(str(e))
        sys.exit(1)
    
    # Paths
    data_dir = str(Path(__file__).parent.parent / "data" / "processed")
    output_file = str(Path(__file__).parent.parent / "data" / "processed" / "entropy_metrics.csv")
    
    # Load data
    subjects = load_epoched_data(data_dir)
    logger.info(f"Loaded {len(subjects)} subjects for entropy computation")
    
    # Compute entropy for all subjects
    all_results = []
    for subject in subjects:
        subj_id = subject.get('subject_id', 'unknown')
        logger.info(f"Computing entropy for subject {subj_id}")
        
        results = compute_entropy_for_subject(subject, logger)
        all_results.append(results)
        
        # Check resources periodically
        if not check_resource_limits(resource_logger):
            logger.warning("Resource usage high, proceeding with caution")
    
    # Save results
    df = pd.DataFrame(all_results)
    df.to_csv(output_file, index=False)
    logger.info(f"Entropy metrics saved to {output_file}")
    
    # Check resources at end
    log_resource_snapshot(resource_logger, "end")
    try:
        enforce_resource_limits(resource_logger)
    except RuntimeError as e:
        logger.critical(str(e))
        sys.exit(1)
    
    logger.info("Entropy computation pipeline completed successfully")

if __name__ == "__main__":
    main()
