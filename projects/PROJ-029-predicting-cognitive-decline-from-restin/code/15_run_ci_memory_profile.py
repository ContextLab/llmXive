"""
CI Memory Profiler Task (T043)

Executes the major pipeline scripts sequentially, monitors peak RAM usage
for each, and appends a structured log entry to data/artifacts/memory_profile.log.

Scripts monitored:
1. 01_download_and_filter.py
2. 02_preprocess_and_parcellate.py
3. 03_compute_graph_metrics.py
4. 04_train_model.py

Output: data/artifacts/memory_profile.log (JSONL format)
"""
import os
import sys
import time
import json
import subprocess
import threading
import psutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_ARTIFACTS_DIR = PROJECT_ROOT / "data" / "artifacts"
LOG_FILE = DATA_ARTIFACTS_DIR / "memory_profile.log"

# Ensure output directory exists
DATA_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Configuration for the scripts to profile
SCRIPTS_TO_PROFILE = [
    "01_download_and_filter.py",
    "02_preprocess_and_parcellate.py",
    "03_compute_graph_metrics.py",
    "04_train_model.py",
]

class MemoryMonitor:
    """
    Background thread to monitor peak memory usage of a target process.
    """
    def __init__(self, pid: int):
        self.pid = pid
        self.peak_memory_gb = 0.0
        self.stop_event = threading.Event()
        self.process = psutil.Process(pid)
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
    
    def start(self):
        self.thread.start()
    
    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=1.0)
    
    def _monitor_loop(self):
        while not self.stop_event.is_set():
            try:
                # Check if process still exists
                if not self.process.is_running():
                    break
                
                mem_info = self.process.memory_info()
                current_gb = mem_info.rss / (1024 ** 3)
                if current_gb > self.peak_memory_gb:
                    self.peak_memory_gb = current_gb
                time.sleep(0.5)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break

def run_script_with_monitoring(script_name: str) -> Dict[str, Any]:
    """
    Runs a specific script and returns a dictionary with execution stats.
    """
    script_path = CODE_DIR / script_name
    
    if not script_path.exists():
        return {
            "script": script_name,
            "status": "skipped",
            "reason": "file_not_found",
            "peak_memory_gb": 0.0,
            "duration_seconds": 0.0,
            "timestamp": datetime.utcnow().isoformat()
        }

    start_time = time.time()
    monitor = None
    
    try:
        # Start the script
        proc = subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=str(CODE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Start memory monitoring
        monitor = MemoryMonitor(proc.pid)
        monitor.start()
        
        # Wait for completion
        stdout, stderr = proc.communicate()
        exit_code = proc.returncode
        
        # Stop monitoring
        monitor.stop()
        
        end_time = time.time()
        duration = end_time - start_time
        
        status = "success" if exit_code == 0 else "failed"
        reason = f"exit_code_{exit_code}" if exit_code != 0 else None
        
        return {
            "script": script_name,
            "status": status,
            "reason": reason,
            "peak_memory_gb": round(monitor.peak_memory_gb, 4),
            "duration_seconds": round(duration, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "exit_code": exit_code
        }

    except Exception as e:
        end_time = time.time()
        if monitor:
            monitor.stop()
        
        return {
            "script": script_name,
            "status": "error",
            "reason": str(e),
            "peak_memory_gb": 0.0,
            "duration_seconds": round(time.time() - start_time, 2),
            "timestamp": datetime.utcnow().isoformat()
        }

def main():
    """
    Main entry point for the CI memory profiling step.
    """
    print(f"Starting CI Memory Profiling at {datetime.utcnow().isoformat()}")
    print(f"Logging to: {LOG_FILE}")
    
    results = []
    
    for script in SCRIPTS_TO_PROFILE:
        print(f"Running profile for: {script}")
        result = run_script_with_monitoring(script)
        results.append(result)
        print(f"  -> Status: {result['status']}, Peak RAM: {result['peak_memory_gb']:.2f} GB")
    
    # Append results to log file (JSONL format)
    with open(LOG_FILE, 'a') as f:
        for res in results:
            f.write(json.dumps(res) + '\n')
    
    print(f"Memory profiling complete. Log written to {LOG_FILE}")
    return 0

if __name__ == "__main__":
    sys.exit(main())