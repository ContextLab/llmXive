"""
Utility for writing model‑load events to ``data/processed/logs/model_load_log.json``.
The file is a JSON array where each element is a dict describing a single load event.
"""
import json
from datetime import datetime
from llmxive_toolkit import paths
from pathlib import Path

LOG_PATH = paths.data("processed", "logs", "model_load_log.json")

def _ensure_log():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_PATH.is_file():
        LOG_PATH.write_text("[]", encoding="utf-8")

def write_load_event(model_name: str, device: str):
    """
    Appends a load event to the JSON log.

    Parameters
    ----------
    model_name : str
        Name of the model that was loaded.
    device : str
        Device the model was placed on (``cpu`` or ``cuda``).
    """
    _ensure_log()
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model_name": model_name,
        "device": device,
    }
    try:
        with LOG_PATH.open("r+", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                data = []
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
    except json.JSONDecodeError:
        # Replace a corrupted log with a fresh one
        with LOG_PATH.open("w", encoding="utf-8") as f:
            json.dump([entry], f, indent=2)
