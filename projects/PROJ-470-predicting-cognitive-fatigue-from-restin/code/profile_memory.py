"""
Memory and performance profiling for the EEG cognitive fatigue pipeline.
Profiles code/preprocess.py and code/features.py to identify memory bottlenecks.
"""
import os
import sys
import time
import json
import tracemalloc
import argparse
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from preprocess import main as preprocess_main, load_config as preprocess_load_config
from features import main as features_main, load_config as features_load_config
from utils.logging import get_logger

def profile_function(func, *args, **kwargs):
    """
    Profiles a given function and returns memory and time statistics.
    """
    tracemalloc.start()
    start_time = time.time()
    
    try:
        result = func(*args, **kwargs)
        success = True
        error_msg = None
    except Exception as e:
        success = False
        error_msg = str(e)
        result = None
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        end_time = time.time()

    return {
        "peak_memory_mb": round(peak / 1024 / 1024, 2),
        "wall_time_s": round(end_time - start_time, 3),
        "success": success,
        "error": error_msg
    }

def profile_preprocessing_pipeline():
    """
    Profiles the preprocessing pipeline (code/preprocess.py).
    """
    logger = get_logger("profile_memory")
    logger.info("Starting preprocessing profile...")
    
    # We cannot simply call main() because it expects arguments or environment setup.
    # Instead, we simulate the core logic flow if possible, or run main() with safe defaults.
    # Since preprocess.py main() likely handles CLI args, we try to run it in a controlled way.
    # However, to avoid side effects (like downloading), we might need to mock or skip if data missing.
    # The task requires profiling the *pipeline*. If data is missing, we report that.
    
    # Attempt to run the actual main if data exists, otherwise report skipped/failed.
    data_dir = Path("data/raw")
    if not data_dir.exists():
        logger.warning("Data directory 'data/raw' not found. Skipping actual preprocessing profile.")
        return {
            "status": "skipped",
            "reason": "data/raw not found",
            "peak_memory_mb": 0.0,
            "wall_time_s": 0.0
        }

    # Save original argv to restore later
    original_argv = sys.argv.copy()
    try:
        # Simulate running the script as if called from CLI
        sys.argv = ["code/preprocess.py"]
        stats = profile_function(preprocess_main)
        return {
            "step": "preprocess",
            "peak_memory_mb": stats["peak_memory_mb"],
            "wall_time_s": stats["wall_time_s"],
            "success": stats["success"],
            "error": stats["error"]
        }
    finally:
        sys.argv = original_argv

def profile_feature_extraction_pipeline():
    """
    Profiles the feature extraction pipeline (code/features.py).
    """
    logger = get_logger("profile_memory")
    logger.info("Starting feature extraction profile...")
    
    processed_dir = Path("data/processed")
    if not processed_dir.exists() or not any(processed_dir.glob("*.fif")):
        logger.warning("Processed data not found. Skipping feature extraction profile.")
        return {
            "status": "skipped",
            "reason": "Processed data not found",
            "peak_memory_mb": 0.0,
            "wall_time_s": 0.0
        }

    original_argv = sys.argv.copy()
    try:
        sys.argv = ["code/features.py"]
        stats = profile_function(features_main)
        return {
            "step": "features",
            "peak_memory_mb": stats["peak_memory_mb"],
            "wall_time_s": stats["wall_time_s"],
            "success": stats["success"],
            "error": stats["error"]
        }
    finally:
        sys.argv = original_argv

def main():
    """
    Main entry point for profiling.
    Generates a JSON report at data/analysis/profile_report.json.
    """
    logger = get_logger("profile_memory")
    logger.info("Starting memory profiling pipeline...")

    # Ensure output directory exists
    output_dir = Path("data/analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "profile_report.json"

    report = {
        "steps": [],
        "summary": {
            "peak_memory_mb": 0.0,
            "wall_time_s": 0.0
        }
    }

    # Profile Preprocessing
    logger.info("Profiling Preprocessing...")
    preprocess_stats = profile_preprocessing_pipeline()
    report["steps"].append(preprocess_stats)

    # Profile Features
    logger.info("Profiling Feature Extraction...")
    features_stats = profile_feature_extraction_pipeline()
    report["steps"].append(features_stats)

    # Calculate Summary (max memory and total time)
    max_mem = 0.0
    total_time = 0.0
    for step in report["steps"]:
        if step.get("peak_memory_mb", 0) > max_mem:
            max_mem = step["peak_memory_mb"]
        if step.get("wall_time_s", 0) > 0:
            total_time += step["wall_time_s"]

    report["summary"]["peak_memory_mb"] = round(max_mem, 2)
    report["summary"]["wall_time_s"] = round(total_time, 3)

    # Write report
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Profile report written to {output_path}")
    print(f"Profile report written to {output_path}")

    # Exit with 0 even if steps were skipped, as the profiling itself succeeded
    return 0

if __name__ == "__main__":
    sys.exit(main())
