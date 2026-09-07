import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from scripts.baseline_runner import ExecutionResult, run_baseline_task
from scripts.ingest import load_swe_bench, load_agent_bench, parse_swe_bench, parse_agent_bench, merge_datasets

def load_baseline_results(baseline_dir: str) -> Dict[str, ExecutionResult]:
    """Load baseline execution results from JSON files."""
    results = {}
    baseline_path = Path(baseline_dir)
    if not baseline_path.exists():
        return results
    
    for json_file in baseline_path.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                task_id = data.get('task_id')
                if task_id:
                    # Reconstruct ExecutionResult or raw dict if class not fully serialized
                    results[task_id] = ExecutionResult(
                        outcome=data.get('outcome', 'Unknown'),
                        duration=data.get('duration', 0.0),
                        error_message=data.get('error_message')
                    )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not parse {json_file}: {e}")
    return results

def load_ingested_tasks(ingested_file: str) -> List[Dict[str, Any]]:
    """Load tasks from the ingested CSV."""
    tasks = []
    if not os.path.exists(ingested_file):
        raise FileNotFoundError(f"Ingested tasks file not found: {ingested_file}")
    
    with open(ingested_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(row)
    return tasks

def process_unparseable_tasks(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identify tasks that are unparseable (e.g., syntax errors in code_diff or original_code).
    This function simulates a check that would happen during ingestion or extraction.
    In a real pipeline, this might be flagged by tree-sitter or a syntax checker.
    For this step, we assume 'unparseable' status is already set or detectable via simple heuristics.
    
    Returns a list of tasks with 'status' updated to 'Unparseable' if detected.
    """
    # In the context of T016, we need to ensure tasks that failed parsing are flagged.
    # Since T010/T011 are marked complete but might not have fully implemented the flagging,
    # we implement the logic here to ensure the ground truth reflects it.
    # We look for a 'parse_status' or similar field, or check if code_diff is empty/malformed.
    
    unparseable_count = 0
    for task in tasks:
        # Check for existing unparseable flag or heuristic
        if task.get('parse_status') == 'unparseable' or task.get('status') == 'Unparseable':
            task['status'] = 'Unparseable'
            task['dynamic_execution_outcome'] = 'Unparseable'
            unparseable_count += 1
        elif not task.get('code_diff') or task.get('code_diff', '').strip() == '':
            # If code_diff is missing, we can't execute, mark as Unparseable for safety
            task['status'] = 'Unparseable'
            task['dynamic_execution_outcome'] = 'Unparseable'
            unparseable_count += 1
        
        # If it's not unparseable, ensure it has a baseline outcome
        if task.get('status') != 'Unparseable':
            # Placeholder: In a real run, this would be populated by baseline_runner
            # For T016 implementation, we ensure the structure exists.
            if 'dynamic_execution_outcome' not in task:
                task['dynamic_execution_outcome'] = 'Pending'
                
    print(f"Processed {unparseable_count} unparseable tasks.")
    return tasks

def generate_ground_truth(tasks: List[Dict[str, Any]], baseline_results: Dict[str, ExecutionResult]) -> List[Dict[str, Any]]:
    """
    Merge ingested tasks with baseline execution results.
    Explicitly handle 'Unparseable' tasks by retaining them with a specific status.
    """
    ground_truth = []
    
    for task in tasks:
        task_id = task.get('task_id')
        outcome = task.get('dynamic_execution_outcome', 'Unknown')
        
        # If marked unparseable, keep as is (T016 requirement)
        if task.get('status') == 'Unparseable':
            # Ensure outcome is explicitly 'Unparseable'
            if outcome != 'Unparseable':
                task['dynamic_execution_outcome'] = 'Unparseable'
            ground_truth.append(task)
            continue
        
        # If not unparseable, try to get outcome from baseline results
        if task_id in baseline_results:
            exec_result = baseline_results[task_id]
            task['dynamic_execution_outcome'] = exec_result.outcome
        else:
            # If no baseline result found, mark as 'Unknown' or 'Skipped'
            # T016 requires specific handling, but if not unparseable, it should be executed.
            # If execution didn't happen, it's a pipeline error, but we record it.
            task['dynamic_execution_outcome'] = 'Unknown'
        
        ground_truth.append(task)
        
    return ground_truth

def main():
    """Main entry point for generating ground truth CSV."""
    # Paths
    ingested_path = Path("data/processed/ingested_tasks.csv")
    baseline_dir = Path("data/processed/baseline_results")
    output_path = Path("data/processed/ground_truth.csv")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print(f"Loading ingested tasks from {ingested_path}...")
    try:
        tasks = load_ingested_tasks(str(ingested_path))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    
    print(f"Loading baseline results from {baseline_dir}...")
    baseline_results = load_baseline_results(str(baseline_dir))
    
    # Process unparseable tasks (T016)
    print("Processing unparseable tasks...")
    tasks = process_unparseable_tasks(tasks)
    
    # Generate ground truth
    print("Generating ground truth...")
    ground_truth = generate_ground_truth(tasks, baseline_results)
    
    # Write to CSV
    if ground_truth:
        fieldnames = list(ground_truth[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(ground_truth)
        print(f"Ground truth written to {output_path}")
    else:
        print("No ground truth data to write.")

if __name__ == "__main__":
    main()
