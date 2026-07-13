"""
CI Memory Profiler for T043.

This script acts as a CI step to log peak memory usage for each major
pipeline script (download, preprocessing, modeling, permutation) to
data/artifacts/memory_profile.log.

It wraps the execution of the target scripts, monitors RAM usage via psutil,
and appends a structured log entry upon completion or failure.
"""
import os
import sys
import time
import json
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path to allow imports if needed, though this script
# primarily spawns subprocesses.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_ARTIFACTS_DIR = PROJECT_ROOT / "data" / "artifacts"
MEMORY_LOG_PATH = DATA_ARTIFACTS_DIR / "memory_profile.log"

# Ensure the artifacts directory exists
DATA_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Define the major scripts to profile based on the pipeline phases
# These correspond to T017, T018, T023/T029, T029 (Permutation)
SCRIPTS_TO_PROFILE = [
    {
        "name": "download_and_filter",
        "script": "01_download_and_filter.py",
        "phase": "Data Ingestion"
    },
    {
        "name": "preprocess_and_parcellate",
        "script": "02_preprocess_and_parcellate.py",
        "phase": "Preprocessing"
    },
    {
        "name": "train_model",
        "script": "04_train_model.py",
        "phase": "Modeling"
    },
    {
        "name": "permutation_test",
        "script": "06_permutation_test.py",
        "phase": "Significance Testing"
    }
]

class MemoryMonitor:
    """
    A lightweight thread-based memory monitor that polls the peak RSS
    of a specific process ID.
    """
    def __init__(self, pid: int):
        self.pid = pid
        self.peak_memory_gb = 0.0
        self.stop_event = threading.Event()
        self.thread = None

    def _monitor_loop(self):
        import psutil
        try:
            process = psutil.Process(self.pid)
            while not self.stop_event.is_set():
                try:
                    mem_info = process.memory_info()
                    current_gb = mem_info.rss / (1024 ** 3)
                    if current_gb > self.peak_memory_gb:
                        self.peak_memory_gb = current_gb
                except psutil.NoSuchProcess:
                    # Process finished
                    break
                time.sleep(0.1) # Poll every 100ms
        except Exception as e:
            # Log error but don't crash the monitor thread
            print(f"Monitor error for PID {self.pid}: {e}", file=sys.stderr)

    def start(self):
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=2.0)

def run_script_with_monitoring(script_path: Path, script_name: str, phase: str) -> Dict[str, Any]:
    """
    Executes a script and monitors its peak memory usage.
    
    Returns a dictionary containing execution status, peak memory, and duration.
    """
    start_time = time.time()
    monitor = None
    result = {
        "script": script_name,
        "phase": phase,
        "timestamp": datetime.now().isoformat(),
        "status": "unknown",
        "peak_memory_gb": 0.0,
        "duration_seconds": 0.0,
        "error": None
    }

    try:
        # Launch the script
        cmd = [sys.executable, str(script_path)]
        # We run it in the context of the code directory to resolve relative imports correctly
        process = subprocess.Popen(
            cmd,
            cwd=str(CODE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Start monitoring the process
        monitor = MemoryMonitor(process.pid)
        monitor.start()

        # Wait for completion
        stdout, stderr = process.communicate()
        
        # Stop monitoring
        monitor.stop()

        result["duration_seconds"] = time.time() - start_time
        result["peak_memory_gb"] = round(monitor.peak_memory_gb, 4)
        
        if process.returncode == 0:
            result["status"] = "success"
        else:
            result["status"] = "failed"
            result["error"] = f"Exit code {process.returncode}"
            # Append stderr to error message if available
            if stderr:
                result["error"] += f" | Stderr: {stderr.decode('utf-8', errors='ignore')[:200]}"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["duration_seconds"] = time.time() - start_time
        if monitor:
            monitor.stop()
            result["peak_memory_gb"] = round(monitor.peak_memory_gb, 4)

    return result

def log_entry(log_data: Dict[str, Any]):
    """
    Appends a JSON log entry to the memory profile log file.
    """
    with open(MEMORY_LOG_PATH, "a") as f:
        f.write(json.dumps(log_data) + "\n")

def main():
    """
    Main entry point for the CI memory profiling step.
    Iterates through defined scripts, runs them (or simulates if they require data),
    and logs the results.
    
    Note: In a real CI environment, the data would be present. If data is missing,
    the underlying scripts will fail (as per T043 requirements to fail loudly),
    and this profiler will capture the failure and memory stats up to the crash.
    """
    print(f"Starting Memory Profiling CI Step for {len(SCRIPTS_TO_PROFILE)} scripts...")
    print(f"Log destination: {MEMORY_LOG_PATH}")
    
    # Clear previous log if we want a fresh run, or append. 
    # For CI auditing, we typically append to a build-specific log or rotate.
    # Here we append to the standard artifact log as requested.
    
    if not MEMORY_LOG_PATH.exists():
        # Write header
        with open(MEMORY_LOG_PATH, "w") as f:
            f.write("# Memory Profile Log for PROJ-029\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write("# Format: JSON per line\n")

    all_results = []
    
    for item in SCRIPTS_TO_PROFILE:
        script_path = CODE_DIR / item["script"]
        
        if not script_path.exists():
            print(f"WARNING: Script {item['script']} not found. Skipping.")
            all_results.append({
                "script": item["script"],
                "phase": item["phase"],
                "status": "skipped",
                "reason": "File not found"
            })
            continue

        print(f"Running profiler for: {item['name']} ({item['script']})...")
        result = run_script_with_monitoring(script_path, item["name"], item["phase"])
        
        # Ensure peak memory is recorded even if failed
        if "peak_memory_gb" not in result:
            result["peak_memory_gb"] = 0.0
            
        log_entry(result)
        all_results.append(result)
        
        status_icon = "✓" if result["status"] == "success" else "✗"
        print(f"  [{status_icon}] {item['name']}: {result['status']} | Peak RAM: {result['peak_memory_gb']:.2f} GB | Time: {result['duration_seconds']:.1f}s")
        
        if result["status"] != "success":
            print(f"    Error: {result.get('error', 'Unknown')}")

    print(f"\nProfiling complete. Results written to {MEMORY_LOG_PATH}")
    
    # Exit with error if any critical script failed, depending on CI policy.
    # For this task, we log and exit 0 if the logging itself worked, 
    # but typically CI would fail if a script failed.
    # We return 0 to indicate the profiling step succeeded, even if scripts failed.
    return 0

if __name__ == "__main__":
    sys.exit(main())