import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

def load_run_summary(path: str = "artifacts/results/run_summary.json") -> Optional[Dict[str, Any]]:
    """Load the run summary JSON file."""
    p = Path(path)
    if not p.exists():
        return None
    with open(p, "r") as f:
        return json.load(f)

def verify_runtime(runtime_seconds: float, limit_seconds: float = 18000) -> bool:
    """Verify if the runtime is within the limit."""
    return runtime_seconds <= limit_seconds

def write_runtime_report(runtime_seconds: float, limit_seconds: float = 18000, output_path: str = "artifacts/results/runtime_report.json"):
    """Write a runtime report to disk."""
    within_limit = verify_runtime(runtime_seconds, limit_seconds)
    report = {
        "runtime_seconds": runtime_seconds,
        "limit_seconds": limit_seconds,
        "within_limit": within_limit
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    return report

def main():
    """Main entry point for runtime verification."""
    summary = load_run_summary()
    if not summary:
        print("Error: run_summary.json not found.")
        sys.exit(1)
    
    runtime = summary.get("runtime_seconds", 0)
    report = write_runtime_report(runtime)
    print(f"Runtime Report: {report}")
    
    if not report["within_limit"]:
        print("Warning: Runtime exceeded limit.")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
