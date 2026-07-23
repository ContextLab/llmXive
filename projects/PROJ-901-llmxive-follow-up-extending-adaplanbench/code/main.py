import os
import sys
import time
import resource
import json
import csv
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict

# Local imports based on provided API surface
from config import (
    Paths,
    ResourceLimits,
    ModelConfig,
    DatasetConfig,
    AnalysisConfig,
    get_paths,
    get_resource_limits,
    get_model_config,
    get_dataset_config,
    get_analysis_config,
    ensure_directories,
    ProjectLogger,
    get_logger
)
from dataset.loader import load_adaplanbench, verify_progressive_constraints, filter_progressive_constraints, save_filtered_dataset, main as loader_main
from analysis.power import run_power_analysis, main as power_main
from analysis.glmm import run_statistical_analysis, main as glmm_main
from analysis.generate_execution_traces import main as traces_main
from analysis.adherence_verifier import main as adherence_main
from analysis.agreement_rate import main as agreement_main
from agent.monolithic_runner import main as monolithic_main
from agent.dual_track_runner import main as dual_track_main

# ---------------------------------------------------------------------------
# Resource Monitor Implementation (T008a)
# ---------------------------------------------------------------------------

@dataclass
class ResourceMetrics:
    """Data class for resource usage metrics."""
    timestamp: str
    task_id: str
    cpu_percent: float
    ram_gb: float

class ResourceLimitExceeded(Exception):
    """Custom exception raised when resource limits are exceeded."""
    pass

class ResourceMonitor:
    """
    Monitors CPU and RAM usage.
    Implements fail-fast mechanism: raises ResourceLimitExceeded if CPU > 90% or RAM > 6.5GB.
    Logs metrics to data/processed/resource_logs.json.
    """
    def __init__(self, task_id: str, output_path: Optional[Path] = None):
        self.task_id = task_id
        self.output_path = output_path or Paths.PROCESSED / "resource_logs.json"
        self.logger = get_logger("ResourceMonitor")
        self.limits = get_resource_limits()
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing logs if file exists
        self.logs: List[Dict[str, Any]] = []
        if self.output_path.exists():
            try:
                with open(self.output_path, 'r') as f:
                    self.logs = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.logs = []

    def _get_current_usage(self) -> ResourceMetrics:
        """Get current CPU and RAM usage."""
        # CPU percent for the current process
        # Note: resource.getrusage returns user+system time, we calculate percent relative to interval
        # For a simple snapshot, we use the process's CPU time delta or a static check
        # Since resource module doesn't give instantaneous % easily without a loop, 
        # we use a simple approximation based on the last check or a 1s sleep if needed.
        # However, for the "wrap task" context, we usually check before and after.
        # Here we implement a snapshot using the current process stats.
        usage = resource.getrusage(resource.RUSAGE_SELF)
        
        # Calculate RAM in GB (maxrss is in KB on Linux)
        ram_gb = usage.ru_maxrss / (1024 * 1024) # Convert KB to GB (assuming 1KB = 1024 bytes)
        
        # CPU percent: For a single snapshot, we can't get % without a delta.
        # We will implement the check in the context manager using a delta approach or 
        # assume the caller checks periodically. 
        # To satisfy the "fail fast" immediately on entry if already high, we check current load.
        # A robust way without external deps: check /proc/stat or use psutil if available.
        # Since we must stick to stdlib or provided deps, we will estimate based on 
        # the fact that if the process is running, we check the *current* usage.
        # For the purpose of this task, we will simulate a check by comparing 
        # current CPU time to wall time over a small interval if possible, 
        # OR simply log the maxrss and a placeholder for CPU if we can't measure % instantly.
        # 
        # Better approach for "fail fast" on start: Check system load if possible, 
        # but the requirement is "CPU > 90%". 
        # Let's use a simple heuristic: if we can't measure % instantly, we assume 
        # the process is running and check the *accumulated* usage vs time? No.
        # 
        # Implementation: We will perform a 0.1s sleep to measure delta for the context manager.
        # For the snapshot method, we return 0.0 for CPU if we can't measure, 
        # but the context manager will handle the actual check.
        # 
        # Actually, resource.getrusage gives ru_utime and ru_stime.
        # We can't get % without a time delta. 
        # Let's implement the check inside the context manager where we have start/end times.
        # For this snapshot, we'll return 0.0 and let the context manager handle the logic.
        cpu_percent = 0.0 
        
        return ResourceMetrics(
            timestamp=datetime.utcnow().isoformat(),
            task_id=self.task_id,
            cpu_percent=cpu_percent,
            ram_gb=ram_gb
        )

    def check_limits(self, cpu_percent: float, ram_gb: float) -> None:
        """
        Check if limits are exceeded.
        Raises ResourceLimitExceeded if CPU > 90% or RAM > 6.5GB.
        """
        if cpu_percent > self.limits.cpu_percent_limit:
            raise ResourceLimitExceeded(
                f"CPU usage {cpu_percent:.2f}% exceeds limit of {self.limits.cpu_percent_limit}%"
            )
        if ram_gb > self.limits.ram_gb_limit:
            raise ResourceLimitExceeded(
                f"RAM usage {ram_gb:.2f}GB exceeds limit of {self.limits.ram_gb_limit}GB"
            )

    def log_metrics(self, cpu_percent: float, ram_gb: float) -> None:
        """Log metrics to the JSON file."""
        metrics = ResourceMetrics(
            timestamp=datetime.utcnow().isoformat(),
            task_id=self.task_id,
            cpu_percent=cpu_percent,
            ram_gb=ram_gb
        )
        self.logs.append(asdict(metrics))
        
        with open(self.output_path, 'w') as f:
            json.dump(self.logs, f, indent=2)
        
        self.logger.info(f"Logged resource metrics for {self.task_id}: CPU={cpu_percent:.2f}%, RAM={ram_gb:.2f}GB")

