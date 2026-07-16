"""
Task T037: Add timing logic to verify pipeline completes within 2-hour CPU budget (FR-010).

This script implements the timing logic required to monitor the pipeline execution
and verify it stays within the 2-hour (7200 seconds) CPU budget.
"""
import os
import sys
import time
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Import the timing utilities from the existing API
from timing import (
    TimingReport,
    timed_pipeline,
    check_budget_usage,
    write_timing_report,
    verify_pipeline_budget
)
from main import run_full_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BUDGET_SECONDS = 7200  # 2 hours
OUTPUT_DIR = Path("data/results")
TIMING_REPORT_FILE = OUTPUT_DIR / "timing_report.json"

def run_simulated_pipeline() -> Dict[str, Any]:
    """
    Run a simulated (partial) pipeline to test timing logic without full execution.
    This is useful for verifying the timing infrastructure works correctly.
    
    Returns:
        Dict containing timing results and budget status
    """
    logger.info("Starting simulated pipeline timing test...")
    
    # Simulate a pipeline that takes a small fraction of the budget
    start_time = time.time()
    
    # Simulate pipeline stages
    stages = [
        ("data_generation", 5.0),
        ("noise_injection", 3.0),
        ("metrics_computation", 10.0),
        ("analysis", 2.0),
        ("visualization", 1.0)
    ]
    
    for stage_name, duration in stages:
        logger.info(f"Simulating {stage_name} stage...")
        time.sleep(duration)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Create timing report
    timing_report = TimingReport(
        total_time_seconds=total_time,
        budget_seconds=BUDGET_SECONDS,
        stages=[
            {"name": name, "duration": dur} for name, dur in stages
        ],
        status="completed" if total_time < BUDGET_SECONDS else "exceeded"
    )
    
    # Verify budget
    budget_ok = verify_pipeline_budget(timing_report)
    
    logger.info(f"Simulated pipeline completed in {total_time:.2f}s")
    logger.info(f"Budget status: {'PASS' if budget_ok else 'FAIL'}")
    
    return {
        "timing_report": timing_report,
        "budget_ok": budget_ok,
        "total_time": total_time
    }

def run_real_pipeline() -> Dict[str, Any]:
    """
    Run the actual full pipeline with timing monitoring.
    This executes the complete data generation, noise injection,
    metrics computation, analysis, and visualization pipeline.
    
    Returns:
        Dict containing timing results and budget status
    """
    logger.info("Starting real pipeline with timing monitoring...")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Run the pipeline with timing
    start_time = time.time()
    
    try:
        # Execute the full pipeline
        # This will generate clean data, inject noise, compute metrics,
        # perform analysis, and generate visualizations
        pipeline_result = run_full_pipeline()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Create timing report
        timing_report = TimingReport(
            total_time_seconds=total_time,
            budget_seconds=BUDGET_SECONDS,
            stages=[],  # Would be populated with actual stage timings in a more detailed implementation
            status="completed" if total_time < BUDGET_SECONDS else "exceeded"
        )
        
        # Verify budget
        budget_ok = verify_pipeline_budget(timing_report)
        
        # Write timing report to file
        write_timing_report(timing_report, TIMING_REPORT_FILE)
        
        logger.info(f"Real pipeline completed in {total_time:.2f}s")
        logger.info(f"Budget status: {'PASS' if budget_ok else 'FAIL'}")
        logger.info(f"Timing report written to {TIMING_REPORT_FILE}")
        
        return {
            "timing_report": timing_report,
            "budget_ok": budget_ok,
            "total_time": total_time,
            "pipeline_result": pipeline_result
        }
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        
        # Create error timing report
        end_time = time.time()
        total_time = end_time - start_time
        
        timing_report = TimingReport(
            total_time_seconds=total_time,
            budget_seconds=BUDGET_SECONDS,
            stages=[],
            status="failed",
            error=str(e)
        )
        
        write_timing_report(timing_report, TIMING_REPORT_FILE)
        
        return {
            "timing_report": timing_report,
            "budget_ok": False,
            "total_time": total_time,
            "error": str(e)
        }

def main():
    """Main entry point for T037 timing verification."""
    parser = argparse.ArgumentParser(
        description="Task T037: Verify pipeline timing within 2-hour budget"
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run simulated pipeline instead of real execution"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(TIMING_REPORT_FILE),
        help="Output path for timing report JSON"
    )
    
    args = parser.parse_args()
    
    if args.simulate:
        logger.info("Running simulated pipeline timing test...")
        result = run_simulated_pipeline()
    else:
        logger.info("Running real pipeline with timing monitoring...")
        result = run_real_pipeline()
    
    # Print summary
    print("\n" + "="*60)
    print("T037 TIMING VERIFICATION SUMMARY")
    print("="*60)
    print(f"Total Time: {result['total_time']:.2f} seconds")
    print(f"Budget: {BUDGET_SECONDS} seconds (2 hours)")
    print(f"Status: {'PASS' if result['budget_ok'] else 'FAIL'}")
    
    if 'error' in result:
        print(f"Error: {result['error']}")
        
    print(f"Timing Report: {args.output}")
    print("="*60 + "\n")
    
    # Exit with appropriate code
    sys.exit(0 if result['budget_ok'] else 1)

if __name__ == "__main__":
    main()
