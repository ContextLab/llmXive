import os
import sys
import time
import json
import tracemalloc
import argparse
import mne
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure we can import project modules
sys.path.insert(0, str(Path(__file__).parent))

from utils.logging import get_logger
from preprocess import load_config, stream_eeg_files, apply_bandpass_filter, reject_artifacts, process_eeg_stream
from features import load_config as load_features_config, calculate_lzc, calculate_permutation_entropy, process_eeg_segments

logger = get_logger("profile_memory")

def profile_function(func, *args, **kwargs):
    """
    Profiles a function's memory usage and execution time.
    Returns a dictionary with memory statistics and timing.
    """
    tracemalloc.start()
    start_time = time.perf_counter()
    
    try:
        result = func(*args, **kwargs)
    except Exception as e:
        tracemalloc.stop()
        logger.error(f"Function {func.__name__} failed during profiling: {e}")
        raise
    
    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return {
        "function_name": func.__name__,
        "execution_time_seconds": end_time - start_time,
        "peak_memory_mb": peak / (1024 * 1024),
        "current_memory_mb": current / (1024 * 1024),
        "status": "success"
    }

def profile_preprocessing_pipeline(config_path="code/config.yaml"):
    """
    Profiles the memory and time usage of the preprocessing pipeline.
    Streams real data from disk to avoid loading everything into memory at once.
    """
    logger.info(f"Loading configuration from {config_path}")
    config = load_config(config_path)
    
    raw_data_dir = Path(config.get("raw_data_dir", "data/raw"))
    if not raw_data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}")
    
    logger.info(f"Starting preprocessing profile on data in {raw_data_dir}")
    
    # Profile the streaming and processing
    results = []
    
    # We profile the stream_eeg_files generator consumption and processing
    # Since stream_eeg_files is a generator, we iterate over it and profile the processing of chunks
    try:
        for chunk in stream_eeg_files(raw_data_dir, config):
            if chunk is None:
                continue
            
            # Profile filter application
            filter_stats = profile_function(apply_bandpass_filter, chunk, config)
            results.append(filter_stats)
            
            # Profile artifact rejection
            reject_stats = profile_function(reject_artifacts, filter_stats.get("result", chunk), config)
            # Note: reject_artifacts might modify in place or return new, depending on impl
            # Assuming it returns the processed data
            processed_data = reject_stats.get("result", None)
            
            if processed_data is not None:
                results.append(reject_stats)
            
            # Stop after first few chunks to avoid long runtime in CI, 
            # but ensure we process at least one full cycle if data is small
            # For a true profile, we might want to process all, but for CI safety:
            if len(results) >= 5: 
                break
                
    except Exception as e:
        logger.error(f"Error during preprocessing profiling: {e}")
        raise

    return results

def profile_feature_extraction_pipeline(config_path="code/config.yaml"):
    """
    Profiles the memory and time usage of the feature extraction pipeline.
    """
    logger.info(f"Loading configuration from {config_path}")
    config = load_features_config(config_path)
    
    processed_data_path = Path(config.get("processed_data_path", "data/processed/preprocessed_eeg.npy"))
    if not processed_data_path.exists():
        raise FileNotFoundError(f"Processed data not found: {processed_data_path}")
    
    logger.info(f"Starting feature extraction profile on {processed_data_path}")
    
    # Load a sample of the data for profiling if it's too large
    # We load the whole thing if it fits, otherwise we stream chunks if the file format supports it
    # Assuming .npy is loaded into memory, we profile the calculation functions directly
    data = np.load(processed_data_path, allow_pickle=True).item()
    
    if isinstance(data, dict) and 'data' in data:
        eeg_data = data['data']
    elif isinstance(data, np.ndarray):
        eeg_data = data
    else:
        # Try to handle if it's a list of segments
        eeg_data = data
    
    results = []
    
    # Profile LZC calculation
    # We need to pass a segment to calculate_lzc. 
    # Assuming eeg_data is shaped (n_channels, n_samples) or similar
    if isinstance(eeg_data, np.ndarray) and eeg_data.ndim >= 2:
        segment = eeg_data[0] # Take first channel as sample
        lzc_stats = profile_function(calculate_lzc, segment, config)
        results.append(lzc_stats)
        
        pe_stats = profile_function(calculate_permutation_entropy, segment, config)
        results.append(pe_stats)
    else:
        logger.warning("Data format unexpected for profiling, skipping calculation profile.")

    return results

def main():
    parser = argparse.ArgumentParser(description="Profile memory and performance of EEG pipeline.")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file")
    parser.add_argument("--output", type=str, default="data/analysis/profile_results.json", help="Output JSON file path")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    logger.info("Starting memory profiling...")
    
    profile_results = {
        "preprocessing": [],
        "feature_extraction": [],
        "summary": {}
    }

    try:
        # Profile Preprocessing
        logger.info("Profiling Preprocessing Pipeline...")
        profile_results["preprocessing"] = profile_preprocessing_pipeline(args.config)
        
        # Profile Feature Extraction
        logger.info("Profiling Feature Extraction Pipeline...")
        profile_results["feature_extraction"] = profile_feature_extraction_pipeline(args.config)

        # Calculate Summary
        if profile_results["preprocessing"]:
            avg_mem_pre = sum(r["peak_memory_mb"] for r in profile_results["preprocessing"]) / len(profile_results["preprocessing"])
            profile_results["summary"]["preprocessing_avg_peak_memory_mb"] = avg_mem_pre
        
        if profile_results["feature_extraction"]:
            avg_mem_feat = sum(r["peak_memory_mb"] for r in profile_results["feature_extraction"]) / len(profile_results["feature_extraction"])
            profile_results["summary"]["feature_extraction_avg_peak_memory_mb"] = avg_mem_feat

        # Write results
        with open(args.output, 'w') as f:
            json.dump(profile_results, f, indent=2)
        
        logger.info(f"Profile results written to {args.output}")
        print(f"Profile completed. Results saved to {args.output}")

    except Exception as e:
        logger.error(f"Profiling failed: {e}")
        # Write partial results or error state
        profile_results["error"] = str(e)
        with open(args.output, 'w') as f:
            json.dump(profile_results, f, indent=2)
        sys.exit(1)

if __name__ == "__main__":
    main()