@contextmanager
def resource_monitor_context(task_id: str, output_path: Optional[Path] = None):
    """
    Context manager to wrap task execution.
    Logs CPU and RAM usage per task to data/processed/resource_logs.json.
    Raises ResourceLimitExceeded if limits are exceeded.
    """
    monitor = ResourceMonitor(task_id, output_path)
    
    # Start monitoring
    start_time = time.time()
    start_rusage = resource.getrusage(resource.RUSAGE_SELF)
    
    try:
        yield monitor
    finally:
        end_time = time.time()
        end_rusage = resource.getrusage(resource.RUSAGE_SELF)
        
        # Calculate usage
        elapsed_time = end_time - start_time
        if elapsed_time > 0:
            cpu_time = (end_rusage.ru_utime + end_rusage.ru_stime) - (start_rusage.ru_utime + start_rusage.ru_stime)
            cpu_percent = (cpu_time / elapsed_time) * 100.0
        else:
            cpu_percent = 0.0
        
        ram_gb = end_rusage.ru_maxrss / (1024 * 1024) # KB to GB
        
        # Check limits BEFORE logging
        try:
            monitor.check_limits(cpu_percent, ram_gb)
        except ResourceLimitExceeded as e:
            # Log the failure event before re-raising? Or just raise.
            # The requirement says "aborting the run", so we raise immediately.
            # But we should probably log the exceeded state for the record.
            monitor.log_metrics(cpu_percent, ram_gb)
            raise e
        
        # Log successful metrics
        monitor.log_metrics(cpu_percent, ram_gb)

# ---------------------------------------------------------------------------
# Task Execution Wrappers
# ---------------------------------------------------------------------------

def run_dataset_preparation(args: argparse.Namespace) -> None:
    """Run dataset preparation tasks with resource monitoring."""
    task_id = "T013_filter"
    with resource_monitor_context(task_id):
        # Simulate calling the loader main with args
        # We need to construct the args for the loader
        loader_args = argparse.Namespace()
        loader_args.verify_only = getattr(args, 'verify_only', False)
        loader_args.filter_min_constraints = getattr(args, 'filter_min_constraints', None)
        loader_args.output = getattr(args, 'output', str(Paths.PROCESSED / "filtered_tasks.csv"))
        loader_main(loader_args)

