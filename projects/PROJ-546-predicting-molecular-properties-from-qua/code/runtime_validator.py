"""
T033b: Validate runtime logs against resource constraints.

Parses logs/dft_execution.log (JSONL) to extract duration and peak_memory_mb,
verifies total runtime <= 6 hours and peak memory <= 7 GB,
and writes validation results to reports/runtime_validation.json.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Constants from Constitution Principle VII (Resource-Bound Execution)
MAX_TOTAL_RUNTIME_HOURS = 6
MAX_PEAK_MEMORY_GB = 7

# Derived limits
MAX_TOTAL_RUNTIME_SECONDS = MAX_TOTAL_RUNTIME_HOURS * 3600
MAX_PEAK_MEMORY_MB = MAX_PEAK_MEMORY_GB * 1024

LOG_FILE_PATH = "logs/dft_execution.log"
OUTPUT_FILE_PATH = "reports/runtime_validation.json"


def load_log_entries(log_path: str) -> List[Dict[str, Any]]:
    """Load JSON lines from the log file."""
    entries = []
    path = Path(log_path)
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping malformed JSON at line {line_num}: {e}")
    return entries


def validate_resources(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate runtime and memory constraints.
    Returns a validation report dictionary.
    """
    total_runtime_seconds = 0.0
    max_peak_memory_mb = 0.0
    entries_count = len(entries)
    failures = []

    for i, entry in enumerate(entries):
        duration = entry.get("duration")
        peak_memory_mb = entry.get("peak_memory_mb")

        if duration is None:
            failures.append({
                "index": i,
                "molecule_id": entry.get("molecule_id", "unknown"),
                "error": "Missing 'duration' field"
            })
        else:
            total_runtime_seconds += float(duration)

        if peak_memory_mb is None:
            failures.append({
                "index": i,
                "molecule_id": entry.get("molecule_id", "unknown"),
                "error": "Missing 'peak_memory_mb' field"
            })
        else:
            current_peak = float(peak_memory_mb)
            if current_peak > max_peak_memory_mb:
                max_peak_memory_mb = current_peak

    total_runtime_hours = total_runtime_seconds / 3600.0
    runtime_ok = total_runtime_seconds <= MAX_TOTAL_RUNTIME_SECONDS
    memory_ok = max_peak_memory_mb <= MAX_PEAK_MEMORY_MB
    overall_pass = runtime_ok and memory_ok and (len(failures) == 0)

    report = {
        "validation_status": "passed" if overall_pass else "failed",
        "constraints": {
            "max_total_runtime_hours": MAX_TOTAL_RUNTIME_HOURS,
            "max_peak_memory_gb": MAX_PEAK_MEMORY_GB
        },
        "results": {
            "total_runtime_seconds": round(total_runtime_seconds, 2),
            "total_runtime_hours": round(total_runtime_hours, 4),
            "peak_memory_mb": round(max_peak_memory_mb, 2),
            "peak_memory_gb": round(max_peak_memory_mb / 1024, 4),
            "entries_processed": entries_count,
            "runtime_constraint_met": runtime_ok,
            "memory_constraint_met": memory_ok
        },
        "failures": failures
    }

    return report


def write_report(report: Dict[str, Any], output_path: str) -> None:
    """Write the validation report to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Validation report written to: {output_path}")


def main() -> int:
    """Main entry point for the validation script."""
    # Ensure we are running from the project root
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    log_path = project_root / LOG_FILE_PATH
    output_path = project_root / OUTPUT_FILE_PATH

    if not log_path.exists():
        print(f"Error: Log file not found at {log_path}")
        print("Did you run the pipeline (T033a) to generate logs?")
        return 1

    try:
        entries = load_log_entries(str(log_path))
        if not entries:
            print("Warning: Log file is empty. No entries to validate.")
            report = {
                "validation_status": "failed",
                "reason": "No log entries found",
                "entries_processed": 0
            }
        else:
            report = validate_resources(entries)

        write_report(report, str(output_path))

        if report["validation_status"] == "passed":
            print("Validation PASSED: Resource constraints met.")
            return 0
        else:
            print("Validation FAILED: Resource constraints not met or errors found.")
            return 1

    except Exception as e:
        print(f"Error during validation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())