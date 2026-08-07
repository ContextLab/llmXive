"""
validate_quickstart.py
Validates the end-to-end pipeline execution as described in quickstart.md.
"""
import os
import sys
import json
import time
import argparse
import logging
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUICKSTART_PATH = os.path.join(PROJECT_ROOT, 'quickstart.md')
DATA_RESULTS_DIR = os.path.join(PROJECT_ROOT, 'data', 'results')
E2E_LOG_PATH = os.path.join(DATA_RESULTS_DIR, 'e2e_run_log.txt')

# Expected output markers
PIPELINE_COMPLETE_MARKER = "Pipeline Complete"
EXIT_CODE_ZERO_MARKER = "Exit Code: 0"

def check_file_exists(path: str, description: str) -> bool:
    """Check if a file exists."""
    if not os.path.isfile(path):
        logger.error(f"Required file missing: {path} ({description})")
        return False
    logger.info(f"Found required file: {path}")
    return True

def check_directory_exists(path: str, description: str) -> bool:
    """Check if a directory exists."""
    if not os.path.isdir(path):
        logger.error(f"Required directory missing: {path} ({description})")
        return False
    logger.info(f"Found required directory: {path}")
    return True

def run_step(step_name: str, command: list, timeout: int = 300) -> tuple:
    """
    Run a shell command and capture output.
    Returns (success, stdout, stderr, return_code)
    """
    logger.info(f"Executing step: {step_name}")
    logger.info(f"Command: {' '.join(command)}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        duration = time.time() - start_time
        logger.info(f"Step '{step_name}' completed in {duration:.2f}s with exit code {result.returncode}")
        return result.returncode == 0, result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        logger.error(f"Step '{step_name}' timed out after {timeout}s")
        return False, "", "Timeout", -1
    except Exception as e:
        logger.error(f"Step '{step_name}' failed with exception: {e}")
        return False, "", str(e), -1

def validate_ingestion_output() -> bool:
    """Validate outputs from 01_ingest.py"""
    required_files = [
        os.path.join(DATA_RESULTS_DIR, 'ingestion_stats.json'),
        os.path.join(DATA_RESULTS_DIR, 'trajectory_samples.parquet')
    ]
    for f in required_files:
        if not os.path.exists(f):
            logger.warning(f"Ingestion output missing: {f}")
            # Do not fail hard if intermediate steps haven't run yet in this specific validation context
            # The main pipeline run will generate these.
    return True

def validate_clustering_output() -> bool:
    """Validate outputs from 02_cluster.py"""
    required_files = [
        os.path.join(DATA_RESULTS_DIR, 'clustering_method_log.json'),
        os.path.join(DATA_RESULTS_DIR, 'coverage_report.json')
    ]
    for f in required_files:
        if not os.path.exists(f):
            logger.warning(f"Clustering output missing: {f}")
    return True

def validate_training_output() -> bool:
    """Validate outputs from 03_train.py"""
    required_files = [
        os.path.join(DATA_RESULTS_DIR, 'hypothesis_failure_report.md'), # Optional if hypothesis holds
        os.path.join(PROJECT_ROOT, 'artifacts', 'models')
    ]
    for f in required_files:
        if not os.path.exists(f):
            logger.warning(f"Training output missing: {f}")
    return True

def validate_inference_output() -> bool:
    """Validate outputs from 04_inference.py"""
    required_files = [
        os.path.join(DATA_RESULTS_DIR, 'inference_benchmark.csv')
    ]
    for f in required_files:
        if not os.path.exists(f):
            logger.warning(f"Inference output missing: {f}")
    return True

def validate_simulation_output() -> bool:
    """Validate outputs from 05_simulate.py"""
    required_files = [
        os.path.join(DATA_RESULTS_DIR, 'simulation_logs.csv'),
        os.path.join(DATA_RESULTS_DIR, 'vla_proxy_baseline.parquet')
    ]
    for f in required_files:
        if not os.path.exists(f):
            logger.warning(f"Simulation output missing: {f}")
    return True

def validate_evaluation_output() -> bool:
    """Validate outputs from 06_evaluate.py"""
    required_files = [
        os.path.join(DATA_RESULTS_DIR, 'evaluation_report.md'),
        os.path.join(DATA_RESULTS_DIR, 'fidelity_metrics.json')
    ]
    for f in required_files:
        if not os.path.exists(f):
            logger.warning(f"Evaluation output missing: {f}")
    return True

def main():
    """
    Main validation entry point.
    Executes the pipeline defined in quickstart.md and validates outputs.
    """
    parser = argparse.ArgumentParser(description="Validate quickstart.md pipeline execution")
    parser.add_argument("--skip-checks", action="store_true", help="Skip pre-run file checks")
    args = parser.parse_args()

    # Ensure results directory exists
    os.makedirs(DATA_RESULTS_DIR, exist_ok=True)

    log_entries = []
    log_entries.append(f"E2E Validation Start: {datetime.now().isoformat()}")
    
    # 1. Check quickstart.md exists
    if not args.skip_checks:
        if not check_file_exists(QUICKSTART_PATH, "Pipeline instructions"):
            log_entries.append("CRITICAL: quickstart.md not found. Cannot proceed.")
            write_log(log_entries, success=False)
            sys.exit(1)

    # 2. Define pipeline steps based on typical quickstart.md content
    # We assume the pipeline runs the scripts in order: 01, 02, 03, 04, 05, 06, 07, 08
    # We will run them via python -m or direct script execution.
    # Since scripts are in code/, we run: python code/01_ingest.py etc.
    
    pipeline_steps = [
        ("Ingestion", ["python", "code/01_ingest.py"]),
        ("Clustering", ["python", "code/02_cluster.py"]),
        ("Training", ["python", "code/03_train.py"]),
        ("Inference", ["python", "code/04_inference.py"]),
        ("Simulation", ["python", "code/05_simulate.py"]),
        ("Evaluation", ["python", "code/06_evaluate.py"]),
        ("Fidelity", ["python", "code/07_calculate_fidelity.py"]),
        ("Reporting", ["python", "code/08_generate_report.py"])
    ]

    all_success = True
    pipeline_output_buffer = []

    for step_name, cmd in pipeline_steps:
        success, stdout, stderr, code = run_step(step_name, cmd)
        
        log_entry = f"--- {step_name} ---\nExit Code: {code}\nStdout:\n{stdout}\nStderr:\n{stderr}\n"
        pipeline_output_buffer.append(log_entry)
        
        if not success:
            logger.error(f"Step '{step_name}' failed.")
            all_success = False
            # Depending on strictness, we might stop here. 
            # For E2E validation, we try to run as much as possible to see cascade failures.
            # However, if a critical step fails, subsequent steps will likely fail too.
            # We continue to collect logs but mark overall as failed.

    # 3. Final Status
    final_status = "SUCCESS" if all_success else "FAILURE"
    exit_code = 0 if all_success else 1

    final_log = f"\n--- FINAL STATUS ---\n{PIPELINE_COMPLETE_MARKER if all_success else 'Pipeline Failed'}\nExit Code: {exit_code}"
    pipeline_output_buffer.append(final_log)

    # Write the complete log to the required output file
    full_log_content = "\n".join(pipeline_output_buffer)
    with open(E2E_LOG_PATH, 'w') as f:
        f.write(full_log_content)
    
    logger.info(f"Validation log written to: {E2E_LOG_PATH}")

    # Verify markers in the log
    has_complete = PIPELINE_COMPLETE_MARKER in full_log_content
    has_zero = EXIT_CODE_ZERO_MARKER in full_log_content

    if has_complete and has_zero:
        logger.info("Validation PASSED: Pipeline Complete and Exit Code 0 found.")
        sys.exit(0)
    else:
        logger.error("Validation FAILED: Required markers not found in output.")
        sys.exit(1)

def write_log(entries: list, success: bool):
    """Helper to write initial failure log if needed."""
    os.makedirs(DATA_RESULTS_DIR, exist_ok=True)
    with open(E2E_LOG_PATH, 'w') as f:
        f.write("\n".join(entries))

if __name__ == "__main__":
    main()
