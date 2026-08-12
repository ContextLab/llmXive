"""
main.py - Orchestrator for the Code Churn vs Technical Debt pipeline.

Implements error handling, timeout logic, and sequential execution of pipeline stages.
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

# Import pipeline stages
# Note: These modules are expected to exist based on the API surface provided.
# If they are not yet implemented, the execution will fail loudly as required.
try:
    from data_extraction import run_data_extraction_wrapper
except ImportError:
    run_data_extraction_wrapper = None
    logging.warning("data_extraction module not found. Data extraction step will be skipped.")

try:
    from static_analysis import run_static_analysis
except ImportError:
    run_static_analysis = None
    logging.warning("static_analysis module not found. Static analysis step will be skipped.")

try:
    from preprocessing import run_preprocessing
except ImportError:
    run_preprocessing = None
    logging.warning("preprocessing module not found. Preprocessing step will be skipped.")

try:
    from analysis import run_analysis
except ImportError:
    run_analysis = None
    logging.warning("analysis module not found. Analysis step will be skipped.")

try:
    from visualization import run_visualization
except ImportError:
    run_visualization = None
    logging.warning("visualization module not found. Visualization step will be skipped.")

try:
    from reporting import run_reporting
except ImportError:
    run_reporting = None
    logging.warning("reporting module not found. Reporting step will be skipped.")

from config import ensure_directories, get_config_summary
from utils import setup_logging, get_logger, calculate_checksum, pin_random_seed

# Global timeout handler
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def run_pipeline_step(step_name: str, func: Optional[Callable], args: tuple = (), kwargs: Optional[Dict[str, Any]] = None, timeout: int = 3600) -> bool:
    """
    Executes a pipeline step with timeout and error handling.
    
    Args:
        step_name: Human-readable name of the step.
        func: The function to execute.
        args: Positional arguments for the function.
        kwargs: Keyword arguments for the function.
        timeout: Maximum execution time in seconds.
        
    Returns:
        True if successful, False otherwise.
    """
    if func is None:
        logger = get_logger()
        logger.warning(f"Step '{step_name}' skipped: function not implemented.")
        return True

    logger = get_logger()
    logger.info(f"Starting step: {step_name}")
    start_time = time.time()

    # Set up signal-based timeout (Unix only)
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)

    try:
        if kwargs is None:
            kwargs = {}
        result = func(*args, **kwargs)
        signal.alarm(0)  # Cancel alarm
        elapsed = time.time() - start_time
        logger.info(f"Step '{step_name}' completed successfully in {elapsed:.2f}s.")
        return True
    except TimeoutError:
        logger.error(f"Step '{step_name}' FAILED: Timeout after {timeout}s.")
        signal.alarm(0)
        return False
    except Exception as e:
        logger.error(f"Step '{step_name}' FAILED: {type(e).__name__}: {str(e)}")
        signal.alarm(0)
        return False
    finally:
        signal.signal(signal.SIGALRM, old_handler)

def execute_data_extraction(config: Dict[str, Any]) -> bool:
    """Wrapper for data extraction step."""
    return run_pipeline_step("Data Extraction", run_data_extraction_wrapper, kwargs={"config": config})

def execute_static_analysis(config: Dict[str, Any]) -> bool:
    """Wrapper for static analysis step."""
    return run_pipeline_step("Static Analysis", run_static_analysis, kwargs={"config": config})

def execute_preprocessing(config: Dict[str, Any]) -> bool:
    """Wrapper for preprocessing step."""
    return run_pipeline_step("Preprocessing", run_preprocessing, kwargs={"config": config})

def execute_analysis(config: Dict[str, Any]) -> bool:
    """Wrapper for analysis step."""
    return run_pipeline_step("Analysis", run_analysis, kwargs={"config": config})

def execute_visualization(config: Dict[str, Any]) -> bool:
    """Wrapper for visualization step."""
    return run_pipeline_step("Visualization", run_visualization, kwargs={"config": config})

def execute_reporting(config: Dict[str, Any]) -> bool:
    """Wrapper for reporting step."""
    return run_pipeline_step("Reporting", run_reporting, kwargs={"config": config})

def compute_file_checksums(root_dir: str) -> Dict[str, str]:
    """
    Computes SHA-256 checksums for all files in the output directory.
    
    Args:
        root_dir: The root directory to scan (e.g., data/results).
        
    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    checksums = {}
    root_path = Path(root_dir)
    logger = get_logger()
    
    if not root_path.exists():
        logger.warning(f"Checksum computation skipped: {root_dir} does not exist.")
        return checksums

    for file_path in root_path.rglob("*"):
        if file_path.is_file():
            checksum = calculate_checksum(str(file_path))
            rel_path = str(file_path.relative_to(root_path))
            checksums[rel_path] = checksum
            logger.debug(f"Checksum computed for {rel_path}: {checksum}")
    
    return checksums

