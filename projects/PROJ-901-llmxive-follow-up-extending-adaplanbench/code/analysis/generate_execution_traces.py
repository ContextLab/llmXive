"""
Generate execution_traces.csv from monolithic and dual-track logs.
This script fulfills T024 by aggregating logs into the required CSV format.
"""
import os
import sys
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import get_paths

def load_execution_logs(file_path: Path) -> List[Dict[str, Any]]:
    """Load execution logs from a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Log file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    if not isinstance(logs, list):
        # If it's a single object, wrap it in a list
        logs = [logs]
        
    return logs

def load_filtered_tasks_map(csv_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Load filtered tasks and create a map of task_id -> task data.
    Needed to retrieve constraint_count for each task.
    """
    task_map = {}
    if not csv_path.exists():
        raise FileNotFoundError(f"Filtered tasks file not found: {csv_path}")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_id = row.get('task_id')
            if task_id:
                # Ensure constraint_count is an integer
                try:
                    constraint_count = int(row.get('constraint_count', 0))
                except (ValueError, TypeError):
                    constraint_count = 0
                task_map[task_id] = {
                    'constraint_count': constraint_count,
                    'raw_prompt': row.get('raw_prompt', ''),
                    'progressive_constraints': row.get('progressive_constraints', '[]')
                }
    return task_map

def extract_trace_data(log: Dict[str, Any], task_map: Dict[str, Dict[str, Any]], architecture: str) -> Dict[str, Any]:
    """
    Extract trace data from a single log entry.
    Ensures all required fields are present and correctly typed.
    """
    task_id = log.get('task_id', 'unknown')
    
    # Get constraint_count from the task map
    task_data = task_map.get(task_id, {})
    constraint_count = task_data.get('constraint_count', 0)
    
    # Extract violation info
    violation_boolean = log.get('violation_boolean', False)
    violation_reason = log.get('violation_reason', None)
    if violation_reason is None:
        violation_reason = ""
    
    # Extract final score
    final_score = log.get('final_score', 0.0)
    try:
        final_score = float(final_score)
    except (ValueError, TypeError):
        final_score = 0.0
    
    return {
        'task_id': task_id,
        'architecture': architecture,
        'constraint_count': int(constraint_count),
        'violation_boolean': bool(violation_boolean),
        'violation_reason': str(violation_reason),
        'final_score': final_score
    }

def write_traces_csv(traces: List[Dict[str, Any]], output_path: Path):
    """Write the extracted traces to a CSV file."""
    fieldnames = [
        'task_id', 
        'architecture', 
        'constraint_count', 
        'violation_boolean', 
        'violation_reason', 
        'final_score'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(traces)

def main():
    """Main entry point for generating execution traces."""
    paths = get_paths()
    
    # Define input paths
    monolithic_logs_path = paths.data_processed / "monolithic_logs.json"
    dual_track_logs_path = paths.data_processed / "dual_track_logs.json"
    filtered_tasks_path = paths.data_processed / "filtered_tasks.csv"
    
    # Define output path
    output_path = paths.data_processed / "execution_traces.csv"
    
    print(f"Loading filtered tasks from: {filtered_tasks_path}")
    task_map = load_filtered_tasks_map(filtered_tasks_path)
    
    all_traces = []
    
    # Process monolithic logs
    if monolithic_logs_path.exists():
        print(f"Loading monolithic logs from: {monolithic_logs_path}")
        monolithic_logs = load_execution_logs(monolithic_logs_path)
        for log in monolithic_logs:
            trace = extract_trace_data(log, task_map, "monolithic")
            all_traces.append(trace)
        print(f"Processed {len(monolithic_logs)} monolithic traces")
    else:
        print(f"Warning: Monolithic logs not found at {monolithic_logs_path}")
    
    # Process dual-track logs
    if dual_track_logs_path.exists():
        print(f"Loading dual-track logs from: {dual_track_logs_path}")
        dual_track_logs = load_execution_logs(dual_track_logs_path)
        for log in dual_track_logs:
            trace = extract_trace_data(log, task_map, "dual_track")
            all_traces.append(trace)
        print(f"Processed {len(dual_track_logs)} dual-track traces")
    else:
        print(f"Warning: Dual-track logs not found at {dual_track_logs_path}")
    
    if not all_traces:
        print("Error: No traces were generated. Check input log files.")
        sys.exit(1)
    
    # Write output
    write_traces_csv(all_traces, output_path)
    print(f"Successfully wrote {len(all_traces)} traces to: {output_path}")
    
    # Validate output
    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    for i, row in enumerate(rows):
        # Validate task_id
        if not row['task_id'] or row['task_id'] == '':
            print(f"Warning: Row {i+1} has empty task_id")
        
        # Validate constraint_count is int
        try:
            int(row['constraint_count'])
        except ValueError:
            print(f"Error: Row {i+1} has non-integer constraint_count: {row['constraint_count']}")
            sys.exit(1)
        
        # Validate violation_boolean is bool-like
        if row['violation_boolean'] not in ['True', 'False', 'true', 'false', '1', '0']:
            print(f"Warning: Row {i+1} has non-boolean violation_boolean: {row['violation_boolean']}")
        
        # Validate final_score is float
        try:
            float(row['final_score'])
        except ValueError:
            print(f"Error: Row {i+1} has non-float final_score: {row['final_score']}")
            sys.exit(1)
    
    print("Validation passed: All rows have valid data types.")

if __name__ == "__main__":
    main()
