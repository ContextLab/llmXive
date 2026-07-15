import json
import sys
import time
import argparse
import gc
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import local modules based on project structure
# Assuming standard project layout where code/ is the root for imports or PYTHONPATH is set
try:
    from config import get_config_summary
    from data.curate import filter_hard_instances, load_derived_ground_truth
    from data.validate_hard import load_hard_subset
    from agent.base import run_baseline
    from agent.iterative import run_iterative_agent
    from agent.sweep_turns import run_sweep
    from utils.hash_artifacts import hash_directory, generate_manifest
except ImportError as e:
    # Fallback for direct execution from project root
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config_summary
    from data.curate import filter_hard_instances, load_derived_ground_truth
    from data.validate_hard import load_hard_subset
    from agent.base import run_baseline
    from agent.iterative import run_iterative_agent
    from agent.sweep_turns import run_sweep
    from utils.hash_artifacts import hash_directory, generate_manifest


class ExecutionMonitor:
    """
    Runtime monitor to track total execution time and enforce SC-005.
    If elapsed time > 5.5 hours, abort remaining non-critical sweeps
    or reduce sample size to ensure completion within 6 hours.
    """
    def __init__(self, start_time: Optional[float] = None, max_duration_hours: float = 5.5):
        self.start_time = start_time if start_time is not None else time.time()
        self.max_duration_seconds = max_duration_hours * 3600
        self.check_interval_seconds = 60  # Check every minute
        self.last_check = self.start_time
        self.is_aborted = False
        self.reason = None

    def check(self, current_phase: str = "general") -> bool:
        """
        Check if execution time exceeds the limit.
        Returns True if execution should continue, False if it should abort.
        """
        now = time.time()
        elapsed = now - self.start_time
        elapsed_hours = elapsed / 3600

        # Only check at intervals to avoid overhead
        if now - self.last_check < self.check_interval_seconds:
            return not self.is_aborted

        self.last_check = now

        if elapsed > self.max_duration_seconds:
            self.is_aborted = True
            self.reason = f"Time limit exceeded: {elapsed_hours:.2f} hours > {self.max_duration_hours:.1f} hours"
            print(f"[ExecutionMonitor] ABORT: {self.reason}")
            return False

        # Log progress periodically
        remaining = self.max_duration_seconds - elapsed
        print(f"[ExecutionMonitor] Progress: {elapsed_hours:.2f}h elapsed, {remaining/3600:.2f}h remaining ({current_phase})")
        return True

    def get_status(self) -> Dict[str, Any]:
        elapsed = time.time() - self.start_time
        return {
            "elapsed_seconds": elapsed,
            "elapsed_hours": elapsed / 3600,
            "max_duration_hours": self.max_duration_hours / 3600,
            "is_aborted": self.is_aborted,
            "reason": self.reason
        }

def load_curated_issues() -> List[Dict[str, Any]]:
    """Load the curated hard subset for execution."""
    curated_path = Path("data/curated/hard_subset.jsonl")
    if not curated_path.exists():
        raise FileNotFoundError(f"Curated dataset not found at {curated_path}. Run data curate tasks first.")
    
    issues = []
    with open(curated_path, 'r') as f:
        for line in f:
            if line.strip():
                issues.append(json.loads(line))
    return issues

def run_single_issue_baseline(issue: Dict[str, Any], monitor: ExecutionMonitor) -> Optional[Dict[str, Any]]:
    """Run baseline agent on a single issue if time permits."""
    if not monitor.check("baseline_single"):
        return None
    try:
        # Placeholder for actual baseline execution logic
        # In a real scenario, this would call the baseline agent
        result = run_baseline([issue])
        return result[0] if result else None
    except Exception as e:
        print(f"[Baseline] Error processing issue {issue.get('issue_id', 'unknown')}: {e}")
        return None

