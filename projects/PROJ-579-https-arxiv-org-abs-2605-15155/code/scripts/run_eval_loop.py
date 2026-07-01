import os
import sys
import json
import subprocess
import time
import signal
from pathlib import Path

# Ensure we can import from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.run_eval_with_timeout import run_task_with_timeout, run_evaluation_suite, calculate_success_rate

def main():
    """
    T024: Ensure the evaluation loop attempts to solve each task and records success/failure.
    
    This script wraps the evaluation logic to explicitly attempt solving each task
    and record the outcome (success/failure) for every task attempted.
    """
    # Configuration matching T022/T023
    num_tasks = 5
    task_timeout = 60  # seconds
    
    # Output paths
    output_dir = Path("outputs/logs")
    output_dir.mkdir(parents=True, exist_ok=True)
    eval_log_path = output_dir / "eval_log.json"
    
    print(f"Starting evaluation loop for {num_tasks} tasks with {task_timeout}s timeout each...")
    
    # Run the evaluation suite which internally calls run_task_with_timeout for each task
    # The run_evaluation_suite function is expected to handle the loop over tasks
    results = run_evaluation_suite(
        num_tasks=num_tasks,
        task_timeout=task_timeout
    )
    
    # Process results to record success/failure for each task
    task_results = []
    total_successes = 0
    
    for i, result in enumerate(results):
        task_id = result.get("task_id", f"task_{i}")
        success = result.get("success", False)
        reason = result.get("reason", "Unknown")
        duration = result.get("duration", 0.0)
        
        task_results.append({
            "task_id": task_id,
            "success": success,
            "reason": reason,
            "duration": duration
        })
        
        if success:
            total_successes += 1
        
        status = "SUCCESS" if success else "FAILURE"
        print(f"Task {task_id}: {status} (Reason: {reason})")
    
    # Calculate success rate
    success_rate = calculate_success_rate(results)
    
    # Prepare final log entry
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "num_tasks": num_tasks,
        "task_timeout": task_timeout,
        "total_successes": total_successes,
        "success_rate": success_rate,
        "tasks": task_results
    }
    
    # Write to log file
    with open(eval_log_path, "w") as f:
        json.dump(log_entry, f, indent=2)
    
    print(f"Evaluation complete. Success Rate: {success_rate:.2%}")
    print(f"Results written to {eval_log_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())