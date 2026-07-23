"""
Generate execution_traces.csv from monolithic and dual-track logs.

This script reads the execution logs produced by T026a (monolithic) and T026b (dual_track),
validates them against the schema defined in T026c, filters out 'implicit_unverified'
rows as per FR-009, and merges them into a single CSV file.

Output: data/processed/execution_traces.csv
"""
import os
import sys
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_paths

def load_execution_logs(file_path: str) -> List[Dict[str, Any]]:
    """Load execution logs from a JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Execution logs file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle case where data is a list or a dict with a 'logs' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'logs' in data:
        return data['logs']
    else:
        # Assume the whole file is the list if it's a dict but no 'logs' key
        return [data] if data else []

def load_filtered_tasks_map(file_path: str) -> Dict[str, int]:
    """Load constraint counts from filtered_tasks.csv for reference."""
    if not os.path.exists(file_path):
        # Return empty dict if file doesn't exist; we can derive count from logs if needed
        return {}
    
    task_map = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_id = row.get('task_id')
            constraint_count = row.get('constraint_count')
            if task_id and constraint_count:
                task_map[task_id] = int(constraint_count)
    return task_map

def extract_trace_data(
    log_entry: Dict[str, Any], 
    architecture: str, 
    task_map: Dict[str, int]
) -> Dict[str, Any]:
    """
    Extract and validate fields for the execution traces CSV.
    
    Schema:
    - task_id (string)
    - architecture (string: 'monolithic' | 'dual_track')
    - constraint_count (int)
    - violation_boolean (bool)
    - violation_reason (string|null)
    - violation_status (string|null)
    - final_score (float)
    """
    task_id = log_entry.get('task_id')
    if not task_id:
        raise ValueError("Log entry missing 'task_id'")
    
    # Determine constraint_count: prefer log entry, fallback to task_map
    constraint_count = log_entry.get('constraint_count')
    if constraint_count is None:
        constraint_count = task_map.get(task_id, 0)
    else:
        constraint_count = int(constraint_count)
    
    violation_boolean = log_entry.get('violation_boolean')
    if violation_boolean is None:
        # Default to False if not present
        violation_boolean = False
    else:
        violation_boolean = bool(violation_boolean)
    
    final_score = log_entry.get('final_score')
    if final_score is None:
        final_score = 0.0
    else:
        final_score = float(final_score)
    
    violation_reason = log_entry.get('violation_reason')
    violation_status = log_entry.get('violation_status')
    
    return {
        'task_id': task_id,
        'architecture': architecture,
        'constraint_count': constraint_count,
        'violation_boolean': violation_boolean,
        'violation_reason': violation_reason,
        'violation_status': violation_status,
        'final_score': final_score
    }

def write_traces_csv(traces: List[Dict[str, Any]], output_path: str) -> None:
    """Write the extracted traces to a CSV file."""
    fieldnames = [
        'task_id', 
        'architecture', 
        'constraint_count', 
        'violation_boolean', 
        'violation_reason', 
        'violation_status', 
        'final_score'
    ]
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for trace in traces:
            writer.writerow(trace)

def main():
    paths = get_paths()
    processed_dir = paths.PROCESSED
    
    monolithic_logs_path = os.path.join(processed_dir, 'monolithic_logs.json')
    dual_track_logs_path = os.path.join(processed_dir, 'dual_track_logs.json')
    filtered_tasks_path = os.path.join(processed_dir, 'filtered_tasks.csv')
    output_path = os.path.join(processed_dir, 'execution_traces.csv')
    
    print(f"Loading filtered tasks from {filtered_tasks_path}...")
    task_map = load_filtered_tasks_map(filtered_tasks_path)
    
    all_traces = []
    
    # Process Monolithic Logs
    if os.path.exists(monolithic_logs_path):
        print(f"Loading monolithic logs from {monolithic_logs_path}...")
        monolithic_logs = load_execution_logs(monolithic_logs_path)
        
        for entry in monolithic_logs:
            # Filter out implicit_unverified as per FR-009
            status = entry.get('violation_status')
            if status == 'implicit_unverified':
                continue
            
            try:
                trace = extract_trace_data(entry, 'monolithic', task_map)
                all_traces.append(trace)
            except ValueError as e:
                print(f"Skipping invalid monolithic log entry: {e}")
    else:
        print(f"Warning: Monolithic logs file not found at {monolithic_logs_path}")
    
    # Process Dual-Track Logs
    if os.path.exists(dual_track_logs_path):
        print(f"Loading dual-track logs from {dual_track_logs_path}...")
        dual_track_logs = load_execution_logs(dual_track_logs_path)
        
        for entry in dual_track_logs:
            # Filter out implicit_unverified as per FR-009
            status = entry.get('violation_status')
            if status == 'implicit_unverified':
                continue
            
            try:
                trace = extract_trace_data(entry, 'dual_track', task_map)
                all_traces.append(trace)
            except ValueError as e:
                print(f"Skipping invalid dual-track log entry: {e}")
    else:
        print(f"Warning: Dual-track logs file not found at {dual_track_logs_path}")
    
    if not all_traces:
        print("Warning: No valid traces found to write. Creating empty CSV.")
    
    print(f"Writing {len(all_traces)} traces to {output_path}...")
    write_traces_csv(all_traces, output_path)
    
    print(f"Successfully generated execution_traces.csv with {len(all_traces)} rows.")

if __name__ == '__main__':
    main()