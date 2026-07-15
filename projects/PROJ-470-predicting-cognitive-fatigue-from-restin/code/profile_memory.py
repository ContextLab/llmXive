import os
import sys
import time
import json
import tracemalloc
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Import real pipeline components to profile
from preprocess import load_config as load_preprocess_config, stream_eeg_files, apply_bandpass_filter, reject_artifacts, process_eeg_stream
from features import load_config as load_features_config, calculate_lzc, calculate_permutation_entropy, process_eeg_segments, save_metrics_to_csv

def profile_function(func, *args, iterations=1, **kwargs):
    """
    Profile a specific function for memory usage and execution time.
    Returns a dictionary with timing and peak memory statistics.
    """
    tracemalloc.start()
    start_time = time.time()
    
    result = None
    for _ in range(iterations):
        result = func(*args, **kwargs)
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    return {
        "function_name": func.__name__,
        "elapsed_seconds": elapsed,
        "peak_memory_mb": peak / (1024 * 1024),
        "current_memory_mb": current / (1024 * 1024)
    }

def profile_preprocessing_pipeline(config_path="code/config.yaml"):
    """
    Profile the full preprocessing pipeline on available real data.
    Measures memory usage per stage: loading, filtering, artifact rejection.
    """
    print(f"Starting preprocessing pipeline profiling...")
    config = load_preprocess_config(config_path)
    
    raw_dir = Path(config.get("raw_data_dir", "data/raw"))
    if not raw_dir.exists():
        print(f"Warning: Raw data directory not found at {raw_dir}. Skipping real data profiling.")
        return {"status": "skipped", "reason": "Raw data directory not found"}

    tracemalloc.start()
    stage_results = {}

    try:
        # Stage 1: Streaming Load
        print("  - Profiling data streaming...")
        stream_start = time.time()
        # We process a small subset (first 1 file) to stay within memory limits during profiling
        # but we use the real streaming API to measure the actual overhead
        file_count = 0
        for chunk in stream_eeg_files(raw_dir, max_files=1):
            file_count += 1
        load_time = time.time() - stream_start
        stage_results["stream_load"] = {
            "elapsed_seconds": load_time,
            "files_processed": file_count
        }
        
        # Stage 2: Filtering & Artifact Rejection (on the loaded chunk)
        # We simulate the processing of the chunk we just loaded to measure memory
        # Since stream_eeg_files yields raw data, we need to process it.
        # To avoid re-reading, we assume the stream yields (filename, data, info)
        # We re-run the logic on the first file for profiling metrics
        
        # Re-load just one file for the filter test
        for filename, data, info in stream_eeg_files(raw_dir, max_files=1):
            # Apply filter
            filter_start = time.time()
            filtered_data = apply_bandpass_filter(data, info, config)
            filter_time = time.time() - filter_start
            
            # Reject artifacts
            reject_start = time.time()
            clean_data, rejected_mask = reject_artifacts(filtered_data, info, config)
            reject_time = time.time() - reject_start
            
            stage_results["apply_bandpass_filter"] = {
                "elapsed_seconds": filter_time,
                "peak_memory_mb": tracemalloc.get_traced_memory()[1] / (1024 * 1024)
            }
            stage_results["reject_artifacts"] = {
                "elapsed_seconds": reject_time,
                "peak_memory_mb": tracemalloc.get_traced_memory()[1] / (1024 * 1024)
            }
            
            # Stop after one file to avoid excessive profiling time
            break

    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        stage_results["total_peak_memory_mb"] = peak / (1024 * 1024)
        stage_results["total_current_memory_mb"] = current / (1024 * 1024)

    return stage_results

