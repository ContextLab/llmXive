"""
Structured JSON resource logging utility.
"""

import json
import os
import time
import psutil
from datetime import datetime
from pathlib import Path

LOG_DIR = "data/logs"

def ensure_log_dir() -> Path:
    """Ensures the log directory exists."""
    path = Path(LOG_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path

class ResourceLogger:
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = ensure_log_dir()
        self.log_file = self.log_dir / f"{self.session_id}.jsonl"
        
        # Ensure file exists
        if not self.log_file.exists():
            self.log_file.touch()

    def log_resource(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Logs a resource event as a JSON line.
        
        Args:
            event_type: Type of event (e.g., "MEMORY_PRESSURE", "MODEL_LOADED")
            data: Dictionary of event data
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "session_id": self.session_id,
            "data": data
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def log_metric(self, name: str, value: float, tags: Optional[Dict[str, Any]] = None) -> None:
        """Logs a metric value."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "METRIC",
            "session_id": self.session_id,
            "data": {
                "name": name,
                "value": value,
                "tags": tags or {}
            }
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_current_ram_gb(self) -> float:
        """Helper to get current RAM usage."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 ** 3)
