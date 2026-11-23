"""
Runtime Validation Script for Avian Migration Pipeline.
Executes the full pipeline wrapped in a timing mechanism and reports results.
"""
import os
import sys
import json
import time
import subprocess
import logging
from pathlib import Path

# Add project root to path if running from elsewhere
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_logger, ensure_directories

logger = get_logger(__name__)

def execute_pipeline_with_timing():
    """
    Executes the pipeline script and measures total execution time.
    Returns the elapsed time in seconds.
    """
    logger.info("Starting pipeline execution for runtime validation...")
    
    pipeline_script = project_root / "code" / "main.py"
    if not pipeline_script.exists():
        raise FileNotFoundError(f"Pipeline script not found at {pipeline_script}")
    
    start_time = time.time()
    
    try:
        # Execute the pipeline with the --validate flag
        # We capture output to parse if needed, but rely on exit code for success
        result = subprocess.run(
            [sys.executable, str(pipeline_script), "--validate"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=21600  # 6 hours timeout
        )
        
        end_time = time.time()
        total_seconds = end_time - start_time
        
        if result.returncode != 0:
            logger.error(f"Pipeline execution failed with exit code {result.returncode}")
            logger.error(f"Stderr: {result.stderr}")
            # We still record the time, but mark as failed
            return total_seconds, False
        
        logger.info(f"Pipeline execution completed successfully in {total_seconds:.2f} seconds.")
        return total_seconds, True

    except subprocess.TimeoutExpired:
        logger.error("Pipeline execution timed out (> 6 hours)")
        end_time = time.time()
        return end_time - start_time, False
    except Exception as e:
        logger.error(f"Error during pipeline execution: {str(e)}")
        end_time = time.time()
        return end_time - start_time, False

def write_validation_report(total_seconds, passed):
    """
    Writes the runtime validation report to data/outputs/runtime_validation.json.
    """
    outputs_dir = project_root / "data" / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = outputs_dir / "runtime_validation.json"
    
    report_data = {
        "total_seconds": round(total_seconds, 2),
        "passed": passed
    }
    
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Validation report written to {report_path}")
    return report_path

def main():
    """
    Main entry point for runtime validation.
    """
    logger.info("Running Runtime Validation (T037)...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Execute pipeline and measure time
    total_seconds, passed = execute_pipeline_with_timing()
    
    # Write report
    report_path = write_validation_report(total_seconds, passed)
    
    # Log final status
    if passed:
        logger.info(f"VALIDATION PASSED: Pipeline completed in {total_seconds:.2f}s (< 21600s limit)")
    else:
        logger.warning(f"VALIDATION FAILED: Pipeline took {total_seconds:.2f}s or failed to execute.")
    
    return 0 if passed else 1

if __name__ == "__main__":
    sys.exit(main())
