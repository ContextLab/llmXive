"""
Main orchestration script for the llmXive AdaPlanBench extension pipeline.

This script orchestrates the execution of the three main phases:
1. Dataset Preparation (filtering and validation)
2. Agent Execution (Dual-Track and Monolithic)
3. Statistical Analysis (Power, GLMM, Agreement)

It includes a ResourceMonitor wrapper to track CPU and RAM usage per task
and fails fast if resource limits (defined in config.py) are exceeded.
"""

import os
import sys
import time
import resource
import json
import csv
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List

# Project imports
from config import Paths, ResourceLimits, set_all_seeds, AnalysisConfig
from dataset.loader import load_adaplanbench, filter_progressive_constraints, save_filtered_dataset
from dataset.add_constraint_count import main as add_constraint_count_main
from dataset.validate_subset import validate_subset
from agent.dual_track import run_dual_track_experiment
from agent.monolithic import main as run_monolithic_main
from analysis.power import run_power_analysis
from analysis.generate_execution_traces import main as generate_traces_main
from analysis.generate_statistical_results import main as generate_stat_results_main
from analysis.agreement_rate import run_agreement_analysis


class ResourceMonitor:
    """
    Monitors CPU and RAM usage for a specific task execution.
    Fails fast if limits defined in config.ResourceLimits are exceeded.
    """

    def __init__(self, limits: ResourceLimits, task_name: str):
        self.limits = limits
        self.task_name = task_name
        self.start_time: Optional[float] = None
        self.start_cpu: Optional[float] = None
        self.start_memory: Optional[int] = None
        self.metrics: Dict[str, Any] = {}

    def _get_current_cpu_time(self) -> float:
        """Returns total CPU time (user + system) in seconds."""
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_utime + usage.ru_stime

    def _get_current_memory_mb(self) -> float:
        """Returns current resident set size (RSS) in MB."""
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux/macOS
        return usage.ru_maxrss / 1024.0

    def start(self):
        """Start monitoring resources."""
        self.start_time = time.time()
        self.start_cpu = self._get_current_cpu_time()
        self.start_memory = self._get_current_memory_mb()
        self.metrics = {
            "task": self.task_name,
            "start_time_iso": datetime.utcnow().isoformat(),
            "status": "running"
        }

    def check(self) -> Dict[str, Any]:
        """
        Check current resource usage against limits.
        If limits are exceeded, raises a RuntimeError with details.
        Returns current metrics.
        """
        current_time = time.time()
        current_cpu = self._get_current_cpu_time()
        current_memory = self._get_current_memory_mb()

        elapsed_time = current_time - self.start_time
        cpu_usage = current_cpu - self.start_cpu
        memory_delta = current_memory - self.start_memory
        peak_memory = current_memory  # Approximation using current max

        self.metrics.update({
            "elapsed_time_sec": elapsed_time,
            "cpu_time_sec": cpu_usage,
            "current_memory_mb": current_memory,
            "peak_memory_mb": peak_memory
        })

        # Check Time Limit
        if self.limits.max_time_sec and elapsed_time > self.limits.max_time_sec:
            raise RuntimeError(
                f"[{self.task_name}] Time limit exceeded: {elapsed_time:.2f}s > {self.limits.max_time_sec}s"
            )

        # Check Memory Limit
        if self.limits.max_memory_mb and peak_memory > self.limits.max_memory_mb:
            raise RuntimeError(
                f"[{self.task_name}] Memory limit exceeded: {peak_memory:.2f}MB > {self.limits.max_memory_mb}MB"
            )

        # Check CPU Limit (if configured as a hard cap on CPU seconds)
        if self.limits.max_cpu_sec and cpu_usage > self.limits.max_cpu_sec:
            raise RuntimeError(
                f"[{self.task_name}] CPU time limit exceeded: {cpu_usage:.2f}s > {self.limits.max_cpu_sec}s"
            )

        return self.metrics

    def stop(self):
        """Finalize monitoring and log results."""
        final_metrics = self.check()
        final_metrics["status"] = "completed"
        final_metrics["end_time_iso"] = datetime.utcnow().isoformat()
        self.metrics = final_metrics
        return final_metrics

def log_resource_metrics(metrics: Dict[str, Any], log_path: Path):
    """Appends resource metrics to a JSONL log file."""
    with open(log_path, 'a') as f:
        f.write(json.dumps(metrics) + '\n')

