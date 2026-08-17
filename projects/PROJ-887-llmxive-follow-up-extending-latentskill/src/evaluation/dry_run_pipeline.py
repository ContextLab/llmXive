"""
T063: Execute the full pipeline in "dry-run" mode (N=1 per task).

This script orchestrates a minimal end-to-end execution of the llmXive pipeline
to verify the flow from ingestion to final report generation without timing out.
It uses a dry-run flag to skip heavy computations (e.g., N=1 instead of N>=5).

Outputs:
    logs/dry_run_pipeline.log: Detailed log of the execution, including any errors or warnings.
"""

import os
import sys
import logging
import time
import argparse
from pathlib import Path
import json
import traceback

# Ensure the project root is in the path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import get_project_root, ensure_directories, set_seed
from src.ingestion.download_weights import main as download_weights_main
from src.ingestion.flatten_lora import main as flatten_lora_main
from src.retrieval.vector_db import main as vector_db_main
from src.retrieval.query import main as query_main
from src.retrieval.strategies import main as strategies_main
from src.validation.linearity_check import main as linearity_main
from src.evaluation.runner import main as runner_main
from src.evaluation.stats import main as stats_main
from src.evaluation.report_generator import main as report_gen_main
from src.evaluation.final_report import main as final_report_main
from src.utils.plotting import main as plotting_main

# Configure logging
def setup_logging(log_path: Path):
    """Setup logging to file and console."""
    ensure_directories(log_path.parent)
    logger = logging.getLogger("dry_run_pipeline")
    logger.setLevel(logging.DEBUG)

    # File handler
    fh = logging.FileHandler(log_path, mode='w')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

def log_step(logger, step_name: str, func, *args, **kwargs):
    """Execute a pipeline step with logging and error handling."""
    logger.info(f"--- Starting Step: {step_name} ---")
    start_time = time.time()
    try:
        # Pass dry_run=True if the function signature supports it
        # We use a try/except to handle signature mismatches gracefully for this dry-run
        import inspect
        sig = inspect.signature(func)
        if 'dry_run' in sig.parameters:
            kwargs['dry_run'] = True
        
        func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.info(f"--- Step {step_name} completed successfully in {elapsed:.2f}s ---")
        return True
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"--- Step {step_name} FAILED after {elapsed:.2f}s ---")
        logger.error(f"Error: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def main():
    parser = argparse.ArgumentParser(description="Dry-run execution of the llmXive pipeline.")
    parser.add_argument("--output-dir", type=str, default="logs", help="Directory for logs.")
    parser.add_argument("--data-dir", type=str, default="data", help="Base data directory.")
    parser.add_argument("--artifacts-dir", type=str, default="artifacts", help="Base artifacts directory.")
    args = parser.parse_args()

    root = get_project_root()
    log_path = root / args.output_dir / "dry_run_pipeline.log"
    logger = setup_logging(log_path)

    logger.info("Starting Dry-Run Pipeline Execution (T063)")
    logger.info(f"Project Root: {root}")
    logger.info(f"Data Dir: {args.data_dir}")
    
    # Set seed for reproducibility
    set_seed(42)

    # Define the pipeline steps
    # Note: We are calling the 'main' functions of each module. 
    # In a real scenario, these might need specific arguments. 
    # For the dry-run, we assume they can be called with defaults or 
    # we wrap them to inject dry_run=True where possible.
    
    steps = [
        ("Ingestion: Download Weights", download_weights_main, []),
        ("Ingestion: Flatten LoRA", flatten_lora_main, []),
        ("Retrieval: Vector DB", vector_db_main, []),
        ("Retrieval: Query", query_main, []),
        ("Retrieval: Strategies", strategies_main, []),
        ("Validation: Linearity Check", linearity_main, []),
        ("Evaluation: Runner", runner_main, []),
        ("Evaluation: Stats", stats_main, []),
        ("Evaluation: Report Generator", report_gen_main, []),
        ("Evaluation: Final Report", final_report_main, []),
        ("Utils: Plotting", plotting_main, []),
    ]

    success_count = 0
    fail_count = 0

    for name, func, args_list in steps:
        # We catch exceptions inside log_step, so we just check the return
        if log_step(logger, name, func, *args_list):
            success_count += 1
        else:
            fail_count += 1
            # Continue to next step to gather all errors, or break? 
            # Task says "verify entire flow", so we continue to see what breaks.
            # But if a critical dependency fails (like download), we might want to note it.
            logger.warning(f"Continuing pipeline despite failure in {name}...")

    logger.info("=" * 50)
    logger.info(f"Dry-Run Summary: {success_count} succeeded, {fail_count} failed.")
    logger.info(f"Log saved to: {log_path}")
    
    # Write a summary JSON to the log directory for programmatic checking
    summary = {
        "status": "completed" if fail_count == 0 else "completed_with_errors",
        "success_count": success_count,
        "fail_count": fail_count,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    summary_path = root / args.output_dir / "dry_run_summary.json"
    ensure_directories(summary_path.parent)
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Summary saved to: {summary_path}")

    if fail_count > 0:
        logger.warning("Pipeline dry-run completed with errors. Check logs for details.")
        # Exit with 0 because the task is to "verify the flow" and log errors, 
        # not necessarily to fail the whole build if a step fails (unless it's a hard block).
        # However, if the goal is to ensure it *runs cleanly*, we might exit 1.
        # Given the task is "Execute... to verify... and log errors", we log and exit 0.
        return 0
    else:
        logger.info("Pipeline dry-run completed successfully.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
