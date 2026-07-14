import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

from config import (
    get_data_dir,
    get_raw_dir,
    get_stratified_dir,
    get_features_dir,
    get_results_dir,
    get_processed_dir,
    ensure_directories,
)
from utils.memory_monitor import get_session_metrics, clear_session_metrics
from utils.seeds import set_global_seed

# Expected artifacts based on tasks T007-T023
EXPECTED_FILES = {
    "raw_dataset": "data/raw/RealEstate10K",  # Directory check
    "stratified_metadata": "data/stratified/metadata.json",
    "feature_files": "data/features",  # Directory check
    "warped_frames": "data/results/sparse_warped_frames.npy",
    "dense_baseline": "data/raw/dense_baseline_frames.npy",
    "metrics_json": "data/results/metrics.json",
    "anova_results": "data/results/anova_results.json",
    "sensitivity_results": "data/results/sensitivity_results.json",
    "hypothesis_report": "data/results/hypothesis_verification.md",
    "memory_logs": "data/results/memory_profile.log",
}

EXPECTED_STRATA_DIRS = [
    "Static-High",
    "Static-Low",
    "Fast-High",
    "Fast-Low",
]

def log_status(status: str, details: str = "") -> Dict[str, Any]:
    """Log a status line and return a structured result."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": timestamp,
        "status": status,
        "details": details,
    }
    print(f"[{status}] {details}")
    return entry

def validate_file_exists(path_str: str) -> Tuple[bool, str]:
    """Check if a specific file exists."""
    path = Path(path_str)
    if not path.exists():
        return False, f"Missing file: {path_str}"
    if not path.is_file():
        return False, f"Path is not a file: {path_str}"
    return True, f"Found file: {path_str}"

def validate_directory(path_str: str, min_files: int = 0, expected_subdirs: List[str] = None) -> Tuple[bool, str]:
    """Check if a directory exists and optionally contains files/subdirs."""
    path = Path(path_str)
    if not path.exists():
        return False, f"Missing directory: {path_str}"
    if not path.is_dir():
        return False, f"Path is not a directory: {path_str}"

    if min_files > 0:
        file_count = len(list(path.glob("*")))
        if file_count < min_files:
            return False, f"Directory {path_str} has {file_count} files, expected >= {min_files}"

    if expected_subdirs:
        for subdir in expected_subdirs:
            sub_path = path / subdir
            if not sub_path.exists():
                return False, f"Missing expected subdirectory: {sub_path}"
            if not sub_path.is_dir():
                return False, f"Expected subdirectory is not a dir: {sub_path}"

    return True, f"Validated directory: {path_str}"

def run_quickstart_validation() -> Dict[str, Any]:
    """
    Execute the full quickstart validation pipeline.
    Checks for all artifacts produced by T007-T023.
    Returns a summary report.
    """
    results = {
        "pipeline_name": "llmXive-follow-up-extending-latent-spati",
        "task_id": "T024",
        "validation_start": time.strftime("%Y-%m-%d %H:%M:%S"),
        "checks": [],
        "summary": {
            "total_checks": 0,
            "passed": 0,
            "failed": 0,
            "critical_failures": [],
        },
    }

    # 1. Initialize Seeds and Config
    set_global_seed(42)
    ensure_directories()
    results["checks"].append(log_status("INFO", "Configuration and seeds initialized."))

    # 2. Validate Raw Data (T007, T016b)
    success, msg = validate_directory(EXPECTED_FILES["raw_dataset"], min_files=1)
    results["checks"].append(log_status("PASS" if success else "FAIL", msg))
    if not success:
        results["summary"]["critical_failures"].append("Raw dataset missing")
    results["summary"]["total_checks"] += 1
    if success:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1

    success, msg = validate_file_exists(EXPECTED_FILES["dense_baseline"])
    results["checks"].append(log_status("PASS" if success else "FAIL", msg))
    if not success:
        results["summary"]["critical_failures"].append("Dense baseline missing")
    results["summary"]["total_checks"] += 1
    if success:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1

    # 3. Validate Stratified Data (T008)
    success, msg = validate_file_exists(EXPECTED_FILES["stratified_metadata"])
    results["checks"].append(log_status("PASS" if success else "FAIL", msg))
    if not success:
        results["summary"]["critical_failures"].append("Stratified metadata missing")
    results["summary"]["total_checks"] += 1
    if success:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1

    success, msg = validate_directory(
        get_stratified_dir(),
        expected_subdirs=EXPECTED_STRATA_DIRS
    )
    results["checks"].append(log_status("PASS" if success else "FAIL", msg))
    if not success:
        results["summary"]["critical_failures"].append("Stratified subdirectories missing")
    results["summary"]["total_checks"] += 1
    if success:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1

    # 4. Validate Features (T009)
    success, msg = validate_directory(EXPECTED_FILES["feature_files"], min_files=1)
    results["checks"].append(log_status("PASS" if success else "FAIL", msg))
    if not success:
        results["summary"]["critical_failures"].append("Feature files missing")
    results["summary"]["total_checks"] += 1
    if success:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1

    # 5. Validate Warped Frames (T012)
    success, msg = validate_file_exists(EXPECTED_FILES["warped_frames"])
    results["checks"].append(log_status("PASS" if success else "FAIL", msg))
    if not success:
        results["summary"]["critical_failures"].append("Warped frames missing")
    results["summary"]["total_checks"] += 1
    if success:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1

    # 6. Validate Metrics and Analysis (T017, T018, T019, T020)
    success, msg = validate_file_exists(EXPECTED_FILES["metrics_json"])
    results["checks"].append(log_status("PASS" if success else "FAIL", msg))
    if not success:
        results["summary"]["critical_failures"].append("Metrics JSON missing")
    results["summary"]["total_checks"] += 1
    if success:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1

    success, msg = validate_file_exists(EXPECTED_FILES["anova_results"])
    results["checks"].append(log_status("PASS" if success else "FAIL", msg))
    if not success:
        results["summary"]["critical_failures"].append("ANOVA results missing")
    results["summary"]["total_checks"] += 1
    if success:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1

    success, msg = validate_file_exists(EXPECTED_FILES["sensitivity_results"])
    results["checks"].append(log_status("PASS" if success else "FAIL", msg))
    if not success:
        results["summary"]["critical_failures"].append("Sensitivity results missing")
    results["summary"]["total_checks"] += 1
    if success:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1

    success, msg = validate_file_exists(EXPECTED_FILES["hypothesis_report"])
    results["checks"].append(log_status("PASS" if success else "FAIL", msg))
    if not success:
        results["summary"]["critical_failures"].append("Hypothesis report missing")
    results["summary"]["total_checks"] += 1
    if success:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1

    success, msg = validate_file_exists(EXPECTED_FILES["memory_logs"])
    results["checks"].append(log_status("PASS" if success else "FAIL", msg))
    if not success:
        results["summary"]["critical_failures"].append("Memory logs missing")
    results["summary"]["total_checks"] += 1
    if success:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1

    # Final Summary
    results["validation_end"] = time.strftime("%Y-%m-%d %H:%M:%S")
    success_rate = results["summary"]["passed"] / results["summary"]["total_checks"] if results["summary"]["total_checks"] > 0 else 0.0
    results["summary"]["success_rate"] = success_rate
    results["summary"]["overall_status"] = "PASS" if len(results["summary"]["critical_failures"]) == 0 else "FAIL"

    print("\n" + "="*50)
    print(f"Quickstart Validation: {results['summary']['overall_status']}")
    print(f"Passed: {results['summary']['passed']}/{results['summary']['total_checks']}")
    if results["summary"]["critical_failures"]:
        print(f"Critical Failures: {', '.join(results['summary']['critical_failures'])}")
    print("="*50)

    # Save report
    report_path = get_results_dir() / "quickstart_validation_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Validation report saved to: {report_path}")

    return results

def main():
    """Entry point for the validation script."""
    try:
        run_quickstart_validation()
    except Exception as e:
        print(f"CRITICAL ERROR during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()