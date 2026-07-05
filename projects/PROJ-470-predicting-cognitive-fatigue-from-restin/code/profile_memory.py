"""
Performance profiling script for preprocess.py and features.py.
Identifies memory bottlenecks in the EEG pipeline.
"""
import os
import sys
import time
import json
import tracemalloc
import argparse
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
import mne
from utils.logging import get_logger

# Import the target modules
from preprocess import load_config, apply_bandpass_filter, reject_artifacts
from features import load_config as load_features_config, calculate_lzc, calculate_permutation_entropy

logger = get_logger("profiler")

def create_synthetic_eeg_data(n_channels=19, n_seconds=120, sfreq=256, seed=42):
    """
    Create synthetic EEG data for profiling.
    This is NOT used as scientific data, but strictly to measure memory usage
    of the pipeline functions on realistic data shapes.
    """
    np.random.seed(seed)
    n_points = n_seconds * sfreq
    
    # Create channel names (standard 10-20 system subset)
    ch_names = [
        'Fp1', 'Fp2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2',
        'F7', 'F8', 'T3', 'T4', 'T5', 'T6', 'Fz', 'Cz', 'Pz'
    ][:n_channels]
    
    # Generate random data with some structure (low freq + noise)
    data = np.random.randn(n_channels, n_points) * 10e-6
    # Add some 50Hz noise to simulate real conditions
    t = np.linspace(0, n_seconds, n_points)
    for i in range(n_channels):
        data[i] += 5e-6 * np.sin(2 * np.pi * 50 * t)
    
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(data, info)
    
    return raw

def profile_function(func, args, func_name, output_path):
    """
    Profile a function using tracemalloc to track memory allocation.
    """
    logger.info(f"Starting memory profile for {func_name}...")
    
    tracemalloc.start()
    start_time = time.time()
    
    try:
        result = func(*args)
        end_time = time.time()
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        elapsed = end_time - start_time
        
        profile_data = {
            "function": func_name,
            "status": "success",
            "execution_time_seconds": round(elapsed, 3),
            "memory_current_mb": round(current / 1024 / 1024, 2),
            "memory_peak_mb": round(peak / 1024 / 1024, 2),
            "input_size_mb": round(sys.getsizeof(args[0]) / 1024 / 1024, 2) if isinstance(args[0], (np.ndarray, pd.DataFrame)) else "N/A"
        }
        
        logger.info(f"{func_name} completed: Peak Memory: {profile_data['memory_peak_mb']} MB, Time: {profile_data['execution_time_seconds']}s")
        
    except Exception as e:
        tracemalloc.stop()
        logger.error(f"{func_name} failed: {str(e)}")
        profile_data = {
            "function": func_name,
            "status": "failed",
            "error": str(e)
        }
    
    # Save individual result
    with open(output_path, 'w') as f:
        json.dump(profile_data, f, indent=2)
    
    return profile_data

def main():
    parser = argparse.ArgumentParser(description="Profile memory usage of EEG pipeline")
    parser.add_argument("--output", type=str, default="data/analysis/memory_profile.json",
                      help="Path to save combined profile results")
    parser.add_argument("--n-channels", type=int, default=19, help="Number of channels for synthetic data")
    parser.add_argument("--duration", type=int, default=120, help="Duration in seconds")
    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Initializing synthetic EEG data: {args.n_channels} channels, {args.duration}s")
    raw = create_synthetic_eeg_data(n_channels=args.n_channels, n_seconds=args.duration)
    
    # Load config
    config = load_config()
    
    results = []
    
    # 1. Profile Bandpass Filter
    logger.info("Profiling Bandpass Filter...")
    filter_output = profile_function(
        apply_bandpass_filter,
        (raw, config),
        "apply_bandpass_filter",
        str(output_path.parent / "profile_filter.json")
    )
    results.append(filter_output)
    
    # 2. Profile Artifact Rejection
    logger.info("Profiling Artifact Rejection...")
    # Use the filtered raw from previous step if possible, or recreate
    raw_filtered = apply_bandpass_filter(raw, config)
    reject_output = profile_function(
        reject_artifacts,
        (raw_filtered, config),
        "reject_artifacts",
        str(output_path.parent / "profile_reject.json")
    )
    results.append(reject_output)
    
    # 3. Profile LZC Calculation
    logger.info("Profiling LZC Calculation...")
    features_config = load_features_config()
    # Extract epochs for features (assuming 2s epochs for complexity)
    epochs = mne.Epochs(raw_filtered, events=np.array([[0, 0, 0]]), tmin=0, tmax=2.0, baseline=None, verbose=False)
    lzc_output = profile_function(
        calculate_lzc,
        (epochs, features_config),
        "calculate_lzc",
        str(output_path.parent / "profile_lzc.json")
    )
    results.append(lzc_output)
    
    # 4. Profile Permutation Entropy
    logger.info("Profiling Permutation Entropy...")
    pe_output = profile_function(
        calculate_permutation_entropy,
        (epochs, features_config),
        "calculate_permutation_entropy",
        str(output_path.parent / "profile_pe.json")
    )
    results.append(pe_output)
    
    # Save combined report
    combined_report = {
        "summary": {
            "total_functions_profiled": len(results),
            "peak_memory_overall_mb": max(r.get("memory_peak_mb", 0) for r in results if isinstance(r.get("memory_peak_mb"), (int, float))),
            "total_time_seconds": sum(r.get("execution_time_seconds", 0) for r in results if isinstance(r.get("execution_time_seconds"), (int, float)))
        },
        "detailed_results": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(combined_report, f, indent=2)
    
    logger.info(f"Profile complete. Results saved to {output_path}")
    print(json.dumps(combined_report, indent=2))

if __name__ == "__main__":
    main()
