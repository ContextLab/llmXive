"""
Resource Monitor Wrapper for Model Training.

This script spawns the model training process (`code/03_model_training.py`)
and runs an external monitoring loop using `psutil` to enforce RAM and Disk limits.

If RAM > 7.0 GB or Disk > 14.0 GB, the training process is killed immediately.
Logs are written to `data/artifacts/resource_monitor.log`.
"""
import os
import sys
import time
import subprocess
import signal
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# Add project root to path to import utils
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from utils.logging import monitor_resources
except ImportError:
    # Fallback if import fails, though T005 should ensure this exists
    def monitor_resources(ram_limit_gb=7.0, disk_limit_gb=14.0):
        """Minimal fallback implementation if utils.logging is missing."""
        import resource
        import shutil
        import psutil

        rusage = resource.getrusage(resource.RUSAGE_SELF)
        ram_mb = rusage.ru_maxrss / 1024.0  # Convert KB to MB (Linux) or check platform
        # Note: ru_maxrss is in KB on Linux, MB on macOS. 
        # For simplicity in this fallback, we assume a generic check or rely on psutil.
        
        # Use psutil for accurate cross-platform RAM
        current_process = psutil.Process(os.getpid())
        ram_info = current_process.memory_info()
        ram_gb = ram_info.rss / (1024 ** 3)
        
        # Disk usage for the project root
        try:
            disk_usage = shutil.disk_usage(project_root)
            disk_gb = disk_usage.used / (1024 ** 3)
        except Exception:
            disk_gb = 0.0

        status = "ok"
        if ram_gb > ram_limit_gb or disk_gb > disk_limit_gb:
            status = "critical"

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ram_gb": round(ram_gb, 3),
            "disk_gb": round(disk_gb, 3),
            "status": status
        }
        
        # Write to log file
        log_file = project_root / "data" / "artifacts" / "resource_monitor.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        if status == "critical":
            return False
        return True

def main():
    """
    Entry point for the resource monitor wrapper.
    """
    # Configuration
    RAM_LIMIT_GB = 7.0
    DISK_LIMIT_GB = 14.0
    MONITOR_INTERVAL_SECONDS = 2.0
    
    training_script_path = project_root / "code" / "03_model_training.py"
    log_file_path = project_root / "data" / "artifacts" / "resource_monitor.log"
    
    # Ensure directories exist
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Log start
    start_time = datetime.now(timezone.utc)
    start_log = {
        "timestamp": start_time.isoformat(),
        "event": "monitor_start",
        "target_script": str(training_script_path),
        "ram_limit_gb": RAM_LIMIT_GB,
        "disk_limit_gb": DISK_LIMIT_GB
    }
    with open(log_file_path, "a") as f:
        f.write(json.dumps(start_log) + "\n")
    
    if not training_script_path.exists():
        print(f"ERROR: Training script not found at {training_script_path}", file=sys.stderr)
        sys.exit(1)
    
    # Spawn the training process
    # We use a subprocess to run the training script
    try:
        print(f"Starting training process: {training_script_path}")
        proc = subprocess.Popen(
            [sys.executable, str(training_script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except Exception as e:
        print(f"ERROR: Failed to start training process: {e}", file=sys.stderr)
        sys.exit(1)
    
    pid = proc.pid
    print(f"Training process started with PID: {pid}")
    
    monitor_start_time = time.time()
    exceeded = False
    
    try:
        while True:
            # Check if training process is still running
            if proc.poll() is not None:
                # Process finished
                stdout, stderr = proc.communicate()
                if stdout:
                    print(stdout)
                if stderr:
                    print(stderr, file=sys.stderr)
                
                # Final log
                end_time = datetime.now(timezone.utc)
                end_log = {
                    "timestamp": end_time.isoformat(),
                    "event": "monitor_end",
                    "exit_code": proc.returncode,
                    "duration_seconds": round(time.time() - monitor_start_time, 2)
                }
                with open(log_file_path, "a") as f:
                    f.write(json.dumps(end_log) + "\n")
                
                if exceeded:
                    sys.exit(1) # Exit with error if we killed it
                sys.exit(proc.returncode)
            
            # Monitor resources
            try:
                # Use psutil to monitor the training process specifically
                training_process = psutil.Process(pid)
                
                # RAM Check
                mem_info = training_process.memory_info()
                current_ram_gb = mem_info.rss / (1024 ** 3)
                
                # Disk Check (Project root usage)
                try:
                    disk_usage = shutil.disk_usage(project_root)
                    current_disk_gb = disk_usage.used / (1024 ** 3)
                except Exception:
                    current_disk_gb = 0.0
                
                # Log current status
                status = "ok"
                if current_ram_gb > RAM_LIMIT_GB or current_disk_gb > DISK_LIMIT_GB:
                    status = "critical"
                
                log_entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "pid": pid,
                    "ram_gb": round(current_ram_gb, 3),
                    "disk_gb": round(current_disk_gb, 3),
                    "status": status
                }
                
                with open(log_file_path, "a") as f:
                    f.write(json.dumps(log_entry) + "\n")
                
                # Print to stderr for immediate visibility
                print(f"[Monitor] PID {pid} | RAM: {current_ram_gb:.2f}GB / {RAM_LIMIT_GB}GB | Disk: {current_disk_gb:.2f}GB / {DISK_LIMIT_GB}GB | Status: {status}", file=sys.stderr)
                
                if status == "critical":
                    print(f"ERROR: Resource limit exceeded. Killing process {pid}.", file=sys.stderr)
                    exceeded = True
                    
                    # Kill the process
                    try:
                        training_process.terminate()
                        training_process.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        print(f"Warning: Process did not terminate gracefully, forcing kill.", file=sys.stderr)
                        training_process.kill()
                        training_process.wait()
                    
                    # Log termination
                    kill_log = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "event": "process_killed",
                        "reason": f"RAM: {current_ram_gb:.2f}GB > {RAM_LIMIT_GB}GB OR Disk: {current_disk_gb:.2f}GB > {DISK_LIMIT_GB}GB"
                    }
                    with open(log_file_path, "a") as f:
                        f.write(json.dumps(kill_log) + "\n")
                    
                    sys.exit(1)
            
            except psutil.NoSuchProcess:
                # Process might have died between checks
                time.sleep(MONITOR_INTERVAL_SECONDS)
                continue
            except Exception as e:
                print(f"Monitor error: {e}", file=sys.stderr)
                # Don't crash the monitor on a single read error, just log and continue
            
            time.sleep(MONITOR_INTERVAL_SECONDS)
    
    except KeyboardInterrupt:
        print("Monitor interrupted by user. Terminating training process...", file=sys.stderr)
        try:
            proc.terminate()
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
        sys.exit(1)

if __name__ == "__main__":
    main()
