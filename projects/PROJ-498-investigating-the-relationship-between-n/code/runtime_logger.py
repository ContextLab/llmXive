"""
Runtime logging module for the neural synchrony pipeline.

Generates data/metrics/runtime_log.json containing start_time, end_time,
total_duration_minutes, and status to verify SC-002.
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
METRICS_DIR = PROJECT_ROOT / "data" / "metrics"
LOG_FILE = METRICS_DIR / "runtime_log.json"

def ensure_metrics_directory():
    """Ensure the metrics directory exists."""
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

def start_timer():
    """
    Initialize the runtime timer.
    
    Returns:
        float: The start time in seconds since epoch.
    """
    return time.time()

def get_elapsed_minutes(start_time):
    """
    Calculate elapsed time in minutes.
    
    Args:
        start_time (float): Start time in seconds since epoch.
        
    Returns:
        float: Elapsed time in minutes.
    """
    end_time = time.time()
    return (end_time - start_time) / 60.0

def save_runtime_log(start_time, end_time, status="success"):
    """
    Save the runtime log to data/metrics/runtime_log.json.
    
    Args:
        start_time (float): Start time in seconds since epoch.
        end_time (float): End time in seconds since epoch.
        status (str): Status of the pipeline ('success' or 'timeout').
    """
    ensure_metrics_directory()
    
    total_duration_minutes = (end_time - start_time) / 60.0
    
    log_data = {
        "start_time": datetime.fromtimestamp(start_time).isoformat(),
        "end_time": datetime.fromtimestamp(end_time).isoformat(),
        "total_duration_minutes": round(total_duration_minutes, 4),
        "status": status
    }
    
    with open(LOG_FILE, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    print(f"Runtime log saved to {LOG_FILE}")
    return log_data

def main():
    """
    Main entry point for testing the runtime logger.
    
    Simulates a short pipeline run and generates the runtime log.
    """
    print("Starting runtime logger test...")
    start = start_timer()
    
    # Simulate some work
    time.sleep(1)
    
    end = time.time()
    status = "success"
    
    log_data = save_runtime_log(start, end, status)
    print(f"Test completed. Status: {log_data['status']}, Duration: {log_data['total_duration_minutes']:.4f} minutes")

if __name__ == "__main__":
    main()
