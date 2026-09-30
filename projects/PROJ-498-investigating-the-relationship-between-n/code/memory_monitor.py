"""
Memory monitoring utilities for the preprocessing pipeline.
Provides functions to track and log memory usage.
"""
import os
import sys
import resource
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any

import psutil

# Import from project modules
from synchrony import get_logger

logger = get_logger(__name__)

MEMORY_LIMIT_GB = 6.5

def ensure_metrics_directory():
    """Ensure the metrics directory exists."""
    metrics_dir = Path("data/metrics")
    metrics_dir.mkdir(parents=True, exist_ok=True)
    return metrics_dir

def get_current_rss_mb() -> float:
    """Get current RSS memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def get_current_rss_gb() -> float:
    """Get current RSS memory usage in GB."""
    return get_current_rss_mb() / 1024

def check_memory_limit(current_rss_gb: float) -> bool:
    """Check if current memory usage exceeds the limit."""
    return current_rss_gb > MEMORY_LIMIT_GB

def log_memory_usage(subject_id: str, peak_rss_gb: float, metrics_dir: Path):
    """Log memory usage for a subject to memory_profile.json."""
    memory_file = metrics_dir / "memory_profile.json"
    
    # Load existing data or create new
    if memory_file.exists():
        with open(memory_file, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}

    # Update with new subject data
    data[subject_id] = {
        "peak_rss_gb": round(peak_rss_gb, 4),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Write back
    with open(memory_file, 'w') as f:
        json.dump(data, f, indent=2)

def save_memory_profile(memory_data: Dict[str, Dict[str, Any]], metrics_dir: Path):
    """Save complete memory profile to JSON file."""
    memory_file = metrics_dir / "memory_profile.json"
    with open(memory_file, 'w') as f:
        json.dump(memory_data, f, indent=2)

class MemoryTracker:
    """Context manager for tracking memory usage during processing."""
    
    def __init__(self, subject_id: str):
        self.subject_id = subject_id
        self.peak_rss_gb = 0.0
        self.metrics_dir = ensure_metrics_directory()
    
    def __enter__(self):
        self.start_time = time.time()
        self.initial_rss = get_current_rss_gb()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        current_rss = get_current_rss_gb()
        
        if current_rss > self.peak_rss_gb:
            self.peak_rss_gb = current_rss
        
        # Log memory usage
        log_memory_usage(self.subject_id, self.peak_rss_gb, self.metrics_dir)
        
        logger.info(f"Subject {self.subject_id}: peak RSS = {self.peak_rss_gb:.2f} GB")
        
        if self.peak_rss_gb > MEMORY_LIMIT_GB:
            logger.warning(f"Memory limit exceeded for {self.subject_id}")
            return False
        
        return True

def monitor_and_ensure_limit(subject_id: str) -> bool:
    """
    Monitor memory usage and ensure it stays within limits.
    Returns True if within limits, False if exceeded.
    """
    with MemoryTracker(subject_id) as tracker:
        # Processing happens here
        pass
    
    return tracker.peak_rss_gb <= MEMORY_LIMIT_GB

def main():
    """Main entry point for memory monitoring tests."""
    logger.info("Memory monitoring module loaded")
    logger.info(f"Memory limit: {MEMORY_LIMIT_GB} GB")
    
    # Test memory tracking
    with MemoryTracker("test_subject") as tracker:
        # Simulate some work
        data = [i for i in range(1000000)]
        time.sleep(0.1)
    
    logger.info(f"Test completed, peak RSS: {tracker.peak_rss_gb:.2f} GB")

if __name__ == "__main__":
    main()