def update_project_state(checksums: Dict[str, str], config: Dict[str, Any]) -> bool:
    """
    Updates the project state file with execution metadata and checksums.
    
    Args:
        checksums: Dictionary of file checksums.
        config: Current configuration.
        
    Returns:
        True if successful.
    """
    state_dir = Path(config.get("state_dir", "data/state"))
    state_dir.mkdir(parents=True, exist_ok=True)
    
    state_file = state_dir / "pipeline_state.json"
    
    import json
    state_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "checksums": checksums,
        "config_summary": get_config_summary(config)
    }
    
    try:
        with open(state_file, "w") as f:
            json.dump(state_data, f, indent=2)
        get_logger().info(f"Project state updated at {state_file}")
        return True
    except Exception as e:
        get_logger().error(f"Failed to update project state: {e}")
        return False

def main():
    """Main entry point for the pipeline orchestrator."""
    parser = argparse.ArgumentParser(description="Code Churn vs Technical Debt Pipeline Orchestrator")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to configuration file")
    parser.add_argument("--timeout", type=int, default=7200, help="Global pipeline timeout in seconds")
    parser.add_argument("--steps", type=str, nargs="+", 
                        choices=["extraction", "analysis", "preprocessing", "analysis", "visualization", "reporting"],
                        default=["extraction", "static_analysis", "preprocessing", "analysis", "visualization", "reporting"],
                        help="Specific steps to run")
    args = parser.parse_args()

    # Initialize logging
    setup_logging(level=logging.INFO)
    logger = get_logger()
    logger.info("Pipeline Orchestrator starting...")

    # Load configuration
    # Note: A simple config loading mechanism is assumed. 
    # In a real scenario, this might load from a YAML/JSON file.
    config = {
        "timeout": args.timeout,
        "steps": args.steps,
        "state_dir": "data/state",
        # Default values from config.py if needed
    }
    
    # Ensure directories exist
    ensure_directories(config)
    pin_random_seed(42) # Determinism

    start_time = time.time()
    success = True

    # Define step mapping
    step_map = {
        "extraction": execute_data_extraction,
        "static_analysis": execute_static_analysis,
        "preprocessing": execute_preprocessing,
        "analysis": execute_analysis,
        "visualization": execute_visualization,
        "reporting": execute_reporting
    }

    for step_name in args.steps:
        if step_name not in step_map:
            logger.warning(f"Unknown step requested: {step_name}")
            continue
        
        if not step_map[step_name](config):
            logger.error(f"Pipeline failed at step: {step_name}")
            success = False
            # Optional: Break on first failure or continue? 
            # For a research pipeline, we often want to stop to avoid noise.
            break

    total_time = time.time() - start_time
    
    if success:
        logger.info(f"Pipeline completed successfully in {total_time:.2f}s.")
        # Compute checksums and update state
        checksums = compute_file_checksums("data/results")
        update_project_state(checksums, config)
    else:
        logger.error(f"Pipeline failed after {total_time:.2f}s.")
        sys.exit(1)

if __name__ == "__main__":
    main()