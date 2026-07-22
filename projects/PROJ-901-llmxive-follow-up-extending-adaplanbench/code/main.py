"""
Main orchestration script for the llmXive automated science pipeline.

Implements resource monitoring (FR-006), task orchestration, and execution flow.
"""

import os
import sys
import time
import resource
import json
import csv
import argparse
import traceback
from pathlib import Path
from typing import Optional, Callable, Any, Dict, List
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# Import from project modules
from config import get_paths, get_resource_limits, ensure_directories
from dataset.loader import main as loader_main
from dataset.validate_subset import validate_subset
from agent.monolithic_runner import main as monolithic_main
from agent.dual_track_runner import main as dual_track_main
from analysis.log_aggregator import main as aggregator_main
from analysis.glmm import main as glmm_main
from analysis.power import main as power_main
from analysis.adherence_verifier import main as adherence_main
from analysis.agreement_rate import main as agreement_main


@dataclass
class ResourceMetrics:
    """Container for resource usage metrics."""
    task_name: str
    cpu_percent: float
    memory_mb: float
    start_time: float
    end_time: float
    duration_seconds: float
    success: bool
    error_message: Optional[str] = None


class ResourceMonitor:
    """
    Resource monitor wrapper for task execution.
    
    Implements FR-006: Logs CPU and RAM usage per task to data/processed/resource_logs.json.
    Fails fast if limits are exceeded.
    """
    
    def __init__(self, log_path: Optional[Path] = None):
        self.paths = get_paths()
        self.log_path = log_path or self.paths.DATA_PROCESSED / "resource_logs.json"
        self.limits = get_resource_limits()
        self.logs: List[Dict[str, Any]] = []
        self._ensure_log_file_exists()
    
    def _ensure_log_file_exists(self):
        """Ensure the log directory and file exist."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            with open(self.log_path, 'w') as f:
                json.dump([], f)
    
    def _get_current_usage(self) -> tuple:
        """Get current CPU and memory usage."""
        # CPU usage - simple approximation (wall clock based)
        # Note: resource.getrusage gives cumulative stats, we'll track delta manually
        mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # ru_maxrss is in kilobytes on Linux, convert to MB
        mem_mb = mem_usage / 1024.0
        return mem_mb
    
    def check_limits(self, mem_mb: float) -> bool:
        """Check if current usage exceeds limits. Returns True if OK, False if exceeded."""
        max_mem_mb = self.limits.max_memory_mb
        if max_mem_mb > 0 and mem_mb > max_mem_mb:
            return False
        return True
    
    @contextmanager
    def monitor_task(self, task_name: str):
        """
        Context manager to monitor resource usage for a task.
        
        Logs CPU/RAM usage and fails fast if limits are exceeded.
        """
        metrics = ResourceMetrics(
            task_name=task_name,
            cpu_percent=0.0,  # Simplified: CPU tracking would require more complex logic
            memory_mb=0.0,
            start_time=time.time(),
            end_time=0.0,
            duration_seconds=0.0,
            success=False
        )
        
        try:
            # Record start memory
            start_mem = self._get_current_usage()
            metrics.memory_mb = start_mem
            
            # Check start limits
            if not self.check_limits(start_mem):
                raise MemoryError(
                    f"Task '{task_name}' exceeded memory limit at start: "
                    f"{start_mem:.2f}MB > {self.limits.max_memory_mb}MB"
                )
            
            yield metrics
            
            # Task completed successfully
            metrics.success = True
            
        except Exception as e:
            metrics.error_message = str(e)
            raise
        
        finally:
            # Record end metrics
            end_mem = self._get_current_usage()
            metrics.end_time = time.time()
            metrics.duration_seconds = metrics.end_time - metrics.start_time
            metrics.memory_mb = end_mem
            
            # Final limit check
            if not self.check_limits(end_mem):
                metrics.error_message = (
                    f"Task '{task_name}' exceeded memory limit at end: "
                    f"{end_mem:.2f}MB > {self.limits.max_memory_mb}MB"
                )
                raise MemoryError(metrics.error_message)
            
            # Log the metrics
            self.logs.append(asdict(metrics))
            self._write_logs()
    
    def _write_logs(self):
        """Write accumulated logs to file."""
        # Read existing logs
        existing_logs = []
        if self.log_path.exists():
            try:
                with open(self.log_path, 'r') as f:
                    existing_logs = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing_logs = []
        
        # Append new logs
        existing_logs.extend(self.logs)
        
        # Write back
        with open(self.log_path, 'w') as f:
            json.dump(existing_logs, f, indent=2)
        
        # Clear in-memory logs
        self.logs = []

def log_resource_metrics(metrics: ResourceMetrics):
    """Utility function to log resource metrics (for backward compatibility)."""
    monitor = ResourceMonitor()
    monitor.logs.append(asdict(metrics))
    monitor._write_logs()

def run_dataset_preparation(args):
    """Run dataset preparation tasks."""
    monitor = ResourceMonitor()
    
    with monitor.monitor_task("dataset_loader"):
        # Prepare args for loader
        loader_args = argparse.Namespace(
            verify_only=getattr(args, 'verify_only', False),
            filter_min_constraints=getattr(args, 'filter_min_constraints', None),
            output=getattr(args, 'output', None)
        )
        loader_main(loader_args)
    
    with monitor.monitor_task("validate_subset"):
        validate_subset()

def run_agent_execution(args):
    """Run agent execution tasks."""
    monitor = ResourceMonitor()
    
    with monitor.monitor_task("monolithic_agent"):
        monolithic_args = argparse.Namespace(
            model=getattr(args, 'model', 'phi-3-mini'),
            input=getattr(args, 'input', 'data/processed/filtered_tasks.csv'),
            output=getattr(args, 'output', 'data/processed/monolithic_logs.json')
        )
        monolithic_main(monolithic_args)
    
    with monitor.monitor_task("dual_track_agent"):
        dual_track_args = argparse.Namespace(
            model=getattr(args, 'model', 'phi-3-mini'),
            input=getattr(args, 'input', 'data/processed/filtered_tasks.csv'),
            output=getattr(args, 'output', 'data/processed/dual_track_logs.json')
        )
        dual_track_main(dual_track_args)

def run_statistical_analysis(args):
    """Run statistical analysis tasks."""
    monitor = ResourceMonitor()
    
    with monitor.monitor_task("log_aggregator"):
        aggregator_args = argparse.Namespace(
            monolithic='data/processed/monolithic_logs.json',
            dual_track='data/processed/dual_track_logs.json',
            output='data/processed/execution_traces.csv'
        )
        aggregator_main(aggregator_args)
    
    with monitor.monitor_task("glmm_analysis"):
        glmm_args = argparse.Namespace(
            input='data/processed/execution_traces.csv',
            output='data/processed/statistical-results.json'
        )
        glmm_main(glmm_args)
    
    with monitor.monitor_task("power_analysis"):
        power_args = argparse.Namespace(
            input='data/processed/filtered_tasks.csv',
            output='data/processed/power_report.json'
        )
        power_main(power_args)
    
    with monitor.monitor_task("adherence_verification"):
        adherence_args = argparse.Namespace(
            input='data/processed/execution_traces.csv',
            output='data/processed/adherence_verification.json'
        )
        adherence_main(adherence_args)
    
    with monitor.monitor_task("agreement_rate"):
        agreement_args = argparse.Namespace(
            traces='data/processed/execution_traces.csv',
            annotations='data/processed/annotation_sample.csv',
            output='data/processed/agreement_rate_report.json'
        )
        agreement_main(agreement_args)

def run_all_tasks(args):
    """Run all pipeline tasks."""
    run_dataset_preparation(args)
    run_agent_execution(args)
    run_statistical_analysis(args)

def main():
    """Main entry point for the orchestration script."""
    parser = argparse.ArgumentParser(
        description='llmXive automated science pipeline orchestrator'
    )
    parser.add_argument(
        '--mode',
        choices=['dataset', 'agent', 'analysis', 'full'],
        default='full',
        help='Execution mode: dataset, agent, analysis, or full pipeline'
    )
    parser.add_argument(
        '--model',
        default='phi-3-mini',
        help='Model to use for agent execution'
    )
    parser.add_argument(
        '--input',
        default=None,
        help='Input file path (overrides defaults)'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output file path (overrides defaults)'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify dataset, do not process'
    )
    parser.add_argument(
        '--filter-min-constraints',
        type=int,
        default=None,
        help='Minimum number of constraints for filtering'
    )
    
    args = parser.parse_args()
    
    # Ensure directories exist
    ensure_directories()
    
    try:
        if args.mode == 'dataset':
            run_dataset_preparation(args)
        elif args.mode == 'agent':
            run_agent_execution(args)
        elif args.mode == 'analysis':
            run_statistical_analysis(args)
        elif args.mode == 'full':
            run_all_tasks(args)
        else:
            print(f"Unknown mode: {args.mode}", file=sys.stderr)
            sys.exit(1)
        
        print("Pipeline completed successfully.")
        sys.exit(0)
        
    except Exception as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()