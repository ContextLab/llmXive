import json
import sys
import time
import argparse
import gc
import os
from pathlib import Path

def load_curated_issues() -> list:
    """Load curated issues from data/curated/hard_subset.jsonl."""
    from config import get_path
    path = get_path("hard_subset")
    if not path.exists():
        raise FileNotFoundError(f"Hard subset not found at {path}")
    
    issues = []
    with open(path, "r") as f:
        for line in f:
            if line.strip():
                issues.append(json.loads(line))
    return issues

def run_single_issue_baseline(issue: dict) -> dict:
    """Run baseline analysis on a single issue."""
    # Placeholder for actual baseline logic
    return {
        "issue_id": issue.get("issue_id"),
        "status": "completed",
        "turns_used": 1,
        "coverage": 0.0
    }

def run_single_issue_iterative(issue: dict, max_turns: int = 3) -> dict:
    """Run iterative analysis on a single issue."""
    # Placeholder for actual iterative logic
    return {
        "issue_id": issue.get("issue_id"),
        "status": "completed",
        "turns_used": max_turns,
        "coverage": 0.0
    }

def merge_results(baseline_results: list, iterative_results: list) -> dict:
    """Merge baseline and iterative results."""
    return {
        "baseline_count": len(baseline_results),
        "iterative_count": len(iterative_results),
        "timestamp": time.time()
    }

class ExecutionMonitor:
    """Monitor execution time and resource usage."""
    def __init__(self, max_hours: float = 6.0):
        self.start_time = time.time()
        self.max_seconds = max_hours * 3600

    def check(self) -> bool:
        """Check if execution time exceeds limit."""
        elapsed = time.time() - self.start_time
        return elapsed < self.max_seconds

def run_full_pipeline(max_hours: float = 6.0) -> dict:
    """Run the full analysis pipeline."""
    monitor = ExecutionMonitor(max_hours)
    
    if not monitor.check():
        raise TimeoutError("Execution time limit exceeded")
    
    issues = load_curated_issues()
    baseline_results = []
    iterative_results = []
    
    for issue in issues:
        if not monitor.check():
            print("Pipeline aborted due to time limit")
            break
        
        baseline_results.append(run_single_issue_baseline(issue))
        iterative_results.append(run_single_issue_iterative(issue))
    
    return merge_results(baseline_results, iterative_results)

def main() -> None:
    """Entry point for the main pipeline."""
    parser = argparse.ArgumentParser(description="Run the llmXive analysis pipeline")
    parser.add_argument("--max-hours", type=float, default=6.0, help="Maximum execution time in hours")
    args = parser.parse_args()

    try:
        results = run_full_pipeline(max_hours=args.max_hours)
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()