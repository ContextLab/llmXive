"""
Versioning utility for atomic state updates.
"""
import json
import os
import tempfile
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

class VersionedState:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if self.path.exists():
            with open(self.path, 'r') as f:
                self._data = json.load(f)
        else:
            self._data = {
                "version": 0,
                "last_updated": None,
                "state": {}
            }

    @property
    def version(self) -> int:
        return self._data.get("version", 0)

    @property
    def state(self) -> Dict[str, Any]:
        return self._data.get("state", {})

    def update(self, new_state: Dict[str, Any]):
        self._data["state"].update(new_state)
        self._data["version"] += 1
        self._data["last_updated"] = datetime.utcnow().isoformat()
        atomic_save_json(self.path, self._data)

def create_state_manager(path: Path) -> VersionedState:
    return VersionedState(path)

def atomic_save_json(path: Path, data: Dict[str, Any]):
    """
    Atomically save JSON data to a file using a temporary file and rename.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

def atomic_update_json(path: Path, updater_func):
    """
    Atomically update JSON data.
    updater_func: A function that takes the current dict and returns the new dict.
    """
    if path.exists():
        with open(path, 'r') as f:
            current = json.load(f)
    else:
        current = {}
    
    new_data = updater_func(current)
    atomic_save_json(path, new_data)
