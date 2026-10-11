"""
Utility configuration helpers for the project.

Provides functions for:
- Determining project‑root, data‑root, and state‑root paths.
- Ensuring directories exist.
- Computing SHA‑256 hashes of files.
- (Optionally) seeding random number generators (seed handling is elsewhere).
"""

import os
import hashlib
from pathlib import Path
from typing import Any

# ----------------------------------------------------------------------
# Path helpers
# ----------------------------------------------------------------------
def get_project_root() -> Path:
    """
    Returns the absolute Path to the project root directory.

    The function assumes this file lives in <project_root>/src/utils/.
    """
    return Path(__file__).resolve().parents[2]

def get_data_root() -> Path:
    """
    Returns the absolute Path to the top‑level data directory (<project_root>/data).
    """
    return get_project_root() / "data"

def get_state_root() -> Path:
    """
    Returns the absolute Path to the state directory (<project_root>/state).
    """
    return get_project_root() / "state"

# ----------------------------------------------------------------------
# Filesystem helpers
# ----------------------------------------------------------------------
def ensure_dir(p: Path) -> None:
    """
    Ensures that the directory represented by ``p`` exists.
    Creates parent directories as needed.
    """
    p.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Hashing helper
# ----------------------------------------------------------------------
def compute_file_hash(file_path: str) -> str:
    """
    Computes the SHA‑256 hash of the file at ``file_path`` and returns
    the hexadecimal digest string.

    Parameters
    ----------
    file_path: str
        Path to the file whose hash should be computed.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    sha256 = hashlib.sha256()
    # Read the file in binary mode in chunks to avoid loading large files fully into memory
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()