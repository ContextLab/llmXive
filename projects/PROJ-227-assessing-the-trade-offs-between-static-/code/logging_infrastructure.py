import json
import os
import time
import threading
from datetime import datetime
from pathlib import Path

import psutil

class ResourceMonitor:
    """
    Monitors CPU and RAM usage of the current process and logs metrics
    to a JSON Lines file at regular intervals.
    """

    def __init__(self, log_path: str, interval_seconds: float = 5.0):
        self.log_path = Path(log_path)
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread = None
        self._process = psutil.Process(os.getpid())

        # Ensure the directory for the log file exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _log_metrics(self):
        """Collects and logs CPU and RAM metrics in JSON Lines format."""
        try:
            cpu_percent = self._process.cpu_percent(interval=None)
            ram_percent = self._process.memory_percent()

            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_percent": cpu_percent,
                "ram_percent": ram_percent
            }

            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")

        except Exception as e:
            # Log errors to stderr to avoid crashing the monitoring thread
            # but ensure the main pipeline can still proceed if needed.
            import sys
            print(f"Error in ResourceMonitor: {e}", file=sys.stderr)

    def _monitor_loop(self):
        """Background loop that logs metrics at fixed intervals."""
        # Initial delay to allow process to stabilize before first measurement
        time.sleep(self.interval_seconds)
        while not self._stop_event.is_set():
            self._log_metrics()
            # Wait for the next interval or stop event
            self._stop_event.wait(self.interval_seconds)

    def start(self):
        """Start the background monitoring thread."""
        if self._thread is not None and self._thread.is_alive():
            return  # Already running

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the background monitoring thread."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

def setup_pipeline_logging(log_path: str, interval_seconds: float = 5.0) -> ResourceMonitor:
    """
    Sets up the pipeline logging infrastructure.
    
    Args:
        log_path: Path to the JSON Lines log file.
        interval_seconds: Interval in seconds between metric logs.
        
    Returns:
        A started ResourceMonitor instance.
    """
    monitor = ResourceMonitor(log_path, interval_seconds)
    monitor.start()
    return monitor

def main():
    """
    Entry point for testing the logging infrastructure.
    Runs the monitor for a short duration to verify output.
    """
    import sys
    from pathlib import Path

    # Default log path relative to project root
    # Adjust path based on where this script is run from
    base_dir = Path(__file__).resolve().parent.parent
    log_file = base_dir / "data" / "logs" / "pipeline.log"

    print(f"Starting ResourceMonitor for 15 seconds, logging to: {log_file}")
    
    monitor = setup_pipeline_logging(str(log_file), interval_seconds=5.0)
    
    try:
        # Keep the main thread alive for the duration of the test
        time.sleep(15)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        monitor.stop()
        print("Monitoring stopped.")
        
        # Verify file creation and content
        if log_file.exists():
            print(f"Verification: Log file exists at {log_file}")
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                print(f"Verification: Found {len(lines)} log entries.")
                if lines:
                    try:
                        sample = json.loads(lines[0])
                        print(f"Verification: Sample entry keys: {list(sample.keys())}")
                    except json.JSONDecodeError:
                        print("Error: First line is not valid JSON.")
        else:
            print("Error: Log file was not created.")
            sys.exit(1)

if __name__ == "__main__":
    main()