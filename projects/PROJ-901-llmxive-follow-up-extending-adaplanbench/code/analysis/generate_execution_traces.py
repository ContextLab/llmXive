"""
T026f: Merge and Validate Execution Logs.
Reads monolithic and dual-track logs, validates against schema, and produces execution_traces.csv.
"""
import os
import sys
import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

# Add project root to path for imports if run as script
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import Paths

# Schema definition from T026c
EXECUTION_LOG_SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {"type": "string"},
        "constraint_count": {"type": "integer"},
        "generated_plan": {"type": "string"},
        "violation_boolean": {"type": "boolean"},
        "violation_reason": {"type": ["string", "null"]},
        "violation_status": {"type": ["string", "null"]},
        "final_score": {"type": "number"}
    },
    "required": ["task_id", "constraint_count", "generated_plan", "violation_boolean", "violation_reason", "violation_status", "final_score"]
}

def load_json_logs(file_path: Path) -> List[Dict[str, Any]]:
    """Load JSON logs from a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Log file not found: {file_path}")
    
    logs = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in {file_path}: {e}")
    return logs

def validate_log_entry(entry: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate a log entry against the schema."""
    required = schema.get("required", [])
    for field in required:
        if field not in entry:
            raise ValueError(f"Missing required field '{field}' in log entry")
    
    # Type checks (basic)
    if not isinstance(entry.get("task_id"), str):
        raise ValueError(f"Invalid type for task_id")
    if not isinstance(entry.get("constraint_count"), int):
        raise ValueError(f"Invalid type for constraint_count")
    if not isinstance(entry.get("violation_boolean"), bool):
        raise ValueError(f"Invalid type for violation_boolean")
    if not isinstance(entry.get("final_score"), (int, float)):
        raise ValueError(f"Invalid type for final_score")
    
    return True

def merge_logs(monolithic_logs: List[Dict], dual_track_logs: List[Dict]) -> List[Dict[str, Any]]:
    """Merge logs from both architectures into a unified list."""
    merged = []
    
    for log in monolithic_logs:
        merged.append({
            "task_id": log["task_id"],
            "architecture": "monolithic",
            "constraint_count": log["constraint_count"],
            "violation_boolean": log["violation_boolean"],
            "violation_reason": log["violation_reason"],
            "violation_status": log["violation_status"],
            "final_score": log["final_score"]
        })
    
    for log in dual_track_logs:
        merged.append({
            "task_id": log["task_id"],
            "architecture": "dual_track",
            "constraint_count": log["constraint_count"],
            "violation_boolean": log["violation_boolean"],
            "violation_reason": log["violation_reason"],
            "violation_status": log["violation_status"],
            "final_score": log["final_score"]
        })
    
    return merged

def write_traces_csv(traces: List[Dict[str, Any]], output_path: Path):
    """Write merged traces to CSV."""
    fieldnames = [
        "task_id", 
        "architecture", 
        "constraint_count", 
        "violation_boolean", 
        "violation_reason", 
        "violation_status", 
        "final_score"
    ]
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(traces)

def run_merge_and_validate(
    monolithic_log_path: Path,
    dual_track_log_path: Path,
    output_path: Path
):
    """Main logic for T026f."""
    print(f"Loading monolithic logs from {monolithic_log_path}...")
    monolithic_logs = load_json_logs(monolithic_log_path)
    print(f"  Loaded {len(monolithic_logs)} entries.")
    
    print(f"Loading dual-track logs from {dual_track_log_path}...")
    dual_track_logs = load_json_logs(dual_track_log_path)
    print(f"  Loaded {len(dual_track_logs)} entries.")
    
    # Validate
    print("Validating log entries against schema...")
    for i, log in enumerate(monolithic_logs):
        validate_log_entry(log, EXECUTION_LOG_SCHEMA)
    for i, log in enumerate(dual_track_logs):
        validate_log_entry(log, EXECUTION_LOG_SCHEMA)
    print("  Validation passed.")
    
    # Merge
    print("Merging logs...")
    merged_traces = merge_logs(monolithic_logs, dual_track_logs)
    print(f"  Merged {len(merged_traces)} entries.")
    
    # Write
    print(f"Writing execution traces to {output_path}...")
    write_traces_csv(merged_traces, output_path)
    print(f"  Done. Total rows: {len(merged_traces)}")
    
    # Verification
    expected_count = len(monolithic_logs) + len(dual_track_logs)
    if len(merged_traces) != expected_count:
        raise RuntimeError(f"Row count mismatch: expected {expected_count}, got {len(merged_traces)}")
    
    print("Verification passed: Row count matches sum of inputs.")

def main():
    parser = argparse.ArgumentParser(description="Merge and validate execution logs (T026f)")
    parser.add_argument("--monolithic-log", type=str, default=str(Paths.DATA_PROCESSED / "monolithic_logs.json"),
                        help="Path to monolithic logs JSONL")
    parser.add_argument("--dual-track-log", type=str, default=str(Paths.DATA_PROCESSED / "dual_track_logs.json"),
                        help="Path to dual-track logs JSONL")
    parser.add_argument("--output", type=str, default=str(Paths.DATA_PROCESSED / "execution_traces.csv"),
                        help="Path for output CSV")
    
    args = parser.parse_args()
    
    monolithic_path = Path(args.monolithic_log)
    dual_track_path = Path(args.dual_track_log)
    output_path = Path(args.output)
    
    try:
        run_merge_and_validate(monolithic_path, dual_track_path, output_path)
    except Exception as e:
        print(f"Error during merge and validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()