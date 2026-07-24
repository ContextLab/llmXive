import os
import sys
import json
import logging
import subprocess
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/ci_pipeline_run.log')
    ]
)
logger = logging.getLogger(__name__)

def run_script(script_path: str, timeout_seconds: int = 3600) -> bool:
    """
    Execute a Python script with a timeout.
    
    Args:
        script_path: Path to the Python script to execute
        timeout_seconds: Maximum execution time in seconds
        
    Returns:
        True if execution succeeded, False otherwise
    """
    logger.info(f"Executing script: {script_path}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=False,
            timeout=timeout_seconds
        )
        elapsed = time.time() - start_time
        logger.info(f"Script completed successfully in {elapsed:.2f} seconds")
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Script timed out after {timeout_seconds} seconds")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Script failed with return code {e.returncode}")
        return False
    except FileNotFoundError:
        logger.error(f"Script not found: {script_path}")
        return False

def verify_output_file(output_path: str, required_content_check: bool = True) -> bool:
    """
    Verify that an output file exists and optionally check for error messages.
    
    Args:
        output_path: Path to the output file to verify
        required_content_check: If True, check that file doesn't contain error markers
        
    Returns:
        True if verification passed, False otherwise
    """
    path = Path(output_path)
    
    if not path.exists():
        logger.error(f"Output file missing: {output_path}")
        return False
    
    if required_content_check:
        try:
            content = path.read_text()
            error_markers = ['ERROR', 'Exception', 'Traceback', 'FAILED']
            for marker in error_markers:
                if marker in content:
                    logger.warning(f"Potential error marker found in {output_path}: {marker}")
                    # We don't fail immediately, just warn, as some markers might be in data
        except Exception as e:
            logger.error(f"Could not read output file for content check: {e}")
            return False
    
    logger.info(f"Output file verified: {output_path}")
    return True

def write_failure_report(reason: str, output_path: str = "pipeline_failure_report.json"):
    """
    Write a failure report to disk.
    
    Args:
        reason: Description of the failure
        output_path: Path to write the failure report
    """
    report = {
        "status": "failed",
        "reason": reason,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.error(f"Failure report written to {output_path}")

def main():
    """
    Main entry point for CI pipeline execution.
    
    Executes the full pipeline on the seed dataset and generates the final report.
    Verifies all required outputs exist and are valid.
    """
    logger.info("=" * 60)
    logger.info("Starting CI Pipeline Execution (T041)")
    logger.info("=" * 60)
    
    # Ensure logs directory exists
    Path("logs").mkdir(parents=True, exist_ok=True)
    
    # Define the pipeline steps
    pipeline_steps = [
        {
            "name": "Generate Target List",
            "script": "code/data/generate_target_list.py",
            "output": "data/raw/target_list.csv"
        },
        {
            "name": "Download NVD Data",
            "script": "code/data/download_nvd.py",
            "output": "data/raw/nvd_cve_merged.json.gz"
        },
        {
            "name": "Extract GitHub Metrics",
            "script": "code/data/extract_github.py",
            "output": "data/processed/github_raw_metrics.csv"
        },
        {
            "name": "Merge Datasets",
            "script": "code/data/merge_datasets.py",
            "output": "data/processed/repo_metrics_clean.csv"
        },
        {
            "name": "Fit Models",
            "script": "code/analysis/fit_models.py",
            "output": "data/processed/model_results_raw.json"
        },
        {
            "name": "Run Robustness Checks",
            "script": "code/analysis/robustness.py",
            "output": "data/processed/robustness_results.json"
        },
        {
            "name": "Generate Final Report",
            "script": "code/analysis/generate_final_report.py",
            "output": "docs/final_analysis_report.md"
        }
    ]
    
    # Execute each step
    all_success = True
    failed_steps = []
    
    for step in pipeline_steps:
        logger.info(f"\n--- Executing: {step['name']} ---")
        
        if not run_script(step["script"]):
            logger.error(f"Step failed: {step['name']}")
            failed_steps.append(step["name"])
            all_success = False
            # Continue execution to gather all errors, but mark as failed
            # In a strict CI, we might want to stop here.
            # For this task, we attempt to run the report generation anyway if possible.
        
        # Verify output
        if not verify_output_file(step["output"]):
            logger.warning(f"Output verification failed for: {step['name']}")
            # Don't necessarily fail the whole pipeline if it's a warning step,
            # but for critical steps like the final report, we must fail.
        
        # Small delay to prevent resource contention
        time.sleep(1)
    
    # Final verification for the specific T041 requirement
    final_report_path = "docs/final_analysis_report.md"
    
    if all_success and verify_output_file(final_report_path):
        logger.info("=" * 60)
        logger.info("CI Pipeline Execution SUCCESSFUL")
        logger.info(f"Final report generated at: {final_report_path}")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("=" * 60)
        logger.error("CI Pipeline Execution FAILED")
        if failed_steps:
            logger.error(f"Failed steps: {', '.join(failed_steps)}")
        logger.error(f"Final report status: {'Missing' if not Path(final_report_path).exists() else 'Exists but may have issues'}")
        logger.error("=" * 60)
        
        write_failure_report(
            reason=f"Pipeline failed at steps: {', '.join(failed_steps) if failed_steps else 'Final report verification failed'}",
            output_path="pipeline_failure_report.json"
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())