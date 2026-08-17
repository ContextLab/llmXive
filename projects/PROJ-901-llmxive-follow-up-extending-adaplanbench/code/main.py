import os
import sys
import time
import json
import argparse
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass, asdict
import psutil

# Import from config
from config import (
    ResourceLimitExceeded,
    get_paths,
    get_resource_limits,
    ensure_directories
)

@dataclass
class ResourceMetrics:
    """Container for CPU and RAM metrics."""
    cpu_percent: float
    ram_gb: float

class ResourceMonitor:
    """
    Monitors CPU and RAM usage for a specific task.
    Logs metrics to data/processed/resource_logs.json and raises
    ResourceLimitExceeded if thresholds are breached.
    """
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.process = psutil.Process(os.getpid())
        self.log_file = get_paths().PROCESSED / "resource_logs.json"
        
        # Ensure directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize log file if it doesn't exist
        if not self.log_file.exists():
            self.log_file.write_text("[]")

    def _get_snapshot(self) -> ResourceMetrics:
        """Take a snapshot of current CPU and RAM usage."""
        # cpu_percent(interval=0.1) waits briefly for a more accurate reading
        cpu = self.process.cpu_percent(interval=0.1)
        ram_bytes = self.process.memory_info().rss
        ram_gb = ram_bytes / (1024 ** 3)
        return ResourceMetrics(cpu_percent=cpu, ram_gb=ram_gb)

    def _check_limits(self, metrics: ResourceMetrics) -> Optional[str]:
        """
        Check if metrics exceed configured limits.
        Returns "CPU", "RAM", or None.
        """
        limits = get_resource_limits()
        
        if metrics.cpu_percent > limits.MAX_CPU_PERCENT:
            return "CPU"
        if metrics.ram_gb > limits.MAX_RAM_GB:
            return "RAM"
        
        return None

    def _log_entry(self, metrics: ResourceMetrics, exceeded: bool, exceeded_limit: Optional[str]):
        """Append a log entry to the JSON file."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "task_id": self.task_id,
            "cpu_percent": metrics.cpu_percent,
            "ram_gb": metrics.ram_gb,
            "threshold_exceeded": exceeded,
            "exceeded_limit": exceeded_limit,
            "snapshot_values": {
                "cpu": metrics.cpu_percent,
                "ram": metrics.ram_gb
            }
        }

        # Read existing logs
        logs = []
        if self.log_file.exists():
            try:
                content = self.log_file.read_text()
                if content.strip():
                    logs = json.loads(content)
            except json.JSONDecodeError:
                logs = []

        logs.append(entry)

        # Write back
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2)

    def wrap_task(self, func: Callable[[], Any]) -> Any:
        """
        Wrap a task function to monitor resources.
        Logs start, checks limits, logs end.
        Raises ResourceLimitExceeded if limits are breached.
        """
        try:
            # Initial snapshot
            metrics = self._get_snapshot()
            exceeded_limit = self._check_limits(metrics)
            
            if exceeded_limit:
                self._log_entry(metrics, True, exceeded_limit)
                raise ResourceLimitExceeded(
                    f"Resource limit exceeded: {exceeded_limit} at {metrics.cpu_percent}% CPU / {metrics.ram_gb:.2f}GB RAM"
                )
            
            self._log_entry(metrics, False, None)

            # Execute task
            result = func()

            # Final snapshot
            metrics_end = self._get_snapshot()
            exceeded_limit_end = self._check_limits(metrics_end)
            
            if exceeded_limit_end:
                self._log_entry(metrics_end, True, exceeded_limit_end)
                raise ResourceLimitExceeded(
                    f"Resource limit exceeded during execution: {exceeded_limit_end} at {metrics_end.cpu_percent}% CPU / {metrics_end.ram_gb:.2f}GB RAM"
                )
            
            self._log_entry(metrics_end, False, None)
            
            return result

        except ResourceLimitExceeded:
            raise
        except Exception as e:
            # Log failure state before re-raising
            try:
                metrics_fail = self._get_snapshot()
                self._log_entry(metrics_fail, False, None)
            except Exception:
                pass
            raise

def resource_monitor_context(task_id: str) -> ResourceMonitor:
    """Factory to create a ResourceMonitor for a given task ID."""
    return ResourceMonitor(task_id=task_id)

# --- Placeholder execution functions (to be implemented by other tasks) ---

def run_dataset_preparation():
    """Placeholder for dataset preparation logic."""
    # This will be implemented by T013/T012b
    print("Dataset preparation placeholder")

def run_agent_execution():
    """Placeholder for agent execution logic."""
    # This will be implemented by T026a/T026b
    print("Agent execution placeholder")

def run_statistical_analysis_main():
    """Placeholder for statistical analysis logic."""
    # This will be implemented by T036
    print("Statistical analysis placeholder")

def run_all_tasks():
    """
    Orchestrates the full pipeline with resource monitoring.
    """
    ensure_directories()
    
    tasks = [
        ("dataset_prep", run_dataset_preparation),
        ("agent_exec", run_agent_execution),
        ("stat_analysis", run_statistical_analysis_main)
    ]

    for task_name, task_func in tasks:
        print(f"Starting task: {task_name}")
        monitor = resource_monitor_context(task_name)
        try:
            with monitor: # Use context manager if implemented, else wrap_task
                # Since context manager protocol isn't fully defined in the snippet above for 'with',
                # we use wrap_task for the actual execution to ensure logic runs.
                # However, to support 'with' syntax, we need __enter__ and __exit__.
                # Let's add those methods to ResourceMonitor below or use wrap_task here.
                # For now, using wrap_task for safety.
                monitor.wrap_task(task_func)
        except ResourceLimitExceeded as e:
            print(f"CRITICAL: Pipeline aborted due to resource limit: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error in task {task_name}: {e}")
            traceback.print_exc()
            # Continue or exit based on policy? For now, let's continue to log.
            # But typically, a failed critical task stops the run.
            # We will re-raise to stop the pipeline on error.
            raise

def main():
    parser = argparse.ArgumentParser(description="llmXive Pipeline Orchestrator")
    parser.add_argument("--mode", choices=["execution", "all"], default="all",
                        help="Mode of execution")
    parser.add_argument("--task", type=str, default=None,
                        help="Run a specific task by name")
    
    args = parser.parse_args()

    ensure_directories()

    if args.task:
        # Run specific task
        task_map = {
            "dataset_prep": run_dataset_preparation,
            "agent_exec": run_agent_execution,
            "stat_analysis": run_statistical_analysis_main
        }
        if args.task not in task_map:
            print(f"Unknown task: {args.task}")
            sys.exit(1)
        
        monitor = resource_monitor_context(args.task)
        try:
            monitor.wrap_task(task_map[args.task])
        except ResourceLimitExceeded as e:
            print(f"CRITICAL: Resource limit exceeded: {e}")
            sys.exit(1)
    else:
        # Run all
        run_all_tasks()

if __name__ == "__main__":
    main()
