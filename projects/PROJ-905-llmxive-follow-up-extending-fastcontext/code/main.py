import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
import csv

from config import get_path, ensure_directories
from stratification import load_scores_from_csv
from fastcontext_lite import run_fastcontext_lite
from baseline_runner import run_baseline_4b
from metrics_logger import create_log_entry, log_metrics

def load_repository_list() -> List[Dict[str, Any]]:
    """
    Load repository list from the stratified sets CSV.
    Returns a list of dicts with 'repo_id', 'regularity_score', and 'split'.
    """
    scores_path = get_path("data/processed/regularity_scores.csv")
    if not scores_path.exists():
        raise FileNotFoundError(f"Stratified scores file not found: {scores_path}")
    
    repos = []
    with open(scores_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            repos.append({
                'repo_id': row['repo_id'],
                'regularity_score': float(row['regularity_score']),
                'split': row['split']
            })
    return repos

def run_experiment():
    """
    Main orchestration logic for T023.
    1. Load stratified repository list.
    2. For each repo, run Lite and Baseline pipelines.
    3. Collect metrics and write to data/results/exploration_logs.jsonl.
    """
    start_time = time.time()
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting Experiment Orchestration (T023)...")
    
    # Ensure output directory exists
    ensure_directories()
    output_path = get_path("data/results/exploration_logs.jsonl")
    
    # Load repositories
    try:
        repos = load_repository_list()
        print(f"Loaded {len(repos)} repositories from stratified sets.")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Please ensure T014 (export regularity scores) has been completed and the file exists.")
        sys.exit(1)

    logs = []
    processed_count = 0

    for repo in repos:
        repo_id = repo['repo_id']
        split = repo['split']
        score = repo['regularity_score']
        
        print(f"Processing [{split}] {repo_id} (score={score:.4f})...")
        
        # Determine repo path. Assuming repos are extracted to data/raw/repos/{repo_id}
        # or we need to fetch them. For this implementation, we assume they are present.
        repo_path = Path(f"data/raw/repos/{repo_id}")
        
        if not repo_path.exists():
            print(f"  Warning: Repository {repo_id} not found at {repo_path}. Skipping.")
            continue

        # Run Lite Pipeline
        lite_metrics = None
        try:
            print(f"  Running FastContext-Lite...")
            lite_start = time.time()
            # run_fastcontext_lite expects repo_path and optionally an issue context
            # We pass None for issue to run a general exploration if specific issue isn't provided
            lite_metrics = run_fastcontext_lite(repo_path, None) 
            if lite_metrics:
                lite_metrics['wall_clock_latency'] = time.time() - lite_start
                lite_metrics['pipeline'] = 'lite'
                print(f"  Lite completed.")
            else:
                print(f"  Lite returned no metrics.")
                continue
        except Exception as e:
            print(f"  Error running Lite on {repo_id}: {e}")
            continue

        # Run Baseline Pipeline
        baseline_metrics = None
        try:
            print(f"  Running Baseline (FastContext-4B)...")
            baseline_start = time.time()
            baseline_metrics = run_baseline_4b(repo_path, None)
            if baseline_metrics:
                baseline_metrics['wall_clock_latency'] = time.time() - baseline_start
                baseline_metrics['pipeline'] = 'baseline'
                print(f"  Baseline completed.")
            else:
                print(f"  Baseline returned no metrics.")
                continue
        except Exception as e:
            print(f"  Error running Baseline on {repo_id}: {e}")
            continue

        # Create Log Entry
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'repo_id': repo_id,
            'regularity_score': score,
            'split': split,
            'lite_metrics': lite_metrics,
            'baseline_metrics': baseline_metrics
        }
        
        logs.append(log_entry)
        processed_count += 1

    # Write logs to file
    with open(output_path, 'w', encoding='utf-8') as f:
        for log in logs:
            f.write(json.dumps(log) + '\n')
    
    total_time = time.time() - start_time
    print(f"Experiment complete. Processed {processed_count} repositories in {total_time:.2f}s.")
    print(f"Results saved to {output_path}")

def main():
    """Entry point for the experiment."""
    run_experiment()

if __name__ == "__main__":
    main()
