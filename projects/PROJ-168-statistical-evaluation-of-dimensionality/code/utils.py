"""
Resource monitoring utilities for the llmXive pipeline.

Provides a wrapper around `/usr/bin/time -v` to capture wall-clock time
and peak RAM usage for pipeline steps, and logs these metrics to a CSV file.
"""
import os
import sys
import subprocess
import logging
import csv
import re
from pathlib import Path
from typing import Optional, Dict, Any, Callable, Tuple
from functools import wraps

from config import Config

# Configure logging for this module
logger = logging.getLogger(__name__)

class ResourceMonitor:
    """
    Manages resource monitoring via /usr/bin/time -v and logs results.
    """
    
    def __init__(self, output_file: Optional[Path] = None):
        """
        Initialize the monitor.
        
        Args:
            output_file: Path to the CSV file for logging metrics.
                        Defaults to Config().results_dir / "monitoring.csv".
        """
        self.config = Config()
        if output_file is None:
            self.output_file = self.config.results_dir / "monitoring.csv"
        else:
            self.output_file = output_file
        
        # Ensure the results directory exists
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize CSV header if file doesn't exist
        if not self.output_file.exists():
            self._write_header()

    def _write_header(self) -> None:
        """Write CSV header if file is new."""
        headers = ["step_name", "wall_clock_seconds", "peak_ram_mb", "exit_code", "timestamp"]
        with open(self.output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def _parse_time_output(self, output: str) -> Dict[str, Any]:
        """
        Parse the output of `/usr/bin/time -v`.
        
        Args:
            output: The stderr output from /usr/bin/time -v.
        
        Returns:
            Dictionary with 'wall_clock_seconds' and 'peak_ram_mb'.
        """
        result = {
            "wall_clock_seconds": 0.0,
            "peak_ram_mb": 0.0
        }

        # Parse Maximum resident set size (kbytes)
        # Pattern: "Maximum resident set size (kbytes): 123456"
        ram_match = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", output)
        if ram_match:
            ram_kb = int(ram_match.group(1))
            result["peak_ram_mb"] = ram_kb / 1024.0

        # Parse Elapsed (wall clock) time
        # Pattern: "Elapsed (wall clock) time (h:mm:ss or m:ss): 0:00.12"
        time_match = re.search(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s*(\d+):(\d+)[.:](\d+)", output)
        if time_match:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            seconds = float(time_match.group(3))
            result["wall_clock_seconds"] = hours * 3600 + minutes * 60 + seconds

        return result

    def log_metrics(self, step_name: str, metrics: Dict[str, Any], exit_code: int = 0) -> None:
        """
        Append metrics to the monitoring CSV.
        
        Args:
            step_name: Name of the pipeline step.
        """
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        
        with open(self.output_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                step_name,
                metrics.get("wall_clock_seconds", 0.0),
                metrics.get("peak_ram_mb", 0.0),
                exit_code,
                timestamp
            ])
        
        logger.info(f"Logged resources for {step_name}: "
                    f"Time={metrics.get('wall_clock_seconds', 0.0):.2f}s, "
                    f"RAM={metrics.get('peak_ram_mb', 0.0):.2f}MB")

    def run_with_monitoring(self, step_name: str, cmd: list, check: bool = True) -> Tuple[int, Dict[str, Any]]:
        """
        Run a command with /usr/bin/time -v monitoring.
        
        Args:
            step_name: Name of the pipeline step for logging.
            cmd: Command and arguments to execute.
            check: If True, raise CalledProcessError on non-zero exit.
        
        Returns:
            Tuple of (exit_code, metrics_dict).
        """
        # Prepend /usr/bin/time -v
        time_cmd = ["/usr/bin/time", "-v"] + cmd
        
        logger.info(f"Running monitored command: {' '.join(time_cmd)}")
        
        try:
            # /usr/bin/time writes its stats to stderr
            result = subprocess.run(
                time_cmd,
                capture_output=True,
                text=True,
                check=False  # We handle the exit code manually
            )
            
            exit_code = result.returncode
            metrics = self._parse_time_output(result.stderr)
            
            # Log the metrics
            self.log_metrics(step_name, metrics, exit_code)
            
            if check and exit_code != 0:
                raise subprocess.CalledProcessError(exit_code, cmd, result.stdout, result.stderr)
            
            return exit_code, metrics

        except FileNotFoundError:
            logger.error("/usr/bin/time not found. Resource monitoring disabled.")
            # Fallback: run without monitoring
            try:
                result = subprocess.run(cmd, check=check, capture_output=True, text=True)
                return result.returncode, {"wall_clock_seconds": 0.0, "peak_ram_mb": 0.0}
            except subprocess.CalledProcessError as e:
                raise e

def time_wrapper(step_name: str):
    """
    Decorator to wrap a function with resource monitoring.
    
    This uses /usr/bin/time -v to measure wall-clock time and peak RAM
    for the decorated function.
    
    Args:
        step_name: Name of the step for logging.
    
    Returns:
        Decorated function.
    """
    monitor = ResourceMonitor()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # We need to run the function inside a subprocess to capture /usr/bin/time output
            # However, since we are wrapping a Python function, we can't easily use /usr/bin/time
            # directly on the Python process.
            # 
            # Alternative strategy:
            # 1. If the function is a script entry point, we use the CLI wrapper.
            # 2. If called from within Python, we use a subprocess to run the script.
            #
            # For this implementation, we assume the decorator is used on functions
            # that are meant to be run as standalone scripts or via a subprocess call.
            #
            # If the function is being called directly, we can't easily measure it with /usr/bin/time
            # without spawning a new process.
            #
            # Let's implement a version that spawns a subprocess if possible,
            # or logs a warning if direct measurement isn't feasible.
            
            # For now, we'll implement a simple version that logs a warning
            # and suggests using the CLI wrapper for accurate measurements.
            logger.warning(f"Direct Python function decoration for {step_name} not supported for /usr/bin/time. "
                           f"Use the CLI wrapper or run as a separate process.")
            
            # Fallback: just run the function
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def run_script_with_monitoring(step_name: str, script_path: str, args: Optional[list] = None) -> Tuple[int, Dict[str, Any]]:
    """
    Run a Python script with resource monitoring.
    
    Args:
        step_name: Name of the step for logging.
        script_path: Path to the Python script.
        args: Additional arguments to pass to the script.
    
    Returns:
        Tuple of (exit_code, metrics_dict).
    """
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    monitor = ResourceMonitor()
    return monitor.run_with_monitoring(step_name, cmd)

def get_resource_monitor() -> ResourceMonitor:
    """
    Get a singleton instance of ResourceMonitor.
    
    Returns:
        ResourceMonitor instance.
    """
    # Simple singleton pattern
    if not hasattr(get_resource_monitor, "_instance"):
        get_resource_monitor._instance = ResourceMonitor()
    return get_resource_monitor._instance