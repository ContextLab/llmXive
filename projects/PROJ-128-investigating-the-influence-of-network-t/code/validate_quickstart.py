import os
import sys
import json
import time
import traceback
from pathlib import Path

# Project root is the directory containing 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = DATA_DIR / "logs"

# Critical output files defined in tasks.md and the pipeline
REQUIRED_FILES = {
    # Structural Metrics (US1)
    "structural_metrics.csv": PROCESSED_DIR / "structural_metrics.csv",
    # Dynamic Metrics (US1)
    "dynamic_metrics.csv": PROCESSED_DIR / "dynamic_metrics.csv",
    # State Assignments (US1)
    "state_assignments.csv": PROCESSED_DIR / "state_assignments.csv",
    # LOO Centroids (US1)
    "loo_centroids.npy": PROCESSED_DIR / "loo_centroids.npy",
    # Correlation Results (US2)
    "correlation_results.csv": PROCESSED_DIR / "correlation_results.csv",
    # Sensitivity Comparison (US3)
    "sensitivity_comparison.csv": PROCESSED_DIR / "sensitivity_comparison.csv",
    # Exclusion Log (US1)
    "exclusion_log.json": LOGS_DIR / "exclusion_log.json",
    # Final Report (US3)
    "final_report.json": DATA_DIR / "final_report.json",
    # Directory structure checks
    "raw_dir": DATA_DIR / "raw",
    "processed_dir": PROCESSED_DIR,
    "logs_dir": LOGS_DIR,
}

def log_step(step_name: str, status: str, details: str = ""):
    """Log a validation step to stdout."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    status_symbol = "✓" if status == "PASS" else "✗"
    print(f"[{timestamp}] {status_symbol} {step_name}: {details}")

def validate_file_exists(path: Path, file_desc: str) -> bool:
    """Check if a file or directory exists."""
    if path.exists():
        if path.is_file():
            size = path.stat().st_size
            log_step(f"File: {file_desc}", "PASS", f"Exists ({size} bytes)")
        else:
            log_step(f"Dir: {file_desc}", "PASS", "Exists")
        return True
    else:
        log_step(f"Missing: {file_desc}", "FAIL", f"Path not found: {path}")
        return False

def validate_file_content(path: Path, file_desc: str, min_lines: int = 1) -> bool:
    """Check if a file exists and has minimum content."""
    if not path.exists():
        log_step(f"Content: {file_desc}", "FAIL", "File missing")
        return False

    try:
        if path.suffix == ".json":
            with open(path, 'r') as f:
                data = json.load(f)
            if isinstance(data, dict) and len(data) > 0:
                log_step(f"Content: {file_desc}", "PASS", f"Valid JSON with keys: {list(data.keys())[:3]}")
                return True
            else:
                log_step(f"Content: {file_desc}", "FAIL", "Empty or invalid JSON")
                return False
        elif path.suffix == ".csv":
            with open(path, 'r') as f:
                lines = f.readlines()
            if len(lines) >= min_lines:
                log_step(f"Content: {file_desc}", "PASS", f"{len(lines)} lines")
                return True
            else:
                log_step(f"Content: {file_desc}", "FAIL", f"Too few lines: {len(lines)}")
                return False
        elif path.suffix == ".npy":
            import numpy as np
            data = np.load(path)
            log_step(f"Content: {file_desc}", "PASS", f"Shape: {data.shape}")
            return True
        else:
            log_step(f"Content: {file_desc}", "PASS", "Exists")
            return True
    except Exception as e:
        log_step(f"Content: {file_desc}", "FAIL", f"Read error: {str(e)}")
        return False

def run_validation():
    """Run the full quickstart validation suite."""
    print("=" * 60)
    print("Running Quickstart Validation Pipeline")
    print("=" * 60)

    all_passed = True

    # 1. Check Directory Structure
    log_step("Directory Structure", "INFO", "Checking data directories...")
    for key, path in REQUIRED_FILES.items():
        if key.endswith("_dir"):
            if not validate_file_exists(path, key):
                all_passed = False

    # 2. Check Processed Data Artifacts
    log_step("Processed Artifacts", "INFO", "Checking pipeline outputs...")
    file_checks = [
        ("structural_metrics.csv", REQUIRED_FILES["structural_metrics.csv"], 2),
        ("dynamic_metrics.csv", REQUIRED_FILES["dynamic_metrics.csv"], 2),
        ("state_assignments.csv", REQUIRED_FILES["state_assignments.csv"], 2),
        ("loo_centroids.npy", REQUIRED_FILES["loo_centroids.npy"], 1),
        ("correlation_results.csv", REQUIRED_FILES["correlation_results.csv"], 2),
        ("sensitivity_comparison.csv", REQUIRED_FILES["sensitivity_comparison.csv"], 2),
        ("exclusion_log.json", REQUIRED_FILES["exclusion_log.json"], 1),
        ("final_report.json", REQUIRED_FILES["final_report.json"], 1),
    ]

    for desc, path, min_lines in file_checks:
        if not validate_file_content(path, desc, min_lines):
            all_passed = False

    # 3. Check Code Artifacts (Basic existence)
    log_step("Code Artifacts", "INFO", "Checking critical scripts...")
    code_files = [
        "code/main.py",
        "code/preprocess/structural.py",
        "code/preprocess/functional.py",
        "code/analysis/correlation.py",
        "code/analysis/robustness.py",
        "code/reports/generate_report.py",
        "code/config.py",
    ]
    for code_path in code_files:
        full_path = PROJECT_ROOT / code_path
        if not validate_file_exists(full_path, code_path):
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("VALIDATION RESULT: SUCCESS")
        print("All critical pipeline artifacts and directories are present.")
        sys.exit(0)
    else:
        print("VALIDATION RESULT: FAILURE")
        print("One or more critical artifacts are missing or invalid.")
        sys.exit(1)

if __name__ == "__main__":
    run_validation()