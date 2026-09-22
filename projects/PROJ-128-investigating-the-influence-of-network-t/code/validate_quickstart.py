import os
import sys
import json
import time
import traceback
from pathlib import Path

def log_step(step_name: str, success: bool, message: str = ""):
    status = "✓" if success else "✗"
    print(f"[{status}] {step_name}: {message}")
    return success

def validate_file_exists(file_path: str) -> bool:
    path = Path(file_path)
    if not path.exists():
        return False
    if path.stat().st_size == 0:
        return False
    return True

def validate_file_content(file_path: str, required_keys: list = None) -> bool:
    path = Path(file_path)
    if not path.exists():
        return False

    try:
        if path.suffix == '.json':
            with open(path, 'r') as f:
                data = json.load(f)
            if required_keys:
                for key in required_keys:
                    if key not in data:
                        return False
        elif path.suffix == '.csv':
            import pandas as pd
            df = pd.read_csv(path)
            if df.empty:
                return False
            if required_keys:
                for key in required_keys:
                    if key not in df.columns:
                        return False
        return True
    except Exception:
        return False

def run_validation_pipeline():
    print("=== Quickstart Validation Pipeline ===")
    start_time = time.time()
    all_passed = True

    # 1. Check Directory Structure
    required_dirs = ['data/raw', 'data/processed', 'data/logs', 'data/reports', 'code', 'tests']
    for d in required_dirs:
        if not validate_file_exists(d):
            all_passed = log_step(f"Directory Check: {d}", False, "Missing")
        else:
            log_step(f"Directory Check: {d}", True)

    # 2. Check Output Artifacts
    outputs = [
        ("data/processed/structural_metrics.csv", ['subject_id', 'global_efficiency', 'clustering_coefficient', 'modularity']),
        ("data/processed/dynamic_metrics.csv", ['subject_id', 'state_id', 'mean_dwell_time', 'num_visits']),
        ("data/processed/correlation_results.csv", ['metric_pair', 'r_value', 'p_value', 'fdr_corrected']),
        ("data/logs/exclusion_log.json", None),
        ("data/reports/final_report.json", None)
    ]

    for path, keys in outputs:
        if keys:
            passed = validate_file_content(path, keys)
            all_passed = log_step(f"Output Check: {path}", passed, "Missing or invalid content" if not passed else "Valid")
        else:
            passed = validate_file_exists(path)
            all_passed = log_step(f"Output Check: {path}", passed, "Missing" if not passed else "Exists")

    # 3. Check Documentation
    doc_path = "docs/quickstart.md"
    if validate_file_exists(doc_path):
        log_step("Documentation Check: docs/quickstart.md", True)
    else:
        all_passed = log_step("Documentation Check: docs/quickstart.md", False, "Missing")

    # 4. Check Config
    config_path = "code/config.py"
    if validate_file_exists(config_path):
        log_step("Config Check: code/config.py", True)
    else:
        all_passed = log_step("Config Check: code/config.py", False, "Missing")

    duration = time.time() - start_time
    print(f"\nValidation completed in {duration:.2f} seconds.")
    if all_passed:
        print("✓ All validation checks passed.")
        return 0
    else:
        print("✗ Some validation checks failed.")
        return 1

def main():
    sys.exit(run_validation_pipeline())

if __name__ == "__main__":
    main()