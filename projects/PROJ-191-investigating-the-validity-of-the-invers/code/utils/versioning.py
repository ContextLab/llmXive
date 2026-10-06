import json
import os
import tempfile
import hashlib
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger("versioning")

class VersionedState:
    def __init__(self, path: Path):
        self.path = path
        self.data = {}
        self.load()

    def load(self):
        if self.path.exists():
            with open(self.path, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {"version": 0, "history": [], "current": {}}

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data["version"] += 1
        self.data["timestamp"] = datetime.now().isoformat()
        with open(self.path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def update(self, key: str, value):
        self.data["current"][key] = value
        self.save()

def create_state_manager(base_path: Path):
    return VersionedState(base_path)

def atomic_update_json(file_path: Path, new_data: dict):
    """
    Atomically updates a JSON file by writing to a temp file and renaming.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(dir=file_path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as tmp:
            json.dump(new_data, tmp, indent=2)
        os.replace(temp_path, file_path)
        logger.info(f"Atomically updated {file_path}")
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

def atomic_save_json(file_path: Path, data: dict):
    atomic_update_json(file_path, data)
