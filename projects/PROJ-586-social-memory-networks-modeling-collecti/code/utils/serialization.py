"""
Serialization utilities for JSON and Pickle operations.
Implements file-locking for concurrent access safety.
"""
import json
import pickle
import fcntl
import os
from pathlib import Path
from typing import Any, Optional
import time


def save_json(data: Any, path: str, mode: str = 'w') -> None:
    """Save data to a JSON file with file locking."""
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, mode) as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            json.dump(data, f, indent=2)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def load_json(path: str, mode: str = 'r') -> Any:
    """Load data from a JSON file with file locking."""
    with open(path, mode) as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        try:
            return json.load(f)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def save_pickle(data: Any, path: str, mode: str = 'wb') -> None:
    """Save data to a pickle file with file locking."""
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, mode) as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            pickle.dump(data, f)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def load_pickle(path: str, mode: str = 'rb') -> Any:
    """Load data from a pickle file with file locking."""
    with open(path, mode) as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        try:
            return pickle.load(f)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
