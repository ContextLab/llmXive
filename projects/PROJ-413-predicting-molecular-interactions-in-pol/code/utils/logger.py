import json
import os
import time
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, List

# Ensure the results directory exists
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

PERFORMANCE_FILE = os.path.join(RESULTS_DIR, "performance.json")

class PerformanceLogger:
    """
    Logger for tracking runtime and memory usage of research scripts.
    Writes metrics to results/performance.json.
    """

    def __init__(self, script_name: str = "unknown"):
        self.script_name = script_name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.memory_samples: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {
            "script_name": self.script_name,
            "start_time": None,
            "end_time": None,
            "duration_seconds": None,
            "memory_usage_mb": None,
            "max_memory_mb": None,
            "status": "pending",
            "error": None,
            "timestamp": datetime.now().isoformat()
        }

    def start(self):
        """Start the timer and initial memory snapshot."""
        self.start_time = time.time()
        self.metrics["start_time"] = datetime.fromtimestamp(self.start_time).isoformat()
        self._record_memory()

    def _record_memory(self):
        """Record current memory usage if psutil is available."""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_mb = process.memory_info().rss / (1024 * 1024)
            self.memory_samples.append({
                "timestamp": time.time(),
                "memory_mb": mem_mb
            })
            # Update running max
            if self.metrics["max_memory_mb"] is None or mem_mb > self.metrics["max_memory_mb"]:
                self.metrics["max_memory_mb"] = mem_mb
        except ImportError:
            # psutil not installed, skip memory tracking
            pass

    def stop(self, status: str = "success"):
        """Stop the timer and finalize metrics."""
        self.end_time = time.time()
        self.metrics["end_time"] = datetime.fromtimestamp(self.end_time).isoformat()
        self.metrics["duration_seconds"] = round(self.end_time - self.start_time, 2)
        self.metrics["status"] = status

        if self.memory_samples:
            self.metrics["max_memory_mb"] = round(max(s["memory_mb"] for s in self.memory_samples), 2)

        self._save()

    def log_error(self, error: Exception):
        """Log an error and stop the timer."""
        self.metrics["status"] = "failed"
        self.metrics["error"] = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc()
        }
        self.stop(status="failed")

    def _save(self):
        """Save metrics to the performance JSON file."""
        # Load existing data to append or update
        existing_data = []
        if os.path.exists(PERFORMANCE_FILE):
            try:
                with open(PERFORMANCE_FILE, 'r') as f:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
            except (json.JSONDecodeError, IOError):
                existing_data = []

        # Append current run
        existing_data.append(self.metrics)

        # Write back
        with open(PERFORMANCE_FILE, 'w') as f:
            json.dump(existing_data, f, indent=2)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.log_error(exc_val)
        else:
            self.stop()
        return False  # Do not suppress exceptions


def get_memory_usage_mb() -> Optional[float]:
    """Get current memory usage in MB."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        return None


def log_performance(script_name: str, duration: float, memory_mb: Optional[float] = None, status: str = "success", error: Optional[str] = None):
    """
    Convenience function to log a single performance entry.
    """
    metrics = {
        "script_name": script_name,
        "start_time": datetime.now().isoformat(),
        "duration_seconds": round(duration, 2),
        "memory_usage_mb": round(memory_mb, 2) if memory_mb else None,
        "max_memory_mb": round(memory_mb, 2) if memory_mb else None,
        "status": status,
        "error": error,
        "timestamp": datetime.now().isoformat()
    }

    existing_data = []
    if os.path.exists(PERFORMANCE_FILE):
        try:
            with open(PERFORMANCE_FILE, 'r') as f:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = [existing_data]
        except (json.JSONDecodeError, IOError):
            existing_data = []

    existing_data.append(metrics)

    with open(PERFORMANCE_FILE, 'w') as f:
        json.dump(existing_data, f, indent=2)
