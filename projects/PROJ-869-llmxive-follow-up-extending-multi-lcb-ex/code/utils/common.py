import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

def ensure_dir(dir_path: Path) -> None:
    """Ensures that a directory exists, creating it if necessary."""
    dir_path.mkdir(parents=True, exist_ok=True)

def load_json(file_path: Path) -> Any:
    """Loads a JSON file and returns its contents."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data: Any, file_path: Path) -> None:
    """Saves data to a JSON file."""
    ensure_dir(file_path.parent)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
