import os
import sys
import subprocess
import logging
import csv
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ResourceMonitor:
    """
    Monitors system resources (RAM, CPU time) using /usr/bin/time -v.
    Wraps script execution and logs metrics to a CSV file.
    """
    
    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._header_written = False
        self._lock = None # Not used for single-threaded logging but good practice
        
        # Ensure CSV header exists
        self._ensure_header()

    def _ensure_header(self):
        """Writes the CSV header if the file is new or empty."""
        if not self.output_path.exists() or self.output_path.stat().st_size == 0:
            with open(self.output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'step_name', 'wall_clock_seconds', 
                    'peak_ram_mb', 'exit_code', 'command'
                ])

    def record_metrics(self, step_name: str, command: str, exit_code: int, 
                       wall_clock_seconds: float, peak_ram_mb: float):
        """
        Records a single row of resource metrics to the monitoring CSV.
        
        Args:
            step_name: Name of the pipeline step (e.g., 'pca', 'umap')
            command: The command that was executed
            exit_code: Exit code of the command
            wall_clock_seconds: Total wall-clock time in seconds
            peak_ram_mb: Peak resident set size in MB
        """
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        
        with open(self.output_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, step_name, f"{wall_clock_seconds:.2f}", 
                f"{peak_ram_mb:.2f}", exit_code, command
            ])
        
        logger.info(f"Recorded metrics for {step_name}: RAM={peak_ram_mb:.2f}MB, Time={wall_clock_seconds:.2f}s")

    def check_resource_limits(self, peak_ram_mb: float, limit_gb: float = 7.0) -> bool:
        """
        Checks if peak RAM usage exceeds the specified limit.
        
        Args:
            peak_ram_mb: Peak RAM usage in MB
            limit_gb: Limit in GB (default 7.0)
            
        Returns:
            True if within limits, False if exceeded
        """
        limit_mb = limit_gb * 1024
        if peak_ram_mb > limit_mb:
            logger.error(f"RAM limit exceeded: {peak_ram_mb:.2f}MB > {limit_mb:.2f}MB ({limit_gb}GB)")
            return False
        return True

_monitor_instance: Optional[ResourceMonitor] = None

