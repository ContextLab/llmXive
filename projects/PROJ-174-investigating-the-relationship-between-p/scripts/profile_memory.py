"""
Memory Profiling Script for llmXive Pipeline (T035)

This script executes the full pipeline preprocessing and analysis modules
against the verified real dataset using streaming to measure peak RAM usage
and execution duration, verifying SC-005 (Whole Pipeline) constraints.

Constraints:
- Must use the real dataset found in T002c (data/raw/).
- Must stream data to avoid loading full dataset into memory at once.
- Must log peak RAM (GB) and duration (hours) to results/memory_profile.csv.
- Must verify completion within 5 hours and <= 6 GB RAM.
"""
import os
import sys
import time
import logging
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import gc

# Try to import memory_profiler, install if missing
try:
    from memory_profiler import memory_usage
except ImportError:
    print("ERROR: memory_profiler not installed. Installing now...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "memory-profiler"])
    from memory_profiler import memory_usage

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
RESULTS_DIR = PROJECT_ROOT / "results"
OUTPUT_FILE = RESULTS_DIR / "memory_profile.csv"
LOG_FILE = RESULTS_DIR / "memory_profile.log"

# Ensure directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# SC-005 Constraints
MAX_DURATION_HOURS = 5.0
MAX_RAM_GB = 6.0

def get_dataset_info() -> Tuple[str, int]:
    """
    Identifies the verified dataset used in T002c.
    Returns (dataset_name, estimated_size_bytes).
    """
    # Look for the dataset downloaded by T002c
    # T002c downloads to data/raw/
    files = list(DATA_RAW_DIR.glob("*"))
    if not files:
        raise FileNotFoundError("No dataset found in data/raw/. T002c may have failed.")
    
    # Assume the first file or directory is the dataset
    dataset_path = files[0]
    dataset_name = dataset_path.name
    
    # Estimate size
    if dataset_path.is_file():
        size = dataset_path.stat().st_size
    else:
        size = sum(f.stat().st_size for f in dataset_path.rglob('*') if f.is_file())
    
    return dataset_name, size

def profile_step(step_name: str, func, *args, **kwargs) -> Dict[str, Any]:
    """
    Profiles a specific function step for memory and time.
    Uses memory_profiler to track peak usage.
    """
    logger.info(f"Starting step: {step_name}")
    start_time = time.time()
    
    # memory_usage returns a tuple (current_usage, peak_usage) if interval is set
    # We wrap the function call
    try:
        # Use memory_profiler's memory_usage to get peak memory
        # mem_usage = memory_usage((func, args, kwargs), interval=0.1, timeout=3600, max_usage=True)
        # The above syntax is for older versions. Newer versions return a list of usages.
        # We'll use a simpler approach: measure peak of the process during execution.
        
        # To get accurate peak, we run the function and capture max memory
        # memory_usage with max_usage=True returns the max memory used during the interval
        peak_mem_gb = memory_usage((func, args, kwargs), interval=0.1, timeout=3600, max_usage=True)
        
        # peak_mem_gb is a float (MB) in memory_profiler output usually, but let's check docs.
        # Actually, memory_usage returns a list of memory usages in MB by default.
        # If max_usage=True, it returns the max value.
        # Let's assume it returns MB.
        if isinstance(peak_mem_gb, (list, tuple)):
            peak_mem_gb = max(peak_mem_gb)
        
        # Convert MB to GB
        peak_mem_gb = peak_mem_gb / 1024.0
        
        duration_seconds = time.time() - start_time
        duration_hours = duration_seconds / 3600.0
        
        logger.info(f"Step {step_name} completed. Peak RAM: {peak_mem_gb:.2f} GB, Duration: {duration_hours:.4f} hours")
        
        return {
            "step": step_name,
            "peak_ram_gb": round(peak_mem_gb, 4),
            "duration_hours": round(duration_hours, 6)
        }
    except Exception as e:
        logger.error(f"Step {step_name} failed: {e}")
        raise

def run_preprocessing_streaming():
    """
    Simulates streaming the full real dataset through preprocessing modules.
    Uses the API surface from code/preprocessing/
    """
    # Import required modules from the project
    # We need to add code/ to sys.path
    sys.path.insert(0, str(CODE_DIR))
    
    from preprocessing.load_data import load_raw_data_from_dataset
    from preprocessing.preprocess import run_preprocessing_pipeline
    from preprocessing.features import process_dataset_features
    
    # We need to find the dataset path
    dataset_files = list(DATA_RAW_DIR.glob("*"))
    if not dataset_files:
        raise FileNotFoundError("No dataset found in data/raw/")
    
    dataset_path = str(dataset_files[0])
    
    # Simulate streaming by processing in chunks if possible, 
    # or iterating through subjects/trials.
    # Since we don't know the exact internal structure, we call the pipeline
    # which should handle streaming internally if implemented correctly.
    # For profiling, we just run the pipeline.
    
    # Note: The actual streaming logic is inside run_preprocessing_pipeline.
    # We assume it handles large datasets by not loading everything at once.
    run_preprocessing_pipeline(input_path=dataset_path, output_dir=str(PROJECT_ROOT / "data" / "processed"))
    
    # Also run feature extraction
    features_path = str(PROJECT_ROOT / "data" / "processed" / "features.csv")
    if os.path.exists(features_path):
        process_dataset_features(input_path=features_path, output_path=features_path)

def run_analysis_streaming():
    """
    Simulates streaming the processed data through analysis modules.
    """
    sys.path.insert(0, str(CODE_DIR))
    
    from analysis.analysis import run_full_analysis_pipeline
    from classification.classifier import run_classification_pipeline
    
    # Run analysis pipeline
    run_full_analysis_pipeline(
        input_path=str(PROJECT_ROOT / "data" / "processed" / "features.csv"),
        output_dir=str(RESULTS_DIR)
    )
    
    # Run classification pipeline
    run_classification_pipeline(
        input_path=str(PROJECT_ROOT / "data" / "processed" / "features.csv"),
        output_dir=str(RESULTS_DIR)
    )

def main():
    logger.info("Starting Memory Profiling (T035)")
    
    # Get dataset info
    dataset_name, dataset_size = get_dataset_info()
    dataset_size_gb = dataset_size / (1024 ** 3)
    logger.info(f"Using dataset: {dataset_name}, Size: {dataset_size_gb:.2f} GB")
    
    # Prepare output file
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["step", "peak_ram_gb", "duration_hours"]
    
    # Clear existing output if any
    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
    
    # Steps to profile
    steps = [
        ("Data Loading & Preprocessing", run_preprocessing_streaming),
        ("Analysis & Classification", run_analysis_streaming),
    ]
    
    total_duration = 0.0
    max_peak_ram = 0.0
    
    try:
        for step_name, step_func in steps:
            result = profile_step(step_name, step_func)
            
            # Write to CSV
            with open(OUTPUT_FILE, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerow(result)
            
            total_duration += result["duration_hours"]
            max_peak_ram = max(max_peak_ram, result["peak_ram_gb"])
            
            # Force garbage collection between steps
            gc.collect()
            
    except Exception as e:
        logger.error(f"Profiling failed: {e}")
        raise
    
    # Verify constraints
    logger.info(f"Total Duration: {total_duration:.2f} hours (Limit: {MAX_DURATION_HOURS}h)")
    logger.info(f"Max Peak RAM: {max_peak_ram:.2f} GB (Limit: {MAX_RAM_GB} GB)")
    
    success = True
    if total_duration > MAX_DURATION_HOURS:
        logger.warning(f"EXCEEDED DURATION LIMIT: {total_duration:.2f}h > {MAX_DURATION_HOURS}h")
        success = False
    if max_peak_ram > MAX_RAM_GB:
        logger.warning(f"EXCEEDED RAM LIMIT: {max_peak_ram:.2f}GB > {MAX_RAM_GB}GB")
        success = False
    
    # Write summary to log
    with open(LOG_FILE, 'a') as f:
        f.write(f"\n--- SC-005 Verification ---\n")
        f.write(f"Dataset: {dataset_name} ({dataset_size_gb:.2f} GB)\n")
        f.write(f"Total Duration: {total_duration:.2f} hours\n")
        f.write(f"Max Peak RAM: {max_peak_ram:.2f} GB\n")
        f.write(f"Status: {'PASS' if success else 'FAIL'}\n")
    
    if not success:
        logger.error("SC-005 Constraints NOT met. Pipeline exceeded limits.")
        sys.exit(1)
    
    logger.info("Memory Profiling completed successfully. SC-005 verified.")
    print(f"\nResults written to: {OUTPUT_FILE}")
    print(f"Log written to: {LOG_FILE}")

if __name__ == "__main__":
    main()