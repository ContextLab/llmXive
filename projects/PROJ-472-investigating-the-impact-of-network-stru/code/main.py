import os
import sys
import argparse
import logging
import json
import signal
from pathlib import Path
from typing import Dict, Any, Optional

# Local imports
from config import get_data_root, N_MIN
from utils.logger import get_logger, log_pipeline_start, log_pipeline_end, log_exception
from data.quality_control import calculate_pipeline_completeness
from data.store import run_store_pipeline
from analysis.metrics import run_metrics_pipeline
from analysis.avalanches import run_avalanche_pipeline
from analysis.fitting import run_fitting_pipeline
from analysis.stats import run_correlation_analysis
from analysis.sensitivity import run_sensitivity_pipeline
from analysis.report import generate_report

logger = get_logger(__name__)

class PipelineTimeoutError(Exception):
    """Raised when the pipeline execution exceeds the time limit."""
    pass

def timeout_handler(signum, frame):
    raise PipelineTimeoutError("Pipeline execution exceeded the time limit.")

def setup_timeout(seconds: int):
    """Setup a timeout for the pipeline execution."""
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
    else:
        logger.warning("SIGALRM not available on this platform. Timeout disabled.")

def clear_timeout():
    """Clear the timeout if it was set."""
    if hasattr(signal, 'SIGALRM'):
        signal.alarm(0)

def load_research_config() -> Dict[str, Any]:
    """Load the research phase configuration."""
    config_path = get_data_root().parent / "specs" / "001-network-structure-avalanche-dynamics" / "research_phase_config.json"
    if not config_path.exists():
        # Return defaults if file doesn't exist
        return {
            "thresholds": [0.70, 0.75, 0.80],
            "N_MIN": N_MIN,
            "simulation_flags": True,
            "model_params": {}
        }
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load research config: {e}")
        return {
            "thresholds": [0.70, 0.75, 0.80],
            "N_MIN": N_MIN,
            "simulation_flags": True,
            "model_params": {}
        }

