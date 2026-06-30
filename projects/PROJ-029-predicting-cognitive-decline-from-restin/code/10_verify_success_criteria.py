"""
Verify that the pipeline meets success criteria:
- ROC-AUC > 0.50
- p-value < 0.05
- Total runtime < 6 hours
"""
import os
import sys
import json
import time
from pathlib import Path
from utils.io import load_json, ensure_dir

def check_roc_auc(perf_data: dict, threshold: float = 0.50) -> bool:
    """Check if ROC-AUC meets the threshold."""
    auc = perf_data.get("mean_auc")
    if auc is None:
        return False
    return auc > threshold

def check_p_value(perm_data: dict, threshold: float = 0.05) -> bool:
    """Check if p-value meets the threshold."""
    p_val = perm_data.get("p_value")
    if p_val is None:
        return False
    return p_val < threshold

def check_runtime(runtime_data: dict, limit_seconds: int = 6 * 3600) -> bool:
    """Check if total runtime is within limit."""
    runtime = runtime_data.get("total_runtime_seconds")
    if runtime is None:
        return False
    return runtime < limit_seconds

def main():
    """Main entry point for success criteria verification."""
    project_root = Path(__file__).resolve().parent.parent
    
    perf_path = project_root / "data" / "processed" / "performance_report.json"
    perm_path = project_root / "data" / "processed" / "permutation_results.json"
    runtime_path = project_root / "data" / "artifacts" / "runtime_report.json"
    output_path = project_root / "data" / "artifacts" / "verification_status.json"

    ensure_dir(output_path.parent)

    # Load data
    try:
        perf_data = load_json(perf_path)
    except Exception:
        perf_data = {}

    try:
        perm_data = load_json(perm_path)
    except Exception:
        perm_data = {}

    try:
        runtime_data = load_json(runtime_path)
    except Exception:
        runtime_data = {}

    # Check criteria
    auc_ok = check_roc_auc(perf_data)
    p_ok = check_p_value(perm_data)
    time_ok = check_runtime(runtime_data)

    status = {
        "roc_auc_pass": auc_ok,
        "p_value_pass": p_ok,
        "runtime_pass": time_ok,
        "all_pass": auc_ok and p_ok and time_ok,
        "details": {
            "roc_auc": perf_data.get("mean_auc"),
            "p_value": perm_data.get("p_value"),
            "runtime_seconds": runtime_data.get("total_runtime_seconds")
        }
    }

    with open(output_path, "w") as f:
        json.dump(status, f, indent=2)

    print(f"Verification Status: {'PASS' if status['all_pass'] else 'FAIL'}")
    print(f"  ROC-AUC > 0.50: {'PASS' if auc_ok else 'FAIL'} ({perf_data.get('mean_auc')})")
    print(f"  p < 0.05: {'PASS' if p_ok else 'FAIL'} ({perm_data.get('p_value')})")
    print(f"  Runtime < 6h: {'PASS' if time_ok else 'FAIL'} ({runtime_data.get('total_runtime_seconds')}s)")

    sys.exit(0 if status['all_pass'] else 1)

if __name__ == "__main__":
    main()
