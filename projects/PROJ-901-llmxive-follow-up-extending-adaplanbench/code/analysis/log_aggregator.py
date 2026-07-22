"""
Log Aggregator for llmXive - AdaPlanBench Extension.

This module aggregates execution logs from monolithic and dual-track agents
into a single CSV file for downstream statistical analysis.

Output Schema (execution_traces.csv):
  - task_id: string
  - architecture: string ('monolithic' or 'dual_track')
  - constraint_count: integer
  - violation_boolean: boolean
  - violation_reason: string (or null/empty)
  - final_score: float
"""
import os
import sys
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import config to get paths
# Using relative import pattern consistent with project structure
try:
    from config import get_paths
except ImportError:
    # Fallback for direct execution in code/ directory
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_paths


def load_execution_logs(log_path: Path) -> List[Dict[str, Any]]:
    """
    Load execution logs from a JSON file.

    Args:
        log_path: Path to the JSON log file.

    Returns:
        List of log entries.

    Raises:
        FileNotFoundError: If the log file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    with open(log_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle case where JSON is a dict with a key (e.g. {"logs": [...]})
    if isinstance(data, dict):
        # Common keys for log containers
        for key in ['logs', 'results', 'data', 'entries']:
            if key in data and isinstance(data[key], list):
                return data[key]
        # If it's a dict but not wrapped, assume it's a single entry or list of dicts
        if 'tasks' in data:
            return data['tasks']
        # Fallback: treat values as logs if they are lists
        for value in data.values():
            if isinstance(value, list):
                return value
        # If still nothing, return empty or raise
        if not data:
            return []
        # If it's a single object, wrap it
        return [data]

    if isinstance(data, list):
        return data

    raise ValueError(f"Unexpected log format in {log_path}: expected list or dict with list values")


def aggregate_logs(
    monolithic_path: Path,
    dual_track_path: Path
) -> List[Dict[str, Any]]:
    """
    Merge monolithic and dual-track logs into a unified list of traces.

    Args:
        monolithic_path: Path to monolithic_logs.json
        dual_track_path: Path to dual_track_logs.json

    Returns:
        List of aggregated trace dictionaries.
    """
    traces = []

    # Load Monolithic Logs
    monolithic_logs = load_execution_logs(monolithic_path)
    for entry in monolithic_logs:
        trace = {
            'task_id': entry.get('task_id', 'unknown'),
            'architecture': 'monolithic',
            'constraint_count': entry.get('constraint_count', 0),
            'violation_boolean': bool(entry.get('violation_boolean', False)),
            'violation_reason': entry.get('violation_reason') or '',
            'final_score': float(entry.get('final_score', 0.0))
        }
        traces.append(trace)

    # Load Dual Track Logs
    dual_track_logs = load_execution_logs(dual_track_path)
    for entry in dual_track_logs:
        trace = {
            'task_id': entry.get('task_id', 'unknown'),
            'architecture': 'dual_track',
            'constraint_count': entry.get('constraint_count', 0),
            'violation_boolean': bool(entry.get('violation_boolean', False)),
            'violation_reason': entry.get('violation_reason') or '',
            'final_score': float(entry.get('final_score', 0.0))
        }
        traces.append(trace)

    return traces


def write_traces_csv(traces: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write aggregated traces to a CSV file.

    Args:
        traces: List of trace dictionaries.
        output_path: Path to the output CSV file.
    """
    if not traces:
        # Write empty file with headers if no data
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'task_id', 'architecture', 'constraint_count',
                'violation_boolean', 'violation_reason', 'final_score'
            ])
            writer.writeheader()
        return

    fieldnames = [
        'task_id', 'architecture', 'constraint_count',
        'violation_boolean', 'violation_reason', 'final_score'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(traces)


def main() -> None:
    """
    Main entry point for the log aggregator script.

    Usage:
        python code/analysis/log_aggregator.py
    """
    paths = get_paths()

    # Define input and output paths based on project structure
    # These paths must match the paths generated by T026a and T026b
    monolithic_log_path = paths.DATA_PROCESSED / "monolithic_logs.json"
    dual_track_log_path = paths.DATA_PROCESSED / "dual_track_logs.json"
    output_csv_path = paths.DATA_PROCESSED / "execution_traces.csv"

    print(f"Loading monolithic logs from: {monolithic_log_path}")
    print(f"Loading dual-track logs from: {dual_track_log_path}")

    try:
        traces = aggregate_logs(monolithic_log_path, dual_track_log_path)
        print(f"Aggregated {len(traces)} execution traces.")

        write_traces_csv(traces, output_csv_path)
        print(f"Successfully wrote execution traces to: {output_csv_path}")

    except FileNotFoundError as e:
        print(f"Error: Input file missing - {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during aggregation: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()