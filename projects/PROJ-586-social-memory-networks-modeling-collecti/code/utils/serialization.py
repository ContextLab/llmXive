"""
Serialization utilities for the social memory network project.
Provides file locking and JSON/pickle serialization helpers.
"""
import json
import pickle
import fcntl
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
import time


def save_json(
    data: Dict[str, Any],
    path: Union[str, Path],
    ensure_dir: bool = True,
    lock_timeout: float = 10.0
) -> None:
    """
    Save data to a JSON file with file locking.

    Args:
        data: Dictionary to serialize.
        path: Target file path.
        ensure_dir: If True, create parent directories if they don't exist.
        lock_timeout: Maximum seconds to wait for a lock.

    Raises:
        TimeoutError: If lock cannot be acquired within timeout.
        IOError: If file write fails.
    """
    path = Path(path)
    if ensure_dir:
        path.parent.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    while True:
        try:
            with open(path, 'w', encoding='utf-8') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                try:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            return
        except BlockingIOError:
            if time.time() - start_time > lock_timeout:
                raise TimeoutError(f"Could not acquire lock on {path} within {lock_timeout}s")
            time.sleep(0.1)


def load_json(
    path: Union[str, Path],
    lock_timeout: float = 10.0
) -> Dict[str, Any]:
    """
    Load data from a JSON file with file locking.

    Args:
        path: Source file path.
        lock_timeout: Maximum seconds to wait for a lock.

    Returns:
        Parsed dictionary.

    Raises:
        FileNotFoundError: If file does not exist.
        TimeoutError: If lock cannot be acquired.
        json.JSONDecodeError: If file is not valid JSON.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    start_time = time.time()
    while True:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
                try:
                    return json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except BlockingIOError:
            if time.time() - start_time > lock_timeout:
                raise TimeoutError(f"Could not acquire lock on {path} within {lock_timeout}s")
            time.sleep(0.1)


def save_pickle(
    data: Any,
    path: Union[str, Path],
    ensure_dir: bool = True,
    lock_timeout: float = 10.0
) -> None:
    """
    Save data to a pickle file with file locking.

    Args:
        data: Object to serialize.
        path: Target file path.
        ensure_dir: If True, create parent directories.
        lock_timeout: Maximum seconds to wait for a lock.
    """
    path = Path(path)
    if ensure_dir:
        path.parent.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    while True:
        try:
            with open(path, 'wb') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                try:
                    pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            return
        except BlockingIOError:
            if time.time() - start_time > lock_timeout:
                raise TimeoutError(f"Could not acquire lock on {path} within {lock_timeout}s")
            time.sleep(0.1)


def load_pickle(
    path: Union[str, Path],
    lock_timeout: float = 10.0
) -> Any:
    """
    Load data from a pickle file with file locking.

    Args:
        path: Source file path.
        lock_timeout: Maximum seconds to wait for a lock.

    Returns:
        Deserialized object.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    start_time = time.time()
    while True:
        try:
            with open(path, 'rb') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
                try:
                    return pickle.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except BlockingIOError:
            if time.time() - start_time > lock_timeout:
                raise TimeoutError(f"Could not acquire lock on {path} within {lock_timeout}s")
            time.sleep(0.1)
