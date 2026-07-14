"""
Main orchestration script for llmXive research pipeline.

Implements:
- Runtime memory monitoring and adaptive throttling
- Time-based execution control (SC-005: 6-hour limit)
- Orchestration of baseline and iterative agent runs
"""
import json
import sys
import time
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Import memory management utilities
from utils.memory_manager import (
    MemoryMonitor, 
    get_global_monitor, 
    batch_process_with_memory_control,
    MemoryExhaustedError,
    get_memory_profile
)
from config import get_config_summary

# Import agent components
from agent.base import load_curated_dataset, run_baseline
from agent.iterative import run_iterative_agent

# Constants for execution control
MAX_EXECUTION_HOURS = 6.0
WARNING_THRESHOLD_HOURS = 5.5
MEMORY_CHECK_INTERVAL = 10  # seconds

class ExecutionMonitor:
    """
    Monitors both time and memory constraints during execution.
    Implements SC-005: Abort non-critical operations if approaching time limit.
    """
    
    def __init__(self, max_hours: float = MAX_EXECUTION_HOURS):
        self.start_time = time.time()
        self.max_seconds = max_hours * 3600
        self.warning_seconds = WARNING_THRESHOLD_HOURS * 3600
        self.memory_monitor = get_global_monitor()
        self.is_critical_mode = False
    
    def get_elapsed_hours(self) -> float:
        """Get elapsed time in hours."""
        return (time.time() - self.start_time) / 3600
    
    def get_remaining_hours(self) -> float:
        """Get remaining time in hours."""
        elapsed = self.get_elapsed_hours()
        return max(0, self.max_seconds / 3600 - elapsed)
    
    def check_constraints(self) -> bool:
        """
        Check time and memory constraints.
        Returns True if execution should continue, False if it should abort.
        """
        # Check time
        if self.get_elapsed_hours() > self.max_hours:
            print(f"[WARN] Execution time exceeded limit: {self.get_elapsed_hours():.2f}h / {MAX_EXECUTION_HOURS}h", file=sys.stderr)
            return False
        
        # Enter warning mode
        if not self.is_critical_mode and self.get_elapsed_hours() > WARNING_THRESHOLD_HOURS:
            print(f"[WARN] Approaching time limit: {self.get_elapsed_hours():.2f}h / {MAX_EXECUTION_HOURS}h. "
                  f"Entering critical mode (reducing sample size).", file=sys.stderr)
            self.is_critical_mode = True
            # Log memory profile
            profile = get_memory_profile()
            print(f"[INFO] Memory profile: {profile}", file=sys.stderr)
        
        # Check memory
        try:
            if self.memory_monitor.check_and_throttle():
                if self.memory_monitor.get_current_usage_mb() > self.memory_monitor.limit_mb * 0.9:
                    print(f"[WARN] High memory usage: {self.memory_monitor.get_current_usage_mb():.1f}MB", file=sys.stderr)
        except MemoryExhaustedError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            return False
        
        return True
    
    def should_reduce_sample(self) -> bool:
        """Check if sample size should be reduced to meet time constraints."""
        return self.is_critical_mode

def load_curated_issues() -> List[Dict[str, Any]]:
    """Load curated issues from data/curated/hard_subset.jsonl."""
    data_path = Path("data/curated/hard_subset.jsonl")
    if not data_path.exists():
        raise FileNotFoundError(f"Curated dataset not found at {data_path}. "
                              "Run data curation tasks first.")
    
    issues = []
    with open(data_path, 'r') as f:
        for line in f:
            if line.strip():
                issues.append(json.loads(line))
    
    return issues

def run_single_issue_baseline(issue: Dict[str, Any], monitor: ExecutionMonitor) -> Optional[Dict[str, Any]]:
    """Run baseline agent on a single issue."""
    if not monitor.check_constraints():
        print(f"[ABORT] Skipping baseline for issue {issue.get('issue_id', 'unknown')} due to constraints.", file=sys.stderr)
        return None
    
    try:
        # Run baseline (static multi-query)
        result = run_baseline(issue)
        return result
    except Exception as e:
        print(f"[ERROR] Baseline failed for issue {issue.get('issue_id')}: {e}", file=sys.stderr)
        return None