def run_agent_execution(args: argparse.Namespace) -> None:
    """Run agent execution tasks with resource monitoring."""
    # Monolithic
    task_id_mono = "T026a_monolithic"
    with resource_monitor_context(task_id_mono):
        mono_args = argparse.Namespace()
        mono_args.input = str(Paths.PROCESSED / "filtered_tasks.csv")
        mono_args.output = str(Paths.PROCESSED / "monolithic_logs.json")
        mono_args.model = getattr(args, 'model', 'phi-3-mini')
        mono_main(mono_args)

    # Dual Track
    task_id_dual = "T026b_dual_track"
    with resource_monitor_context(task_id_dual):
        dual_args = argparse.Namespace()
        dual_args.input = str(Paths.PROCESSED / "filtered_tasks.csv")
        dual_args.output = str(Paths.PROCESSED / "dual_track_logs.json")
        dual_main(dual_args)

def run_statistical_analysis_main(args: argparse.Namespace) -> None:
    """Run statistical analysis tasks with resource monitoring."""
    # Power Analysis
    task_id_power = "T030_power"
    with resource_monitor_context(task_id_power):
        power_args = argparse.Namespace()
        power_args.input = str(Paths.PROCESSED / "filtered_tasks.csv")
        power_args.output = str(Paths.PROCESSED / "power_report.json")
        power_main(power_args)

    # GLMM
    task_id_glmm = "T031_glmm"
    with resource_monitor_context(task_id_glmm):
        glmm_args = argparse.Namespace()
        glmm_args.input = str(Paths.PROCESSED / "execution_traces.csv") # Note: This file must be generated first
        glmm_args.output = str(Paths.PROCESSED / "statistical-results.json")
        # Check if file exists, if not, maybe run traces generation first?
        # For now, we assume the pipeline order is correct or the user passes the right file.
        if not os.path.exists(glmm_args.input):
            # Try to generate traces if missing
            traces_args = argparse.Namespace()
            traces_args.monolithic_log = str(Paths.PROCESSED / "monolithic_logs.json")
            traces_args.dual_track_log = str(Paths.PROCESSED / "dual_track_logs.json")
            traces_args.output = str(Paths.PROCESSED / "execution_traces.csv")
            traces_main(traces_args)
        
        glmm_main(glmm_args)

    # Adherence Verifier
    task_id_adherence = "T035_adherence"
    with resource_monitor_context(task_id_adherence):
        adh_args = argparse.Namespace()
        adh_args.input = str(Paths.PROCESSED / "execution_traces.csv")
        adh_args.output = str(Paths.PROCESSED / "adherence_verification.json")
        adherence_main(adh_args)

    # Agreement Rate
    task_id_agreement = "T034_agreement"
    with resource_monitor_context(task_id_agreement):
        agr_args = argparse.Namespace()
        agr_args.input = str(Paths.PROCESSED / "execution_traces.csv")
        agr_args.annotation_sample = str(Paths.PROCESSED / "annotation_sample.csv")
        agr_args.output = str(Paths.PROCESSED / "agreement_rate_report.json")
        agreement_main(agr_args)

def run_all_tasks(args: argparse.Namespace) -> None:
    """Run all tasks in sequence."""
    # 1. Dataset Prep
    run_dataset_preparation(args)
    
    # 2. Agent Execution
    run_agent_execution(args)
    
    # 3. Statistical Analysis
    run_statistical_analysis_main(args)

def main():
    parser = argparse.ArgumentParser(description="llmXive Main Orchestration Script")
    parser.add_argument("--mode", choices=["full", "dataset", "agent", "analysis"], default="full",
                        help="Execution mode")
    parser.add_argument("--model", type=str, default="phi-3-mini", help="Model to use for agents")
    parser.add_argument("--output", type=str, default=None, help="Output directory for logs (optional)")
    
    # Dataset specific args
    parser.add_argument("--verify-only", action="store_true", help="Verify dataset only")
    parser.add_argument("--filter-min-constraints", type=int, help="Filter min constraints")
    
    args = parser.parse_args()
    
    ensure_directories()
    logger = get_logger("Main")
    logger.info(f"Starting main orchestration in mode: {args.mode}")
    
    try:
        if args.mode == "full":
            run_all_tasks(args)
        elif args.mode == "dataset":
            run_dataset_preparation(args)
        elif args.mode == "agent":
            run_agent_execution(args)
        elif args.mode == "analysis":
            run_statistical_analysis_main(args)
        
        logger.info("All tasks completed successfully.")
    except ResourceLimitExceeded as e:
        logger.error(f"Resource limit exceeded: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        raise

if __name__ == "__main__":
    main()