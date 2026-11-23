"""
Generate ground truth CSV from baseline execution results and ingested tasks.

This script consumes:
- Baseline execution results (from baseline_runner.py)
- Ingested tasks (from ingest.py)
- Unparseable task flags (from T016 error handling)

And produces:
- data/processed/ground_truth.csv with columns:
  task_id, code_diff, dynamic_execution_outcome
"""
import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from scripts.baseline_runner import ExecutionResult


def load_baseline_results(results_dir: Path) -> Dict[str, ExecutionResult]:
    """
    Load baseline execution results from JSON files.
    
    Args:
        results_dir: Directory containing execution result JSON files
        
    Returns:
        Dictionary mapping task_id to ExecutionResult
    """
    results = {}
    if not results_dir.exists():
        return results
        
    for json_file in results_dir.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                # Extract task_id from filename or data
                task_id = data.get('task_id', json_file.stem)
                results[task_id] = ExecutionResult(
                    task_id=task_id,
                    status=data.get('status', 'Unknown'),
                    duration=data.get('duration', 0.0),
                    output=data.get('output', ''),
                    error=data.get('error', '')
                )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not parse {json_file}: {e}")
            continue
            
    return results


def load_ingested_tasks(ingest_file: Path) -> List[Dict[str, Any]]:
    """
    Load ingested tasks from the CSV produced by ingest.py.
    
    Args:
        ingest_file: Path to the ingested tasks CSV
        
    Returns:
        List of task dictionaries
    """
    tasks = []
    if not ingest_file.exists():
        return tasks
        
    with open(ingest_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(row)
            
    return tasks


def process_unparseable_tasks(tasks: List[Dict[str, Any]], unparseable_marker: str = "Unparseable") -> Dict[str, bool]:
    """
    Identify tasks that are marked as unparseable.
    
    Args:
        tasks: List of task dictionaries
        unparseable_marker: Marker string used to flag unparseable tasks
        
    Returns:
        Dictionary mapping task_id to unparseable status
    """
    unparseable_map = {}
    for task in tasks:
        task_id = task.get('task_id', '')
        # Check if task is marked as unparseable in various fields
        is_unparseable = False
        
        # Check code_diff field
        code_diff = task.get('code_diff', '')
        if unparseable_marker in str(code_diff):
            is_unparseable = True
            
        # Check for explicit status field
        status = task.get('status', '')
        if unparseable_marker in status:
            is_unparseable = True
            
        unparseable_map[task_id] = is_unparseable
        
    return unparseable_map


def generate_ground_truth(
    baseline_results: Dict[str, ExecutionResult],
    tasks: List[Dict[str, Any]],
    unparseable_map: Dict[str, bool],
    output_path: Path
) -> None:
    """
    Generate the ground truth CSV file.
    
    Args:
        baseline_results: Dictionary of execution results
        tasks: List of ingested tasks
        unparseable_map: Dictionary of unparseable task flags
        output_path: Path to write the ground truth CSV
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare output rows
    output_rows = []
    
    for task in tasks:
        task_id = task.get('task_id', '')
        code_diff = task.get('code_diff', '')
        
        # Determine dynamic_execution_outcome
        if unparseable_map.get(task_id, False):
            # Unparseable tasks get a special outcome
            outcome = "Unparseable"
        elif task_id in baseline_results:
            # Use the actual execution result
            result = baseline_results[task_id]
            outcome = result.status
        else:
            # No execution result found - this should ideally not happen
            # but we handle it gracefully
            outcome = "Missing_Execution_Result"
            
        output_rows.append({
            'task_id': task_id,
            'code_diff': code_diff,
            'dynamic_execution_outcome': outcome
        })
    
    # Write to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['task_id', 'code_diff', 'dynamic_execution_outcome']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
        
    print(f"Generated ground truth CSV with {len(output_rows)} rows: {output_path}")


def main():
    """Main entry point for ground truth generation."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / 'data'
    
    # Input paths
    baseline_results_dir = data_dir / 'raw' / 'baseline_results'
    ingested_tasks_file = data_dir / 'processed' / 'ingested_tasks.csv'
    
    # Output path
    ground_truth_file = data_dir / 'processed' / 'ground_truth.csv'
    
    # Load data
    print("Loading baseline execution results...")
    baseline_results = load_baseline_results(baseline_results_dir)
    print(f"  Loaded {len(baseline_results)} execution results")
    
    print("Loading ingested tasks...")
    tasks = load_ingested_tasks(ingested_tasks_file)
    print(f"  Loaded {len(tasks)} tasks")
    
    if not tasks:
        print("Error: No ingested tasks found. Run ingest.py first.")
        return
    
    # Process unparseable tasks
    print("Processing unparseable task flags...")
    unparseable_map = process_unparseable_tasks(tasks)
    unparseable_count = sum(1 for v in unparseable_map.values() if v)
    print(f"  Found {unparseable_count} unparseable tasks")
    
    # Generate ground truth
    print("Generating ground truth CSV...")
    generate_ground_truth(baseline_results, tasks, unparseable_map, ground_truth_file)
    
    # Validate output
    if ground_truth_file.exists():
        with open(ground_truth_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        # Check for missing values
        missing_count = 0
        for row in rows:
            for key in ['task_id', 'code_diff', 'dynamic_execution_outcome']:
                if not row.get(key):
                    missing_count += 1
                    
        if missing_count > 0:
            print(f"Warning: {missing_count} rows have missing values")
        else:
            print("Validation: No missing values in ground truth CSV")
            
        print(f"Ground truth generation complete. Output: {ground_truth_file}")
    else:
        print("Error: Ground truth file was not created")


if __name__ == "__main__":
    main()
