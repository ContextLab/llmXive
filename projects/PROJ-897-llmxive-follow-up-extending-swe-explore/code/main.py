"""
Main entry point for the llmXive pipeline.
Orchestrates the full pipeline execution.
"""
import json
import sys
import time
import argparse
import gc
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import get_path, get_config_summary, MAX_EXECUTION_HOURS

class ExecutionMonitor:
    """Monitor execution time and resource usage."""
    
    def __init__(self, max_hours: float = MAX_EXECUTION_HOURS):
        self.start_time = time.time()
        self.max_seconds = max_hours * 3600
        self.checkpoints = []
    
    def checkpoint(self, name: str):
        """Record a checkpoint."""
        elapsed = time.time() - self.start_time
        self.checkpoints.append({
            "name": name,
            "elapsed_seconds": elapsed,
            "elapsed_hours": elapsed / 3600
        })
        print(f"Checkpoint: {name} (elapsed: {elapsed/3600:.2f}h)")
    
    def is_time_exceeded(self) -> bool:
        """Check if max execution time has been exceeded."""
        elapsed = time.time() - self.start_time
        return elapsed > self.max_seconds
    
    def get_remaining_time(self) -> float:
        """Get remaining time in seconds."""
        elapsed = time.time() - self.start_time
        return max(0, self.max_seconds - elapsed)

def load_curated_issues() -> List[Dict[str, Any]]:
    """Load curated issues from data/curated/hard_subset.jsonl."""
    input_file = get_path('curated') / "hard_subset.jsonl"
    if not input_file.exists():
        raise FileNotFoundError(f"Curated issues not found: {input_file}")
    
    issues = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            issues.append(json.loads(line))
    return issues

def run_single_issue_baseline(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Run baseline query on a single issue."""
    # Placeholder for actual baseline execution
    return {
        "issue_id": issue.get('instance_id'),
        "query_count": 1,
        "retrieved_context_ids": [],
        "coverage_score": 0.0,
        "status": "skipped"  # Placeholder
    }

def run_single_issue_iterative(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Run iterative agent loop on a single issue."""
    # Placeholder for actual iterative execution
    return {
        "issue_id": issue.get('instance_id'),
        "query_history": [],
        "static_analysis_signals": [],
        "turn_reasons": [],
        "coverage_score": 0.0,
        "status": "skipped"  # Placeholder
    }

def merge_results(baseline_logs: List[Dict], iterative_logs: List[Dict]) -> List[Dict]:
    """Merge baseline and iterative results."""
    # Placeholder for merging logic
    return baseline_logs + iterative_logs

def run_full_pipeline(monitor: ExecutionMonitor) -> Dict[str, Any]:
    """
    Execute the full pipeline.
    
    This function orchestrates:
    1. Data loading
    2. Baseline execution
    3. Iterative execution
    4. Metrics calculation
    5. Statistical analysis
    6. Report generation
    """
    results = {
        "baseline": [],
        "iterative": [],
        "metrics": {},
        "stats": {},
        "report": None
    }
    
    # Load data
    if monitor.is_time_exceeded():
        print("Execution time exceeded. Aborting pipeline.")
        return results
    
    print("Loading curated issues...")
    issues = load_curated_issues()
    print(f"Loaded {len(issues)} issues.")
    monitor.checkpoint("data_loaded")
    
    # Run baseline (placeholder - actual implementation in T022)
    print("Running baseline queries...")
    for issue in issues:
        if monitor.is_time_exceeded():
            break
        result = run_single_issue_baseline(issue)
        results["baseline"].append(result)
    monitor.checkpoint("baseline_complete")
    
    # Run iterative (placeholder - actual implementation in T023)
    print("Running iterative agent loop...")
    for issue in issues:
        if monitor.is_time_exceeded():
            break
        result = run_single_issue_iterative(issue)
        results["iterative"].append(result)
    monitor.checkpoint("iterative_complete")
    
    # Calculate metrics (placeholder - actual implementation in T028/T029)
    print("Calculating metrics...")
    # ... metrics calculation ...
    monitor.checkpoint("metrics_complete")
    
    # Statistical analysis (placeholder - actual implementation in T030)
    print("Running statistical analysis...")
    # ... stats ...
    monitor.checkpoint("stats_complete")
    
    # Generate report (placeholder - actual implementation in T033)
    print("Generating report...")
    # ... report ...
    monitor.checkpoint("report_complete")
    
    return results

def main():
    """Entry point for the main script."""
    parser = argparse.ArgumentParser(description="llmXive Pipeline")
    parser.add_argument(
        "--max-hours",
        type=float,
        default=MAX_EXECUTION_HOURS,
        help=f"Maximum execution time in hours (default: {MAX_EXECUTION_HOURS})"
    )
    
    args = parser.parse_args()
    
    print("Starting llmXive pipeline...")
    print(f"Configuration: {get_config_summary()}")
    print(f"Max execution time: {args.max_hours} hours")
    
    monitor = ExecutionMonitor(max_hours=args.max_hours)
    
    try:
        results = run_full_pipeline(monitor)
        
        # Save results
        output_file = get_path('results') / "pipeline_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"Pipeline complete. Results saved to: {output_file}")
        
    except Exception as e:
        print(f"ERROR: Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
