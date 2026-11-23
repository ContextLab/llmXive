"""
Memory monitoring utility for the Neural Narrative Networks pipeline.

This module implements memory tracking to ensure peak RAM usage stays
within the 7GB limit specified in the project constraints.

Usage:
    from code.08_memory_monitor import MemoryMonitor
  
    monitor = MemoryMonitor(limit_gb=7.0)
    monitor.start()
    
    # ... run code ...
    
      monitor.stop()
      results = monitor.get_results()
      if results['peak_gb'] > results['limit_gb']:
          raise MemoryError(f"Peak memory {results['peak_gb']:.2f}GB exceeded limit {results['limit_gb']:.2f}GB")
"""
import os
import gc
import time
import json
import psutil
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import project config for the RAM limit
from config import get_config
from utils.logging_config import get_logger, info, error, warning, debug

# Initialize logger
logger = get_logger(__name__)

class MemoryMonitor:
    """
    Monitors memory usage during execution to enforce the 7GB RAM limit.
    
    Tracks peak memory usage and logs results to a JSON file for audit.
    """
    
    def __init__(self, limit_gb: Optional[float] = None):
        """
        Initialize the memory monitor.
        
        Args:
            limit_gb: Maximum allowed RAM in GB. If None, uses config value (default 7GB).
        """
        if limit_gb is None:
            config = get_config()
            self.limit_gb = config.get('max_ram_gb', 7)
        else:
            self.limit_gb = limit_gb
        
        self.process = psutil.Process(os.getpid())
        self.peak_memory_bytes: float = 0.0
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = float
        self.is_monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.samples: List[float] = []
        
        # Output path for monitoring results
        self.results_path = Path("data/results/memory_monitor_results.json")
        
    def _get_memory_bytes(self) -> float:
        """Get current memory usage in bytes."""
        # Use RSS (Resident Set Size) for actual physical memory usage
        mem_info = self.process.memory_info()
        return float(mem_info.rss)
    
    def _background_monitor(self):
        """Background thread to sample memory usage periodically."""
        while not self._stop_event.is_set():
            current_mem = self._get_memory_bytes()
            self.samples.append(current_mem)
            
            if current_mem > self.peak_memory_bytes:
                self.peak_memory_bytes = current_mem
            
            # Sample every 100ms
            self._stop_event.wait(0.1)
    
    def start(self):
        """Start memory monitoring."""
        gc.collect()  # Force garbage collection before starting
        self.peak_memory_bytes = self._get_memory_bytes()
        self.samples = [self.peak_memory_bytes]
        self.start_time = time.time()
        self.is_monitoring = True
        self._stop_event.clear()
        
        # Start background monitoring thread
        self._monitor_thread = threading.Thread(target=self._background_monitor, daemon=True)
        self._monitor_thread.start()
        
        info(f"Memory monitoring started. Limit: {self.limit_gb}GB")
    
    def stop(self) -> Dict[str, Any]:
        """
        Stop monitoring and return results.
        
        Returns:
            Dictionary with monitoring results.
        """
        if not self.is_monitoring:
            warning("Memory monitoring was not started")
            return {}
        
        # Stop background thread
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        
        self.end_time = time.time()
        self.is_monitoring = False
        
        # Final memory check
        final_mem = self._get_memory_bytes()
        if final_mem > self.peak_memory_bytes:
            self.peak_memory_bytes = final_mem
        
        # Calculate results
        duration = self.end_time - self.start_time if self.end_time and self.start_time else 0.0
        peak_gb = self.peak_memory_bytes / (1024 ** 3)
        samples_count = len(self.samples)
        
        results = {
            "start_time": datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None,
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "duration_seconds": duration,
            "peak_memory_bytes": self.peak_memory_bytes,
            "peak_memory_gb": peak_gb,
            "limit_gb": self.limit_gb,
            "exceeded_limit": peak_gb > self.limit_gb,
            "samples_count": samples_count,
            "config": get_config()
        }
        
        # Log results
        status = "EXCEEDED" if results["exceeded_limit"] else "OK"
        info(f"Memory monitoring completed. Peak: {peak_gb:.2f}GB / {self.limit_gb}GB limit [{status}]")
        
        # Save results to file
        self._save_results(results)
        
        # Raise error if limit exceeded
        if results["exceeded_limit"]:
            error(f"MEMORY_LIMIT_EXCEEDED: Peak memory {peak_gb:.2f}GB exceeded limit {self.limit_gb}GB")
            raise MemoryError(f"Peak memory {peak_gb:.2f}GB exceeded limit {self.limit_gb}GB")
        
        return results
    
    def _save_results(self, results: Dict[str, Any]):
        """Save monitoring results to JSON file."""
        try:
            self.results_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing results if present
            existing_results = []
            if self.results_path.exists():
                try:
                    with open(self.results_path, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            existing_results = data
                        elif isinstance(data, dict):
                            existing_results = [data]
                except (json.JSONDecodeError, IOError):
                    existing_results = []
            
            # Append new results
            existing_results.append(results)
            
            # Write back
            with open(self.results_path, 'w') as f:
                json.dump(existing_results, f, indent=2)
            
            debug(f"Memory results saved to {self.results_path}")
            
        except Exception as e:
            warning(f"Failed to save memory results: {e}")
    
    def get_results(self) -> Dict[str, Any]:
        """
        Get current results without stopping monitoring.
        
        Returns:
            Current monitoring results dictionary.
        """
        current_mem = self._get_memory_bytes()
        if current_mem > self.peak_memory_bytes:
            self.peak_memory_bytes = current_mem
        
        duration = (time.time() - self.start_time) if self.start_time else 0.0
        peak_gb = self.peak_memory_bytes / (1024 ** 3)
        
        return {
            "is_monitoring": self.is_monitoring,
            "current_memory_gb": current_mem / (1024 ** 3),
            "peak_memory_gb": peak_gb,
            "limit_gb": self.limit_gb,
            "duration_seconds": duration,
            "samples_count": len(self.samples)
        }
    
    def check_limit(self) -> bool:
        """
        Check if current memory is within limits.
        
        Returns:
            True if within limit, False otherwise.
        """
        current_mem = self._get_memory_bytes()
        current_gb = current_mem / (1024 ** 3)
        within_limit = current_gb <= self.limit_gb
        
        if not within_limit:
            warning(f"Current memory {current_gb:.2f}GB exceeds limit {self.limit_gb}GB")
        
        return within_limit

def main():
    """
    Standalone test of memory monitoring.
    Simulates a workload and verifies monitoring works.
    """
    logger.info("Starting memory monitor test")
    
    monitor = MemoryMonitor(limit_gb=7.0)
    monitor.start()
    
    try:
        # Simulate a workload that allocates memory
        # This should stay well within 7GB
        logger.info("Simulating memory allocation...")
        
        data_chunks = []
        for i in range(100):
            # Allocate ~10MB chunks
            chunk = [0.0] * (10 * 1024 * 1024 // 8)  # 10MB of floats
            data_chunks.append(chunk)
            
            if i % 10 == 0:
                mem_status = monitor.get_results()
                logger.info(f"Progress {i}/100, Current: {mem_status['current_memory_gb']:.2f}GB, Peak: {mem_status['peak_memory_gb']:.2f}GB")
        
        # Force garbage collection
        del data_chunks
        gc.collect()
        
        logger.info("Workload complete, stopping monitor...")
        
    except MemoryError as e:
        error(f"Memory limit exceeded: {e}")
        raise
    finally:
        results = monitor.stop()
        logger.info(f"Final results: Peak={results['peak_memory_gb']:.2f}GB, Limit={results['limit_gb']}GB, Status={'OK' if not results['exceeded_limit'] else 'EXCEEDED'}")
    
    return results

if __name__ == "__main__":
    main()