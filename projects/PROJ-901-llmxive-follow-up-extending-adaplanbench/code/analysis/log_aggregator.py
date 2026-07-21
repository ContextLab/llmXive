"""
Module to aggregate execution logs from monolithic and dual-track agents.
This script merges the JSON logs from both architectures into a single CSV
file for statistical analysis, adhering to the schema defined in
contracts/execution-log.schema.yaml (conceptually) and the task specification.

Output Schema:
  - task_id: str
  - architecture: str ('monolithic' or 'dual_track')
  - constraint_count: int
  - violation_boolean: bool
  - violation_reason: str (or null/empty)
  - final_score: float
"""
import os
import sys
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Paths, get_paths

def load_execution_logs(log_path: Path) -> List[Dict[str, Any]]:
    """Load execution logs from a JSON file."""
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    with open(log_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle different JSON structures (list of logs or dict with 'logs' key)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'logs' in data:
        return data['logs']
    else:
        # If it's a single object, wrap it
        return [data] if not isinstance(data, list) else data

def aggregate_logs(monolithic_path: Path, dual_track_path: Path) -> List[Dict[str, Any]]:
    """
    Aggregate logs from monolithic and dual-track runs.
    Normalizes the fields to the required output schema.
    """
    aggregated = []

    # Process Monolithic Logs
    if monolithic_path.exists():
        monolithic_logs = load_execution_logs(monolithic_path)
        for log in monolithic_logs:
            # Map fields from monolithic log to output schema
            entry = {
                'task_id': log.get('task_id', ''),
                'architecture': 'monolithic',
                'constraint_count': int(log.get('constraint_count', 0)),
                'violation_boolean': bool(log.get('violation_boolean', False)),
                'violation_reason': log.get('violation_reason', None) or log.get('violation_reason', ''),
                'final_score': float(log.get('final_score', 0.0))
            }
            aggregated.append(entry)

    # Process Dual-Track Logs
    if dual_track_path.exists():
        dual_track_logs = load_execution_logs(dual_track_path)
        for log in dual_track_logs:
            # Map fields from dual-track log to output schema
            entry = {
                'task_id': log.get('task_id', ''),
                'architecture': 'dual_track',
                'constraint_count': int(log.get('constraint_count', 0)),
                'violation_boolean': bool(log.get('violation_boolean', False)),
                'violation_reason': log.get('violation_reason', None) or log.get('violation_reason', ''),
                'final_score': float(log.get('final_score', 0.0))
            }
            aggregated.append(entry)

    return aggregated

def write_traces_csv(logs: List[Dict[str, Any]], output_path: Path):
    """Write aggregated logs to a CSV file for analysis."""
    if not logs:
        # Write empty file with headers if no logs found
        fieldnames = ['task_id', 'architecture', 'constraint_count', 'violation_boolean', 'violation_reason', 'final_score']
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        return

    fieldnames = ['task_id', 'architecture', 'constraint_count', 'violation_boolean', 'violation_reason', 'final_score']
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for log in logs:
            # Ensure types are correct for CSV writing
            row = {
                'task_id': str(log['task_id']),
                'architecture': str(log['architecture']),
                'constraint_count': int(log['constraint_count']),
                'violation_boolean': str(log['violation_boolean']).lower(), # CSV standard for bool often lower, but keeping raw bool for python reading if needed, or string 'True'/'False'
                'violation_reason': str(log['violation_reason']) if log['violation_reason'] else '',
                'final_score': float(log['final_score'])
            }
            # Fix boolean representation for standard CSV reading (True/False strings)
            row['violation_boolean'] = 'True' if log['violation_boolean'] else 'False'
            writer.writerow(row)

def main():
    """Main entry point for log aggregation."""
    paths = get_paths()
    
    monolithic_path = paths.DATA_PROCESSED / "monolithic_logs.json"
    dual_track_path = paths.DATA_PROCESSED / "dual_track_logs.json"
    output_path = paths.DATA_PROCESSED / "execution_traces.csv"

    print(f"Aggregating logs from {monolithic_path} and {dual_track_path}")
    
    try:
        # Check if input files exist before proceeding
        if not monolithic_path.exists() and not dual_track_path.exists():
            print(f"Error: Neither monolithic nor dual-track log files found.")
            print(f"Expected: {monolithic_path}, {dual_track_path}")
            sys.exit(1)

        logs = aggregate_logs(monolithic_path, dual_track_path)
        print(f"Aggregated {len(logs)} log entries.")
        
        if len(logs) == 0:
            print("Warning: No log entries found to aggregate.")
        
        write_traces_csv(logs, output_path)
        print(f"Execution traces written to {output_path}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during aggregation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()