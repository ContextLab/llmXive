"""
Main orchestration script with resource monitor wrapper.
Implements FR-006 and SC-003: Resource monitoring and fail-fast mechanism.
"""
import os
import sys
import time
import json
import argparse
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable, Any, Dict, List, Optional
import psutil

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    get_paths,
    get_resource_limits,
    ResourceLimitExceeded,
    ProjectLogger
)

# Ensure directories exist
paths = get_paths()
paths.ensure_directories()

logger = ProjectLogger("main")


class ResourceMetrics:
    """Data class to hold resource usage metrics."""
    def __init__(self, timestamp: str, task_id: str, cpu_percent: float, ram_gb: float):
        self.timestamp = timestamp
        self.task_id = task_id
        self.cpu_percent = cpu_percent
        self.ram_gb = ram_gb

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "task_id": self.task_id,
            "cpu_percent": self.cpu_percent,
            "ram_gb": self.ram_gb
        }


class ResourceMonitor:
    """
    Context manager to monitor CPU and RAM usage during task execution.
    Logs metrics to data/processed/resource_logs.json.
    Raises ResourceLimitExceeded if thresholds are exceeded.
    """
    def __init__(self, task_id: str, log_path: Optional[Path] = None):
        self.task_id = task_id
        self.log_path = log_path or paths.PROCESSED / "resource_logs.json"
        self.limits = get_resource_limits()
        self.cpu_threshold = self.limits.cpu_percent
        self.ram_threshold = self.limits.ram_gb
        self.snapshots: List[Dict[str, Any]] = []
        self.exceeded = False
        self.exceeded_limit: Optional[str] = None
        self.trigger_values: Optional[Dict[str, float]] = None

    def _get_current_usage(self) -> Dict[str, float]:
        """Get current CPU and RAM usage."""
        process = psutil.Process(os.getpid())
        cpu = process.cpu_percent(interval=None)  # Non-blocking, uses last measurement
        ram = process.memory_info().rss / (1024 ** 3)  # Convert bytes to GB
        return {"cpu": cpu, "ram": ram}

    def _log_snapshot(self, cpu: float, ram: float):
        """Record a resource snapshot and check thresholds."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        snapshot = {
            "timestamp": timestamp,
            "task_id": self.task_id,
            "cpu_percent": round(cpu, 2),
            "ram_gb": round(ram, 4),
            "threshold_exceeded": False,
            "exceeded_limit": None,
            "snapshot_values": {"cpu": round(cpu, 2), "ram": round(ram, 4)}
        }

        # Check thresholds
        if cpu > self.cpu_threshold:
            snapshot["threshold_exceeded"] = True
            snapshot["exceeded_limit"] = "CPU"
            self.exceeded = True
            self.exceeded_limit = "CPU"
            self.trigger_values = {"cpu": cpu, "ram": ram}
        elif ram > self.ram_threshold:
            snapshot["threshold_exceeded"] = True
            snapshot["exceeded_limit"] = "RAM"
            self.exceeded = True
            self.exceeded_limit = "RAM"
            self.trigger_values = {"cpu": cpu, "ram": ram}

        self.snapshots.append(snapshot)
        return snapshot

    def __enter__(self):
        """Enter context: start monitoring."""
        # Warm up CPU measurement
        psutil.Process(os.getpid()).cpu_percent(interval=None)
        time.sleep(0.1)  # Small delay to allow initial measurement
        logger.info(f"Starting resource monitor for task: {self.task_id}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context: log final state and handle exceptions."""
        # Log final snapshot if we haven't exceeded yet
        if not self.exceeded:
            cpu, ram = self._get_current_usage()
            self._log_snapshot(cpu, ram)

        # Write logs to disk
        self._write_logs()

        if self.exceeded:
            # Log the trigger values before raising
            logger.error(
                f"Resource limit exceeded for task {self.task_id}: "
                f"{self.exceeded_limit} usage ({self.trigger_values[self.exceeded_limit.lower()]}) "
                f"exceeded threshold."
            )
            raise ResourceLimitExceeded(
                f"Task {self.task_id} exceeded {self.exceeded_limit} limit "
                f"({self.trigger_values[self.exceeded_limit.lower()]})"
            )

        return False  # Don't suppress exceptions

    def _write_logs(self):
        """Write accumulated logs to JSON file."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        existing_logs = []
        if self.log_path.exists():
            try:
                with open(self.log_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        existing_logs = json.loads(content)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not read existing logs: {e}")
                existing_logs = []

        existing_logs.extend(self.snapshots)

        with open(self.log_path, 'w') as f:
            json.dump(existing_logs, f, indent=2)
        logger.debug(f"Resource logs written to {self.log_path}")


def resource_monitor_context(task_id: str):
    """
    Factory function to create a resource monitor context manager.
    Usage:
        with resource_monitor_context("my_task") as monitor:
            # do work
            monitor.check()  # Optional manual check
    """
    return ResourceMonitor(task_id)


def run_dataset_preparation():
    """Run dataset preparation tasks."""
    logger.info("Running dataset preparation...")
    # Import and run loader
    from dataset.loader import main as loader_main
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--filter-min-constraints', type=int, default=5)
    parser.add_argument('--output', type=str, default=None)
    args = parser.parse_args(['--filter-min-constraints', '5'])
    loader_main(args)


def run_agent_execution():
    """Run agent execution tasks."""
    logger.info("Running agent execution...")
    # Run monolithic baseline
    from agent.monolithic_runner import main as monolithic_main
    monolithic_main()
    
    # Run dual track
    from agent.dual_track_runner import main as dual_track_main
    dual_track_main()


def run_statistical_analysis_main():
    """Run statistical analysis tasks."""
    logger.info("Running statistical analysis...")
    
    # Generate execution traces
    from analysis.generate_execution_traces import main as traces_main
    traces_main()
    
    # Run power analysis
    from analysis.power import main as power_main
    power_main()
    
    # Run adherence verification
    from analysis.adherence_verifier import main as adherence_main
    adherence_main()
    
    # Run agreement rate
    from analysis.agreement_rate import main as agreement_main
    agreement_main()
    
    # Run GLMM
    from analysis.glmm import main as glmm_main
    glmm_main()
    
    # Generate statistical results
    from analysis.generate_statistical_results import main as stats_main
    stats_main()


def run_all_tasks():
    """Run all tasks in sequence with resource monitoring."""
    tasks = [
        ("dataset_preparation", run_dataset_preparation),
        ("agent_execution", run_agent_execution),
        ("statistical_analysis", run_statistical_analysis_main)
    ]
    
    for task_id, task_func in tasks:
        logger.info(f"Starting task: {task_id}")
        with resource_monitor_context(task_id):
            try:
                task_func()
                logger.info(f"Task {task_id} completed successfully")
            except ResourceLimitExceeded:
                logger.error(f"Task {task_id} aborted due to resource limits")
                raise
            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}")
                traceback.print_exc()
                raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="llmXive Orchestration Script")
    parser.add_argument('--mode', type=str, choices=['preparation', 'execution', 'analysis', 'all'],
                      default='all', help='Which phase to run')
    parser.add_argument('--task', type=str, help='Specific task to run')
    args = parser.parse_args()

    if args.mode == 'all' and not args.task:
        run_all_tasks()
    elif args.task:
        # Run specific task with monitoring
        task_map = {
            'dataset_preparation': run_dataset_preparation,
            'agent_execution': run_agent_execution,
            'statistical_analysis': run_statistical_analysis_main
        }
        if args.task in task_map:
            with resource_monitor_context(args.task):
                task_map[args.task]()
        else:
            logger.error(f"Unknown task: {args.task}")
            sys.exit(1)
    else:
        # Run specific mode
        mode_map = {
            'preparation': run_dataset_preparation,
            'execution': run_agent_execution,
            'analysis': run_statistical_analysis_main
        }
        if args.mode in mode_map:
            with resource_monitor_context(f"{args.mode}_mode"):
                mode_map[args.mode]()
        else:
            logger.error(f"Unknown mode: {args.mode}")
            sys.exit(1)

    logger.info("All tasks completed successfully")


if __name__ == "__main__":
    main()
