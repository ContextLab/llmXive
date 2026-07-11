import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from sibling module (T012/T013/T016 implementation)
from scripts.baseline_runner import ExecutionResult, run_baseline_task
from scripts.ingest import load_swe_bench, load_agent_bench, parse_swe_bench, parse_agent_bench, merge_datasets, write_to_csv

# Configuration
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_FILE = PROCESSED_DIR / "ground_truth.csv"
BASELINE_RESULTS_FILE = PROCESSED_DIR / "baseline_results.json"
INGESTED_FILE = PROCESSED_DIR / "merged_dataset.csv"

def load_baseline_results() -> Dict[str, ExecutionResult]:
    """Load baseline execution results from JSON file."""
    if not BASELINE_RESULTS_FILE.exists():
        raise FileNotFoundError(f"Baseline results file not found: {BASELINE_RESULTS_FILE}")
    
    with open(BASELINE_RESULTS_FILE, 'r') as f:
        raw_results = json.load(f)
    
    results = {}
    for task_id, data in raw_results.items():
        results[task_id] = ExecutionResult(
            status=data['status'],
            duration=data['duration'],
            error_message=data.get('error_message')
        )
    return results

def load_ingested_tasks() -> List[Dict[str, Any]]:
    """Load merged dataset from CSV."""
    if not INGESTED_FILE.exists():
        raise FileNotFoundError(f"Ingested dataset not found: {INGESTED_FILE}")
    
    tasks = []
    with open(INGESTED_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(row)
    return tasks

def process_unparseable_tasks(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process tasks that were marked as 'Unparseable' during ingestion.
    These tasks should be included in ground truth with a specific status.
    """
    for task in tasks:
        if task.get('parse_status') == 'Unparseable':
            # Ensure unparseable tasks have the correct outcome flag
            if 'dynamic_execution_outcome' not in task:
                task['dynamic_execution_outcome'] = 'Unparseable'
            if 'code_diff' not in task or not task['code_diff']:
                # Keep empty or original diff as is
                pass
    return tasks

def generate_ground_truth() -> None:
    """
    Generate ground_truth.csv with columns:
    - task_id
    - code_diff
    - dynamic_execution_outcome
    
    Consumes results from:
    - T010/T011: Ingested dataset (merged_dataset.csv)
    - T012/T013: Baseline execution results (baseline_results.json)
    - T016: Unparseable task flags
    """
    # Ensure output directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load baseline results
    baseline_results = load_baseline_results()
    
    # Load ingested tasks
    tasks = load_ingested_tasks()
    
    # Process unparseable tasks
    tasks = process_unparseable_tasks(tasks)
    
    # Prepare ground truth data
    ground_truth_rows = []
    
    for task in tasks:
        task_id = task.get('task_id')
        code_diff = task.get('code_diff', '')
        
        # Determine dynamic execution outcome
        if task.get('parse_status') == 'Unparseable':
            # T016: Flag as Unparseable, skip execution outcome lookup
            outcome = 'Unparseable'
        elif task_id in baseline_results:
            # T012/T013: Use baseline execution result
            result = baseline_results[task_id]
            outcome = result.status
        else:
            # Task was ingested but not executed (should not happen in normal flow)
            outcome = 'Skipped'
        
        ground_truth_rows.append({
            'task_id': task_id,
            'code_diff': code_diff,
            'dynamic_execution_outcome': outcome
        })
    
    # Write to CSV
    fieldnames = ['task_id', 'code_diff', 'dynamic_execution_outcome']
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ground_truth_rows)
    
    print(f"Ground truth generated: {OUTPUT_FILE}")
    print(f"Total tasks: {len(ground_truth_rows)}")
    
    # Summary statistics
    outcome_counts = {}
    for row in ground_truth_rows:
        outcome = row['dynamic_execution_outcome']
        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
    
    print("Outcome distribution:")
    for outcome, count in sorted(outcome_counts.items()):
        print(f"  {outcome}: {count}")

def main():
    """Main entry point for ground truth generation."""
    try:
        generate_ground_truth()
        print("Task T015 completed successfully.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure T010, T011, T012, T013, and T016 have been completed first.")
        raise
    except Exception as e:
        print(f"Error generating ground truth: {e}")
        raise

if __name__ == "__main__":
    main()