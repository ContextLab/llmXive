"""
Configuration and utility functions for the project.
"""
import os
import sys
import signal
import time
import json
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

# Random seeds
RANDOM_SEED = 42

# API Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
NVD_API_KEY = os.getenv("NVD_API_KEY", "")

# Pipeline Timeout Configuration (5.5 hours in seconds)
# SC-001 requires execution within 6 hours. We leave 30 mins buffer.
PIPELINE_TIMEOUT_SECONDS = 19800  # 5.5 * 60 * 60
TIMEOUT_OUTPUT_FILE = DATA_PROCESSED_DIR / "pipeline_timeout.json"

def ensure_directories():
    """
    Creates the required directory structure for the project.
    This function ensures that data/raw, data/processed, logs, and contracts directories exist.
    """
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        LOGS_DIR,
        CONTRACTS_DIR,
        PROJECT_ROOT / "code" / "data",
        PROJECT_ROOT / "code" / "analysis",
        PROJECT_ROOT / "tests" / "unit",
        PROJECT_ROOT / "tests" / "integration",
        PROJECT_ROOT / "tests" / "contract",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    # Initialize __init__.py files if missing
    init_files = [
        PROJECT_ROOT / "code" / "__init__.py",
        PROJECT_ROOT / "code" / "data" / "__init__.py",
        PROJECT_ROOT / "code" / "analysis" / "__init__.py",
        PROJECT_ROOT / "tests" / "__init__.py",
        PROJECT_ROOT / "tests" / "unit" / "__init__.py",
        PROJECT_ROOT / "tests" / "integration" / "__init__.py",
        PROJECT_ROOT / "tests" / "contract" / "__init__.py",
    ]
    for f in init_files:
        if not f.exists():
            f.touch()

class TimeoutError(Exception):
    """Custom exception raised when the pipeline timeout is exceeded."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout on Unix systems."""
    raise TimeoutError("Pipeline execution exceeded the 5.5-hour limit.")

@contextmanager
def pipeline_timeout_guard():
    """
    Context manager to enforce a hard timeout on the pipeline execution.
    Uses signal.alarm on Linux/Unix. On Windows, it uses a threading watchdog.
    
    If timeout occurs:
    1. Writes pipeline_timeout.json to data/processed/
    2. Exits the process with code 1.
    """
    # Check if we are on a Unix-like system (supports signal.alarm)
    if hasattr(signal, 'alarm'):
        # Set the alarm
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(PIPELINE_TIMEOUT_SECONDS)
        try:
            yield
        finally:
            # Cancel the alarm
            signal.alarm(0)
    else:
        # Fallback for Windows: Use a daemon thread to monitor time
        import threading
        start_time = time.time()
        timeout_occurred = False

        def watchdog():
            nonlocal timeout_occurred
            while not timeout_occurred:
                if time.time() - start_time > PIPELINE_TIMEOUT_SECONDS:
                    timeout_occurred = True
                    _write_timeout_file_and_exit()
                time.sleep(1) # Check every second

        timer_thread = threading.Thread(target=watchdog, daemon=True)
        timer_thread.start()
        try:
            yield
        finally:
            # If we exit normally, the daemon thread will die with the process
            pass

def _write_timeout_file_and_exit():
    """Writes the timeout JSON file and exits with code 1."""
    ensure_directories()
    timeout_data = {
        "status": "timeout",
        "limit_seconds": PIPELINE_TIMEOUT_SECONDS,
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Pipeline execution exceeded the 5.5-hour limit defined in config.py."
    }
    with open(TIMEOUT_OUTPUT_FILE, 'w') as f:
        json.dump(timeout_data, f, indent=2)
    print(f"CRITICAL: Pipeline timeout detected. Wrote {TIMEOUT_OUTPUT_FILE}", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    ensure_directories()
    print("Directories ensured.")
    print(f"Pipeline timeout set to {PIPELINE_TIMEOUT_SECONDS} seconds (5.5 hours).")
    print(f"Timeout output file: {TIMEOUT_OUTPUT_FILE}")
