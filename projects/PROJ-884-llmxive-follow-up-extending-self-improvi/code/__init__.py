import json
import os
import time
import resource
from datetime import datetime, timezone
from pathlib import Path

# Ensure the data/processed directory exists
DATA_PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
LOG_FILE_PATH = DATA_PROCESSED_DIR / "experiment.log"

def _get_resource_usage():
    """
    Captures current resource usage (CPU time and memory) using the resource module.
    Returns a dictionary with 'user_time', 'system_time', and 'max_rss_kb'.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "user_time": usage.ru_utime,
        "system_time": usage.ru_stime,
        "max_rss_kb": usage.ru_maxrss
    }

def log_experiment_entry():
    """
    Captures a single log entry with timestamp, wall-clock time, and resource usage.
    Appends the entry as a JSON line to data/processed/experiment.log.
    """
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    entry = {
        "timestamp": now.isoformat(),
        "wall_clock": time.time(),
        "resource_usage": _get_resource_usage()
    }

    with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def setup_logging():
    """
    Initializes the logging infrastructure by ensuring the log file exists.
    Can be called at the start of an experiment to create a fresh log or
    append to an existing one.
    """
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE_PATH.exists():
        LOG_FILE_PATH.touch()

# Convenience alias for immediate usage
log = log_experiment_entry
