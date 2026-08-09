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
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import psutil

# Configuration
LOG_DIR = "data/processed"
COMPARISON_LOG_FILE = os.path.join(LOG_DIR, "comparison_log.json")
RESOURCE_LOG_FILE = os.path.join(LOG_DIR, "resource_stats.json")

# Global state for resource monitoring
_monitoring_active = False
_monitor_thread: Optional[threading.Thread] = None
_resource_stats: List[Dict[str, Any]] = []
_resource_lock = threading.Lock()
_logger: Optional[logging.Logger] = None

def _get_logger() -> logging.Logger:
    """Get or create the project logger."""
    global _logger
    if _logger is None:
        _logger = logging.getLogger("llmXive")
        _logger.setLevel(logging.INFO)
        if not _logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            _logger.addHandler(handler)
    return _logger

def init_logging():
    """Initialize the logging infrastructure."""
    logger = _get_logger()
    logger.info("Logging initialized")
    
    # Ensure output directory exists
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Clear existing log files to start fresh
    if os.path.exists(COMPARISON_LOG_FILE):
        os.remove(COMPARISON_LOG_FILE)
    
    return logger

def log_pairwise_comparison(
    pair_id: str,
    doc1_id: str,
    doc2_id: str,
    cosine_sim: float,
    is_wasted: bool,
    timestamp: Optional[str] = None
):
    """
    Log a pairwise comparison to the JSONL file.
    
    Args:
        pair_id: Unique identifier for the comparison pair
        doc1_id: ID of the first document
        doc2_id: ID of the second document
        cosine_sim: Cosine similarity score between the documents
        is_wasted: Boolean indicating if this is a wasted call
        timestamp: Optional ISO format timestamp (auto-generated if None)
    
    This function serves FR-003 by recording every pairwise comparison.
    The log format is JSONL with one entry per line.
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat() + "Z"
    
    log_entry = {
        "pair_id": pair_id,
        "doc1_id": doc1_id,
        "doc2_id": doc2_id,
        "cosine_sim": float(cosine_sim),
        "is_wasted": bool(is_wasted),
        "timestamp": timestamp
    }
    
    # Append to the log file in JSONL format
    with open(COMPARISON_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

def _collect_resource_stats():
    """Collect current resource usage statistics."""
    process = psutil.Process(os.getpid())
    
    stats = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "cpu_percent": process.cpu_percent(),
        "memory_percent": process.memory_percent(),
        "memory_mb": process.memory_info().rss / (1024 * 1024),
        "thread_count": process.num_threads()
    }
    
    with _resource_lock:
        _resource_stats.append(stats)

def start_resource_monitoring(interval_seconds: float = 5.0):
    """
    Start background thread to monitor resource usage.
    
    Args:
        interval_seconds: How often to collect stats (default: 5 seconds)
    """
    global _monitoring_active, _monitor_thread
    
    if _monitoring_active:
        return
    
    _monitoring_active = True
    _resource_stats.clear()
    
    def monitor_loop():
        while _monitoring_active:
            _collect_resource_stats()
            time.sleep(interval_seconds)
    
    _monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    _monitor_thread.start()
    
    _get_logger().info("Resource monitoring started")

def stop_resource_monitoring():
    """Stop the resource monitoring thread and write stats to disk."""
    global _monitoring_active, _monitor_thread
    
    _monitoring_active = False
    if _monitor_thread is not None:
        _monitor_thread.join(timeout=2.0)
        _monitor_thread = None
    
    # Write resource stats to file
    with _resource_lock:
        stats_snapshot = _resource_stats.copy()
    
    if stats_snapshot:
        # Calculate summary statistics
        summary = {
            "total_samples": len(stats_snapshot),
            "max_memory_mb": max(s["memory_mb"] for s in stats_snapshot),
            "avg_memory_mb": sum(s["memory_mb"] for s in stats_snapshot) / len(stats_snapshot),
            "max_cpu_percent": max(s["cpu_percent"] for s in stats_snapshot),
            "avg_cpu_percent": sum(s["cpu_percent"] for s in stats_snapshot) / len(stats_snapshot),
            "samples": stats_snapshot
        }
        
        with open(RESOURCE_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        
        _get_logger().info(f"Resource monitoring stopped. Max memory: {summary['max_memory_mb']:.2f} MB")

def get_comparison_log_path() -> str:
    """Return the path to the comparison log file."""
    return COMPARISON_LOG_FILE

def get_resource_log_path() -> str:
    """Return the path to the resource stats log file."""
    return RESOURCE_LOG_FILE

def main():
    """Main entry point for testing the logging infrastructure."""
    init_logging()
    start_resource_monitoring(interval_seconds=1.0)
    
    # Simulate some comparisons
    for i in range(5):
        log_pairwise_comparison(
            pair_id=f"pair_{i}",
            doc1_id=f"doc_{i}",
            doc2_id=f"doc_{i+1}",
            cosine_sim=0.90 + (i * 0.02),
            is_wasted=(0.90 + (i * 0.02)) > 0.95
        )
        time.sleep(0.5)
    
    stop_resource_monitoring()
    print(f"Comparison log written to: {get_comparison_log_path()}")
    print(f"Resource log written to: {get_resource_log_path()}")

if __name__ == "__main__":
    main()