def run_single_issue_iterative(issue: Dict[str, Any], monitor: ExecutionMonitor) -> Optional[Dict[str, Any]]:
    """Run iterative agent on a single issue."""
    if not monitor.check_constraints():
        print(f"[ABORT] Skipping iterative for issue {issue.get('issue_id', 'unknown')} due to constraints.", file=sys.stderr)
        return None
    
    try:
        # Run iterative agent
        result = run_iterative_agent(issue)
        return result
    except Exception as e:
        print(f"[ERROR] Iterative failed for issue {issue.get('issue_id')}: {e}", file=sys.stderr)
        return None

def main():
    """Main entry point for the research pipeline."""
    parser = argparse.ArgumentParser(description="llmXive Research Pipeline Orchestrator")
    parser.add_argument("--mode", choices=["baseline", "iterative", "both"], default="both",
                      help="Which agent mode to run")
    parser.add_argument("--limit", type=int, default=None,
                      help="Maximum number of issues to process (default: all)")
    parser.add_argument("--memory-limit", type=int, default=6500,
                      help="Memory limit in MB (default: 6500)")
    args = parser.parse_args()

    # Initialize memory monitor
    memory_monitor = MemoryMonitor(args.memory_limit)
    memory_monitor.start_monitoring(interval=MEMORY_CHECK_INTERVAL)

    # Initialize execution monitor
    exec_monitor = ExecutionMonitor()

    print(f"[INFO] Starting llmXive pipeline at {datetime.now().isoformat()}")
    print(f"[INFO] Config: {get_config_summary()}")
    print(f"[INFO] Memory limit: {args.memory_limit}MB, Time limit: {MAX_EXECUTION_HOURS}h")

    # Load dataset
    try:
        issues = load_curated_issues()
    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    # Apply limit if specified
    if args.limit:
        issues = issues[:args.limit]
        print(f"[INFO] Processing first {len(issues)} issues (limit: {args.limit})")

    results = {"baseline": [], "iterative": []}
    start_time = time.time()

    try:
        # Run baseline if requested
        if args.mode in ["baseline", "both"]:
            print(f"[INFO] Running baseline on {len(issues)} issues...")
            for i, issue in enumerate(issues):
                if not exec_monitor.check_constraints():
                    print(f"[WARN] Stopping baseline early due to constraints at issue {i+1}/{len(issues)}")
                    break
                
                result = run_single_issue_baseline(issue, exec_monitor)
                if result:
                    results["baseline"].append(result)
                
                if (i + 1) % 10 == 0:
                    print(f"[INFO] Baseline progress: {i+1}/{len(issues)}, "
                          f"Elapsed: {exec_monitor.get_elapsed_hours():.2f}h, "
                          f"Remaining: {exec_monitor.get_remaining_hours():.2f}h")

        # Run iterative if requested
        if args.mode in ["iterative", "both"]:
            print(f"[INFO] Running iterative agent on {len(issues)} issues...")
            for i, issue in enumerate(issues):
                if not exec_monitor.check_constraints():
                    print(f"[WARN] Stopping iterative early due to constraints at issue {i+1}/{len(issues)}")
                    break
                
                result = run_single_issue_iterative(issue, exec_monitor)
                if result:
                    results["iterative"].append(result)
                
                if (i + 1) % 10 == 0:
                    print(f"[INFO] Iterative progress: {i+1}/{len(issues)}, "
                          f"Elapsed: {exec_monitor.get_elapsed_hours():.2f}h, "
                          f"Remaining: {exec_monitor.get_remaining_hours():.2f}h")

    except KeyboardInterrupt:
        print("\n[WARN] Interrupted by user", file=sys.stderr)
    except MemoryExhaustedError as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
    finally:
        # Save results
        output_path = Path("data/results/pipeline_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        results["metadata"] = {
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "end_time": datetime.now().isoformat(),
            "elapsed_hours": exec_monitor.get_elapsed_hours(),
            "issues_total": len(issues),
            "issues_processed_baseline": len(results["baseline"]),
            "issues_processed_iterative": len(results["iterative"]),
            "memory_limit_mb": args.memory_limit,
            "time_limit_hours": MAX_EXECUTION_HOURS
        }
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"[INFO] Results saved to {output_path}")
        print(f"[INFO] Total elapsed time: {exec_monitor.get_elapsed_hours():.2f}h")
        
        # Stop memory monitoring
        memory_monitor.stop_monitoring()

    # Return success if we processed at least some data
    if results["baseline"] or results["iterative"]:
        sys.exit(0)
    else:
        print("[ERROR] No results generated", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
