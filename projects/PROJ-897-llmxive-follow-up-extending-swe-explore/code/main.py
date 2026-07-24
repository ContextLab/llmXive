import json
import sys
import time
import argparse
import gc
import os
from pathlib import Path
from typing import Optional, Dict, Any

from config import get_path, ensure_directories, get_config_summary

class ExecutionMonitor:
    def __init__(self, max_hours: float):
        self.max_hours = max_hours
        self.start_time = time.time()
        self.elapsed = 0

    def check_time(self) -> bool:
        """Returns False if time limit exceeded."""
        self.elapsed = (time.time() - self.start_time) / 3600
        if self.elapsed > self.max_hours:
            print(f"Time limit exceeded: {self.elapsed:.2f} hours > {self.max_hours} hours")
            return False
        return True

def load_curated_issues():
    """Loads the curated hard subset."""
    path = get_path("curated_hard_subset")
    if not path.exists():
        raise FileNotFoundError(f"Curated hard subset not found at {path}")
    with open(path, 'r') as f:
        return [json.loads(line) for line in f]

def run_single_issue_baseline(issue: Dict[str, Any], monitor: ExecutionMonitor):
    """Placeholder for baseline execution logic."""
    if not monitor.check_time():
        return None
    # Logic would go here
    return {"issue_id": issue.get("id"), "status": "completed_baseline"}

def run_single_issue_iterative(issue: Dict[str, Any], monitor: ExecutionMonitor):
    """Placeholder for iterative execution logic."""
    if not monitor.check_time():
        return None
    # Logic would go here
    return {"issue_id": issue.get("id"), "status": "completed_iterative"}

def merge_results(baseline_logs: list, iterative_logs: list) -> Dict[str, Any]:
    """Merges baseline and iterative results."""
    return {
        "baseline_count": len(baseline_logs),
        "iterative_count": len(iterative_logs),
        "merged_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

def main():
    parser = argparse.ArgumentParser(description="llmXive Main Pipeline Runner")
    parser.add_argument("--max-hours", type=float, default=6.0, help="Maximum execution time in hours")
    # Removed --mode flag as it caused argparse errors
    
    args = parser.parse_args()
    
    ensure_directories()
    monitor = ExecutionMonitor(args.max_hours)
    
    print("Starting llmXive Pipeline...")
    print(f"Max execution time: {args.max_hours} hours")
    
    try:
        issues = load_curated_issues()
        print(f"Loaded {len(issues)} issues.")
        
        baseline_results = []
        iterative_results = []
        
        for issue in issues:
            if not monitor.check_time():
                print("Pipeline aborted due to time limit.")
                break
            
            print(f"Processing issue: {issue.get('id')}")
            
            # Run Baseline
            res_base = run_single_issue_baseline(issue, monitor)
            if res_base:
                baseline_results.append(res_base)
            
            # Run Iterative
            res_iter = run_single_issue_iterative(issue, monitor)
            if res_iter:
                iterative_results.append(res_iter)
            
            gc.collect()
        
        final_report = merge_results(baseline_results, iterative_results)
        output_path = get_path("results_final_report")
        with open(output_path, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        print(f"Pipeline completed. Report saved to {output_path}")
        return 0
        
    except Exception as e:
        print(f"Pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())