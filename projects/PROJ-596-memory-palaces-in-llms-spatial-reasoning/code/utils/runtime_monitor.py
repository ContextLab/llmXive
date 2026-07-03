import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Constants
MAX_RUNTIME_SECONDS = 5 * 60 * 60  # 5 hours in seconds
ARTIFACTS_DIR = Path("artifacts")
RESULTS_DIR = ARTIFACTS_DIR / "results"
RUNTIME_REPORT_PATH = RESULTS_DIR / "runtime_report.json"

def ensure_results_directory():
    """Ensure the results directory exists."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_run_summary() -> Optional[Dict[str, Any]]:
    """Load the run summary from artifacts/results/run_summary.json if it exists."""
    run_summary_path = RESULTS_DIR / "run_summary.json"
    if not run_summary_path.exists():
        return None
    try:
        with open(run_summary_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

def write_runtime_report(runtime_seconds: float, within_limit: bool):
    """Write the runtime report to artifacts/results/runtime_report.json."""
    ensure_results_directory()
    report = {
        "runtime_seconds": runtime_seconds,
        "within_limit": within_limit,
        "limit_seconds": MAX_RUNTIME_SECONDS
    }
    with open(RUNTIME_REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

def main():
    """
    Main entry point for T017c.
    Reads runtime_seconds from run_summary.json (produced by T016),
    verifies it is <= 5 hours, and writes runtime_report.json.
    """
    ensure_results_directory()
    summary = load_run_summary()
    
    if summary is None:
        print("Error: artifacts/results/run_summary.json not found. "
              "Ensure T016 has been executed successfully.")
        # Create a failure report to indicate the missing dependency
        write_runtime_report(0.0, False) 
        return

    runtime_seconds = summary.get("runtime_seconds")
    if runtime_seconds is None:
        print("Error: 'runtime_seconds' key missing in run_summary.json.")
        write_runtime_report(0.0, False)
        return

    within_limit = runtime_seconds <= MAX_RUNTIME_SECONDS
    
    write_runtime_report(runtime_seconds, within_limit)
    
    status = "PASSED" if within_limit else "FAILED"
    print(f"T017c Runtime Verification: {status}")
    print(f"  Total Runtime: {runtime_seconds:.2f} seconds")
    print(f"  Limit: {MAX_RUNTIME_SECONDS} seconds (5 hours)")
    print(f"  Report written to: {RUNTIME_REPORT_PATH}")

if __name__ == "__main__":
    main()