def run_single_issue_iterative(issue: Dict[str, Any], monitor: ExecutionMonitor) -> Optional[Dict[str, Any]]:
    """Run iterative agent on a single issue if time permits."""
    if not monitor.check("iterative_single"):
        return None
    try:
        # Placeholder for actual iterative execution logic
        result = run_iterative_agent([issue])
        return result[0] if result else None
    except Exception as e:
        print(f"[Iterative] Error processing issue {issue.get('issue_id', 'unknown')}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="llmXive Execution Pipeline with Runtime Monitoring")
    parser.add_argument('--mode', choices=['baseline', 'iterative', 'full', 'sweep'], default='full',
                        help='Execution mode: baseline, iterative, full (both), or sweep')
    parser.add_argument('--max-hours', type=float, default=5.5,
                        help='Maximum execution time in hours before aborting non-critical tasks')
    parser.add_argument('--sample-size', type=int, default=None,
                        help='Override sample size for sweep mode')
    args = parser.parse_args()

    print("Starting llmXive Execution Pipeline...")
    config_summary = get_config_summary()
    print(f"Config: {config_summary}")

    monitor = ExecutionMonitor(max_duration_hours=args.max_hours)
    
    # Load issues
    try:
        issues = load_curated_issues()
        print(f"Loaded {len(issues)} issues from curated dataset.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Determine execution plan
    baseline_results = []
    iterative_results = []
    sweep_results = []

    if args.mode in ['baseline', 'full']:
        print("Running Baseline Agent...")
        for i, issue in enumerate(issues):
            if not monitor.check("baseline_batch"):
                print("Aborting baseline due to time limit.")
                break
            result = run_single_issue_baseline(issue, monitor)
            if result:
                baseline_results.append(result)
            # Clean up memory periodically
            if i % 5 == 0:
                gc.collect()

    if args.mode in ['iterative', 'full']:
        print("Running Iterative Agent...")
        for i, issue in enumerate(issues):
            if not monitor.check("iterative_batch"):
                print("Aborting iterative due to time limit.")
                break
            result = run_single_issue_iterative(issue, monitor)
            if result:
                iterative_results.append(result)
            if i % 5 == 0:
                gc.collect()

    if args.mode == 'sweep':
        print("Running Turn Limit Sweep...")
        sample_size = args.sample_size if args.sample_size else min(20, len(issues))
        if not monitor.check("sweep_start"):
            print("Aborting sweep due to time limit.")
        else:
            # Reduce sample size if time is critical
            if monitor.max_duration_seconds - (time.time() - monitor.start_time) < 300:
                sample_size = min(sample_size, 5)
                print(f"Reducing sweep sample size to {sample_size} due to time pressure.")
            
            sweep_issues = issues[:sample_size]
            sweep_results = run_sweep(sweep_issues, monitor)
            monitor.check("sweep_end")

    # Save results
    results_dir = Path("data/results")
    results_dir.mkdir(exist_ok=True)

    if baseline_results:
        with open(results_dir / "baseline_results.json", 'w') as f:
            json.dump(baseline_results, f, indent=2)
        print(f"Saved {len(baseline_results)} baseline results.")

    if iterative_results:
        with open(results_dir / "iterative_results.json", 'w') as f:
            json.dump(iterative_results, f, indent=2)
        print(f"Saved {len(iterative_results)} iterative results.")

    if sweep_results:
        with open(results_dir / "sweep_results.json", 'w') as f:
            json.dump(sweep_results, f, indent=2)
        print(f"Saved {len(sweep_results)} sweep results.")

    # Final status
    final_status = monitor.get_status()
    with open(results_dir / "execution_status.json", 'w') as f:
        json.dump(final_status, f, indent=2)
    
    print(f"Pipeline finished. Status: {final_status}")
    
    # Hash artifacts if not aborted
    if not monitor.is_aborted:
        try:
            hash_directory(results_dir)
            print("Artifacts hashed successfully.")
        except Exception as e:
            print(f"Warning: Failed to hash artifacts: {e}")

if __name__ == "__main__":
    main()