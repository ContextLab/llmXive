"""
Main entry point for the llmXive automated science pipeline.

This module orchestrates the full research workflow:
1. Setup logging and environment configuration.
2. Validate dependencies.
3. Execute the pipeline stages (Download, Preprocess, Metrics, Analysis, Report).
4. Profile memory usage and verify runtime targets (< 4 hours).
"""
import logging
import sys
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Import local modules using the defined API surface
from config_utils import load_config, set_random_seed, setup_environment
from download import main as run_download
from preprocess import main as run_preprocess
from metrics import main as run_metrics
from analysis import main as run_analysis
from report import main as run_report
from quickstart_validator import verify_outputs

# Setup logging configuration
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for the pipeline.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file. If None, logs to stderr only.
    
    Returns:
        The root logger instance.
    """
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def validate_dependencies() -> bool:
    """
    Validate that all required third-party libraries are installed.
    
    Returns:
        True if all dependencies are available, False otherwise.
    """
    required_modules = [
        'mne', 'statsmodels', 'networkx', 'scipy', 'pandas', 'numpy', 'pyedflib'
    ]
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        logging.error(f"Missing required dependencies: {', '.join(missing)}")
        logging.error("Please install them via: pip install -r code/requirements.txt")
        return False
    
    logging.info("All required dependencies are installed.")
    return True

def get_memory_usage_bytes() -> int:
    """
    Get current memory usage in bytes.
    
    Returns:
        Memory usage in bytes, or 0 if unavailable.
    """
    try:
        import resource
        # Get RSS (Resident Set Size) in bytes
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    except (ImportError, AttributeError):
        logging.warning("Could not determine memory usage (resource module not available).")
        return 0

def profile_memory_usage(threshold_gb: float = 4.0) -> bool:
    """
    Profile memory usage against a threshold.
    
    Args:
        threshold_gb: Maximum allowed memory usage in GB.
    
    Returns:
        True if memory usage is within limits, False otherwise.
    """
    usage_bytes = get_memory_usage_bytes()
    usage_gb = usage_bytes / (1024 ** 3)
    
    if usage_gb > threshold_gb:
        logging.error(f"Memory usage ({usage_gb:.2f} GB) exceeds threshold ({threshold_gb} GB).")
        return False
    
    logging.info(f"Memory usage within limits: {usage_gb:.2f} GB / {threshold_gb} GB")
    return True

def verify_runtime_target(start_time: datetime, target_hours: float = 4.0) -> bool:
    """
    Verify that the runtime is within the target limit.
    
    Args:
        start_time: The start time of the pipeline execution.
        target_hours: Target maximum runtime in hours.
    
    Returns:
        True if within target, False if exceeded.
    """
    elapsed = datetime.now() - start_time
    elapsed_hours = elapsed.total_seconds() / 3600
    
    if elapsed_hours > target_hours:
        logging.warning(
            f"Runtime target exceeded: {elapsed_hours:.2f} hours / {target_hours} hours"
        )
        return False
    
    logging.info(
        f"Runtime target met: {elapsed_hours:.2f} hours / {target_hours} hours"
    )
    return True

def main():
    """
    Main entry point for the pipeline.
    
    Orchestrates the full research workflow:
    1. Setup logging and environment.
    2. Validate dependencies.
    3. Execute pipeline stages (Download, Preprocess, Metrics, Analysis, Report).
    4. Profile memory and verify runtime targets (< 4 hours).
    """
    start_time = datetime.now()
    logging.info(f"Pipeline started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load configuration
    config = load_config()
    if not config:
        logging.error("Failed to load configuration.")
        sys.exit(1)
    
    # Setup environment and random seeds
    setup_environment(config)
    set_random_seed(config.get('random_seed', 42))
    
    # Setup logging
    log_file = config.get('log_file')
    log_level = config.get('log_level', 'INFO')
    setup_logging(log_level=log_level, log_file=log_file)
    
    # Validate dependencies
    if not validate_dependencies():
        sys.exit(1)
    
    # Execute pipeline stages
    stages = [
        ("Download", run_download),
        ("Preprocess", run_preprocess),
        ("Metrics", run_metrics),
        ("Analysis", run_analysis),
        ("Report", run_report),
    ]
    
    for stage_name, stage_func in stages:
        try:
            logging.info(f"Starting stage: {stage_name}")
            stage_func()
            logging.info(f"Completed stage: {stage_name}")
        except Exception as e:
            logging.error(f"Stage {stage_name} failed: {str(e)}")
            sys.exit(1)
    
    # Verify outputs
    try:
        verify_outputs()
        logging.info("Output verification passed.")
    except Exception as e:
        logging.error(f"Output verification failed: {str(e)}")
        sys.exit(1)
    
    # Check memory usage
    if not profile_memory_usage(threshold_gb=4.0):
        logging.warning("Memory usage exceeded recommended limits.")
    
    # Verify runtime target
    if not verify_runtime_target(start_time, target_hours=4.0):
        logging.warning("Runtime target exceeded.")
    
    end_time = datetime.now()
    total_duration = end_time - start_time
    logging.info(
        f"Pipeline completed successfully in {total_duration.total_seconds()/3600:.2f} hours."
    )

if __name__ == "__main__":
    main()