def run_dataset_preparation(resource_monitor: ResourceMonitor) -> bool:
    """
    Executes Phase 1 & 2 of the pipeline:
    1. Load raw dataset
    2. Filter for progressive constraints >= 5
    3. Add constraint_count column
    4. Validate subset
    """
    print(f"Starting Dataset Preparation: {resource_monitor.task_name}")
    resource_monitor.start()

    try:
        # 1. Load and Filter
        print("Loading and filtering AdaPlanBench dataset...")
        # The loader handles fetching and filtering
        # Note: We assume the dataset is fetched and filtered here.
        # In a real run, this might take a moment.
        # We call the main logic from the dataset module to ensure side effects (saving) happen.
        from dataset.loader import main as loader_main
        loader_main()

        # 2. Add Constraint Count
        print("Adding constraint_count column...")
        add_constraint_count_main()

        # 3. Validate Subset
        print("Validating subset...")
        validate_subset()

        # Check resources after heavy operations
        metrics = resource_monitor.check()
        print(f"Dataset Prep Resource Check: {metrics}")

        resource_monitor.stop()
        return True

    except Exception as e:
        resource_monitor.stop()
        resource_monitor.metrics["status"] = "failed"
        resource_monitor.metrics["error"] = str(e)
        print(f"Dataset Preparation FAILED: {e}")
        raise

def run_agent_execution(resource_monitor: ResourceMonitor) -> bool:
    """
    Executes Phase 3: Dual-Track and Monolithic agent execution.
    """
    print(f"Starting Agent Execution: {resource_monitor.task_name}")
    resource_monitor.start()

    try:
        # 1. Run Dual-Track
        print("Running Dual-Track Agent...")
        run_dual_track_experiment()

        # 2. Run Monolithic
        print("Running Monolithic Agent...")
        run_monolithic_main()

        # 3. Generate Execution Traces
        print("Generating Execution Traces...")
        generate_traces_main()

        metrics = resource_monitor.check()
        print(f"Agent Execution Resource Check: {metrics}")

        resource_monitor.stop()
        return True

    except Exception as e:
        resource_monitor.stop()
        resource_monitor.metrics["status"] = "failed"
        resource_monitor.metrics["error"] = str(e)
        print(f"Agent Execution FAILED: {e}")
        raise

def run_statistical_analysis(resource_monitor: ResourceMonitor) -> bool:
    """
    Executes Phase 4: Statistical analysis (Power, GLMM, Agreement).
    """
    print(f"Starting Statistical Analysis: {resource_monitor.task_name}")
    resource_monitor.start()

    try:
        # 1. Power Analysis
        print("Running Power Analysis...")
        run_power_analysis()

        # 2. Generate Statistical Results (GLMM)
        print("Running Statistical Analysis (GLMM)...")
        generate_stat_results_main()

        # 3. Agreement Rate
        print("Running Agreement Rate Analysis...")
        run_agreement_analysis()

        metrics = resource_monitor.check()
        print(f"Statistical Analysis Resource Check: {metrics}")

        resource_monitor.stop()
        return True

    except Exception as e:
        resource_monitor.stop()
        resource_monitor.metrics["status"] = "failed"
        resource_monitor.metrics["error"] = str(e)
        print(f"Statistical Analysis FAILED: {e}")
        raise

def run_all_tasks():
    """
    Orchestrates the full pipeline with resource monitoring.
    """
    from config import Paths, ResourceLimits

    paths = Paths()
    limits = ResourceLimits()
    log_path = paths.processed_dir / "resource_metrics.jsonl"

    # Ensure log file exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.touch()

    tasks = [
        ("Dataset Preparation", run_dataset_preparation),
        ("Agent Execution", run_agent_execution),
        ("Statistical Analysis", run_statistical_analysis)
    ]

    all_success = True

    for name, task_func in tasks:
        monitor = ResourceMonitor(limits, name)
        try:
            success = task_func(monitor)
            log_resource_metrics(monitor.metrics, log_path)
            if not success:
                all_success = False
        except Exception as e:
            print(f"Critical failure in {name}: {e}")
            all_success = False
            # Continue to next task or break?
            # Usually in a pipeline, if one fails, we might stop,
            # but the prompt asks to log per task. Let's log and continue
            # if the failure is recoverable, but for this script,
            # a failure in a phase usually blocks the next.
            # We will break to prevent cascading errors on missing files.
            break

    if all_success:
        print("Pipeline completed successfully.")
    else:
        print("Pipeline completed with errors.")
        sys.exit(1)

def main():
    """Entry point."""
    print("llmXive AdaPlanBench Extension Pipeline")
    print("---------------------------------------")
    run_all_tasks()

if __name__ == "__main__":
    main()