def count_usable_subjects() -> int:
    """Count the number of usable subjects from the QC output."""
    usable_subjects_path = get_data_root() / "processed" / "usable_subjects.json"
    if not usable_subjects_path.exists():
        logger.warning(f"Usable subjects file not found at {usable_subjects_path}. Returning 0.")
        return 0
    try:
        with open(usable_subjects_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return len(data)
            elif isinstance(data, dict) and "subject_ids" in data:
                return len(data["subject_ids"])
            else:
                logger.error(f"Unexpected format in usable_subjects.json: {data}")
                return 0
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to read usable subjects: {e}")
        return 0

def run_null_result_protocol(n_subjects: int, n_min: int) -> bool:
    """
    Execute the null result protocol if sample size is insufficient.
    Returns True if the pipeline should halt (N=0), False if it should proceed with limited analysis (0 < N < N_MIN).
    """
    if n_subjects == 0:
        logger.critical("No usable subjects found. Halting pipeline.")
        return True # Halt

    if n_subjects < n_min:
        logger.warning(f"Sample size ({n_subjects}) is below minimum threshold ({n_min}). Generating insufficient sample report.")
        report_path = get_data_root() / "results" / "insufficient_sample_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write(f"# Insufficient Sample Size Report\n\n")
            f.write(f"**Date**: {__import__('datetime').datetime.now().isoformat()}\n\n")
            f.write(f"**Minimum Required Subjects (N_MIN)**: {n_min}\n\n")
            f.write(f"**Actual Usable Subjects (N)**: {n_subjects}\n\n")
            f.write(f"**Status**: Analysis will proceed with limited statistical power.\n\n")
            f.write(f"**Note**: The study is constrained by the available sample size. Statistical findings should be interpreted with caution and considered preliminary.\n\n")
        
        logger.info(f"Insufficient sample report generated at {report_path}")
        
        # Update routing state for limited path
        routing_state = {
            "path": "limited",
            "N": n_subjects,
            "N_MIN": n_min,
            "status": "limited"
        }
        routing_path = get_data_root() / "processed" / "routing_state.json"
        with open(routing_path, 'w') as f:
            json.dump(routing_state, f, indent=2)
        
        return False # Proceed with limited analysis
    
    return False # Proceed normally

def run_correlation_protocol():
    """Run the full correlation and analysis pipeline."""
    logger.info("Starting correlation protocol.")
    
    # Run metrics
    logger.info("Running structural metrics pipeline...")
    run_metrics_pipeline()
    
    # Run avalanche detection
    logger.info("Running avalanche detection pipeline...")
    run_avalanche_pipeline()
    
    # Run fitting
    logger.info("Running power-law fitting pipeline...")
    run_fitting_pipeline()
    
    # Run correlation analysis
    logger.info("Running correlation analysis...")
    run_correlation_analysis()
    
    # Run sensitivity analysis
    logger.info("Running sensitivity analysis...")
    run_sensitivity_pipeline()
    
    # Generate final report
    logger.info("Generating final report...")
    generate_report()
    
    logger.info("Correlation protocol completed.")

def check_sample_size_gate():
    """
    Implement the Sample Size Check runtime gate (T029c).
    1. Count usable subjects N from data/processed/usable_subjects.json.
    2. Read N_MIN from config.
    3. If N < N_MIN: Generate insufficient_sample_report.md, set routing state to 'limited', proceed if N > 0.
    4. If N = 0: Halt with error.
    5. If N >= N_MIN: Set routing state to 'correlation', proceed.
    """
    logger.info("Executing Sample Size Check Gate (T029c).")
    
    n_subjects = count_usable_subjects()
    n_min = N_MIN
    
    logger.info(f"Usable subjects: {n_subjects}, Minimum required: {n_min}")
    
    routing_state_path = get_data_root() / "processed" / "routing_state.json"
    routing_state_path.parent.mkdir(parents=True, exist_ok=True)
    
    if n_subjects == 0:
        logger.critical("Sample size is 0. Halting pipeline execution.")
        # Write a failure state
        state = {
            "path": "halt",
            "N": 0,
            "N_MIN": n_min,
            "status": "halt",
            "error": "No usable subjects found."
        }
        with open(routing_state_path, 'w') as f:
            json.dump(state, f, indent=2)
        raise RuntimeError("Pipeline halted: No usable subjects found.")
    
    if n_subjects < n_min:
        logger.warning(f"Sample size ({n_subjects}) is below minimum ({n_min}). Proceeding with limited analysis.")
        # Run null result protocol to generate report and set state
        should_halt = run_null_result_protocol(n_subjects, n_min)
        if should_halt:
            raise RuntimeError("Pipeline halted due to insufficient sample size (N=0).")
        
        # Update routing state to 'limited' (overwriting previous state if any)
        state = {
            "path": "limited",
            "N": n_subjects,
            "N_MIN": n_min,
            "status": "limited"
        }
        with open(routing_state_path, 'w') as f:
            json.dump(state, f, indent=2)
        logger.info("Routing state updated to 'limited'. Proceeding to limited analysis.")
        return "limited"
    
    # N >= N_MIN
    logger.info(f"Sample size ({n_subjects}) meets minimum requirement ({n_min}). Proceeding to full correlation analysis.")
    state = {
        "path": "correlation",
        "N": n_subjects,
        "N_MIN": n_min,
        "status": "proceed"
    }
    with open(routing_state_path, 'w') as f:
        json.dump(state, f, indent=2)
    logger.info("Routing state updated to 'correlation'. Proceeding to full analysis.")
    return "correlation"

def run_pipeline(args):
    """Main pipeline execution logic."""
    log_pipeline_start("Network Structure Avalanche Dynamics Pipeline")
    
    try:
        # Setup timeout if specified
        if args.timeout > 0:
            setup_timeout(args.timeout)
        
        # Ensure data directories exist
        data_root = get_data_root()
        data_root.mkdir(parents=True, exist_ok=True)
        (data_root / "raw").mkdir(exist_ok=True)
        (data_root / "processed").mkdir(exist_ok=True)
        (data_root / "results").mkdir(exist_ok=True)
        
        # 1. Check Sample Size Gate (T029c)
        # This must happen after QC (T012) which produces usable_subjects.json
        # If this task is run directly, it assumes T012 has completed.
        gate_status = check_sample_size_gate()
        
        if gate_status == "halt":
            # Should have raised an error already
            return
        
        # 2. Run Store Pipeline (if not already done by previous steps)
        # The task description implies this gate is a checkpoint. 
        # If we are here, we have data. We proceed to analysis.
        # Note: T013 (store) is usually run before T012 (QC) or T029c.
        # We assume the data is already stored and usable_subjects.json exists.
        
        # 3. Run Analysis based on gate status
        if gate_status == "correlation":
            run_correlation_protocol()
        elif gate_status == "limited":
            logger.info("Running limited analysis protocol.")
            # Run a subset of the analysis or the full analysis but with warnings
            # For now, we run the full correlation protocol but the report will reflect the limitation
            run_correlation_protocol()
            
    except PipelineTimeoutError as e:
        logger.critical(f"Pipeline timed out: {e}")
        timeout_report_path = get_data_root() / "results" / "runtime_timeout_report.md"
        with open(timeout_report_path, 'w') as f:
            f.write(f"# Runtime Timeout Report\n\n")
            f.write(f"**Error**: {e}\n\n")
            f.write(f"**Time Limit**: {args.timeout} seconds\n\n")
        raise
    except Exception as e:
        log_exception(e)
        raise
    finally:
        clear_timeout()
        log_pipeline_end()

def parse_args():
    parser = argparse.ArgumentParser(description="Network Structure Avalanche Dynamics Pipeline")
    parser.add_argument("--timeout", type=int, default=0, help="Timeout in seconds (0 = no timeout)")
    parser.add_argument("--validate", action="store_true", help="Run validation checks only")
    return parser.parse_args()

def main():
    args = parse_args()
    if args.validate:
        logger.info("Running validation checks...")
        # Simple validation: check if required files exist
        data_root = get_data_root()
        required_files = [
            data_root / "processed" / "usable_subjects.json",
            data_root / "processed" / "routing_state.json" # This task writes this
        ]
        missing = [str(f) for f in required_files if not f.exists()]
        if missing:
            logger.error(f"Validation failed. Missing files: {missing}")
            sys.exit(1)
        logger.info("Validation passed.")
        sys.exit(0)
    
    run_pipeline(args)

if __name__ == "__main__":
    main()