import logging
import json
import os
import sys
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
LOG_DIR = "data/logs"
COMPARISON_LOG_FILE = "comparisons.jsonl"
RESOURCE_LOG_FILE = "resource_stats.jsonl"

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

def init_logging(name: str = "llmXive") -> logging.Logger:
    """
    Initializes the logger for the pipeline.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Console handler
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler for general logs
        file_handler = logging.FileHandler(os.path.join(LOG_DIR, f"{name}.log"))
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def log_pairwise_comparison(
    query_id: str,
    doc1_id: str,
    doc2_id: str,
    similarity: float,
    is_wasted: bool,
    timestamp: Optional[float] = None
) -> None:
    """
    Logs a pairwise comparison to the comparisons.jsonl file.
    
    Args:
        query_id: The query identifier.
        doc1_id: First document identifier.
        doc2_id: Second document identifier.
        similarity: Calculated similarity score.
        is_wasted: Whether this call is considered 'wasted'.
        timestamp: Optional timestamp (defaults to current time).
    """
    if timestamp is None:
        timestamp = time.time()
    
    log_entry = {
        "timestamp": timestamp,
        "query_id": query_id,
        "doc1_id": doc1_id,
        "doc2_id": doc2_id,
        "similarity": similarity,
        "is_wasted": is_wasted,
        "datetime": datetime.fromtimestamp(timestamp).isoformat()
    }
    
    log_path = os.path.join(LOG_DIR, COMPARISON_LOG_FILE)
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')

# Resource monitoring globals
_monitoring_active = False
_monitor_thread: Optional[threading.Thread] = None
_start_time: Optional[float] = None

def _resource_monitor_loop(interval: float = 5.0) -> None:
    """
    Background thread that monitors resource usage.
    """
    import resource
    global _monitoring_active
    
    while _monitoring_active:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        log_entry = {
            "timestamp": time.time(),
            "max_rss_kb": usage.ru_maxrss,
            "user_time": usage.ru_utime,
            "system_time": usage.ru_stime,
            "datetime": datetime.now().isoformat()
        }
        
        log_path = os.path.join(LOG_DIR, RESOURCE_LOG_FILE)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        time.sleep(interval)

def start_resource_monitoring(interval: float = 5.0) -> None:
    """
    Starts the background resource monitoring thread.
    """
    global _monitoring_active, _monitor_thread, _start_time
    
    if _monitoring_active:
        return
    
    _monitoring_active = True
    _start_time = time.time()
    _monitor_thread = threading.Thread(target=_resource_monitor_loop, args=(interval,), daemon=True)
    _monitor_thread.start()

def stop_resource_monitoring() -> Dict[str, Any]:
    """
    Stops the resource monitoring and returns final stats.
    """
    global _monitoring_active, _monitor_thread
    
    _monitoring_active = False
    if _monitor_thread:
        _monitor_thread.join(timeout=2.0)
        _monitor_thread = None
    
    import resource
    usage = resource.getrusage(resource.RUSAGE_SELF)
    end_time = time.time()
    
    stats = {
        "total_runtime_seconds": end_time - (_start_time or end_time),
        "max_rss_kb": usage.ru_maxrss,
        "user_time": usage.ru_utime,
        "system_time": usage.ru_stime,
        "total_cpu_time": usage.ru_utime + usage.ru_stime
    }
    
    # Log final stats
    log_entry = {
        "timestamp": end_time,
        "final": True,
        "stats": stats,
        "datetime": datetime.now().isoformat()
    }
    
    log_path = os.path.join(LOG_DIR, RESOURCE_LOG_FILE)
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    return stats

def get_comparison_log_path() -> str:
    """Returns the path to the comparison log file."""
    return os.path.join(LOG_DIR, COMPARISON_LOG_FILE)

def get_resource_log_path() -> str:
    """Returns the path to the resource stats log file."""
    return os.path.join(LOG_DIR, RESOURCE_LOG_FILE)

def main():
    """
    Test function to verify logging infrastructure.
    """
    logger = init_logging("test_logging")
    logger.info("Logging infrastructure initialized.")
    
    start_resource_monitoring(interval=1.0)
    time.sleep(2.0)
    
    log_pairwise_comparison("q1", "d1", "d2", 0.96, True)
    log_pairwise_comparison("q1", "d3", "d4", 0.50, False)
    
    stats = stop_resource_monitoring()
    print(f"Monitoring stats: {stats}")
    
    logger.info("Test completed. Check data/logs/ for output files.")

if __name__ == "__main__":
    main()
