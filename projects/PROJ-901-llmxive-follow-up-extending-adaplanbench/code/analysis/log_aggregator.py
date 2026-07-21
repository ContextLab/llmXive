"""
Module to aggregate execution logs from monolithic and dual-track agents.
This is an alternative implementation for generating execution traces,
ensuring compatibility with the pipeline.
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

    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'logs' in data:
        return data['logs']
    else:
        return [data] if not isinstance(data, list) else data

def aggregate_logs(monolithic_path: Path, dual_track_path: Path) -> List[Dict[str, Any]]:
    """
    Aggregate logs from monolithic and dual-track runs.
    Returns a list of aggregated log entries.
    """
    aggregated = []

    if monolithic_path.exists():
        monolithic_logs = load_execution_logs(monolithic_path)
        for log in monolithic_logs:
            log['agent_type'] = 'monolithic'
            aggregated.append(log)

    if dual_track_path.exists():
        dual_track_logs = load_execution_logs(dual_track_path)
        for log in dual_track_logs:
            log['agent_type'] = 'dual_track'
            aggregated.append(log)

    return aggregated

def write_traces_csv(logs: List[Dict[str, Any]], output_path: Path):
    """Write aggregated logs to a CSV file for analysis."""
    if not logs:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['task_id', 'agent_type', 'success', 'violations'])
            writer.writeheader()
        return

    # Flatten the data for CSV
    rows = []
    for log in logs:
        row = {
            'task_id': log.get('task_id', ''),
            'agent_type': log.get('agent_type', 'unknown'),
            'success': log.get('success', False),
            'violations': json.dumps(log.get('violations', [])),
            'constraint_count': log.get('constraint_count', 0),
            'final_score': log.get('final_score', 0.0)
        }
        rows.append(row)

    fieldnames = ['task_id', 'agent_type', 'success', 'violations', 'constraint_count', 'final_score']
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main():
    """Main entry point for log aggregation."""
    paths = get_paths()
    
    monolithic_path = paths.DATA_PROCESSED / "monolithic_logs.json"
    dual_track_path = paths.DATA_PROCESSED / "dual_track_logs.json"
    output_path = paths.DATA_PROCESSED / "execution_traces.csv"

    print(f"Aggregating logs from {monolithic_path} and {dual_track_path}")
    
    try:
        logs = aggregate_logs(monolithic_path, dual_track_path)
        print(f"Aggregated {len(logs)} log entries.")
        write_traces_csv(logs, output_path)
        print(f"Execution traces written to {output_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
