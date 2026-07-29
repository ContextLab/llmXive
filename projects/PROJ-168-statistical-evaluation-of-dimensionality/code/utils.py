import os
import sys
import subprocess
import logging
import csv
import re
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from contextlib import contextmanager

# Configuration for monitoring
MONITORING_LOG_FILE = "results/monitoring.csv"
TIME_LOG_PATTERN = r"Maximum resident set size \(kbytes\): (\d+)"
ELAPSED_TIME_PATTERN = r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): ([0-9:.]+)"

logger = logging.getLogger(__name__)

class ResourceMonitor:
    """Context manager to wrap execution with /usr/bin/time -v monitoring."""

    def __init__(self, output_path: Optional[str] = None, accession: Optional[str] = None, step: Optional[str] = None):
        self.output_path = output_path or MONITORING_LOG_FILE
        self.accession = accession or "unknown"
        self.step = step or "unknown"
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.ram_kb: Optional[int] = None
        self.elapsed_seconds: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        return False

    def parse_time_output(self, time_output: str) -> Tuple[Optional[int], Optional[float]]:
        """Parse the output of /usr/bin/time -v to extract RAM and elapsed time."""
        ram_match = re.search(TIME_LOG_PATTERN, time_output)
        elapsed_match = re.search(ELAPSED_TIME_PATTERN, time_output)

        ram_kb = int(ram_match.group(1)) if ram_match else None

        elapsed_seconds = None
        if elapsed_match:
            time_str = elapsed_match.group(1)
            parts = time_str.split(':')
            if len(parts) == 3:
                # h:mm:ss
                hours = int(parts[0])
                mins = int(parts[1])
                secs = float(parts[2])
                elapsed_seconds = hours * 3600 + mins * 60 + secs
            elif len(parts) == 2:
                # m:ss
                mins = int(parts[0])
                secs = float(parts[1])
                elapsed_seconds = mins * 60 + secs
            else:
                # Assume seconds if single number (rare)
                elapsed_seconds = float(parts[0])

        return ram_kb, elapsed_seconds

    def record_metrics(self, time_output: str):
        """Parse time output and record metrics to CSV."""
        ram_kb, elapsed_seconds = self.parse_time_output(time_output)
        self.ram_kb = ram_kb
        self.elapsed_seconds = elapsed_seconds

        # Ensure directory exists
        output_path = Path(self.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        file_exists = output_path.exists()

        with open(output_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['timestamp', 'accession', 'step', 'peak_ram_kb', 'elapsed_seconds'])

            writer.writerow([
                time.strftime('%Y-%m-%d %H:%M:%S'),
                self.accession,
                self.step,
                self.ram_kb if self.ram_kb is not None else 'N/A',
                self.elapsed_seconds if self.elapsed_seconds is not None else 'N/A'
            ])

        logger.info(f"Recorded monitoring metrics for {self.step} ({self.accession}): RAM={self.ram_kb}KB, Time={self.elapsed_seconds}s")

@contextmanager
def time_wrapper(cmd: List[str], accession: str, step: str, output_log: Optional[str] = None):
    """
    Execute a command wrapped with /usr/bin/time -v to capture resource usage.
    Parses the output and records metrics to the monitoring CSV.

    Args:
        cmd: Command and arguments to execute.
        accession: Dataset accession ID for tracking.
        step: Name of the pipeline step (e.g., 'pca', 'umap').
        output_log: Optional path to save the raw time output.
    """
    full_cmd = ['time', '-v'] + cmd
    logger.info(f"Running command with monitoring: {' '.join(full_cmd)}")

    result = subprocess.run(
        full_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # /usr/bin/time -v writes to stderr
    time_output = result.stderr

    if output_log:
        with open(output_log, 'w') as f:
            f.write(time_output)

    # Record metrics
    monitor = ResourceMonitor(accession=accession, step=step)
    monitor.record_metrics(time_output)

    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, output=result.stdout, stderr=result.stderr)

    yield result

def run_script_with_monitoring(
    script_path: str,
    accession: str,
    step: str,
    args: Optional[List[str]] = None,
    python_executable: Optional[str] = None
) -> Tuple[Optional[int], Optional[int], Optional[float]]:
    """
    Run a Python script wrapped with /usr/bin/time -v.

    Args:
        script_path: Path to the Python script to run.
        accession: Dataset accession ID.
        step: Pipeline step name.
        args: Additional arguments to pass to the script.
        python_executable: Python executable to use (defaults to sys.executable).

    Returns:
        Tuple of (return_code, peak_ram_kb, elapsed_seconds)
    """
    py_exec = python_executable or sys.executable
    cmd = [py_exec, script_path]
    if args:
        cmd.extend(args)

    monitor = ResourceMonitor(accession=accession, step=step)

    try:
        with time_wrapper(cmd, accession, step) as result:
            return result.returncode, monitor.ram_kb, monitor.elapsed_seconds
    except subprocess.CalledProcessError as e:
        logger.error(f"Script {script_path} failed with return code {e.returncode}")
        return e.returncode, monitor.ram_kb, monitor.elapsed_seconds

def get_resource_monitor() -> ResourceMonitor:
    """
    Factory function to get a configured ResourceMonitor instance.
    Useful for scripts that want to manually monitor specific blocks.
    """
    return ResourceMonitor()

# Parser function specifically for T021 requirement
def parse_time_logs(log_files: List[str]) -> List[Dict[str, Any]]:
    """
    Parse multiple /usr/bin/time -v log files and return a list of metric dictionaries.

    Args:
        log_files: List of file paths containing time -v output.

    Returns:
        List of dictionaries with keys: 'file', 'peak_ram_kb', 'elapsed_seconds', 'status'
    """
    results = []
    for log_file in log_files:
        if not os.path.exists(log_file):
            logger.warning(f"Log file not found: {log_file}")
            continue

        try:
            with open(log_file, 'r') as f:
                content = f.read()

            ram_kb, elapsed_seconds = parse_time_output_static(content)

            results.append({
                'file': log_file,
                'peak_ram_kb': ram_kb,
                'elapsed_seconds': elapsed_seconds,
                'status': 'success'
            })
        except Exception as e:
            logger.error(f"Error parsing {log_file}: {e}")
            results.append({
                'file': log_file,
                'peak_ram_kb': None,
                'elapsed_seconds': None,
                'status': 'error',
                'error': str(e)
            })

    return results

def parse_time_output_static(time_output: str) -> Tuple[Optional[int], Optional[float]]:
    """Static version of parse_time_output for use outside class instances."""
    ram_match = re.search(TIME_LOG_PATTERN, time_output)
    elapsed_match = re.search(ELAPSED_TIME_PATTERN, time_output)

    ram_kb = int(ram_match.group(1)) if ram_match else None

    elapsed_seconds = None
    if elapsed_match:
        time_str = elapsed_match.group(1)
        parts = time_str.split(':')
        if len(parts) == 3:
            hours = int(parts[0])
            mins = int(parts[1])
            secs = float(parts[2])
            elapsed_seconds = hours * 3600 + mins * 60 + secs
        elif len(parts) == 2:
            mins = int(parts[0])
            secs = float(parts[1])
            elapsed_seconds = mins * 60 + secs
        else:
            elapsed_seconds = float(parts[0])

    return ram_kb, elapsed_seconds

def main():
    """CLI entry point for testing the parser and monitor."""
    import argparse
    parser = argparse.ArgumentParser(description="Resource monitoring utilities")
    parser.add_argument('--log', nargs='+', help="Log files to parse")
    parser.add_argument('--output', default=MONITORING_LOG_FILE, help="Output CSV path")
    args = parser.parse_args()

    if args.log:
        results = parse_time_logs(args.log)
        for r in results:
            print(f"File: {r['file']}, RAM: {r['peak_ram_kb']}KB, Time: {r['elapsed_seconds']}s, Status: {r['status']}")
    else:
        print("Usage: python utils.py --log <file1> [file2 ...]")

if __name__ == "__main__":
    main()