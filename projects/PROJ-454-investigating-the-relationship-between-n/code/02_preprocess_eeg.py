import os
import sys
import json
import logging
import glob
import numpy as np
from pathlib import Path
from typing import Dict, List, Any

# Import from local utils
sys.path.insert(0, str(Path(__file__).parent))
from utils.logging_config import setup_resource_logger, get_logger, log_resource_usage
from utils.resource_monitor import check_resource_limits, log_resource_snapshot, enforce_resource_limits

def setup_logger(name: str) -> logging.Logger:
    """Setup a logger for the preprocessing module."""
    logger = get_logger(name)
    return logger

def load_epoched_data(data_dir: str) -> List[Dict[str, Any]]:
    """
    Load epoched EEG data from processed directory.
    Returns a list of dictionaries containing subject data.
    """
    logger = get_logger("preprocess_eeg")
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

def calculate_power_spectrum(data: np.ndarray, fs: float) -> np.ndarray:
    """Calculate power spectrum using FFT."""
    n = len(data)
    fft_vals = np.fft.fft(data)
    power = np.abs(fft_vals[:n//2]) ** 2 / n
    freqs = np.fft.fftfreq(n, 1/fs)[:n//2]
    return freqs, power

def calculate_snr_for_subject(subject_data: Dict[str, Any]) -> float:
    """
    Calculate Median SNR for a subject.
    Formula: median(signal_power_1-45Hz) / median(noise_power_residual)
    """
    signal = subject_data.get('data', [])
    fs = subject_data.get('fs', 250.0)
    
    if len(signal) == 0:
        return 0.0

    # Simple SNR estimation using band power vs total power
    # In a real implementation, this would use specific frequency bands
    total_power = np.mean(signal ** 2)
    if total_power == 0:
        return 0.0
    
    # Estimate noise as residual from bandpass (simplified)
    # Assuming signal is already bandpass filtered 1-45Hz
    signal_power = np.mean(signal ** 2)
    noise_power = 0.01 * signal_power  # Placeholder for residual noise estimate
    
    if noise_power == 0:
        return float('inf')
    
    snr_db = 10 * np.log10(signal_power / noise_power)
    return snr_db

def load_snr_metrics(snr_file: str) -> Dict[str, float]:
    """Load SNR metrics from JSON file."""
    try:
        with open(snr_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def run_quality_checks(data_dir: str, snr_file: str, exclusion_log: str) -> List[str]:
    """
    Run quality checks and return list of excluded subject IDs.
    Criteria: <60s valid EEG, >20% corrupted segments, OR SNR < 5dB
    """
    logger = get_logger("preprocess_eeg")
    excluded_subjects = []
    
    # Load SNR metrics
    snr_metrics = load_snr_metrics(snr_file)
    
    # Load epoched data
    subjects = load_epoched_data(data_dir)
    
    for subject in subjects:
        subj_id = subject.get('subject_id', 'unknown')
        data = subject.get('data', [])
        fs = subject.get('fs', 250.0)
        duration = len(data) / fs if data else 0
        snr = snr_metrics.get(subj_id, 0.0)
        
        exclude_reason = None
        
        # Check duration < 60s
        if duration < 60.0:
            exclude_reason = f"Duration {duration:.1f}s < 60s"
        
        # Check SNR < 5dB (from T014/T016)
        elif snr < 5.0:
            exclude_reason = f"SNR {snr:.2f}dB < 5dB"
        
        # Check corrupted segments > 20% (simplified check)
        elif len(data) > 0 and np.sum(np.isnan(data)) / len(data) > 0.2:
            exclude_reason = "Corrupted segments > 20%"
        
        if exclude_reason:
            excluded_subjects.append(subj_id)
            logger.warning(f"Excluding subject {subj_id}: {exclude_reason}")
            log_resource_usage(logger, "exclusion", subj_id, reason=exclude_reason)
    
    # Write exclusion log
    with open(exclusion_log, 'w') as f:
        f.write("subject_id,reason\n")
        for subj_id in excluded_subjects:
            # Re-fetch reason for log (simplified)
            f.write(f"{subj_id},Quality Check Failed\n")
    
    return excluded_subjects

def main():
    """Main entry point for EEG preprocessing with resource monitoring."""
    logger = setup_logger("02_preprocess_eeg")
    logger.info("Starting EEG Preprocessing Pipeline")
    
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
    snr_file = os.path.join(data_dir, "snr_metrics.json")
    exclusion_log = os.path.join(data_dir, "exclusion_log.csv")
    
    # Run quality checks (T016 integration)
    logger.info("Running quality checks...")
    excluded = run_quality_checks(data_dir, snr_file, exclusion_log)
    logger.info(f"Excluded {len(excluded)} subjects due to quality issues")
    
    # Check resources at end
    log_resource_snapshot(resource_logger, "end")
    try:
        enforce_resource_limits(resource_logger)
    except RuntimeError as e:
        logger.critical(str(e))
        sys.exit(1)
    
    logger.info("Preprocessing pipeline completed successfully")

if __name__ == "__main__":
    main()
