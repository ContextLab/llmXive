import os
import sys
import time
import json
import tracemalloc
import argparse
from pathlib import Path

# Import existing pipeline functions from sibling modules
from preprocess import load_config as load_preprocess_config, process_eeg_stream, stream_eeg_files
from features import load_config as load_features_config, process_eeg_segments, calculate_lzc, calculate_permutation_entropy
from utils.logging import get_logger

# Ensure output directory exists
OUTPUT_DIR = Path("data/analysis")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PROFILE_OUTPUT = OUTPUT_DIR / "memory_profile_results.json"

def profile_function(func, *args, **kwargs):
    """
    Profile a specific function for memory usage and execution time.
    
    Args:
        func: The function to profile.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.
        
    Returns:
        dict: Profile results including peak memory, current memory, and duration.
    """
    tracemalloc.start()
    start_time = time.time()
    
    try:
        result = func(*args, **kwargs)
    except Exception as e:
        # If the function fails due to missing data, we record the failure
        # but still report memory stats up to the point of failure
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {
            "status": "failed",
            "error": str(e),
            "peak_memory_mb": peak / 1024 / 1024,
            "current_memory_mb": current / 1024 / 1024,
            "duration_seconds": end_time - start_time
        }
        
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return {
        "status": "success",
        "peak_memory_mb": peak / 1024 / 1024,
        "current_memory_mb": current / 1024 / 1024,
        "duration_seconds": end_time - start_time,
        "result_type": str(type(result))
    }

def profile_preprocessing_pipeline():
    """
    Profile the preprocessing pipeline (download -> filter -> artifact rejection).
    Since download.py might fail if data isn't present, we profile the core
    processing logic assuming data is available or handle the missing data case gracefully.
    """
    logger = get_logger("profile_memory")
    logger.info("Starting preprocessing pipeline profiling")
    
    config = load_preprocess_config()
    data_dir = Path(config.get("data_dir", "data/raw"))
    
    results = {
        "pipeline": "preprocessing",
        "config": config,
        "stages": {}
    }
    
    # Profile stream loading
    logger.info("Profiling stream loading...")
    if data_dir.exists():
        # We attempt to stream, but if no files exist, we catch the error
        # and report that memory usage is negligible for empty input
        try:
            stream = stream_eeg_files(data_dir)
            # We don't consume the stream fully here to avoid heavy processing,
            # just check initialization and first item if available
            first_item = next(stream, None)
            results["stages"]["stream_loading"] = {
                "status": "success",
                "message": "Stream initialized successfully" if first_item else "Stream initialized, no files found"
            }
        except Exception as e:
            results["stages"]["stream_loading"] = {
                "status": "failed",
                "error": str(e)
            }
    else:
        results["stages"]["stream_loading"] = {
            "status": "skipped",
            "message": f"Data directory not found: {data_dir}"
        }
        
    # Profile the main processing function (which would normally process the stream)
    # Since we can't guarantee data, we profile the function signature and logic
    # by attempting a dry run or reporting expected behavior if data were present
    logger.info("Profiling core processing logic...")
    # Note: We cannot easily profile process_eeg_stream without a real stream object
    # that yields data. We will record the function availability and expected memory behavior.
    results["stages"]["core_processing"] = {
        "status": "info",
        "message": "Core processing logic defined. Actual memory usage depends on input data size.",
        "expected_peak_memory_mb": "Variable (depends on dataset size)"
    }
    
    return results

