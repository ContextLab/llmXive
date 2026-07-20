"""
Generate execution_traces.csv from agent execution logs.

This script reads the execution logs produced by the dual-track and monolithic
agents (from T023), extracts the relevant fields (architecture type, constraint
count, violation boolean, final score), and writes them to a CSV file.
"""
import os
import sys
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import Paths


def load_execution_logs(log_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all JSON execution logs from the specified directory.

    Args:
        log_dir: Path to directory containing execution log JSON files.

    Returns:
        List of parsed log dictionaries.
    """
    logs = []
    if not log_dir.exists():
        raise FileNotFoundError(f"Execution log directory not found: {log_dir}")

    for log_file in sorted(log_dir.glob("*.json")):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
                logs.append(log_data)
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse {log_file}: {e}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"Warning: Failed to read {log_file}: {e}", file=sys.stderr)
            continue

    if not logs:
        raise ValueError(f"No valid execution logs found in {log_dir}")

    return logs


def extract_trace_data(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract trace data from execution logs.

    Expected log structure (based on agent implementation):
    {
        "task_id": "...",
        "architecture": "dual_track" | "monolithic",
        "constraint_count": int,
        "violations": [
            {
                "type": "violation_type",
                "description": "...",
                "corrected": bool,
                ...
            }
        ],
        "final_score": float,
        ...
    }

    Args:
        logs: List of execution log dictionaries.

    Returns:
        List of trace dictionaries with required fields.
    """
    traces = []

    for log in logs:
        task_id = log.get("task_id", "unknown")
        architecture = log.get("architecture", "unknown")
        constraint_count = log.get("constraint_count", 0)
        final_score = log.get("final_score", 0.0)

        # Determine if any violation occurred
        violations = log.get("violations", [])
        has_violation = len(violations) > 0

        # Extract violation type if present (for debugging, not required in CSV)
        violation_types = [v.get("type", "unknown") for v in violations]

        trace = {
            "task_id": task_id,
            "architecture": architecture,
            "constraint_count": constraint_count,
            "has_violation": has_violation,
            "final_score": final_score,
            "violation_types": ",".join(violation_types) if violation_types else ""
        }
        traces.append(trace)

    return traces


def load_filtered_tasks_map(filtered_csv_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Load filtered tasks CSV to create a task_id -> task_data map.
    This is used to verify constraint counts if needed.

    Args:
        filtered_csv_path: Path to filtered_tasks.csv.

    Returns:
        Dictionary mapping task_id to task data.
    """
    task_map = {}
    if not filtered_csv_path.exists():
        print(f"Warning: Filtered tasks file not found: {filtered_csv_path}", file=sys.stderr)
        return task_map

    try:
        import pandas as pd
        df = pd.read_csv(filtered_csv_path)
        for _, row in df.iterrows():
            task_id = str(row.get("task_id", ""))
            if task_id:
                task_map[task_id] = row.to_dict()
    except Exception as e:
        print(f"Warning: Failed to load filtered tasks: {e}", file=sys.stderr)

    return task_map


def write_traces_csv(traces: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write execution traces to a CSV file.

    Args:
        traces: List of trace dictionaries.
        output_path: Path to output CSV file.
    """
    if not traces:
        raise ValueError("No traces to write")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["task_id", "architecture", "constraint_count", "has_violation", "final_score", "violation_types"]

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for trace in traces:
            writer.writerow(trace)

    print(f"Wrote {len(traces)} traces to {output_path}")


def main() -> None:
    """Main entry point for generating execution traces."""
    paths = Paths()

    # Define paths
    log_dir = paths.data_processed / "agent_logs"
    output_path = paths.data_processed / "execution_traces.csv"

    print(f"Loading execution logs from: {log_dir}")
    logs = load_execution_logs(log_dir)
    print(f"Loaded {len(logs)} execution logs")

    print("Extracting trace data...")
    traces = extract_trace_data(logs)
    print(f"Extracted {len(traces)} traces")

    print(f"Writing execution traces to: {output_path}")
    write_traces_csv(traces, output_path)

    print("Execution traces generation complete.")


if __name__ == "__main__":
    main()
