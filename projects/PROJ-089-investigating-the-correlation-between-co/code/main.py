"""
main.py - Orchestrator for the Code Churn vs Technical Debt Pipeline.

This module implements the main execution flow, error handling, and timeout logic.
It coordinates the execution of data extraction, static analysis, preprocessing,
statistical analysis, visualization, and reporting modules.
"""

import argparse
import logging
import signal
import sys
import time
import os
import hashlib
from pathlib import Path
from typing import Optional, Callable, Dict, Any

# Import pipeline step functions from sibling modules
from config import ensure_directories, get_config_summary, get_env_override
from utils import setup_logging, get_logger, calculate_checksum, pin_random_seed
from data_extraction import run_data_extraction_wrapper
from static_analysis import run_static_analysis
from preprocessing import run_preprocessing
from analysis import run_analysis
from visualization import run_visualization  # Assuming this exists or is created later
from reporting import run_reporting
from parallelism_config import update_config_with_limits

# Custom exception for timeout errors
class TimeoutError(Exception):
    """Custom timeout exception for pipeline steps."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout events."""
    raise TimeoutError("Pipeline step exceeded the allowed time limit.")

def run_pipeline_step(
    step_name: str,
    step_func: Callable,
    timeout_seconds: Optional[int] = None,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Execute a pipeline step with optional timeout and error handling.
    
    Args:
        step_name: Human-readable name of the step for logging.
        step_func: The function to execute.
        timeout_seconds: Optional timeout in seconds. If None, no timeout is applied.
        logger: Logger instance. If None, a default logger is used.
        
    Returns:
        True if the step completed successfully, False otherwise.
    """
    if logger is None:
        logger = get_logger()
    
    logger.info(f"Starting pipeline step: {step_name}")
    start_time = time.time()
    
    # Set up timeout handler if timeout is specified
    old_handler = None
    if timeout_seconds is not None:
        # Only set signal handler on Unix-like systems
        if hasattr(signal, 'SIGALRM'):
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
        else:
            logger.warning(f"Timeout not supported on this platform for step: {step_name}")
    
    try:
        # Execute the step function
        step_func(logger=logger)
        elapsed = time.time() - start_time
        logger.info(f"Completed pipeline step: {step_name} in {elapsed:.2f} seconds")
        return True
        
    except TimeoutError as e:
        logger.error(f"Timeout error in step {step_name}: {e}")
        return False
        
    except Exception as e:
        logger.error(f"Error in pipeline step {step_name}: {e}", exc_info=True)
        return False
        
    finally:
        # Restore old signal handler and cancel alarm
        if timeout_seconds is not None and hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
            if old_handler:
                signal.signal(signal.SIGALRM, old_handler)

def execute_data_extraction(logger: logging.Logger) -> None:
    """Execute the data extraction pipeline step."""
    run_data_extraction_wrapper(logger=logger)

def execute_static_analysis(logger: logging.Logger) -> None:
    """Execute the static analysis pipeline step."""
    run_static_analysis(logger=logger)

def execute_preprocessing(logger: logging.Logger) -> None:
    """Execute the preprocessing pipeline step."""
    run_preprocessing(logger=logger)

def execute_analysis(logger: logging.Logger) -> None:
    """Execute the statistical analysis pipeline step."""
    run_analysis(logger=logger)

def execute_visualization(logger: logging.Logger) -> None:
    """Execute the visualization pipeline step."""
    # Placeholder for visualization module if not yet implemented
    try:
        run_visualization(logger=logger)
    except ImportError:
        logger.warning("Visualization module not yet implemented. Skipping visualization step.")

def execute_reporting(logger: logging.Logger) -> None:
    """Execute the reporting pipeline step."""
    run_reporting(logger=logger)

def compute_file_checksums(root_dir: str, logger: logging.Logger) -> None:
    """
    Compute and log checksums for all output files in the project.
    
    Args:
        root_dir: The root directory of the project.
        logger: Logger instance.
    """
    logger.info("Computing checksums for output files...")
    checksums = {}
    
    output_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "data/logs"
    ]
    
    for dir_name in output_dirs:
        dir_path = Path(root_dir) / dir_name
        if not dir_path.exists():
            continue
            
        for file_path in dir_path.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(root_dir)
                checksum = calculate_checksum(str(file_path))
                checksums[str(rel_path)] = checksum
                logger.debug(f"Checksum for {rel_path}: {checksum}")
    
    # Save checksums to a file
    checksum_file = Path(root_dir) / "data" / "results" / "checksums.txt"
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_file, "w") as f:
        for file_path, checksum in checksums.items():
            f.write(f"{file_path}: {checksum}\n")
    
    logger.info(f"Checksums saved to {checksum_file}")

def update_project_state(root_dir: str, logger: logging.Logger) -> None:
    """
    Update the project state file with the current status.
    
    Args:
        root_dir: The root directory of the project.
        logger: Logger instance.
    """
    logger.info("Updating project state...")
    state_dir = Path(root_dir) / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    state_file = state_dir / "pipeline_state.yaml"
    
    # Create or update state file
    state = {
        "pipeline_version": "1.0.0",
        "last_run": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "completed",
        "steps_completed": [
            "data_extraction",
            "static_analysis",
            "preprocessing",
            "analysis",
            "visualization",
            "reporting"
        ]
    }
    
    # Simple YAML serialization (avoiding pyyaml dependency for now)
    with open(state_file, "w") as f:
        f.write("# Pipeline State File\n")
        for key, value in state.items():
            if isinstance(value, list):
                f.write(f"{key}:\n")
                for item in value:
                    f.write(f"  - {item}\n")
            else:
                f.write(f"{key}: {value}\n")
    
    logger.info(f"Project state updated in {state_file}")

def main():
    """Main entry point for the pipeline orchestrator."""
    parser = argparse.ArgumentParser(
        description="Code Churn vs Technical Debt Pipeline Orchestrator"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,  # Default 1 hour timeout
        help="Timeout in seconds for each pipeline step"
    )
    parser.add_argument(
        "--parallel-limit",
        type=int,
        default=4,
        help="Maximum number of concurrent repository processes"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to custom configuration file"
    )
    parser.add_argument(
        "--steps",
        type=str,
        default="all",
        help="Comma-separated list of steps to run (e.g., 'data_extraction,analysis')"
    )
    
    args = parser.parse_args()
    
    # Initialize logging
    logger = setup_logging()
    logger.info("Starting Code Churn vs Technical Debt Pipeline")
    
    # Ensure directories exist
    ensure_directories()
    
    # Update parallelism config
    update_config_with_limits(max_repos=args.parallel_limit)
    
    # Pin random seed for reproducibility
    pin_random_seed(42)
    
    # Print config summary
    logger.info("Configuration Summary:")
    for key, value in get_config_summary().items():
        logger.info(f"  {key}: {value}")
    
    # Define pipeline steps
    steps = {
        "data_extraction": (execute_data_extraction, args.timeout),
        "static_analysis": (execute_static_analysis, args.timeout),
        "preprocessing": (execute_preprocessing, args.timeout),
        "analysis": (execute_analysis, args.timeout),
        "visualization": (execute_visualization, args.timeout),
        "reporting": (execute_reporting, args.timeout),
    }
    
    # Determine which steps to run
    if args.steps == "all":
        steps_to_run = list(steps.keys())
    else:
        steps_to_run = [s.strip() for s in args.steps.split(",")]
    
    # Execute pipeline steps
    success = True
    for step_name in steps_to_run:
        if step_name not in steps:
            logger.error(f"Unknown step: {step_name}")
            success = False
            continue
            
        step_func, timeout = steps[step_name]
        if not run_pipeline_step(step_name, step_func, timeout, logger):
            logger.error(f"Pipeline failed at step: {step_name}")
            success = False
            break
    
    if success:
        # Compute checksums and update state
        compute_file_checksums(".", logger)
        update_project_state(".", logger)
        logger.info("Pipeline completed successfully!")
    else:
        logger.error("Pipeline execution failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()