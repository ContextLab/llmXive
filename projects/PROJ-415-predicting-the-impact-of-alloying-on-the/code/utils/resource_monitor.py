import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime

# Attempt to import psutil; if missing, fail loudly as per constraints
try:
    import psutil
except ImportError:
    raise ImportError(
        "psutil is required for resource monitoring. "
        "Install it via: pip install psutil"
    )

from config import REPORTS_DIR, PROJECT_ROOT
from utils.logging import get_logger

@dataclass
class ResourceSnapshot:
    stage: str
    timestamp: str
    ram_mb: float
    ram_gb: float
    warning_issued: bool

class ResourceMonitor:
    """
    Monitors RAM usage at key pipeline stages and logs to reports/resource_usage.json.
    """
    RAM_THRESHOLD_GB = 6.0
    LOG_FILE_PATH = Path(REPORTS_DIR) / "resource_usage.json"

    def __init__(self):
        self.logger = get_logger(__name__)
        self.snapshots: list[Dict[str, Any]] = []
        self.process = psutil.Process(os.getpid())
        self._ensure_report_dir()

    def _ensure_report_dir(self) -> None:
        """Ensure the reports directory exists."""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    def _get_current_ram_mb(self) -> float:
        """Get current RAM usage in MB."""
        return self.process.memory_info().rss / (1024 * 1024)

    def log_stage(self, stage_name: str) -> None:
        """
        Log RAM usage for a specific stage.
        If usage > 6GB, logs a warning.
        """
        ram_mb = self._get_current_ram_mb()
        ram_gb = ram_mb / 1024.0
        warning_issued = False

        if ram_gb > self.RAM_THRESHOLD_GB:
            warning_msg = f"RAM Warning: Usage exceeded 6GB threshold at stage '{stage_name}' ({ram_gb:.2f} GB)"
            self.logger.warning(warning_msg)
            warning_issued = True
        else:
            self.logger.info(f"RAM usage at stage '{stage_name}': {ram_gb:.2f} GB")

        snapshot = ResourceSnapshot(
            stage=stage_name,
            timestamp=datetime.now().isoformat(),
            ram_mb=ram_mb,
            ram_gb=ram_gb,
            warning_issued=warning_issued
        )
        self.snapshots.append(asdict(snapshot))

    def save_report(self) -> None:
        """Saves the accumulated snapshots to reports/resource_usage.json."""
        if not self.snapshots:
            self.logger.warning("No resource snapshots recorded. Skipping report save.")
            return

        report_data = {
            "monitor_timestamp": datetime.now().isoformat(),
            "threshold_gb": self.RAM_THRESHOLD_GB,
            "snapshots": self.snapshots
        }

        # Write to file
        with open(self.LOG_FILE_PATH, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.logger.info(f"Resource usage report saved to {self.LOG_FILE_PATH}")

    def wrap_function(self, func: Callable, stage_name: str) -> Callable:
        """
        Decorator to wrap a function and log RAM usage at start and end.
        """
        def wrapper(*args, **kwargs):
            self.log_stage(f"{stage_name}_START")
            try:
                result = func(*args, **kwargs)
            finally:
                self.log_stage(f"{stage_name}_END")
            return result
        return wrapper

# Global instance for easy access in pipeline stages
monitor = ResourceMonitor()

def log_resource_usage(stage_name: str) -> None:
    """Convenience function to log RAM usage for a stage."""
    monitor.log_stage(stage_name)

def save_resource_report() -> None:
    """Convenience function to save the final report."""
    monitor.save_report()

def main() -> None:
    """
    Main entry point for the resource monitor.
    This script is intended to be imported and used by the pipeline,
    but can also be run to initialize the monitor if needed.
    """
    logger = get_logger(__name__)
    logger.info("Resource Monitor initialized.")
    logger.info(f"Threshold set to {ResourceMonitor.RAM_THRESHOLD_GB} GB.")
    
    # Example usage if run directly (though typically imported)
    # In a real pipeline, the monitor would be instantiated and methods called
    # at specific points in code/main.py or stage scripts.
    if __name__ == "__main__":
        # Simulate a few stages for demonstration if run directly
        log_resource_usage("Initialization")
        time.sleep(0.1) # Simulate work
        log_resource_usage("Data Acquisition")
        time.sleep(0.1)
        log_resource_usage("Model Training")
        time.sleep(0.1)
        log_resource_usage("Validation")
        save_resource_report()

if __name__ == "__main__":
    main()
