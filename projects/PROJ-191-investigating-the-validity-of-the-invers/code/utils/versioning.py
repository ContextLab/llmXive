import json
import os
import tempfile
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

class VersionedState:
    """Manages versioned state updates with atomic operations."""
    
    def __init__(self, state_path: Path):
        self.state_path = state_path
        self.version = "0.0.1"
    
    def create_snapshot(self, data: Dict[str, Any]) -> str:
        """Create a snapshot of the current state and return its hash."""
        timestamp = datetime.now().isoformat()
        snapshot = {
            "version": self.version,
            "timestamp": timestamp,
            "data": data,
            "hash": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        }
        return snapshot["hash"]
    
    def increment_version(self):
        """Increment the version number."""
        major, minor, patch = map(int, self.version.split('.'))
        patch += 1
        self.version = f"{major}.{minor}.{patch}"

def create_state_manager(state_path: Path) -> VersionedState:
    """Create a state manager for the given path."""
    return VersionedState(state_path)

def atomic_update_json(file_path: Path, update_func, backup: bool = True) -> bool:
    """Atomically update a JSON file using a temporary file and rename."""
    try:
        # Read current content
        if file_path.exists():
            with open(file_path, 'r') as f:
                current_data = json.load(f)
        else:
            current_data = {}
        
        # Apply update function
        new_data = update_func(current_data)
        
        # Write to temporary file
        dir_name = file_path.parent
        fd, temp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
        try:
            with os.fdopen(fd, 'w') as tmp:
                json.dump(new_data, tmp, indent=2)
            
            # Atomic rename
            if backup and file_path.exists():
                backup_path = file_path.with_suffix('.bak')
                file_path.rename(backup_path)
            
            Path(temp_path).rename(file_path)
            return True
        except Exception:
            # Clean up temp file on failure
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise
    except Exception as e:
        print(f"Atomic update failed: {str(e)}")
        return False

def atomic_save_json(file_path: Path, data: Dict[str, Any], backup: bool = True) -> bool:
    """Atomically save data to a JSON file."""
    return atomic_update_json(file_path, lambda _: data, backup)
