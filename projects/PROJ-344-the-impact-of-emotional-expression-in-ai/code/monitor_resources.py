"""
Resource monitoring module for the llmXive pipeline.

Tracks peak RAM usage during execution and logs it to state/memory_log.csv.
Asserts that memory usage stays within the 7GB limit defined in project constraints.
"""
import os
import csv
import psutil
import time
import sys
from datetime import datetime
from typing import Optional, Dict, Any

# Import logging utilities from existing project modules
from logging_config import get_logger, get_state_log_path

# Initialize logger
logger = get_logger(__name__)

# Configuration constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024**3
STATE_DIR = "state"
MEMORY_LOG_FILE = os.path.join(STATE_DIR, "memory_log.csv")

class ResourceMonitor:
    """Monitors system resource usage, specifically peak RAM consumption."""

    def __init__(self, process: Optional[psutil.Process] = None):
        """
        Initialize the resource monitor.
        
        Args:
            process: psutil.Process object to monitor. Defaults to current process.
        """
        self.process = process if process else psutil.Process()
        self.peak_memory_bytes = 0
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.log_entries: list[Dict[str, Any]] = []

    def start_monitoring(self):
        """Start tracking memory usage."""
        self.start_time = time.time()
        # Initialize peak with current usage
        current_mem = self.process.memory_info().rss
        self.peak_memory_bytes = current_mem
        logger.info(f"Resource monitoring started. Initial memory: {current_mem / (1024**2):.2f} MB")

    def check_memory(self) -> Dict[str, Any]:
        """
        Check current memory usage and update peak if necessary.
        
        Returns:
            Dict containing current and peak memory stats.
        """
        current_mem = self.process.memory_info().rss
        
        if current_mem > self.peak_memory_bytes:
            self.peak_memory_bytes = current_mem
            logger.debug(f"New peak memory detected: {current_mem / (1024**2):.2f} MB")
        
        return {
            "current_bytes": current_mem,
            "current_gb": current_mem / (1024**3),
            "peak_bytes": self.peak_memory_bytes,
            "peak_gb": self.peak_memory_bytes / (1024**3),
            "limit_gb": MEMORY_LIMIT_GB,
            "timestamp": datetime.now().isoformat()
        }

    def assert_within_limits(self) -> bool:
        """
        Assert that peak memory usage is within the defined limit.
        
        Returns:
            True if within limits, False otherwise.
            
        Raises:
            MemoryError: If peak memory exceeds the limit.
        """
        stats = self.check_memory()
        if stats["peak_gb"] > MEMORY_LIMIT_GB:
            error_msg = (
                f"Memory limit exceeded! Peak usage: {stats['peak_gb']:.2f} GB, "
                f"Limit: {MEMORY_LIMIT_GB} GB"
            )
            logger.error(error_msg)
            raise MemoryError(error_msg)
        
        logger.info(f"Memory check passed. Peak: {stats['peak_gb']:.2f} GB < {MEMORY_LIMIT_GB} GB")
        return True

    def stop_monitoring(self):
        """Stop monitoring and finalize stats."""
        self.end_time = time.time()
        stats = self.check_memory()
        duration = self.end_time - self.start_time if self.start_time else 0
        
        stats["duration_seconds"] = duration
        stats["status"] = "passed" if stats["peak_gb"] <= MEMORY_LIMIT_GB else "exceeded"
        
        self.log_entries.append(stats)
        logger.info(f"Monitoring stopped. Duration: {duration:.2f}s, Peak: {stats['peak_gb']:.2f} GB")
        
        return stats

    def log_to_csv(self, filepath: Optional[str] = None):
        """
        Log the collected memory statistics to a CSV file.
        
        Args:
            filepath: Path to the CSV file. Defaults to state/memory_log.csv.
        """
        target_path = filepath if filepath else MEMORY_LOG_FILE
        
        # Ensure state directory exists
        state_dir = os.path.dirname(target_path)
        if state_dir:
            os.makedirs(state_dir, exist_ok=True)
        
        fieldnames = [
            "timestamp", "current_gb", "peak_gb", "limit_gb", 
            "duration_seconds", "status", "process_id"
        ]
        
        file_exists = os.path.isfile(target_path)
        
        with open(target_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            for entry in self.log_entries:
                writer.writerow({
                    "timestamp": entry["timestamp"],
                    "current_gb": f"{entry['current_gb']:.4f}",
                    "peak_gb": f"{entry['peak_gb']:.4f}",
                    "limit_gb": MEMORY_LIMIT_GB,
                    "duration_seconds": f"{entry.get('duration_seconds', 0):.2f}",
                    "status": entry.get("status", "running"),
                    "process_id": self.process.pid
                })
        
        logger.info(f"Memory log written to {target_path}")

def run_with_monitoring(func, *args, **kwargs):
    """
    Decorator-like function to run a function with resource monitoring.
    
    Args:
        func: The function to execute.
        *args: Arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.
        
    Returns:
        The result of the function execution.
        
    Raises:
        MemoryError: If memory limit is exceeded during execution.
    """
    monitor = ResourceMonitor()
    monitor.start_monitoring()
    
    try:
        result = func(*args, **kwargs)
        stats = monitor.stop_monitoring()
        monitor.assert_within_limits()
        monitor.log_to_csv()
        return result
    except MemoryError:
        monitor.stop_monitoring()
        monitor.log_to_csv()
        raise
    except Exception as e:
        monitor.stop_monitoring()
        monitor.log_to_csv()
        logger.error(f"Error during monitored execution: {e}")
        raise

def main():
    """
    Main entry point for resource monitoring script.
    
    This script can be run standalone to test memory monitoring or
    imported to wrap other functions with memory tracking.
    """
    logger.info("Starting standalone resource monitoring test...")
    
    # Create a monitor instance
    monitor = ResourceMonitor()
    monitor.start_monitoring()
    
    # Simulate some work (optional, can be replaced with actual pipeline call)
    # For demonstration, we just check memory a few times
    for i in range(5):
        stats = monitor.check_memory()
        logger.debug(f"Check {i+1}: {stats['current_gb']:.4f} GB")
        time.sleep(0.1)
    
    # Finalize
    stats = monitor.stop_monitoring()
    
    try:
        monitor.assert_within_limits()
        print(f"SUCCESS: Peak memory usage {stats['peak_gb']:.2f} GB is within limit ({MEMORY_LIMIT_GB} GB)")
    except MemoryError as e:
        print(f"FAILED: {e}")
        sys.exit(1)
    
    # Log to CSV
    monitor.log_to_csv()
    print(f"Memory log saved to {MEMORY_LOG_FILE}")

if __name__ == "__main__":
    main()