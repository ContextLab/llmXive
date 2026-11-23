"""
Logging infrastructure for the llmXive pipeline.

Records pairwise comparisons and resource usage stats in JSONL format.
Serves FR-003 and ensures executability.
"""
import logging
import json
import os
import sys
import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime
from config import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration for log paths
# Ensure we use the project's data directory structure
DATA_DIR = "data/processed"
# Corrected paths to match task spec: JSONL for comparisons, JSON for resources
COMPARISON_LOG_PATH = os.path.join(DATA_DIR, "comparison_log.jsonl")
RESOURCE_LOG_PATH = os.path.join(DATA_DIR, "resource_log.json")

# Global lock for thread-safe file writing
_log_lock = threading.Lock()
_resource_monitor_thread: Optional[threading.Thread] = None
_stop_monitoring_event = threading.Event()
_monitor_start_time: Optional[float] = None

def _get_timestamp() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.utcnow().isoformat() + "Z"

def init_logging():
    """Initialize logging infrastructure and ensure directories exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    # Clear existing logs to ensure a fresh run
    if os.path.exists(COMPARISON_LOG_PATH):
        os.remove(COMPARISON_LOG_PATH)
    if os.path.exists(RESOURCE_LOG_PATH):
        os.remove(RESOURCE_LOG_PATH)
    logger.info(f"Logging initialized. Comparison log: {COMPARISON_LOG_PATH}, Resource log: {RESOURCE_LOG_PATH}")

def get_comparison_log_path() -> str:
    return COMPARISON_LOG_PATH

def get_resource_log_path() -> str:
    return RESOURCE_LOG_PATH

def log_pairwise_comparison(pair_id: str, doc1_id: str, doc2_id: str, cosine_sim: float, is_wasted: bool):
    """
    Append a comparison log entry to the JSONL file.
    Format: {"pair_id": str, "doc1_id": str, "doc2_id": str, "cosine_sim": float, "is_wasted": bool, "timestamp": str}
    """
    entry = {
        "pair_id": pair_id,
        "doc1_id": doc1_id,
        "doc2_id": doc2_id,
        "cosine_sim": float(cosine_sim),
        "is_wasted": bool(is_wasted),
        "timestamp": _get_timestamp()
    }
    
    with _log_lock:
        with open(COMPARISON_LOG_PATH, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    logger.debug(f"Logged comparison: {pair_id} (wasted={is_wasted})")

def _collect_resource_stats() -> Dict[str, Any]:
    """Collect current CPU time and memory usage."""
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, convert to MB
        max_rss_mb = usage.ru_maxrss / 1024.0 
        
        # Calculate elapsed time if monitoring started
        elapsed = time.time() - _monitor_start_time if _monitor_start_time else 0.0

        return {
            "timestamp": _get_timestamp(),
            "elapsed_sec": elapsed,
            "max_rss_mb": max_rss_mb,
            "user_cpu_sec": usage.ru_utime,
            "system_cpu_sec": usage.ru_stime,
            "voluntary_context_switches": usage.ru_nvcsw,
            "involuntary_context_switches": usage.ru_nivcsw
        }
    except Exception as e:
        logger.warning(f"Could not collect resource stats: {e}")
        return {
            "timestamp": _get_timestamp(),
            "error": str(e)
        }

def _monitor_loop(interval_seconds: float = 60.0):
    """Background thread to periodically collect resource stats."""
    while not _stop_monitoring_event.is_set():
        stats = _collect_resource_stats()
        with _log_lock:
            with open(RESOURCE_LOG_PATH, 'a') as f:
                f.write(json.dumps(stats) + '\n')
        # Wait with interruptible sleep
        _stop_monitoring_event.wait(interval_seconds)

def start_resource_monitoring(interval_seconds: float = 60.0):
    """Start the background thread for resource monitoring."""
    global _resource_monitor_thread, _monitor_start_time
    if _resource_monitor_thread is not None and _resource_monitor_thread.is_alive():
        logger.warning("Resource monitoring already running")
        return

    _monitor_start_time = time.time()
    _stop_monitoring_event.clear()
    _resource_monitor_thread = threading.Thread(
        target=_monitor_loop, 
        args=(interval_seconds,), 
        daemon=True
    )
    _resource_monitor_thread.start()
    logger.info("Resource monitoring started")

def stop_resource_monitoring():
    """Stop the background monitoring thread and write final stats."""
    global _resource_monitor_thread
    if _resource_monitor_thread is None:
        return

    _stop_monitoring_event.set()
    _resource_monitor_thread.join(timeout=5.0)
    
    # Write final stats
    final_stats = _collect_resource_stats()
    final_stats["status"] = "stopped"
    with _log_lock:
        with open(RESOURCE_LOG_PATH, 'a') as f:
            f.write(json.dumps(final_stats) + '\n')
    
    _resource_monitor_thread = None
    logger.info("Resource monitoring stopped")

def main():
    """CLI entry point for testing logging functionality."""
    init_logging()
    start_resource_monitoring(interval_seconds=1.0)
    
    # Simulate a few comparisons
    for i in range(5):
        log_pairwise_comparison(
            pair_id=f"test_pair_{i}",
            doc1_id=f"doc_A_{i}",
            doc2_id=f"doc_B_{i}",
            cosine_sim=0.95 + (i * 0.01),
            is_wasted=(0.95 + (i * 0.01)) > 0.95
        )
        time.sleep(0.1)
    
    stop_resource_monitoring()
    logger.info("Test run complete. Check data/processed/comparison_log.jsonl and data/processed/resource_log.json")

if __name__ == "__main__":
    main()