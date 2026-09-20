"""
Quickstart Validator (T028)

Validates the end-to-end pipeline execution.
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Local imports
from config import get_results_dir, get_raw_dir, get_features_dir, ensure_directories
from utils.seeds import set_global_seed

# Required files
REQUIRED_FILES = [
    ("data/raw/dense_baseline_frames.npy", get_raw_dir),
    ("data/results/sparse_warped_frames.npy", get_results_dir),
    ("data/results/metrics.json", get_results_dir),
    ("data/results/anova_results.json", get_results_dir),
    ("data/results/sensitivity_analysis.json", get_results_dir),
]

def log_status(status: str, message: str) -> None:
    """Log status message."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {status}: {message}")

def validate_file_exists(file_path: Path) -> Tuple[bool, str]:
    """Check if a file exists."""
    if file_path.exists():
        return True, "OK"
    else:
        return False, f"Missing: {file_path}"

def validate_directory(dir_path: Path) -> Tuple[bool, str]:
    """Check if a directory exists."""
    if dir_path.exists() and dir_path.is_dir():
        return True, "OK"
    else:
        return False, f"Missing or not a directory: {dir_path}"

def run_quickstart_validation() -> Dict[str, Any]:
    """Run validation checks."""
    results = {
        "timestamp": str(time.time()),
        "checks": []
    }
    
    # Check directories
    dirs = [get_raw_dir(), get_results_dir(), get_features_dir()]
    for d in dirs:
        ok, msg = validate_directory(d)
        results["checks"].append({
            "type": "directory",
            "path": str(d),
            "status": "PASS" if ok else "FAIL",
            "message": msg
        })
    
    # Check files
    for rel_path, getter in REQUIRED_FILES:
        file_path = getter() / Path(rel_path).relative_to("data")
        ok, msg = validate_file_exists(file_path)
        results["checks"].append({
            "type": "file",
            "path": str(file_path),
            "status": "PASS" if ok else "FAIL",
            "message": msg
        })
    
    # Overall status
    failed = [c for c in results["checks"] if c["status"] == "FAIL"]
    results["overall_status"] = "PASS" if not failed else "FAIL"
    results["failed_checks"] = len(failed)
    
    return results

def main():
    """Main entry point for validation."""
    set_global_seed(42)
    
    log_status("INFO", "Starting quickstart validation...")
    
    results = run_quickstart_validation()
    
    # Save results
    results_dir = get_results_dir()
    ensure_directories(results_dir)
    output_path = results_dir / "quickstart_validation.json"
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    log_status("INFO", f"Validation complete. Status: {results['overall_status']}")
    
    # Print summary
    for check in results["checks"]:
        status_icon = "✓" if check["status"] == "PASS" else "✗"
        print(f"  {status_icon} {check['type']}: {check['path']} - {check['message']}")
    
    if results["overall_status"] == "FAIL":
        sys.exit(1)

if __name__ == "__main__":
    main()
