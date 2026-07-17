"""
Runtime monitoring utilities for the Memory Palaces project.
Ensures that execution times are tracked and reported correctly.
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

def ensure_results_directory():
    """Ensure the results directory exists."""
    results_dir = Path("artifacts/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir

def load_run_summary() -> Optional[Dict[str, Any]]:
    """Load the run summary if it exists."""
    summary_path = Path("artifacts/results/run_summary.json")
    if summary_path.exists():
        with open(summary_path, "r") as f:
            return json.load(f)
    return None

def write_runtime_report(runtime_seconds: float, within_limit: bool = True):
    """
    Write the runtime report to artifacts/results/runtime_report.json.
    
    Args:
        runtime_seconds: Total execution time in seconds.
        within_limit: Boolean indicating if the runtime was within the 5-hour limit.
    """
    ensure_results_directory()
    report_path = Path("artifacts/results/runtime_report.json")
    
    report_data = {
        "runtime_seconds": runtime_seconds,
        "within_limit": within_limit,
        "limit_seconds": 18000
    }
    
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)
    
    print(f"Runtime report written to {report_path}")

def main():
    """
    CLI entry point for runtime monitoring tasks.
    Currently used to verify existing reports or generate placeholders if needed.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Runtime Monitor Utilities")
    parser.add_argument("--check", action="store_true", help="Check if run_summary.json exists")
    args = parser.parse_args()

    if args.check:
        summary = load_run_summary()
        if summary:
            print(f"Run summary found: {summary}")
        else:
            print("No run summary found.")
            return 1
    return 0

if __name__ == "__main__":
    exit(main())