"""
Versioning utility for atomic state updates.

Provides atomic JSON operations and a state manager for tracking
pipeline execution state with versioning and checksums.
"""
import json
import os
import tempfile
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Callable

class VersionedState:
    """
    Manages a versioned state file with atomic updates.
    
    Attributes:
        path: Path to the state JSON file.
        version: Current version number (increments on update).
        state: The underlying state dictionary.
    """
    def __init__(self, path: Path):
        self.path = path
        # Ensure parent directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Any] = {}
        self._load()

    def _load(self):
        """Load existing state or initialize default structure."""
        if self.path.exists():
            with open(self.path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
        else:
            self._data = {
                "version": 0,
                "last_updated": None,
                "checksum": None,
                "state": {}
            }

    @property
    def version(self) -> int:
        """Get the current version number."""
        return self._data.get("version", 0)

    @property
    def state(self) -> Dict[str, Any]:
        """Get the current state dictionary."""
        return self._data.get("state", {})

    def update(self, new_state: Dict[str, Any]):
        """
        Atomically update the state with new values.
        
        Increments version, updates timestamp, and recalculates checksum.
        
        Args:
            new_state: Dictionary of key-value pairs to update.
        """
        self._data["state"].update(new_state)
        self._data["version"] += 1
        self._data["last_updated"] = datetime.utcnow().isoformat()
        self._data["checksum"] = self._compute_checksum()
        atomic_save_json(self.path, self._data)

    def set_state(self, new_state: Dict[str, Any]):
        """
        Replace the entire state dictionary atomically.
        
        Args:
            new_state: The new state dictionary to set.
        """
        self._data["state"] = new_state
        self._data["version"] += 1
        self._data["last_updated"] = datetime.utcnow().isoformat()
        self._data["checksum"] = self._compute_checksum()
        atomic_save_json(self.path, self._data)

    def _compute_checksum(self) -> str:
        """Compute SHA-256 checksum of the current state."""
        state_str = json.dumps(self._data["state"], sort_keys=True)
        return hashlib.sha256(state_str.encode('utf-8')).hexdigest()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the state dictionary."""
        return self._data.get("state", {}).get(key, default)

    def exists(self) -> bool:
        """Check if the state file exists."""
        return self.path.exists()

def create_state_manager(path: Path) -> VersionedState:
    """
    Factory function to create a VersionedState instance.
    
    Args:
        path: Path to the state file.
        
    Returns:
        A configured VersionedState instance.
    """
    return VersionedState(path)

def atomic_save_json(path: Path, data: Dict[str, Any]):
    """
    Atomically save JSON data to a file using a temporary file and rename.
    
    This ensures that if the process is interrupted during the write,
    the original file remains intact or no file is created, preventing
    corruption.
    
    Args:
        path: Target file path.
        data: Dictionary to save as JSON.
        
    Raises:
        OSError: If the file operation fails.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

def atomic_update_json(path: Path, updater_func: Callable[[Dict[str, Any]], Dict[str, Any]]):
    """
    Atomically update JSON data by applying an updater function.
    
    Args:
        path: Path to the JSON file.
        updater_func: A function that takes the current dict and returns the new dict.
        
    Raises:
        OSError: If file operations fail.
    """
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            current = json.load(f)
    else:
        current = {}
    
    new_data = updater_func(current)
    atomic_save_json(path, new_data)