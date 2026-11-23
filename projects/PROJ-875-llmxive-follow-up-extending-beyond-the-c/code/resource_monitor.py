"""
Resource Monitor for llmXive project.

Implements Constitution Principle VII: Log peak RAM and CPU usage
to results/resource_profile.json after every agent run.

Output Schema:
{
  "peak_ram_mb": float,
  "cpu_percent": float,
  "run_id": string
}

Frequency: Logs at regular, periodic intervals during execution.
Verification: Assert peak_ram_mb <= 7168 and cpu_percent <= 200.
"""
import os
import json
import time
import threading
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Try to import psutil, fallback to /proc on Linux if not available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    import resource
    import subprocess

logger = logging.getLogger(__name__)

class ResourceMonitor:
    """
    Monitors RAM and CPU usage of the current process.
    
    Logs periodic samples and provides final aggregated stats.
    """
    
    def __init__(self, run_id: str, interval_seconds: float = 1.0):
        """
        Initialize the resource monitor.
        
        Args:
            run_id: Unique identifier for this agent run.
            interval_seconds: Frequency of sampling (default 1.0s).
        """
        self.run_id = run_id
        self.interval_seconds = interval_seconds
        self.samples: list[Dict[str, Any]] = []
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self._start_time: Optional[float] = None
        
    def _get_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            return mem_info.rss / (1024 * 1024)
        else:
            # Fallback to resource module (Unix only)
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # ru_maxrss is in KB on Linux, bytes on macOS
            # Normalize to MB
            maxrss = usage.ru_maxrss
            if os.name == 'posix' and sys.platform != 'darwin':
                # Linux: KB
                return maxrss / 1024.0
            else:
                # macOS/other: assume bytes or KB, try to detect
                # For safety, assume KB if value is reasonable for MB
                if maxrss > 1000000000:  # > 1GB in bytes
                    return maxrss / (1024 * 1024)
                else:
                    return maxrss / 1024.0
        
    def _get_cpu_percent(self) -> float:
        """Get current CPU usage percentage."""
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            return process.cpu_percent(interval=None)
        else:
            # Fallback: approximate using /proc/stat
            try:
                with open('/proc/stat', 'r') as f:
                    line = f.readline()
                parts = line.split()
                if parts[0] == 'cpu':
                    # user + nice + system + idle + iowait + irq + softirq + steal
                    total = sum(int(x) for x in parts[1:8])
                    idle = int(parts[4])
                    # This is a rough approximation
                    return 100.0 * (1 - idle / total) if total > 0 else 0.0
            except Exception:
                return 0.0
        
    def _monitor_loop(self):
        """Background thread loop to collect resource samples."""
        while not self._stop_event.is_set():
            try:
                timestamp = datetime.utcnow().isoformat()
                mem_mb = self._get_memory_mb()
                cpu_pct = self._get_cpu_percent()
                
                sample = {
                    "timestamp": timestamp,
                    "peak_ram_mb": mem_mb,
                    "cpu_percent": cpu_pct
                }
                self.samples.append(sample)
                
                # Log every 10 samples to avoid spam
                if len(self.samples) % 10 == 0:
                    logger.debug(f"Resource sample {len(self.samples)}: RAM={mem_mb:.2f}MB, CPU={cpu_pct:.2f}%")
                
            except Exception as e:
                logger.warning(f"Error collecting resource sample: {e}")
            
            self._stop_event.wait(self.interval_seconds)
    
    def start(self):
        """Start the resource monitoring thread."""
        if self._monitor_thread is not None:
            logger.warning("ResourceMonitor already started")
            return
        
        self._start_time = time.time()
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info(f"ResourceMonitor started for run_id={self.run_id}")
    
    def stop(self) -> Dict[str, Any]:
        """
        Stop monitoring and return aggregated results.
        
        Returns:
            Dictionary with peak_ram_mb, cpu_percent, and run_id.
        """
        if self._monitor_thread is None:
            return {
                "peak_ram_mb": 0.0,
                "cpu_percent": 0.0,
                "run_id": self.run_id
            }
        
        self._stop_event.set()
        self._monitor_thread.join(timeout=2.0)
        
        if self.samples:
            peak_ram = max(s["peak_ram_mb"] for s in self.samples)
            # Use average CPU or peak? Task says "cpu_percent" - using peak for safety
            peak_cpu = max(s["cpu_percent"] for s in self.samples)
            avg_cpu = sum(s["cpu_percent"] for s in self.samples) / len(self.samples)
        else:
            peak_ram = 0.0
            peak_cpu = 0.0
            avg_cpu = 0.0
        
        result = {
            "peak_ram_mb": round(peak_ram, 2),
            "cpu_percent": round(peak_cpu, 2),
            "run_id": self.run_id,
            "sample_count": len(self.samples),
            "duration_seconds": round(time.time() - self._start_time, 2) if self._start_time else 0.0
        }
        
        logger.info(f"ResourceMonitor stopped for run_id={self.run_id}: "
                   f"peak_ram={peak_ram:.2f}MB, peak_cpu={peak_cpu:.2f}%")
        
        return result
    
    def save_report(self, output_path: str):
        """
        Save the resource profile to a JSON file.
        
        Args:
            output_path: Path to save the JSON report.
        """
        result = self.stop()
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Resource profile saved to {output_path}")
        
        # Verification: Assert constraints
        if result["peak_ram_mb"] > 7168:
            logger.warning(f"PEAK RAM EXCEEDED: {result['peak_ram_mb']:.2f}MB > 7168MB")
        if result["cpu_percent"] > 200:
            logger.warning(f"PEAK CPU EXCEEDED: {result['cpu_percent']:.2f}% > 200%")
        
        return result


def run_resource_monitoring_test(run_id: str = "test_run", 
                                 duration_seconds: float = 5.0,
                                 output_path: str = "results/resource_profile.json"):
    """
    Run a test of the resource monitor for a specified duration.
    
    Args:
        run_id: Unique identifier for this test run.
        duration_seconds: How long to monitor.
        output_path: Where to save the report.
    
    Returns:
        Dictionary with monitoring results.
    """
    monitor = ResourceMonitor(run_id=run_id, interval_seconds=0.5)
    monitor.start()
    
    # Simulate some work
    time.sleep(duration_seconds)
    
    # Save and return results
    result = monitor.save_report(output_path)
    
    # Verification
    assert result["peak_ram_mb"] <= 7168, f"RAM exceeded limit: {result['peak_ram_mb']}"
    assert result["cpu_percent"] <= 200, f"CPU exceeded limit: {result['cpu_percent']}"
    
    return result


def main():
    """Main entry point for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Resource Monitor for llmXive")
    parser.add_argument("--run_id", type=str, default="standalone_run",
                      help="Unique run identifier")
    parser.add_argument("--duration", type=float, default=5.0,
                      help="Monitoring duration in seconds")
    parser.add_argument("--output", type=str, default="results/resource_profile.json",
                      help="Output path for the resource profile")
    
    args = parser.parse_args()
    
    logger.info(f"Starting resource monitor: run_id={args.run_id}, "
               f"duration={args.duration}s, output={args.output}")
    
    result = run_resource_monitoring_test(
        run_id=args.run_id,
        duration_seconds=args.duration,
        output_path=args.output
    )
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
