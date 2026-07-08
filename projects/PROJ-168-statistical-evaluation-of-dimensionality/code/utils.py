import os
import sys
import subprocess
import logging
import csv
import re
import time
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Callable, Tuple
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ResourceMonitor:
    """
    Monitors RAM usage and execution time for a process.
    Implements FR-008: Abort if RAM > 7GB.
    """
    MAX_RAM_GB = 7.0
    MAX_RAM_KB = MAX_RAM_GB * 1024 * 1024  # Convert GB to KB (1024^2)
    
    def __init__(self, log_path: Optional[str] = None):
        self.log_path = log_path or str(Config.RESULTS_DIR / "monitoring.csv")
        self._ensure_log_file()
        self.step_history: list = []

    def _ensure_log_file(self):
        """Initialize the monitoring CSV if it doesn't exist."""
        log_file = Path(self.log_path)
        if not log_file.exists():
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['step', 'timestamp', 'wall_time_seconds', 'peak_ram_kb', 'peak_ram_gb', 'status'])

    def check_ram_usage(self, pid: int) -> Tuple[float, bool]:
        """
        Checks the current RAM usage of a process by its PID.
        Returns (peak_ram_gb, is_exceeded).
        
        Uses /usr/bin/time -v logic via psutil-like parsing or direct /proc if available.
        Since we cannot rely on psutil being installed without adding deps, we use
        /proc/<pid>/status or `ps` command as a fallback.
        """
        try:
            # Try to read from /proc first (Linux)
            status_path = f"/proc/{pid}/status"
            if os.path.exists(status_path):
                with open(status_path, 'r') as f:
                    for line in f:
                        if line.startswith("VmPeak:"):
                            # Format: "VmPeak:     123456 kB"
                            parts = line.split()
                            if len(parts) >= 2:
                                ram_kb = int(parts[1])
                                ram_gb = ram_kb / (1024 * 1024)
                                is_exceeded = ram_kb > self.MAX_RAM_KB
                                return ram_gb, is_exceeded
            
            # Fallback to `ps` command if /proc fails or not on Linux
            # ps -o rss=,pid= <pid> returns RSS in KB
            result = subprocess.run(
                ['ps', '-o', 'rss=', '-p', str(pid)],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                ram_kb = int(result.stdout.strip())
                ram_gb = ram_kb / (1024 * 1024)
                is_exceeded = ram_kb > self.MAX_RAM_KB
                return ram_gb, is_exceeded
            
            logger.warning(f"Could not determine RAM usage for PID {pid}.")
            return 0.0, False

        except (ValueError, subprocess.TimeoutExpired, FileNotFoundError, PermissionError) as e:
            logger.error(f"Error checking RAM for PID {pid}: {e}")
            return 0.0, False

    def log_metrics(self, step_name: str, wall_time: float, peak_ram_gb: float, status: str):
        """Logs metrics to the CSV file."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        peak_ram_kb = peak_ram_gb * 1024 * 1024
        
        with open(self.log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([step_name, timestamp, f"{wall_time:.2f}", f"{peak_ram_kb:.0f}", f"{peak_ram_gb:.2f}", status])
        
        self.step_history.append({
            'step': step_name,
            'timestamp': timestamp,
            'wall_time': wall_time,
            'peak_ram_gb': peak_ram_gb,
            'status': status
        })
        logger.info(f"Monitored {step_name}: {peak_ram_gb:.2f} GB RAM, {wall_time:.2f}s. Status: {status}")

def time_wrapper(cmd: str, step_name: str) -> subprocess.CompletedProcess:
    """
    Runs a command with resource monitoring.
    Uses /usr/bin/time -v to capture wall time and max memory.
    
    Args:
        cmd: The command string to execute.
        step_name: Identifier for logging.
    
    Returns:
        CompletedProcess instance.
    
    Raises:
        RuntimeError: If RAM usage exceeds MAX_RAM_GB.
    """
    monitor = ResourceMonitor()
    
    # Prepare the command to include /usr/bin/time -v
    # We need to capture the output of /usr/bin/time to parse it
    # Format: /usr/bin/time -v <command>
    full_cmd = ["/usr/bin/time", "-v", "-o", "/dev/stderr", "--append", "-f", "%e|%M", cmd]
    # Note: %e is elapsed real time, %M is max resident set size (KB)
    
    # However, parsing /usr/bin/time output is tricky with subprocess.
    # Alternative: Run the script, and in the script itself, we can call a wrapper.
    # But the task asks for a wrapper in utils.py.
    
    # Let's use a simpler approach: Run the command, and use `ps` to monitor periodically?
    # No, the requirement is to abort if > 7GB.
    # The most reliable way with standard tools is to wrap the execution.
    
    # Let's assume the command is a python script or a shell command.
    # We will run it and monitor.
    
    # Since we cannot easily parse /usr/bin/time output in real-time to abort,
    # we will run the command and then check the exit code and the time output.
    # BUT the requirement is to ABORT if > 7GB. This implies real-time monitoring.
    
    # Re-evaluating: The task says "check RAM usage during execution and abort".
    # This requires a background thread or a wrapper that monitors the child process.
    
    # Let's implement a robust wrapper using a monitoring thread.
    
    process = subprocess.Popen(
        cmd, 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True
    )
    
    start_time = time.time()
    peak_ram_gb = 0.0
    exceeded = False
    
    # Monitor loop
    while process.poll() is None:
        current_ram_gb, is_exceeded = monitor.check_ram_usage(process.pid)
        if current_ram_gb > peak_ram_gb:
            peak_ram_gb = current_ram_gb
        
        if is_exceeded:
            logger.error(f"RAM limit exceeded ({peak_ram_gb:.2f} GB > {monitor.MAX_RAM_GB} GB) in step '{step_name}'. Aborting.")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            monitor.log_metrics(step_name, time.time() - start_time, peak_ram_gb, "ABORTED_RAM_LIMIT")
            raise RuntimeError(f"Resource limit exceeded: RAM usage {peak_ram_gb:.2f} GB > {monitor.MAX_RAM_GB} GB")
        
        time.sleep(1) # Check every second
    
    # Process finished
    wall_time = time.time() - start_time
    final_ram_gb, _ = monitor.check_ram_usage(process.pid)
    if final_ram_gb > peak_ram_gb:
        peak_ram_gb = final_ram_gb
    
    status = "COMPLETED" if process.returncode == 0 else "FAILED"
    monitor.log_metrics(step_name, wall_time, peak_ram_gb, status)
    
    # Return a fake CompletedProcess if we need to, but usually we just let the exception propagate
    # or return the actual process.
    return process

def run_script_with_monitoring(script_path: str, step_name: str, args: Optional[list] = None) -> int:
    """
    Runs a python script with resource monitoring.
    If RAM > 7GB, it aborts and logs to results/monitoring.csv.
    
    Args:
        script_path: Path to the python script.
        step_name: Name for logging.
        args: Optional list of arguments.
    
    Returns:
        Exit code of the script (or raises RuntimeError on RAM limit).
    """
    cmd_parts = [sys.executable, script_path]
    if args:
        cmd_parts.extend(args)
    cmd = " ".join(cmd_parts)
    
    # We use the time_wrapper logic but tailored for a script
    monitor = ResourceMonitor()
    
    process = subprocess.Popen(
        cmd_parts,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    start_time = time.time()
    peak_ram_gb = 0.0
    
    # Monitor loop
    while process.poll() is None:
        current_ram_gb, is_exceeded = monitor.check_ram_usage(process.pid)
        if current_ram_gb > peak_ram_gb:
            peak_ram_gb = current_ram_gb
        
        if is_exceeded:
            logger.error(f"RAM limit exceeded ({peak_ram_gb:.2f} GB > {monitor.MAX_RAM_GB} GB) in step '{step_name}'. Aborting.")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            monitor.log_metrics(step_name, time.time() - start_time, peak_ram_gb, "ABORTED_RAM_LIMIT")
            raise RuntimeError(f"Resource limit exceeded: RAM usage {peak_ram_gb:.2f} GB > {monitor.MAX_RAM_GB} GB")
        
        time.sleep(1)
    
    wall_time = time.time() - start_time
    final_ram_gb, _ = monitor.check_ram_usage(process.pid)
    if final_ram_gb > peak_ram_gb:
        peak_ram_gb = final_ram_gb
    
    status = "COMPLETED" if process.returncode == 0 else "FAILED"
    monitor.log_metrics(step_name, wall_time, peak_ram_gb, status)
    
    return process.returncode

def get_resource_monitor() -> ResourceMonitor:
    """
    Factory function to get a singleton-like ResourceMonitor instance.
    """
    return ResourceMonitor()