"""
Memory profiling script for the preprocessing pipeline.

This script runs the preprocessing pipeline on available data and logs
peak RAM usage to results/memory_profile.csv.
"""

import os
import sys
import csv
import time
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False
    import warnings
    warnings.warn("resource module not available (non-Unix system). Memory profiling may be limited.")

# Import the preprocessing pipeline
from preprocessing.preprocess import run_preprocessing_pipeline
from config import load_config
from logging_config import setup_logging, get_logger

# Constants
RESULTS_DIR = project_root / "results"
MEMORY_PROFILE_FILE = RESULTS_DIR / "memory_profile.csv"


def get_peak_memory_mb() -> float:
    """
    Get the peak memory usage of the current process in MB.

    Returns:
        float: Peak memory usage in MB, or -1.0 if measurement is not possible.
    """
    if not HAS_RESOURCE:
        return -1.0

    # resource.getrusage(resource.RUSAGE_SELF).ru_maxrss is in KB on Linux/macOS
    # On some systems it might be in bytes, but typically KB
    try:
        maxrss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # Convert KB to MB
        return maxrss_kb / 1024.0
    except Exception:
        return -1.0


def initialize_memory_profile_csv() -> None:
    """
    Initialize the memory profile CSV file with headers if it doesn't exist.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if not MEMORY_PROFILE_FILE.exists():
        with open(MEMORY_PROFILE_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'peak_memory_mb', 'status', 'details'])


def append_memory_profile(timestamp: str, peak_memory_mb: float, status: str, details: str) -> None:
    """
    Append a memory profile entry to the CSV file.
    """
    with open(MEMORY_PROFILE_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, peak_memory_mb, status, details])


def run_preprocessing_with_memory_tracking(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run the preprocessing pipeline while tracking memory usage.

    Args:
        config: Optional configuration dictionary. If None, loads from config.yaml.

    Returns:
        Dict containing profiling results.
    """
    logger = get_logger("memory_profile")

    # Get initial memory
    initial_memory = get_peak_memory_mb()
    logger.info(f"Initial peak memory: {initial_memory:.2f} MB")

    start_time = time.time()

    try:
        # Run the preprocessing pipeline
        logger.info("Starting preprocessing pipeline...")
        result = run_preprocessing_pipeline(config=config)
        pipeline_success = True
        pipeline_message = "Pipeline completed successfully"
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        pipeline_success = False
        pipeline_message = str(e)
        result = None

    end_time = time.time()
    duration = end_time - start_time

    # Get final peak memory
    final_memory = get_peak_memory_mb()
    memory_delta = final_memory - initial_memory if initial_memory > 0 and final_memory > 0 else 0

    logger.info(f"Final peak memory: {final_memory:.2f} MB")
    logger.info(f"Memory delta: {memory_delta:.2f} MB")
    logger.info(f"Pipeline duration: {duration:.2f} seconds")

    return {
        'success': pipeline_success,
        'duration': duration,
        'initial_memory_mb': initial_memory,
        'final_memory_mb': final_memory,
        'memory_delta_mb': memory_delta,
        'message': pipeline_message,
        'result': result
    }


def main() -> int:
    """
    Main entry point for memory profiling.
    """
    # Setup logging
    setup_logging()
    logger = get_logger("memory_profile")

    logger.info("=" * 60)
    logger.info("Memory Profiling Script for Preprocessing Pipeline")
    logger.info("=" * 60)

    # Initialize CSV file
    initialize_memory_profile_csv()

    # Parse arguments
    parser = argparse.ArgumentParser(description="Profile memory usage during preprocessing")
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to configuration file (default: code/config.yaml)'
    )
    args = parser.parse_args()

    # Load configuration
    config = None
    if args.config:
        config_path = Path(args.config)
        if config_path.exists():
            config = load_config(config_path)
            logger.info(f"Loaded configuration from: {config_path}")
        else:
            logger.warning(f"Configuration file not found: {config_path}, using defaults")
    else:
        try:
            config_path = project_root / "code" / "config.yaml"
            if config_path.exists():
                config = load_config(config_path)
                logger.info(f"Loaded configuration from: {config_path}")
            else:
                logger.warning(f"Configuration file not found: {config_path}, using defaults")
        except Exception as e:
            logger.warning(f"Could not load configuration: {e}, using defaults")

    # Run profiling
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    profiling_result = run_preprocessing_with_memory_tracking(config)

    # Log results
    status = "SUCCESS" if profiling_result['success'] else "FAILED"
    details = f"Duration: {profiling_result['duration']:.2f}s; " \
              f"Initial: {profiling_result['initial_memory_mb']:.2f} MB; " \
              f"Final: {profiling_result['final_memory_mb']:.2f} MB; " \
              f"Delta: {profiling_result['memory_delta_mb']:.2f} MB; " \
              f"Message: {profiling_result['message']}"

    logger.info(f"Profiling completed: {status}")
    logger.info(f"Details: {details}")

    # Append to CSV
    peak_memory = profiling_result['final_memory_mb'] if profiling_result['final_memory_mb'] > 0 else -1.0
    append_memory_profile(timestamp, peak_memory, status, details)

    logger.info(f"Memory profile logged to: {MEMORY_PROFILE_FILE}")

    # Return exit code
    return 0 if profiling_result['success'] else 1


if __name__ == "__main__":
    sys.exit(main())
