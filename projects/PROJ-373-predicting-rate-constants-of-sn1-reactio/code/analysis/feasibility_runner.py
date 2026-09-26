import os
import sys
import json
import logging
import argparse
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs, DataConfig, TrainingConfig
from utils.logger import get_logger

logger = get_logger(__name__)

# Constants
TIMEOUT_SECONDS = 6 * 3600  # 6 hours in seconds
DATA_PATH = "data/processed/cleaned_sn1.csv"
OUTPUT_PATH = "artifacts/feasibility_test_log.json"

def count_rows(file_path: str) -> int:
    """Count rows in a CSV file efficiently."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    count = 0
    with open(file_path, 'r') as f:
        # Skip header
        next(f, None)
        for line in f:
            count += 1
    return count

def run_command_with_timeout(cmd: list, timeout: int, cwd: str = None) -> Dict[str, Any]:
    """Run a command with a timeout using subprocess."""
    start_time = time.time()
    result = {
        'success': False,
        'exit_code': None,
        'runtime_seconds': 0,
        'error': None,
        'timed_out': False
    }
    
    try:
        process = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        result['exit_code'] = process.returncode
        result['runtime_seconds'] = time.time() - start_time
        result['success'] = (process.returncode == 0)
        if process.stderr:
            result['error'] = process.stderr
    except subprocess.TimeoutExpired as e:
        result['timed_out'] = True
        result['runtime_seconds'] = timeout
        result['error'] = f"Command timed out after {timeout} seconds"
        logger.error(f"Command timed out: {e}")
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Command failed: {e}")
    
    return result

def run_full_pipeline(max_configs: Optional[int] = None) -> Dict[str, Any]:
    """Run the full pipeline with optional max_configs limit."""
    cmd = [sys.executable, "code/main.py"]
    
    if max_configs is not None:
        cmd.append(f"--max-configs={max_configs}")
    
    logger.info(f"Running pipeline with command: {' '.join(cmd)}")
    return run_command_with_timeout(cmd, TIMEOUT_SECONDS)

def verify_artifacts() -> Dict[str, bool]:
    """Verify that all required artifacts exist."""
    required_artifacts = [
        "data/processed/cleaned_sn1.csv",
        "data/processed/exclusion_report.csv",
        "artifacts/best_model.pt",
        "artifacts/metrics.json",
        "artifacts/final_report.md"
    ]
    
    verification = {}
    for artifact in required_artifacts:
        exists = os.path.exists(artifact) and os.path.getsize(artifact) > 0
        verification[artifact] = exists
        if not exists:
            logger.warning(f"Missing or empty artifact: {artifact}")
    
    return verification

def evaluate_sc002(runtime_seconds: float) -> str:
    """Evaluate Success Criterion 002: Runtime <= 6 hours."""
    if runtime_seconds <= TIMEOUT_SECONDS:
        return "PASS"
    else:
        return "FAIL"

def main():
    parser = argparse.ArgumentParser(description="Run final feasibility validation")
    parser.add_argument("--max-configs", type=int, default=None,
                      help="Maximum number of hyperparameter configurations to search")
    parser.add_argument("--input", type=str, default=DATA_PATH,
                      help="Path to input dataset")
    parser.add_argument("--output", type=str, default=OUTPUT_PATH,
                      help="Path to output log file")
    args = parser.parse_args()

    ensure_dirs()
    
    logger.info("Starting feasibility validation run (T040)")
    
    # Step 1: Count rows and determine budgeting
    try:
        row_count = count_rows(args.input)
        logger.info(f"Input dataset contains {row_count} rows")
    except FileNotFoundError as e:
        error_result = {
            'status': 'ERROR',
            'reason': 'input_missing',
            'message': str(e),
            'sc002_status': 'FAIL',
            'artifacts_verified': False,
            'runtime_seconds': 0
        }
        with open(args.output, 'w') as f:
            json.dump(error_result, f, indent=2)
        sys.exit(1)

    # Step 2: Determine max_configs if not provided
    max_configs = args.max_configs
    if max_configs is None and row_count >= 2000:
        max_configs = 10  # Reduced for large datasets
        logger.info(f"Dataset size >= 2000 rows. Reducing hyperparameter search to {max_configs} configs")
    
    # Step 3: Run pipeline with timeout
    pipeline_result = run_full_pipeline(max_configs)
    
    # Step 4: Evaluate SC-002
    sc002_status = evaluate_sc002(pipeline_result['runtime_seconds'])
    
    # Step 5: Verify artifacts if pipeline succeeded
    artifacts_verified = False
    if pipeline_result['success']:
        artifacts_verified = all(verify_artifacts().values())
    
    # Step 6: Compile final result
    final_result = {
        'status': 'SUCCESS' if pipeline_result['success'] and artifacts_verified else 'FAILURE',
        'runtime_seconds': pipeline_result['runtime_seconds'],
        'timed_out': pipeline_result['timed_out'],
        'exit_code': pipeline_result['exit_code'],
        'sc002_status': sc002_status,
        'row_count': row_count,
        'max_configs_used': max_configs,
        'artifacts_verified': artifacts_verified,
        'error': pipeline_result.get('error'),
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Step 7: Write output
    with open(args.output, 'w') as f:
        json.dump(final_result, f, indent=2)
    
    logger.info(f"Feasibility test completed. Status: {final_result['status']}")
    logger.info(f"SC-002 (Runtime <= 6h): {sc002_status}")
    
    if not pipeline_result['success'] or not artifacts_verified:
        sys.exit(1)

if __name__ == "__main__":
    main()
