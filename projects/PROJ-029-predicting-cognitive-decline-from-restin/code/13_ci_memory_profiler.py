"""
CI Memory Profiler Task (T043)

This script acts as a CI step to log peak memory usage for each major
research script in the pipeline. It runs the scripts sequentially,
monitors their peak RAM usage using psutil (via the existing memory_profiler utility),
and appends a structured log entry to data/artifacts/memory_profile.log.

Scripts profiled:
- 00_data_gate.py
- 01_download_and_filter.py
- 02_preprocess_and_parcellate.py
- 03_compute_graph_metrics.py
- 04_train_model.py
- 06_permutation_test.py (mapped from task description 'permutation')
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

# Add the code directory to the path so we can import local utilities if needed,
# though we will primarily use subprocess to run the scripts.
CODE_DIR = Path(__file__).parent
PROJECT_ROOT = CODE_DIR.parent
ARTIFACTS_DIR = PROJECT_ROOT / "data" / "artifacts"
LOG_FILE = ARTIFACTS_DIR / "memory_profile.log"

# Ensure the artifacts directory exists
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# List of major scripts to profile, relative to code/
# Note: 06_permutation_test.py is the script for permutation testing as per tasks.md
SCRIPTS_TO_PROFILE = [
    "00_data_gate.py",
    "01_download_and_filter.py",
    "02_preprocess_and_parcellate.py",
    "03_compute_graph_metrics.py",
    "04_train_model.py",
    "06_permutation_test.py",
]

def get_memory_usage_gb():
    """Get current memory usage of the current process in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def run_script_with_monitoring(script_name: str, timeout_seconds: int = 3600) -> dict:
    """
    Runs a script via subprocess, monitors its peak memory usage.
    
    Since we cannot easily attach to the child process's memory from the parent
    without complex IPC, we will use a wrapper approach:
    1. We rely on the fact that the scripts themselves might not be instrumented
       to report memory in a standard way.
    2. We will spawn a monitoring thread that checks the child process's memory
       periodically until it exits.
    
    Returns a dict with script_name, status, peak_memory_gb, duration_seconds.
    """
    script_path = CODE_DIR / script_name
    
    if not script_path.exists():
        return {
            "script": script_name,
            "status": "failed",
            "error": "Script not found",
            "peak_memory_gb": 0.0,
            "duration_seconds": 0.0
        }

    start_time = time.time()
    peak_memory_gb = 0.0
    child_process = None

    # Start the child process
    try:
        child_process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(CODE_DIR)
        )
    except Exception as e:
        return {
            "script": script_name,
            "status": "failed",
            "error": str(e),
            "peak_memory_gb": 0.0,
            "duration_seconds": time.time() - start_time
        }

    # Monitoring thread
    def monitor_memory():
        nonlocal peak_memory_gb
        while True:
            try:
                if child_process.poll() is not None:
                    break
                try:
                    # psutil can track the child process by PID
                    p = psutil.Process(child_process.pid)
                    mem = p.memory_info().rss / (1024 ** 3)
                    if mem > peak_memory_gb:
                        peak_memory_gb = mem
                except psutil.NoSuchProcess:
                    break
            except Exception:
                break
            time.sleep(0.5) # Check every 500ms

    monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
    monitor_thread.start()

    # Wait for process to finish or timeout
    try:
        stdout, stderr = child_process.communicate(timeout=timeout_seconds)
        return_code = child_process.returncode
    except subprocess.TimeoutExpired:
        child_process.kill()
        stdout, stderr = child_process.communicate()
        return_code = -1
    
    monitor_thread.join() # Ensure monitoring stops

    duration = time.time() - start_time

    if return_code == 0:
        status = "completed"
    else:
        # Check if it's a specific "no data" exit code or expected failure
        # For T043, we want to log memory even if the script exits early due to missing data,
        # as long as it ran. However, if it crashed immediately, it might be an error.
        # We'll mark it as 'completed_with_exit_code' if it ran for a bit, or 'failed' if instant.
        if duration > 5.0:
            status = "completed_with_exit_code"
        else:
            status = "failed"

    return {
        "script": script_name,
        "status": status,
        "exit_code": return_code,
        "peak_memory_gb": round(peak_memory_gb, 4),
        "duration_seconds": round(duration, 2),
        "stdout_sample": stdout.decode('utf-8', errors='ignore')[:500] if stdout else "",
        "stderr_sample": stderr.decode('utf-8', errors='ignore')[:500] if stderr else ""
    }

def log_entry(result: dict):
    """Appends a log entry to the memory_profile.log file."""
    timestamp = datetime.now().isoformat()
    entry = {
        "timestamp": timestamp,
        **result
    }
    
    # Append as JSONL (one JSON object per line) for easy parsing later
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def main():
    print(f"Starting CI Memory Profiler for project: {PROJECT_ROOT.name}")
    print(f"Logging to: {LOG_FILE}")
    
    # Clear previous log if it exists? No, we append for audit trail.
    # But let's print a header if the file is new.
    if not LOG_FILE.exists():
        with open(LOG_FILE, "w") as f:
            f.write(f"# Memory Profile Log for {PROJECT_ROOT.name}\n")
            f.write(f"# Generated at {datetime.now().isoformat()}\n")
            f.write("# Format: JSONL\n\n")

    results = []
    
    for script in SCRIPTS_TO_PROFILE:
        print(f"\n--- Profiling {script} ---")
        try:
            result = run_script_with_monitoring(script)
            results.append(result)
            log_entry(result)
            print(f"  Status: {result['status']}")
            print(f"  Peak Memory: {result['peak_memory_gb']:.2f} GB")
            print(f"  Duration: {result['duration_seconds']:.1f} s")
            
            if result['status'] in ['failed', 'completed_with_exit_code']:
                print(f"  Note: Script exited with code {result.get('exit_code', 'N/A')}")
                if result.get('stderr_sample'):
                    print(f"  Stderr (truncated): {result['stderr_sample']}")
        except Exception as e:
            error_result = {
                "script": script,
                "status": "exception",
                "error": str(e),
                "peak_memory_gb": 0.0,
                "duration_seconds": 0.0
            }
            results.append(error_result)
            log_entry(error_result)
            print(f"  Error: {e}")

    print(f"\n--- Summary ---")
    print(f"Total scripts profiled: {len(results)}")
    for r in results:
        print(f"  {r['script']}: {r['status']} ({r['peak_memory_gb']:.2f} GB)")
    
    print(f"\nFull log written to: {LOG_FILE}")
    return 0

if __name__ == "__main__":
    sys.exit(main())