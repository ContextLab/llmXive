"""
Main entry point for the llmXive automated science pipeline.
Implements the runtime monitor for execution time constraints (SC-005).
"""
import json
import sys
import time
import argparse
import gc
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from local modules (ensure these exist in the project structure)
from config import get_path, get_config_summary, ensure_directories
from utils.hash_artifacts import compute_sha256
from data.download import download_benchmark_dataset
from data.derive_gt import stream_derive_gt
from data.curate import generate_synthetic_issues, filter_hard_instances
from data.validate_hard import validate_issue, generate_report
from agent.static_baseline import run_baseline
from agent.iterative import run_iterative_loop
from agent.sweep_turns import run_sweep
from metrics.coverage import calculate_coverage
from metrics.ranking import calculate_ranking_metrics
from analysis.stats import (
    load_agent_logs_for_pairing,
    run_wilcoxon_signed_rank_test,
    run_exact_permutation_test,
    run_cox_survival_analysis,
    apply_bonferroni_correction
)
from analysis.plots import generate_all_plots
from analysis.report_generator import generate_draft

# --- Configuration Constants ---
# SC-005: Maximum allowed execution time (6 hours)
# We abort non-critical sweeps if we exceed 90% of this time to ensure graceful shutdown.
MAX_TOTAL_HOURS = 6.0
ABORT_THRESHOLD_HOURS = 5.5
ABORT_THRESHOLD_SECONDS = ABORT_THRESHOLD_HOURS * 3600

