import os
import sys
import json
import logging
import argparse
import subprocess
import time
from pathlib import Path
from config import ensure_dirs, AnalysisConfig
from utils.logger import get_logger

logger = get_logger(__name__)

def count_rows(file_path: str) -> int:
    """Count rows in a CSV file."""
    import pandas as pd
    if not os.path.exists(file_path):
        return 0
    df = pd.read_csv(file_path)
    return len(df)

def run_command_with_timeout(command: list, timeout_seconds: int, cwd: str = None) -> tuple:
    """
    Run a command with a timeout using subprocess.
    Returns (return_code, stdout, stderr, timed_out)
    """
    start_time = time.time()
    try:
        result = subprocess.run(
            command,
            timeout=timeout_seconds,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        elapsed = time.time() - start_time
        return result.returncode, result.stdout, result.stderr, False, elapsed
    except subprocess.TimeoutExpired as e:
        elapsed = time.time() - start_time
        # Handle partial output if available
        stdout = e.stdout.decode() if e.stdout else ""
        stderr = e.stderr.decode() if e.stderr else ""
        return -1, stdout, stderr, True, elapsed

def run_full_pipeline(config_path: str = None, max_configs: int = None) -> tuple:
    """
    Run the full pipeline via main.py with dynamic budgeting.
    Returns (return_code, stdout, stderr, timed_out, runtime)
    """
    # Determine max configs based on dataset size
    cleaned_data_path = "data/processed/cleaned_sn1.csv"
    n_rows = count_rows(cleaned_data_path)
    
    if n_rows >= 2000:
        # Reduce hyperparameter search configurations if dataset is large
        if max_configs is None:
            max_configs = 10  # Reduced limit for large datasets
        logger.info(f"Large dataset detected ({n_rows} rows). Reducing HP search to {max_configs} configs.")
    else:
        if max_configs is None:
            max_configs = 50  # Default limit for smaller datasets

    # Build command
    cmd = ["python", "code/main.py"]
    if max_configs is not None:
        cmd.extend(["--max-configs", str(max_configs)])
    
    logger.info(f"Running pipeline with command: {' '.join(cmd)}")
    
    # Run with timeout (6 hours = 21600 seconds, but we use a safety margin)
    timeout_limit = 21600  # 6 hours
    return_code, stdout, stderr, timed_out, runtime = run_command_with_timeout(cmd, timeout_limit)
    
    return return_code, stdout, stderr, timed_out, runtime

def verify_artifacts() -> dict:
    """Verify that all required artifacts exist after pipeline run."""
    required_artifacts = [
        "data/processed/cleaned_sn1.csv",
        "data/processed/exclusion_report.csv",
        "artifacts/best_model.pt",
        "artifacts/metrics.json",
        "artifacts/feasibility_test_log.json"
    ]
    
    results = {}
    all_exist = True
    
    for artifact in required_artifacts:
        exists = os.path.exists(artifact)
        results[artifact] = exists
        if not exists:
            all_exist = False
            logger.warning(f"Missing artifact: {artifact}")
    
    return {"all_exist": all_exist, "details": results}

def evaluate_sc002(runtime: float, status: str) -> dict:
    """
    Evaluate Success Criterion 002 (runtime <= 6 hours).
    Returns dict with status and details.
    """
    max_runtime_hours = 6.0
    max_runtime_seconds = max_runtime_hours * 3600
    
    if status == "TIMEOUT":
        sc_status = "FAIL"
        reason = "Runtime exceeded timeout limit"
    elif runtime > max_runtime_seconds:
        sc_status = "FAIL"
        reason = f"Runtime ({runtime:.2f}s) exceeded limit ({max_runtime_seconds}s)"
    else:
        sc_status = "PASS"
        reason = f"Runtime ({runtime:.2f}s) within limit ({max_runtime_seconds}s)"
    
    return {
        "sc_id": "SC-002",
        "status": sc_status,
        "reason": reason,
        "runtime_seconds": runtime,
        "limit_seconds": max_runtime_seconds
    }

def main():
    parser = argparse.ArgumentParser(description="Feasibility test runner for T040")
    parser.add_argument("--config-path", type=str, default=None, help="Path to config file")
    parser.add_argument("--max-configs", type=int, default=None, help="Max HP search configurations")
    args = parser.parse_args()

    ensure_dirs()
    
    logger.info("Starting feasibility test run (T040)...")
    
    # Run full pipeline
    return_code, stdout, stderr, timed_out, runtime = run_full_pipeline(
        config_path=args.config_path,
        max_configs=args.max_configs
    )
    
    # Verify artifacts
    artifact_verification = verify_artifacts()
    
    # Evaluate SC-002
    if timed_out:
        pipeline_status = "TIMEOUT"
    elif return_code != 0:
        pipeline_status = "FAILURE"
    else:
        pipeline_status = "SUCCESS"
    
    sc002_result = evaluate_sc002(runtime, pipeline_status)
    
    # Compile final log
    feasibility_log = {
        "task_id": "T040",
        "pipeline_status": pipeline_status,
        "return_code": return_code,
        "runtime_seconds": runtime,
        "timed_out": timed_out,
        "sc002_evaluation": sc002_result,
        "artifact_verification": artifact_verification,
        "stdout_sample": stdout[:500] if stdout else "",
        "stderr_sample": stderr[:500] if stderr else ""
    }
    
    # Save feasibility log
    output_path = "artifacts/feasibility_test_log.json"
    with open(output_path, "w") as f:
        json.dump(feability_log, f, indent=2)
    
    logger.info(f"Feability test log saved to {output_path}")
    
    if not artifact_verification["all_exist"] or return_code != 0:
        logger.error("Feability test failed: artifacts missing or pipeline failed.")
        sys.exit(1)
    
    logger.info("Feability test completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()