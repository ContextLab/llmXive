"""
Logging infrastructure for the LLM analysis trade-offs pipeline.

Implements JSON Lines logging with a resource monitoring hook that
records CPU and RAM usage every 5 seconds.
"""
import json
import os
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import psutil
except ImportError:
    raise ImportError(
        "psutil is required for resource monitoring. "
        "Install it via: pip install psutil"
    )


class ResourceMonitor:
    """
    Monitors CPU and RAM usage and logs them to a JSON Lines file.
    
    Runs in a background thread, logging metrics at a specified interval.
    """
    
    def __init__(
        self, 
        log_path: str, 
        interval: float = 5.0, 
        logger_name: str = "resource_monitor"
    ):
        self.log_path = Path(log_path)
        self.interval = interval
        self.logger_name = logger_name
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._process = psutil.Process(os.getpid())
        
        # Ensure the log directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _log_resource_usage(self) -> None:
        """Collect and log resource usage metrics."""
        try:
            metrics = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "logger": self.logger_name,
                "event_type": "resource_usage",
                "data": {
                    "cpu_percent": self._process.cpu_percent(),
                    "ram_percent": self._process.memory_percent(),
                    # Also log system-wide for context if needed
                    "system_cpu_percent": psutil.cpu_percent(interval=None),
                    "system_ram_percent": psutil.virtual_memory().percent,
                }
            }
            
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(metrics) + "\n")
                
        except Exception as e:
            # Log errors to stderr to avoid crashing the monitor
            import sys
            print(f"Error in resource monitor: {e}", file=sys.stderr)
    
    def _monitor_loop(self) -> None:
        """Background loop that logs resources at the specified interval."""
        # Initial capture
        self._process.cpu_percent()  # First call returns 0, so we discard it
        time.sleep(0.1)
        
        while not self._stop_event.is_set():
            self._log_resource_usage()
            # Wait for the interval or until stop signal
            self._stop_event.wait(self.interval)
    
    def start(self) -> None:
        """Start the resource monitoring thread."""
        if self._thread is not None and self._thread.is_alive():
            return  # Already running
        
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._monitor_loop, 
            daemon=True, 
            name="ResourceMonitor"
        )
        self._thread.start()
    
    def stop(self) -> None:
        """Stop the resource monitoring thread."""
        if self._thread is None:
            return
        
        self._stop_event.set()
        self._thread.join(timeout=self.interval + 1.0)
        self._thread = None


def setup_pipeline_logging(
    log_path: str = "projects/PROJ-227-assessing-the-trade-offs-between-static-/data/logs/pipeline.log",
    interval: float = 5.0
) -> ResourceMonitor:
    """
    Initialize the pipeline logging infrastructure.
    
    Args:
        log_path: Path to the JSON Lines log file.
        interval: Interval in seconds between resource metric logs.
        
    Returns:
        A ResourceMonitor instance that is already started.
    """
    monitor = ResourceMonitor(log_path=log_path, interval=interval)
    monitor.start()
    return monitor


def main() -> None:
    """
    Entry point for testing the logging infrastructure.
    
    Runs for 15 seconds to generate enough log entries for verification,
    then stops and reports success.
    """
    import sys
    from pathlib import Path

    # Default path relative to project root
    project_root = Path(__file__).resolve().parent.parent
    log_path = project_root / "data" / "logs" / "pipeline.log"
    
    print(f"Starting pipeline logging infrastructure...")
    print(f"Log file: {log_path}")
    
    try:
        monitor = setup_pipeline_logging(str(log_path), interval=5.0)
        
        # Run for 15 seconds to capture at least 3 resource logs
        print("Monitoring resources for 15 seconds...")
        time.sleep(15)
        
        monitor.stop()
        
        # Verify the log file exists and has content
        if not log_path.exists():
            print(f"ERROR: Log file {log_path} was not created.", file=sys.stderr)
            sys.exit(1)
        
        line_count = 0
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if "data" in entry and "cpu_percent" in entry["data"]:
                        line_count += 1
                except json.JSONDecodeError:
                    print(f"WARNING: Invalid JSON in log: {line}", file=sys.stderr)
        
        if line_count < 3:
            print(f"ERROR: Expected at least 3 resource logs, found {line_count}.", file=sys.stderr)
            sys.exit(1)
        
        print(f"SUCCESS: Generated {line_count} resource logs to {log_path}")
        print("Verification: Log file exists, contains valid JSON, and includes CPU/RAM metrics.")
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()