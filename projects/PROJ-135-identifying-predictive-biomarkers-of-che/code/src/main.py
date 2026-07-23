"""
Main Orchestrator for the Biomarker Discovery Pipeline.

This script coordinates the execution of data acquisition, preprocessing,
biomarker identification, and model validation stages.
"""
import sys
import argparse
import json
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any

# Import project configuration and utilities
from .config import ensure_directories, PROJECT_ROOT, DATA_DIR, RESULTS_DIR, STATE_DIR
from .utils import (
    setup_logging,
    watchdog,
    get_file_size_mb,
    TimeoutError,
    update_state_artifact_hashes,
)
from .data_acquisition import (
    download_tcga_data,
    run_data_feasibility_gate,
    write_feasibility_gate_result,
)
from .preprocessing import process_tumor_type
# Future imports for US2 and US3 will be added as those tasks are implemented
# from .differential_expression import run_differential_expression
# from .meta_analysis import run_meta_analysis
# from .modeling import run_modeling
# from .validation import run_validation

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Orchestrator for Chemotherapy Biomarker Discovery Pipeline"
    )
    parser.add_argument(
        "--stages",
        type=str,
        default="all",
        help="Comma-separated list of stages to run (e.g., 'acquisition,preprocessing'). Default: all",
    )
    parser.add_argument(
        "--tumor-types",
        type=str,
        default=None,
        help="Comma-separated list of specific tumor types to process. If None, processes all available.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=18000,  # 5 hours in seconds
        help="Maximum runtime in seconds before termination.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print configuration and exit without executing stages.",
    )
    return parser.parse_args()

def run_acquisition_stage(args: argparse.Namespace) -> Dict[str, Any]:
    """Execute the data acquisition stage."""
    logging.info("Starting Data Acquisition Stage")
    
    # Determine tumor types to acquire
    tumor_types = args.tumor_types.split(",") if args.tumor_types else None
    
    # Run TCGA download
    # Note: This will trigger the feasibility gate internally if configured
    success = download_tcga_data(target_tumor_types=tumor_types)
    
    if not success:
        logging.error("Data acquisition failed. Halting pipeline.")
        return {"status": "failed", "stage": "acquisition"}
    
    # Run Feasibility Gate
    gate_result = run_data_feasibility_gate()
    if gate_result.get("status") == "halted":
        write_feasibility_gate_result(gate_result)
        logging.error(f"Feasibility Gate Halted: {gate_result.get('reason')}")
        return {"status": "halted", "stage": "acquisition", "reason": gate_result.get("reason")}
    
    return {"status": "success", "stage": "acquisition"}

def run_preprocessing_stage(args: argparse.Namespace) -> Dict[str, Any]:
    """Execute the preprocessing stage."""
    logging.info("Starting Preprocessing Stage")
    
    tumor_types = args.tumor_types.split(",") if args.tumor_types else None
    
    # We need to know which tumor types were successfully acquired.
    # For now, we assume a standard set or read from a manifest if T019/T020 created one.
    # In a full implementation, we would read `data/raw/manifest.json` or similar.
    # Here we call the process function which handles the logic per type.
    
    results = []
    # Placeholder for actual tumor type list derived from acquisition
    # In T012/T013, we will know exactly what was downloaded.
    # For the skeleton, we iterate a known set or empty if none specified.
    if not tumor_types:
        # Default to processing if acquisition happened, but we need a list.
        # Let's assume the acquisition stage wrote a list of successful types to a temp file
        # or we scan data/raw. For the skeleton, we just log.
        logging.info("No specific tumor types defined for preprocessing. Skipping actual processing in skeleton.")
        return {"status": "skipped", "stage": "preprocessing", "reason": "No tumor types specified"}

    for t_type in tumor_types:
        res = process_tumor_type(t_type)
        results.append(res)
    
    return {"status": "success", "stage": "preprocessing", "details": results}

def main() -> int:
    """Main entry point for the orchestrator."""
    args = parse_args()
    
    # Setup logging
    log_file = RESULTS_DIR / "pipeline.log"
    logger = setup_logging(log_file=log_file, level=logging.INFO)
    
    logging.info("=" * 60)
    logging.info("llmXive Biomarker Discovery Pipeline Started")
    logging.info(f"Project Root: {PROJECT_ROOT}")
    logging.info(f"Stages to run: {args.stages}")
    logging.info("=" * 60)

    # Ensure directories exist
    ensure_directories()

    if args.dry_run:
        logging.info("Dry run mode. Exiting.")
        return 0

    # Initialize metrics
    start_time = time.time()
    runtime_metrics = {
        "start_time": start_time,
        "timeout_limit": args.timeout,
        "timeout_triggered": False,
        "peak_memory_mb": 0,
        "stages_completed": []
    }

    try:
        # Wrap execution in watchdog for timeout
        def run_pipeline():
            stages_to_run = [s.strip() for s in args.stages.split(",")]
            
            if "all" in stages_to_run or "acquisition" in stages_to_run:
                res = run_acquisition_stage(args)
                if res["status"] in ["failed", "halted"]:
                    return res
                runtime_metrics["stages_completed"].append("acquisition")
            
            if "all" in stages_to_run or "preprocessing" in stages_to_run:
                res = run_preprocessing_stage(args)
                if res["status"] == "failed":
                    return res
                runtime_metrics["stages_completed"].append("preprocessing")
            
            # Future stages (US2, US3) would be called here
            
            return {"status": "success"}

        # Execute pipeline with timeout
        result = watchdog(run_pipeline, timeout_seconds=args.timeout)
        
        if result is None:
            # Timeout occurred
            runtime_metrics["timeout_triggered"] = True
            logging.error("Pipeline timed out.")
            return 1
        
        if result.get("status") in ["failed", "halted"]:
            logging.error(f"Pipeline failed or halted: {result.get('reason', 'Unknown')}")
            return 1

        runtime_metrics["end_time"] = time.time()
        runtime_metrics["duration_seconds"] = runtime_metrics["end_time"] - start_time
        
        # Write runtime metrics
        metrics_path = RESULTS_DIR / "runtime_metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(runtime_metrics, f, indent=2)
        
        logging.info("Pipeline completed successfully.")
        logging.info(f"Runtime metrics written to {metrics_path}")
        return 0

    except TimeoutError:
        runtime_metrics["timeout_triggered"] = True
        logging.error("Pipeline execution timed out.")
        # Write metrics even on timeout
        metrics_path = RESULTS_DIR / "runtime_metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(runtime_metrics, f, indent=2)
        return 1
    except Exception as e:
        logging.exception(f"Pipeline execution failed with unhandled exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())