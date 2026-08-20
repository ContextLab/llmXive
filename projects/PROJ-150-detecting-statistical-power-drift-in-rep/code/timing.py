"""
code/timing.py
Instruments pipeline execution and generates results/timing_report.json.

This module wraps the main pipeline execution to measure wall-clock time,
ensuring the full analysis runs within the 6-hour (21600s) constraint defined
in FR-010. It invokes the orchestrator in code/main.py and logs start/end
timestamps along with the total duration.
"""
import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from main import run_pipeline, generate_final_report

# Configure logging
# Ensure logs directory exists before configuring file handler
logs_dir = project_root / 'logs'
logs_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(logs_dir / 'pipeline_timing.log')
    ]
)
logger = logging.getLogger('timing')

def ensure_dirs():
    """Ensure required directories exist."""
    (project_root / 'results').mkdir(parents=True, exist_ok=True)
    (project_root / 'logs').mkdir(parents=True, exist_ok=True)

def run_timed_pipeline():
    """Run the full pipeline and measure execution time.
    
    Executes the main pipeline logic from code/main.py and captures
    start/end timestamps and total duration.
    
    Returns:
        dict: Report data containing timing information and status.
    """
    logger.info("Starting timed pipeline execution...")
    start_time = time.time()
    start_dt = datetime.now().isoformat()

    try:
        # Run the main pipeline orchestrator
        run_pipeline()
        
        # Generate the final report
        generate_final_report()
        
        end_time = time.time()
        end_dt = datetime.now().isoformat()
        
        duration_seconds = end_time - start_time
        
        logger.info(f"Pipeline completed successfully in {duration_seconds:.2f} seconds")
        
        return {
            "start_time": start_dt,
            "end_time": end_dt,
            "duration_seconds": round(duration_seconds, 2),
            "status": "success",
            "message": "Full pipeline executed within time limit"
        }
        
    except Exception as e:
        end_time = time.time()
        end_dt = datetime.now().isoformat()
        duration_seconds = end_time - start_time
        
        logger.error(f"Pipeline failed after {duration_seconds:.2f} seconds: {str(e)}")
        
        return {
            "start_time": start_dt,
            "end_time": end_dt,
            "duration_seconds": round(duration_seconds, 2),
            "status": "failed",
            "error": str(e)
        }

def save_timing_report(report_data):
    """Save timing report to results/timing_report.json.
    
    Args:
        report_data (dict): The timing report dictionary to save.
        
    Returns:
        Path: The path to the saved report file.
    """
    output_path = project_root / 'results' / 'timing_report.json'
    
    # Ensure results directory exists
    (project_root / 'results').mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Timing report saved to {output_path}")
    return output_path

def main():
    """Main entry point for timing instrumentation.
    
    Orchestrates the full pipeline execution with timing measurement,
    saves the report, and verifies compliance with the 6-hour limit.
    
    Returns:
        int: 0 if successful and within time limit, 1 otherwise.
    """
    logger.info("=" * 60)
    logger.info("T034a: Running full pipeline with timing instrumentation")
    logger.info("=" * 60)
    
    ensure_dirs()
    
    # Run the pipeline
    report_data = run_timed_pipeline()
    
    # Save the report
    save_timing_report(report_data)
    
    # Check if within 6-hour limit (21600 seconds)
    if report_data['status'] == 'success':
        if report_data['duration_seconds'] <= 21600:
            logger.info(f"✓ Pipeline completed within 6-hour limit: {report_data['duration_seconds']}s")
            return 0
        else:
            logger.warning(f"✗ Pipeline exceeded 6-hour limit: {report_data['duration_seconds']}s")
            return 1
    else:
        logger.error("Pipeline execution failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())