def profile_feature_extraction_pipeline(config_path="code/config.yaml"):
    """
    Profile the feature extraction pipeline (LZC and Permutation Entropy).
    """
    print(f"Starting feature extraction pipeline profiling...")
    config = load_features_config(config_path)
    
    processed_dir = Path(config.get("processed_data_dir", "data/processed"))
    preprocessed_file = processed_dir / "preprocessed_eeg.npy"
    
    if not preprocessed_file.exists():
        print(f"Warning: Preprocessed data not found at {preprocessed_file}. Skipping real data profiling.")
        return {"status": "skipped", "reason": "Preprocessed data not found"}

    tracemalloc.start()
    stage_results = {}

    try:
        # Load data (real data)
        print("  - Loading preprocessed data...")
        load_start = time.time()
        eeg_data = np.load(preprocessed_file)
        load_time = time.time() - load_start
        stage_results["load_data"] = {
            "elapsed_seconds": load_time,
            "shape": list(eeg_data.shape),
            "peak_memory_mb": tracemalloc.get_traced_memory()[1] / (1024 * 1024)
        }

        # Profile LZC calculation
        print("  - Profiling LZC calculation...")
        # Take a small slice if data is huge to ensure profiling completes quickly
        # but measure on real data structure
        sample_size = min(eeg_data.shape[0], 100) 
        lzc_start = time.time()
        lzc_results = []
        for i in range(sample_size):
            # Calculate LZC for a segment
            lzc_val = calculate_lzc(eeg_data[i])
            lzc_results.append(lzc_val)
        lzc_time = time.time() - lzc_start
        
        stage_results["calculate_lzc"] = {
            "elapsed_seconds": lzc_time,
            "samples_processed": sample_size,
            "peak_memory_mb": tracemalloc.get_traced_memory()[1] / (1024 * 1024)
        }

        # Profile Permutation Entropy
        print("  - Profiling Permutation Entropy calculation...")
        pe_start = time.time()
        pe_results = []
        for i in range(sample_size):
            pe_val = calculate_permutation_entropy(eeg_data[i])
            pe_results.append(pe_val)
        pe_time = time.time() - pe_start

        stage_results["calculate_permutation_entropy"] = {
            "elapsed_seconds": pe_time,
            "samples_processed": sample_size,
            "peak_memory_mb": tracemalloc.get_traced_memory()[1] / (1024 * 1024)
        }

    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        stage_results["total_peak_memory_mb"] = peak / (1024 * 1024)
        stage_results["total_current_memory_mb"] = current / (1024 * 1024)

    return stage_results

def main():
    """
    Main entry point for performance profiling.
    Profiles both preprocessing and feature extraction on real data.
    Outputs a JSON report to data/analysis/memory_profile.json.
    """
    parser = argparse.ArgumentParser(description="Profile memory and time for EEG pipeline")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file")
    parser.add_argument("--output", type=str, default="data/analysis/memory_profile.json", help="Output JSON path")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "config_path": args.config,
        "stages": {}
    }

    # Profile Preprocessing
    print("=== Profiling Preprocessing Pipeline ===")
    prep_results = profile_preprocessing_pipeline(args.config)
    report["stages"]["preprocessing"] = prep_results

    # Profile Feature Extraction
    print("=== Profiling Feature Extraction Pipeline ===")
    feat_results = profile_feature_extraction_pipeline(args.config)
    report["stages"]["feature_extraction"] = feat_results

    # Identify Bottlenecks
    bottlenecks = []
    if "stages" in report and "preprocessing" in report["stages"]:
        prep = report["stages"]["preprocessing"]
        if "total_peak_memory_mb" in prep:
            if prep["total_peak_memory_mb"] > 4000: # 4GB threshold
                bottlenecks.append(f"Preprocessing peak memory: {prep['total_peak_memory_mb']:.2f} MB")
    
    if "stages" in report and "feature_extraction" in report["stages"]:
        feat = report["stages"]["feature_extraction"]
        if "total_peak_memory_mb" in feat:
            if feat["total_peak_memory_mb"] > 4000:
                bottlenecks.append(f"Feature extraction peak memory: {feat['total_peak_memory_mb']:.2f} MB")
        
        # Check for slow operations
        if "calculate_lzc" in feat and feat["calculate_lzc"]["elapsed_seconds"] > 10:
            bottlenecks.append(f"LZC calculation took {feat['calculate_lzc']['elapsed_seconds']:.2f}s")
        if "calculate_permutation_entropy" in feat and feat["calculate_permutation_entropy"]["elapsed_seconds"] > 10:
            bottlenecks.append(f"Permutation Entropy took {feat['calculate_permutation_entropy']['elapsed_seconds']:.2f}s")

    report["bottlenecks"] = bottlenecks
    report["summary"] = "Memory profiling complete. Check bottlenecks list for issues." if bottlenecks else "Memory usage within expected limits."

    # Write report
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Profile report written to: {output_path}")
    print(f"Summary: {report['summary']}")
    if bottlenecks:
        print("Detected Bottlenecks:")
        for b in bottlenecks:
            print(f"  - {b}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
