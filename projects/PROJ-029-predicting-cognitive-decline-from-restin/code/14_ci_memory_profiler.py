"""
CI Memory Profiler for llmXive Pipeline (T043)

This script is designed to be run in a CI environment to log peak memory usage
for each major pipeline script. It wraps the execution of the primary scripts,
monitors RAM usage via `psutil`, and appends a structured log entry to
`data/artifacts/memory_profile.log`.

It does not re-implement the logic of the scripts but orchestrates their execution
with memory monitoring.
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

# Project root relative to this file's location
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
ARTIFACTS_DIR = PROJECT_ROOT / "data" / "artifacts"
LOG_FILE = ARTIFACTS_DIR / "memory_profile.log"

# Scripts to profile (relative to code/)
# Order matters for logical flow, though T043 is a CI step
SCRIPTS_TO_PROFILE = [
    "00_data_gate.py",
    "01_download_and_filter.py",
    "02_preprocess_and_parcellate.py",
    "03_compute_graph_metrics.py",
    "04_train_model.py",
    "06_runtime_verifier.py", # Includes training logic
    "06_permutation_test.py", # If it exists, otherwise handled by 04/05 flow
    "07_sensitivity_analysis.py",
    "09_generate_report.py",
]

# Fallback for permutation test if script name differs or is integrated
# Based on tasks.md, 06_permutation_test.py is the target
if not (CODE_DIR / "06_permutation_test.py").exists():
    # If the file doesn't exist yet (e.g. if we are running before T029), skip it or note it
    # For T043, we assume the pipeline scripts exist as per completed tasks.
    # If 06_permutation_test.py is missing, we might skip or log a warning.
    pass

def get_memory_usage_gb():
    """Get current process memory usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def run_script_with_monitoring(script_name: str) -> dict:
    """
    Runs a script and monitors peak memory usage.
    Returns a dict with script_name, status, peak_memory_gb, duration_seconds, error.
    """
    script_path = CODE_DIR / script_name
    if not script_path.exists():
        return {
            "script": script_name,
            "status": "skipped",
            "reason": "File not found",
            "peak_memory_gb": 0.0,
            "duration_seconds": 0.0
        }

    start_time = time.time()
    peak_memory = 0.0
    error_msg = None
    status = "failed"

    # Thread to monitor memory of the subprocess
    # We need to monitor the subprocess, not this parent process.
    # We will spawn the process and monitor it.
    try:
        # Start the process
        proc = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT)
        )

        # Monitor loop
        while proc.poll() is None:
            try:
                mem_gb = proc.memory_info().rss / (1024 ** 3)
                if mem_gb > peak_memory:
                    peak_memory = mem_gb
            except psutil.NoSuchProcess:
                # Process might have exited between checks
                break
            time.sleep(0.5)

        # Final check after exit
        try:
            mem_gb = proc.memory_info().rss / (1024 ** 3)
            if mem_gb > peak_memory:
                peak_memory = mem_gb
        except psutil.NoSuchProcess:
            pass

        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            status = "failed"
            error_msg = stderr.decode('utf-8', errors='ignore')
        else:
            status = "completed"

    except Exception as e:
        status = "error"
        error_msg = str(e)

    duration = time.time() - start_time

    return {
        "script": script_name,
        "status": status,
        "peak_memory_gb": round(peak_memory, 4),
        "duration_seconds": round(duration, 2),
        "error": error_msg
    }

def log_entry(entry: dict):
    """Appends a JSON log entry to the memory profile log file."""
    ensure_dir(LOG_FILE.parent)
    timestamp = datetime.now().isoformat()
    log_record = {
        "timestamp": timestamp,
        **entry
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_record) + "\n")

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def main():
    print(f"Starting CI Memory Profiling for {len(SCRIPTS_TO_PROFILE)} scripts...")
    print(f"Output log: {LOG_FILE}")

    # Ensure artifacts directory exists
    ensure_dir(ARTIFACTS_DIR)

    # Clear previous log for this CI run? Or append?
    # Task says "logs ... for future audit", appending is safer for history,
    # but for a specific CI run, a fresh log or a run ID is better.
    # We will append to allow accumulation, but include timestamp.
    # If the file exists, we could rename it or just append.
    # Let's append.

    results = []
    for script in SCRIPTS_TO_PROFILE:
        print(f"Profiling: {script} ...")
        result = run_script_with_monitoring(script)
        results.append(result)
        log_entry(result)
        print(f"  -> Status: {result['status']}, Peak RAM: {result['peak_memory_gb']:.2f} GB")

    print("\nProfiling complete. Results written to memory_profile.log")

    # Optional: Exit with error if any critical script failed?
    # For T043, we just need to log.
    return 0

if __name__ == "__main__":
    sys.exit(main())