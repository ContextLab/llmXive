"""
Module to generate execution traces CSV from agent execution logs.
This script consolidates monolithic and dual-track logs into a unified format
for statistical analysis.
"""
import os
import sys
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Paths, get_dataset_config, get_analysis_config

def load_execution_logs(log_path: Path) -> List[Dict[str, Any]]:
    """Load execution logs from a JSON file."""
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    with open(log_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both single list and dict with 'logs' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'logs' in data:
        return data['logs']
    else:
        # Assume it's a dict containing a single log entry or list of entries
        return [data] if not isinstance(data, list) else data

def load_filtered_tasks_map(tasks_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load filtered tasks and create a mapping by task_id."""
    if not tasks_path.exists():
        raise FileNotFoundError(f"Tasks file not found: {tasks_path}")

    tasks_map = {}
    with open(tasks_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_id = row.get('task_id')
            if task_id:
                tasks_map[task_id] = row
    return tasks_map

def extract_trace_data(log_entry: Dict[str, Any], tasks_map: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Extract relevant fields from a log entry for the execution trace."""
    task_id = log_entry.get('task_id')
    if not task_id or task_id not in tasks_map:
        return None

    task_meta = tasks_map[task_id]
    
    # Determine architecture type
    source_file = log_entry.get('source', '').lower()
    if 'dual' in source_file:
        architecture = 'dual_track'
    elif 'monolithic' in source_file:
        architecture = 'monolithic'
    else:
        architecture = log_entry.get('architecture', 'unknown')

    # Extract constraint count from metadata
    constraint_count = int(task_meta.get('constraint_count', 0))

    # Determine violation status
    violations = log_entry.get('violations', [])
    has_violation = len(violations) > 0

    # Extract final score (success/failure or numeric score)
    # Assuming log structure has 'success' or 'final_score'
    final_score = log_entry.get('final_score', log_entry.get('success', False))
    if isinstance(final_score, bool):
        final_score = 1.0 if final_score else 0.0
    
    return {
        'task_id': task_id,
        'architecture': architecture,
        'constraint_count': constraint_count,
        'has_violation': has_violation,
        'final_score': final_score,
        'raw_log': json.dumps(log_entry)  # Store full log for debugging
    }

def write_traces_csv(traces: List[Dict[str, Any]], output_path: Path):
    """Write execution traces to a CSV file."""
    if not traces:
        print("Warning: No traces to write.")
        # Create empty file with headers
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['task_id', 'architecture', 'constraint_count', 'has_violation', 'final_score', 'raw_log'])
            writer.writeheader()
        return

    fieldnames = ['task_id', 'architecture', 'constraint_count', 'has_violation', 'final_score', 'raw_log']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(traces)

def main():
    """Main entry point for generating execution traces."""
    paths = get_paths()
    dataset_config = get_dataset_config()
    analysis_config = get_analysis_config()

    # Define input and output paths
    tasks_path = paths.DATA_PROCESSED / "filtered_tasks.csv"
    monolithic_logs_path = paths.DATA_PROCESSED / "monolithic_logs.json"
    dual_track_logs_path = paths.DATA_PROCESSED / "dual_track_logs.json"
    output_path = paths.DATA_PROCESSED / "execution_traces.csv"

    print(f"Loading filtered tasks from: {tasks_path}")
    tasks_map = load_filtered_tasks_map(tasks_path)

    all_traces = []

    # Process monolithic logs
    if monolithic_logs_path.exists():
        print(f"Processing monolithic logs from: {monolithic_logs_path}")
        monolithic_logs = load_execution_logs(monolithic_logs_path)
        for log in monolithic_logs:
            trace = extract_trace_data(log, tasks_map)
            if trace:
                trace['source_file'] = 'monolithic_logs.json'
                all_traces.append(trace)
    else:
        print(f"Warning: Monolithic logs not found at {monolithic_logs_path}")

    # Process dual-track logs
    if dual_track_logs_path.exists():
        print(f"Processing dual-track logs from: {dual_track_logs_path}")
        dual_track_logs = load_execution_logs(dual_track_logs_path)
        for log in dual_track_logs:
            trace = extract_trace_data(log, tasks_map)
            if trace:
                trace['source_file'] = 'dual_track_logs.json'
                all_traces.append(trace)
    else:
        print(f"Warning: Dual-track logs not found at {dual_track_logs_path}")

    # Write output
    print(f"Writing {len(all_traces)} traces to: {output_path}")
    write_traces_csv(all_traces, output_path)
    print("Execution traces generation complete.")

if __name__ == "__main__":
    main()
