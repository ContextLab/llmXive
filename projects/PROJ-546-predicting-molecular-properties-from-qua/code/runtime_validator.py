import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

LOG_FILE = Path("logs/dft_execution.log")
REPORT_FILE = Path("reports/runtime_validation.json")

MAX_RUNTIME_HOURS = 6
MAX_MEMORY_GB = 7

def load_log_entries(log_path: Path) -> List[Dict[str, Any]]:
    if not log_path.exists():
        return []
    
    entries = []
    with open(log_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError:
                continue
    return entries

def validate_resources(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not entries:
        return {
            "status": "SKIPPED",
            "reason": "Missing execution logs",
            "total_runtime_hours": 0,
            "peak_memory_gb": 0,
            "constraint_met": False
        }

    total_duration_seconds = 0.0
    peak_memory_mb = 0.0

    for entry in entries:
        duration = entry.get("duration", 0.0)
        memory_mb = entry.get("peak_memory_mb", 0.0)
        
        total_duration_seconds += duration
        if memory_mb > peak_memory_mb:
            peak_memory_mb = memory_mb

    total_runtime_hours = total_duration_seconds / 3600.0
    peak_memory_gb = peak_memory_mb / 1024.0

    runtime_ok = total_runtime_hours <= MAX_RUNTIME_HOURS
    memory_ok = peak_memory_gb <= MAX_MEMORY_GB
    constraint_met = runtime_ok and memory_ok

    return {
        "status": "PASSED" if constraint_met else "FAILED",
        "total_runtime_hours": round(total_runtime_hours, 4),
        "peak_memory_gb": round(peak_memory_gb, 4),
        "constraint_met": constraint_met,
        "details": {
            "max_runtime_hours": MAX_RUNTIME_HOURS,
            "max_memory_gb": MAX_MEMORY_GB,
            "runtime_ok": runtime_ok,
            "memory_ok": memory_ok
        }
    }

def write_report(report_data: Dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)

def main() -> int:
    if not LOG_FILE.exists():
        report = {
            "status": "SKIPPED",
            "reason": "Missing execution logs",
            "total_runtime_hours": 0,
            "peak_memory_gb": 0,
            "constraint_met": False
        }
        write_report(report, REPORT_FILE)
        print(f"SKIPPED: Missing execution logs at {LOG_FILE}")
        return 0

    entries = load_log_entries(LOG_FILE)
    if not entries:
        report = {
            "status": "SKIPPED",
            "reason": "Missing execution logs",
            "total_runtime_hours": 0,
            "peak_memory_gb": 0,
            "constraint_met": False
        }
        write_report(report, REPORT_FILE)
        print(f"SKIPPED: Execution log at {LOG_FILE} is empty or invalid JSON")
        return 0

    result = validate_resources(entries)
    write_report(result, REPORT_FILE)
    
    status_msg = "PASSED" if result["constraint_met"] else "FAILED"
    print(f"Validation {status_msg}: Total runtime {result['total_runtime_hours']:.2f}h, Peak memory {result['peak_memory_gb']:.2f}GB")
    return 0 if result["constraint_met"] else 1

if __name__ == "__main__":
    sys.exit(main())