import argparse
import logging
import signal
import sys
import time
import os
import hashlib
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable

from utils import get_logger, calculate_checksum
from config import ensure_directories, get_config_summary

# Import pipeline step wrappers
from data_extraction import run_data_extraction_wrapper
from static_analysis import run_static_analysis
from preprocessing import run_preprocessing
from analysis import run_analysis
from visualization import run_visualization
from reporting import run_reporting

logger = get_logger(__name__)

# Configuration for state tracking
STATE_DIR = Path("state/projects")
PROJECT_ID = "PROJ-089-investigating-the-correlation-between-co"

def timeout_handler(signum, frame):
    """Signal handler for pipeline timeout."""
    logger.error("Pipeline execution timed out. Terminating.")
    sys.exit(1)

def run_pipeline_step(step_name: str, func: Callable, timeout_seconds: Optional[int] = None) -> bool:
    """
    Execute a pipeline step with optional timeout and error handling.
    
    Args:
        step_name: Human-readable name of the step
        func: Function to execute
        timeout_seconds: Optional timeout in seconds
        
    Returns:
        True if step completed successfully, False otherwise
    """
    logger.info(f"Starting step: {step_name}")
    start_time = time.time()
    
    try:
        if timeout_seconds:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
        
        func()
        
        elapsed = time.time() - start_time
        logger.info(f"Completed step: {step_name} in {elapsed:.2f}s")
        
        if timeout_seconds:
            signal.alarm(0)  # Cancel alarm
            
        return True
        
    except Exception as e:
        logger.error(f"Step failed: {step_name} with error: {str(e)}")
        if timeout_seconds:
            signal.alarm(0)
        return False

def execute_data_extraction():
    """Run data extraction pipeline."""
    run_data_extraction_wrapper()

def execute_static_analysis():
    """Run static analysis pipeline."""
    run_static_analysis()

def execute_preprocessing():
    """Run preprocessing pipeline."""
    run_preprocessing()

def execute_analysis():
    """Run statistical analysis pipeline."""
    run_analysis()

def execute_visualization():
    """Run visualization pipeline."""
    run_visualization()

def execute_reporting():
    """Run reporting pipeline."""
    run_reporting()

def compute_file_checksums(file_paths: list) -> Dict[str, str]:
    """
    Compute SHA256 checksums for a list of files.
    
    Args:
        file_paths: List of file paths to checksum
        
    Returns:
        Dictionary mapping file paths to their checksums
    """
    checksums = {}
    for file_path in file_paths:
        path = Path(file_path)
        if path.exists():
            checksums[str(path)] = calculate_checksum(path)
        else:
            logger.warning(f"File not found for checksum: {path}")
    return checksums

def update_project_state(checksums: Dict[str, str], execution_time: float, success: bool):
    """
    Update the project state YAML file with execution metadata and checksums.
    
    Args:
        checksums: Dictionary of file checksums
        execution_time: Total pipeline execution time in seconds
        success: Whether the pipeline completed successfully
    """
    ensure_directories()
    
    state_path = STATE_DIR / f"{PROJECT_ID}.yaml"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    current_state = {}
    if state_path.exists():
        try:
            with open(state_path, 'r') as f:
                current_state = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.warning(f"Could not parse existing state file: {e}")
            current_state = {}
    
    # Update state
    state_data = {
        "project_id": PROJECT_ID,
        "last_run": datetime.now().isoformat(),
        "execution_time_seconds": execution_time,
        "status": "completed" if success else "failed",
        "checksums": checksums,
        "config_summary": get_config_summary()
    }
    
    # Merge with existing state if needed
    if current_state:
        state_data["previous_runs"] = current_state.get("previous_runs", [])
        state_data["previous_runs"].append({
            "timestamp": state_data["last_run"],
            "execution_time": state_data["execution_time_seconds"],
            "status": state_data["status"]
        })
    
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Project state updated: {state_path}")

def main():
    """
    Main entry point for the pipeline orchestrator.
    Executes the full pipeline and finalizes with checksums and state update.
    """
    parser = argparse.ArgumentParser(description="Code Churn vs Technical Debt Pipeline")
    parser.add_argument("--timeout", type=int, default=3600, help="Pipeline timeout in seconds")
    parser.add_argument("--steps", type=str, default="all", 
                      help="Comma-separated list of steps to run (default: all)")
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/logs/pipeline.log')
        ]
    )
    
    logger.info("Starting Code Churn vs Technical Debt Pipeline")
    start_time = time.time()
    
    # Define pipeline steps
    steps = {
        "data_extraction": (execute_data_extraction, 1800),
        "static_analysis": (execute_static_analysis, 1800),
        "preprocessing": (execute_preprocessing, 600),
        "analysis": (execute_analysis, 900),
        "visualization": (execute_visualization, 600),
        "reporting": (execute_reporting, 300)
    }
    
    # Determine which steps to run
    if args.steps == "all":
        step_order = list(steps.keys())
    else:
        step_order = [s.strip() for s in args.steps.split(",")]
    
    success = True
    for step_name in step_order:
        if step_name not in steps:
            logger.error(f"Unknown step: {step_name}")
            success = False
            break
        
        func, timeout = steps[step_name]
        if not run_pipeline_step(step_name, func, timeout):
            success = False
            break
    
    total_time = time.time() - start_time
    
    # Finalize: Compute checksums and update state
    if success:
        # Define output files to checksum
        output_files = [
            "data/processed/unified_metrics.csv",
            "data/results/correlation_results.csv",
            "data/results/sensitivity_analysis.csv",
            "data/results/meta_analysis_results.csv",
            "data/results/summary_report.txt",
            "data/logs/tool_validation_log.csv"
        ]
        
        # Add plot files if they exist
        plots_dir = Path("data/results/plots")
        if plots_dir.exists():
            for plot_file in plots_dir.glob("*.png"):
                output_files.append(str(plot_file))
        
        checksums = compute_file_checksums(output_files)
        update_project_state(checksums, total_time, True)
        logger.info(f"Pipeline completed successfully in {total_time:.2f}s")
    else:
        update_project_state({}, total_time, False)
        logger.error("Pipeline failed. State updated with failure status.")
        sys.exit(1)

if __name__ == "__main__":
    main()