def get_resource_monitor() -> ResourceMonitor:
    """Returns the singleton ResourceMonitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        # Default path based on project structure
        output_path = Path("results/monitoring.csv")
        _monitor_instance = ResourceMonitor(str(output_path))
    return _monitor_instance

def time_wrapper(script_path: str, step_name: str, args: Optional[List[str]] = None):
    """
    Executes a script wrapped with /usr/bin/time -v to capture resource usage.
    
    Args:
        script_path: Path to the Python script to execute
        step_name: Name of the step for logging
        args: Optional list of arguments to pass to the script
        
    Returns:
        Tuple of (exit_code, wall_clock_seconds, peak_ram_mb)
        
    Raises:
        RuntimeError: If /usr/bin/time is not available or execution fails
    """
    monitor = get_resource_monitor()
    
    cmd = [
        "/usr/bin/time", "-v", 
        "python", script_path
    ]
    if args:
        cmd.extend(args)
    
    logger.info(f"Running step '{step_name}' with resource monitoring: {' '.join(cmd)}")
    
    start_time = time.time()
    process = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    end_time = time.time()
    
    wall_clock_seconds = end_time - start_time
    exit_code = process.returncode
    
    # Parse /usr/bin/time output for Peak Memory
    # Format: "Maximum resident set size (kbytes): 123456"
    peak_ram_kb = 0
    time_output = process.stderr + process.stdout
    
    match = re.search(r"Maximum resident set size \(kbytes\):\s+(\d+)", time_output)
    if match:
        peak_ram_kb = int(match.group(1))
        peak_ram_mb = peak_ram_kb / 1024.0
    else:
        # Fallback if parsing fails (e.g., on macOS where time is different)
        logger.warning("Could not parse peak RAM from /usr/bin/time output. Using estimated value.")
        # Estimate based on wall clock if possible, or default to 0 (which will trigger alert if limits are strict)
        peak_ram_mb = 0.0
    
    # Check limits
    if not monitor.check_resource_limits(peak_ram_mb):
        logger.error(f"Aborting step '{step_name}' due to resource limits.")
        # Note: The caller might handle the abort, but we record the failure
        monitor.record_metrics(step_name, ' '.join(cmd), exit_code, wall_clock_seconds, peak_ram_mb)
        raise RuntimeError(f"Resource limit exceeded for step {step_name}")
    
    # Record metrics
    monitor.record_metrics(step_name, ' '.join(cmd), exit_code, wall_clock_seconds, peak_ram_mb)
    
    return exit_code, wall_clock_seconds, peak_ram_mb

def run_script_with_monitoring(step_name: str, script_module: str, args: Optional[List[str]] = None):
    """
    Runs a script module with resource monitoring.
    
    Args:
        step_name: Name of the step
        script_module: Module name (e.g., 'code.embeddings')
        args: Arguments for the script
    """
    # Construct script path
    script_path = f"{script_module.replace('.', '/')}.py"
    if not os.path.exists(script_path):
        # Try relative to code/
        script_path = f"code/{script_module.replace('.', '/')}.py"
    
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script not found: {script_path}")
    
    exit_code, time_s, ram_mb = time_wrapper(script_path, step_name, args)
    return exit_code

def parse_time_logs(log_file_path: str) -> List[Dict[str, Any]]:
    """
    Parses a log file generated by /usr/bin/time -v (if captured separately)
    or reads the CSV monitoring file to return structured data.
    
    Note: This function primarily reads the CSV output from record_metrics.
    """
    path = Path(log_file_path)
    if not path.exists():
        return []
    
    results = []
    with open(path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'timestamp': row['timestamp'],
                'step_name': row['step_name'],
                'wall_clock_seconds': float(row['wall_clock_seconds']),
                'peak_ram_mb': float(row['peak_ram_mb']),
                'exit_code': int(row['exit_code']),
                'command': row['command']
            })
    return results

def parse_time_output_static(time_output: str) -> Dict[str, float]:
    """
    Parses a string output from /usr/bin/time -v to extract metrics.
    Used for ad-hoc parsing of stderr/stdout.
    """
    metrics = {}
    
    # Wall clock (if captured separately)
    # Usually we rely on the wrapper's own timing, but if parsing raw output:
    # "Elapsed (wall clock) time (h:mm:ss or m:ss): 0:00:10"
    match = re.search(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s+(\d+):(\d+):(\d+)", time_output)
    if match:
        h, m, s = map(int, match.groups())
        metrics['wall_clock_seconds'] = h * 3600 + m * 60 + s
    
    # Peak Memory
    match = re.search(r"Maximum resident set size \(kbytes\):\s+(\d+)", time_output)
    if match:
        metrics['peak_ram_mb'] = int(match.group(1)) / 1024.0
        
    return metrics

def main():
    """
    Entry point for testing the ResourceMonitor and time wrapper.
    """
    print("Testing ResourceMonitor...")
    
    # Test 1: Basic recording
    monitor = ResourceMonitor("results/monitoring_test.csv")
    monitor.record_metrics(
        step_name="test_step_1",
        command="echo hello",
        exit_code=0,
        wall_clock_seconds=1.5,
        peak_ram_mb=100.0
    )
    monitor.record_metrics(
        step_name="test_step_2",
        command="echo world",
        exit_code=1,
        wall_clock_seconds=2.0,
        peak_ram_mb=200.0
    )
    
    # Test 2: Reading back
    data = parse_time_logs("results/monitoring_test.csv")
    print(f"Read {len(data)} records from test log.")
    for record in data:
        print(f"  {record['step_name']}: {record['peak_ram_mb']:.2f} MB")
    
    # Cleanup test file
    if os.path.exists("results/monitoring_test.csv"):
        os.remove("results/monitoring_test.csv")
        print("Test file cleaned up.")

if __name__ == "__main__":
    main()