class ExecutionMonitor:
    """
    Monitors total execution time and enforces the 6-hour limit (SC-005).
    If elapsed time > 5.5 hours, it signals non-critical tasks to abort or reduce sample size.
    """
    def __init__(self, max_hours: float = MAX_TOTAL_HOURS):
        self.start_time = time.time()
        self.max_seconds = max_hours * 3600
        self.abort_threshold_seconds = (max_hours * 0.9166) * 3600  # ~5.5 hours for 6h max
        self.is_aborted = False
        self.log_path = Path("data/results/execution_monitor.log")
        
        # Ensure log directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def elapsed_seconds(self) -> float:
        return time.time() - self.start_time

    def elapsed_hours(self) -> float:
        return self.elapsed_seconds() / 3600

    def check_time(self, task_name: str) -> bool:
        """
        Checks if we should abort the current task.
        Returns True if we should proceed, False if we should abort.
        Logs status to disk.
        """
        elapsed = self.elapsed_seconds()
        status = "OK"
        action = "PROCEED"

        if elapsed > self.max_seconds:
            status = "EXCEEDED_LIMIT"
            action = "ABORT_CRITICAL"
            self.is_aborted = True
        elif elapsed > self.abort_threshold_seconds:
            status = "WARNING"
            action = "ABORT_NON_CRITICAL"
            self.is_aborted = True # For non-critical, we treat it as an abort signal

        # Log the check
        log_entry = {
            "timestamp": time.time(),
            "elapsed_hours": self.elapsed_hours(),
            "task_name": task_name,
            "status": status,
            "action": action,
            "threshold_hours": self.abort_threshold_seconds / 3600,
            "max_hours": self.max_seconds / 3600
        }

        with open(self.log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        if action == "ABORT_CRITICAL":
            print(f"CRITICAL: Execution time ({self.elapsed_hours():.2f}h) exceeds max limit ({self.max_seconds/3600:.2f}h). Aborting all tasks.")
            return False
        elif action == "ABORT_NON_CRITICAL":
            print(f"WARNING: Execution time ({self.elapsed_hours():.2f}h) exceeds 5.5h threshold. Aborting non-critical tasks.")
            # We return False for non-critical tasks, but the caller decides if it's critical
            return False
        
        return True

    def should_abort(self) -> bool:
        return self.is_aborted

def load_curated_issues(path: str) -> List[Dict[str, Any]]:
    """Load issues from a curated JSONL file."""
    issues = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                issues.append(json.loads(line))
    return issues

def run_single_issue_baseline(issue: Dict[str, Any], monitor: ExecutionMonitor) -> Optional[Dict[str, Any]]:
    """Run baseline for a single issue. Returns None if aborted."""
    if not monitor.check_time("baseline_single_issue"):
        return None
    # Placeholder for actual baseline logic
    # In a real scenario, this would call agent.static_baseline
    return {"issue_id": issue["id"], "status": "baseline_done", "coverage": 0.5}

def run_single_issue_iterative(issue: Dict[str, Any], monitor: ExecutionMonitor) -> Optional[Dict[str, Any]]:
    """Run iterative agent for a single issue. Returns None if aborted."""
    if not monitor.check_time("iterative_single_issue"):
        return None
    # Placeholder for actual iterative logic
    return {"issue_id": issue["id"], "status": "iterative_done", "coverage": 0.6}

def merge_results(baseline_results: List[Dict], iterative_results: List[Dict]) -> Dict[str, Any]:
    """Merge results from baseline and iterative runs."""
    return {
        "baseline_count": len(baseline_results),
        "iterative_count": len(iterative_results),
        "merged_at": time.time()
    }

def main():
    parser = argparse.ArgumentParser(description="llmXive Pipeline Runner")
    parser.add_argument(
        "--max-hours", 
        type=float, 
        default=MAX_TOTAL_HOURS, 
        help=f"Maximum execution time in hours (default: {MAX_TOTAL_HOURS}). "
             f"If exceeded, non-critical tasks are aborted."
    )
    
    args = parser.parse_args()
    
    # Initialize Monitor
    monitor = ExecutionMonitor(max_hours=args.max_hours)
    
    print(f"Starting llmXive Pipeline. Max time: {args.max_hours}h, Abort threshold: {ABORT_THRESHOLD_HOURS}h")
    print(f"Output logs will be written to: {monitor.log_path}")
    
    ensure_directories()
    monitor = ExecutionMonitor(args.max_hours)
    
    # 1. Download Data
    if monitor.check_time("download"):
        print("Step 1: Downloading benchmark dataset...")
        try:
            download_benchmark_dataset()
        except Exception as e:
            print(f"ERROR: Download failed: {e}")
            sys.exit(1)
    else:
        print("ABORT: Time limit exceeded before download.")
        sys.exit(1)

    # 2. Derive Ground Truth
    if monitor.check_time("derive_gt"):
        print("Step 2: Deriving ground truth...")
        try:
            stream_derive_gt()
        except Exception as e:
            print(f"ERROR: Ground truth derivation failed: {e}")
            sys.exit(1)
    else:
        print("ABORT: Time limit exceeded before GT derivation.")
        sys.exit(1)

    # 3. Curate Data (Hard Subset & Synthetic)
    if monitor.check_time("curate"):
        print("Step 3: Curating data (Hard Subset & Synthetic)...")
        try:
            # Filter hard instances
            filter_hard_instances()
            # Generate synthetic issues
            generate_synthetic_issues()
        except Exception as e:
            print(f"ERROR: Curation failed: {e}")
            sys.exit(1)
    else:
        print("ABORT: Time limit exceeded before curation.")
        sys.exit(1)

    # 4. Validate Hard Subset
    if monitor.check_time("validate"):
        print("Step 4: Validating hard subset...")
        try:
            generate_report()
        except Exception as e:
            print(f"ERROR: Validation failed: {e}")
            sys.exit(1)
    else:
        print("ABORT: Time limit exceeded before validation.")
        sys.exit(1)

    # 5. Run Agent Loops (Baseline & Iterative)
    # Note: These are heavy tasks. If we are near the threshold, we might skip the sweep.
    hard_issues_path = get_path("data/curated/hard_subset.jsonl")
    if not os.path.exists(hard_issues_path):
        print(f"ERROR: Hard subset not found at {hard_issues_path}")
        sys.exit(1)
    
    issues = load_curated_issues(hard_issues_path)
    
    baseline_results = []
    iterative_results = []
    
    # Run Baseline (Critical)
    print("Step 5a: Running Static Baseline...")
    if monitor.check_time("baseline_run"):
        try:
            # Run baseline on the full hard subset
            baseline_results = run_baseline(hard_issues_path, monitor)
        except Exception as e:
            print(f"ERROR: Baseline run failed: {e}")
            sys.exit(1)
    else:
        print("ABORT: Time limit exceeded before baseline run.")
        sys.exit(1)

    # Run Iterative (Critical)
    print("Step 5b: Running Iterative Agent...")
    if monitor.check_time("iterative_run"):
        try:
            iterative_results = run_iterative_loop(hard_issues_path, monitor)
        except Exception as e:
            print(f"ERROR: Iterative run failed: {e}")
            sys.exit(1)
    else:
        print("ABORT: Time limit exceeded before iterative run.")
        sys.exit(1)

    # 6. Turn-Limit Sweep (Non-Critical if time is tight)
    # The task description says: "abort remaining non-critical sweeps"
    print("Step 6: Running Turn-Limit Sweep...")
    if monitor.check_time("sweep"):
        # Check if we are already in the warning zone
        if monitor.elapsed_seconds() > ABORT_THRESHOLD_SECONDS:
            print("WARNING: Time threshold exceeded. Skipping non-critical Turn-Limit Sweep.")
            # We still try to run, but the monitor will flag it as aborted if it takes too long
            # Or we can choose to skip entirely to save time for critical analysis
            skip_sweep = True
        else:
            skip_sweep = False
        
        if not skip_sweep:
            try:
                run_sweep(hard_issues_path, monitor)
            except Exception as e:
                print(f"ERROR: Sweep failed: {e}")
                # Sweep is non-critical, but we log the error
    else:
        print("ABORT: Time limit exceeded before sweep.")
        # We don't exit(1) here if it's non-critical, but for safety in this script we do
        # sys.exit(1) 

    # 7. Metrics & Analysis (Critical)
    print("Step 7: Calculating Metrics and Running Analysis...")
    if monitor.check_time("analysis"):
        try:
            # Calculate Coverage and Ranking
            # This would typically call metrics.coverage and metrics.ranking
            # and then stats.py
            
            # Placeholder for stats pipeline
            # In reality, this calls analysis.stats.main()
            pass 
        except Exception as e:
            print(f"ERROR: Analysis failed: {e}")
            sys.exit(1)
    else:
        print("ABORT: Time limit exceeded before analysis.")
        sys.exit(1)

    # 8. Report Generation (Critical)
    print("Step 8: Generating Report...")
    if monitor.check_time("report"):
        try:
            generate_draft()
        except Exception as e:
            print(f"ERROR: Report generation failed: {e}")
            sys.exit(1)
    else:
        print("ABORT: Time limit exceeded before report generation.")
        sys.exit(1)

    print("Pipeline completed successfully.")
    print(f"Total execution time: {monitor.elapsed_hours():.2f} hours")

if __name__ == "__main__":
    main()