def profile_feature_extraction_pipeline():
    """
    Profile the feature extraction pipeline (LZC, Permutation Entropy).
    This function attempts to load preprocessed data if it exists, otherwise
    profiles the calculation functions with synthetic data to establish baselines.
    """
    logger = get_logger("profile_memory")
    logger.info("Starting feature extraction pipeline profiling")
    
    config = load_features_config()
    input_file = Path(config.get("input_file", "data/processed/preprocessed_eeg.npy"))
    
    results = {
        "pipeline": "feature_extraction",
        "config": config,
        "stages": {}
    }
    
    # Profile LZC calculation
    logger.info("Profiling LZC calculation...")
    if input_file.exists():
        import numpy as np
        try:
            data = np.load(input_file)
            # Profile on a small chunk to avoid OOM if file is huge
            chunk = data[0, :1000] if data.ndim > 1 else data[:1000]
            profile_result = profile_function(calculate_lzc, chunk)
            results["stages"]["lzc_calculation"] = profile_result
        except Exception as e:
            results["stages"]["lzc_calculation"] = {
                "status": "failed",
                "error": str(e)
            }
    else:
        # If no real data, profile with a synthetic signal to get baseline
        logger.info("No preprocessed data found. Profiling with synthetic signal...")
        import numpy as np
        synthetic_signal = np.sin(np.linspace(0, 100, 1000)) + np.random.normal(0, 0.1, 1000)
        profile_result = profile_function(calculate_lzc, synthetic_signal)
        results["stages"]["lzc_calculation"] = {
            **profile_result,
            "note": "Profiled on synthetic signal due to missing real data"
        }
        
    # Profile Permutation Entropy calculation
    logger.info("Profiling Permutation Entropy calculation...")
    if input_file.exists():
        import numpy as np
        try:
            data = np.load(input_file)
            chunk = data[0, :1000] if data.ndim > 1 else data[:1000]
            profile_result = profile_function(calculate_permutation_entropy, chunk)
            results["stages"]["pe_calculation"] = profile_result
        except Exception as e:
            results["stages"]["pe_calculation"] = {
                "status": "failed",
                "error": str(e)
            }
    else:
        logger.info("No preprocessed data found. Profiling with synthetic signal...")
        import numpy as np
        synthetic_signal = np.sin(np.linspace(0, 100, 1000)) + np.random.normal(0, 0.1, 1000)
        profile_result = profile_function(calculate_permutation_entropy, synthetic_signal)
        results["stages"]["pe_calculation"] = {
            **profile_result,
            "note": "Profiled on synthetic signal due to missing real data"
        }
        
    return results

def main():
    """
    Main entry point for the memory profiling script.
    Runs profiling on preprocessing and feature extraction pipelines.
    """
    logger = get_logger("profile_memory")
    logger.info("Starting memory profiling for preprocess.py and features.py")
    
    tracemalloc.start()
    
    # Profile Preprocessing Pipeline
    preprocess_results = profile_preprocessing_pipeline()
    
    # Profile Feature Extraction Pipeline
    feature_results = profile_feature_extraction_pipeline()
    
    # Aggregate results
    final_results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "preprocessing": preprocess_results,
        "feature_extraction": feature_results,
        "summary": {
            "total_peak_memory_mb": tracemalloc.get_traced_memory()[1] / 1024 / 1024,
            "bottlenecks_identified": []
        }
    }
    
    # Analyze for bottlenecks (simple heuristic)
    if preprocess_results["stages"].get("core_processing", {}).get("expected_peak_memory_mb") == "Variable (depends on dataset size)":
        final_results["summary"]["bottlenecks_identified"].append(
            "Preprocessing memory usage is data-dependent. Ensure streaming is used for large datasets."
        )
        
    if feature_results["stages"].get("lzc_calculation", {}).get("peak_memory_mb", 0) > 100:
        final_results["summary"]["bottlenecks_identified"].append(
            "LZC calculation shows high memory usage (>100MB). Consider chunking or optimizing algorithm."
        )
        
    if feature_results["stages"].get("pe_calculation", {}).get("peak_memory_mb", 0) > 100:
        final_results["summary"]["bottlenecks_identified"].append(
            "Permutation Entropy calculation shows high memory usage (>100MB). Consider chunking or optimizing algorithm."
        )
        
    tracemalloc.stop()
    
    # Write results to file
    with open(PROFILE_OUTPUT, 'w') as f:
        json.dump(final_results, f, indent=2)
        
    logger.info(f"Memory profiling results written to {PROFILE_OUTPUT}")
    print(f"Memory profiling completed. Results saved to {PROFILE_OUTPUT}")
    print(json.dumps(final_results, indent=2))

if __name__ == "__main__":
    main()