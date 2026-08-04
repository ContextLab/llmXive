import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from baseline_runner as per API surface
from scripts.baseline_runner import ExecutionResult, run_baseline_task

def load_baseline_results(results_dir: str) -> Dict[str, ExecutionResult]:
    """
    Load execution results from the baseline runner output directory.
    Expects JSON files named {task_id}.json containing execution outcomes.
    """
    results = {}
    results_path = Path(results_dir)
    if not results_path.exists():
        # If no results exist, return empty dict (will be handled downstream)
        return results

    for json_file in results_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                task_id = json_file.stem
                # Map JSON fields to ExecutionResult attributes
                # Expected JSON structure: {"status": "Pass"|"Fail"|"Timeout", "duration": float, "error": str}
                status = data.get("status", "Unknown")
                duration = data.get("duration", 0.0)
                error_msg = data.get("error", "")
                
                results[task_id] = ExecutionResult(
                    task_id=task_id,
                    status=status,
                    duration=duration,
                    error=error_msg
                )
        except (json.JSONDecodeError, KeyError) as e:
            # Log warning but continue processing other files
            print(f"Warning: Could not parse {json_file}: {e}")
            continue
    
    return results

def load_ingested_tasks(csv_path: str) -> List[Dict[str, Any]]:
    """
    Load the merged dataset from the ingestion step.
    Expects CSV with columns: task_id, code_diff, original_code, source_dataset
    """
    tasks = []
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"Ingested tasks CSV not found: {csv_path}")

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(row)
    
    return tasks

def process_unparseable_tasks(tasks: List[Dict[str, Any]], unparseable_marker: str = "Unparseable") -> List[Dict[str, Any]]:
    """
    Ensure tasks flagged as unparseable (from T016) are retained with correct status.
    This function validates that 'Unparseable' tasks have a specific outcome marker.
    """
    processed = []
    for task in tasks:
        # If the task was already marked as unparseable in the ingestion/processing step,
        # ensure it gets a specific outcome if not already set by baseline runner
        if task.get("status") == "Unparseable" or task.get("code_diff") == "":
            task["dynamic_execution_outcome"] = "Unparseable"
        processed.append(task)
    return processed

def generate_ground_truth(
    ingested_tasks_path: str,
    baseline_results_path: str,
    output_path: str,
    unparseable_marker: str = "Unparseable"
) -> None:
    """
    Generate the final ground truth CSV by merging ingested tasks with baseline execution results.
    
    Columns: task_id, code_diff, dynamic_execution_outcome
    - Loads tasks from ingested_tasks_path (CSV)
    - Loads execution results from baseline_results_path (JSON files)
    - Merges data, handling cases where baseline results are missing or tasks are unparseable.
    - Writes to output_path.
    """
    # Load data
    tasks = load_ingested_tasks(ingested_tasks_path)
    baseline_results = load_baseline_results(baseline_results_path)
    
    # Process unparseable tasks first
    tasks = process_unparseable_tasks(tasks, unparseable_marker)
    
    # Prepare output rows
    output_rows = []
    for task in tasks:
        task_id = task.get("task_id")
        code_diff = task.get("code_diff", "")
        
        # Determine outcome
        if task.get("dynamic_execution_outcome") == "Unparseable":
            outcome = "Unparseable"
        elif task_id in baseline_results:
            # Use the status from the baseline runner result
            result = baseline_results[task_id]
            outcome = result.status
        else:
            # If no baseline result exists, mark as "Missing_Baseline"
            # This should ideally not happen if T012/T013 ran successfully for all tasks
            outcome = "Missing_Baseline"
        
        output_rows.append({
            "task_id": task_id,
            "code_diff": code_diff,
            "dynamic_execution_outcome": outcome
        })
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["task_id", "code_diff", "dynamic_execution_outcome"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    
    print(f"Ground truth generated: {output_path}")
    print(f"Total tasks processed: {len(output_rows)}")
    outcome_counts = {}
    for row in output_rows:
        outcome = row["dynamic_execution_outcome"]
        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
    print(f"Outcome distribution: {outcome_counts}")

def main():
    """
    Entry point for generating ground truth.
    Reads from default paths or environment variables.
    """
    # Default paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    ingested_csv = project_root / "data" / "processed" / "ingested_tasks.csv"
    baseline_results_dir = project_root / "data" / "processed" / "baseline_results"
    output_csv = project_root / "data" / "processed" / "ground_truth.csv"
    
    # Allow override via environment variables
    ingested_csv = Path(os.getenv("INGESTED_TASKS_PATH", ingested_csv))
    baseline_results_dir = Path(os.getenv("BASELINE_RESULTS_DIR", baseline_results_dir))
    output_csv = Path(os.getenv("GROUND_TRUTH_PATH", output_csv))
    
    if not ingested_csv.exists():
        raise FileNotFoundError(f"Ingested tasks file not found: {ingested_csv}")
    
    generate_ground_truth(
        ingested_tasks_path=str(ingested_csv),
        baseline_results_path=str(baseline_results_dir),
        output_path=str(output_csv)
    )

if __name__ == "__main__":
    main()
