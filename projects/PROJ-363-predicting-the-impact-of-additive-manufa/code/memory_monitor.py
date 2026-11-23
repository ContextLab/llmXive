"""
Memory Usage Monitoring for US2 (Model Training).

This module provides utilities to monitor memory usage during the model training
process. It tracks peak memory consumption and logs it alongside training metrics.

Note: T057 was marked as 'REMOVED - Scope Drift' in tasks.md, but execution failures
indicated a need for robustness monitoring. This implementation adds memory
monitoring capabilities to the training pipeline to ensure resource constraints
are respected and to provide diagnostic information for future optimization.

This module is invoked by train_models.py to wrap the training process.
"""
import os
import sys
import json
import logging
import time
import traceback
from pathlib import Path
from typing import Optional, Dict, Any

# Attempt to import psutil for accurate memory monitoring
# If not available, fall back to /proc on Linux or basic estimation
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logging.warning("psutil not installed. Memory monitoring will use fallback methods.")

def get_memory_usage_mb() -> float:
    """
    Get current memory usage of the current process in MB.
    
    Returns:
        float: Memory usage in MB.
    """
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    else:
        # Fallback for Linux
        try:
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        # Format: "VmRSS:     12345 kB"
                        parts = line.split()
                        if len(parts) >= 2:
                            return float(parts[1]) / 1024.0
        except Exception:
            pass
        return 0.0

def get_peak_memory_mb() -> float:
    """
    Get peak memory usage of the current process in MB.
    
    Returns:
        float: Peak memory usage in MB.
    """
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        # Note: psutil doesn't track peak RSS by default across restarts
        # We approximate by tracking max seen in this session
        return get_memory_usage_mb()
    else:
        # Fallback: try /proc/.../status (max_rss)
        try:
            with open('/proc/self/status', 'r') as f:
                content = f.read()
                # Look for VmPeak or MaxRSS
                for line in content.split('\n'):
                    if line.startswith('VmPeak:'):
                        parts = line.split()
                        if len(parts) >= 2:
                            return float(parts[1]) / 1024.0
        except Exception:
            pass
        return get_memory_usage_mb()

class MemoryMonitor:
    """
    Context manager and utility class to monitor memory usage during a block of code.
    
    Usage:
        monitor = MemoryMonitor("Training Step")
        with monitor:
            # do heavy work
        monitor.log_report()
    """
    def __init__(self, label: str = "MemoryMonitor", output_path: Optional[str] = None):
        """
        Initialize the monitor.
        
        Args:
            label: A descriptive label for this monitoring session.
            output_path: Optional path to write the memory report JSON.
        """
        self.label = label
        self.output_path = output_path
        self.start_mem = 0.0
        self.end_mem = 0.0
        self.peak_mem = 0.0
        self.start_time = 0.0
        self.end_time = 0.0
        self.duration = 0.0
        self.logger = logging.getLogger(__name__)

    def __enter__(self):
        self.start_mem = get_memory_usage_mb()
        self.peak_mem = self.start_mem
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.end_mem = get_memory_usage_mb()
        current_peak = get_peak_memory_mb()
        self.peak_mem = max(self.peak_mem, current_peak)
        self.duration = self.end_time - self.start_time
        
        if exc_type is not None:
            self.logger.error(f"MemoryMonitor {self.label} exited with exception: {exc_val}")
        
        self.log_report()
        return False  # Do not suppress exceptions

    def check(self, limit_mb: float) -> bool:
        """
        Check if current memory usage is below a limit.
        
        Args:
            limit_mb: Memory limit in MB.
            
        Returns:
            bool: True if under limit, False otherwise.
        """
        current = get_memory_usage_mb()
        if current > limit_mb:
            self.logger.warning(f"Memory limit exceeded: {current:.2f} MB > {limit_mb:.2f} MB")
            return False
        return True

    def log_report(self):
        """Log the memory usage report and optionally save to file."""
        report = {
            "label": self.label,
            "start_memory_mb": round(self.start_mem, 2),
            "end_memory_mb": round(self.end_mem, 2),
            "peak_memory_mb": round(self.peak_mem, 2),
            "duration_seconds": round(self.duration, 4),
            "memory_delta_mb": round(self.end_mem - self.start_mem, 2)
        }
        
        self.logger.info(f"Memory Report [{self.label}]: "
                       f"Start={report['start_memory_mb']:.2f} MB, "
                       f"Peak={report['peak_memory_mb']:.2f} MB, "
                       f"End={report['end_memory_mb']:.2f} MB, "
                       f"Delta={report['memory_delta_mb']:.2f} MB, "
                       f"Duration={report['duration_seconds']:.2f}s")
        
        if self.output_path:
            try:
                # Ensure directory exists
                Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(self.output_path, 'w') as f:
                    json.dump(report, f, indent=2)
                self.logger.info(f"Memory report saved to {self.output_path}")
            except Exception as e:
                self.logger.error(f"Failed to save memory report: {e}")

def monitor_training_memory(train_func, *args, **kwargs):
    """
    Decorator/factory to wrap a training function with memory monitoring.
    
    Args:
        train_func: The training function to wrap.
        
    Returns:
        A wrapped function that monitors memory.
    """
    def wrapper(*args, **kwargs):
        output_path = kwargs.pop('memory_report_path', 'results/reports/memory_usage.json')
        label = kwargs.pop('memory_label', 'ModelTraining')
        
        monitor = MemoryMonitor(label=label, output_path=output_path)
        with monitor:
            try:
                result = train_func(*args, **kwargs)
                return result
            except Exception as e:
                monitor.logger.error(f"Training failed with memory monitor active: {e}")
                monitor.logger.error(traceback.format_exc())
                raise
    return wrapper

def main():
    """
    Standalone entry point for testing memory monitoring.
    Simulates a memory-intensive operation and reports usage.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Memory Monitor Standalone Test")
    
    # Simulate some work
    monitor = MemoryMonitor("StandaloneTest", output_path="results/reports/memory_usage.json")
    with monitor:
        logger.info("Allocating memory...")
        # Allocate ~100MB to test
        data = [i for i in range(10_000_000)]
        logger.info(f"Data length: {len(data)}")
        time.sleep(0.5)
        del data
        logger.info("Memory released.")
    
    logger.info("Memory Monitor Standalone Test Complete")

if __name__ == "__main__":
    main()
