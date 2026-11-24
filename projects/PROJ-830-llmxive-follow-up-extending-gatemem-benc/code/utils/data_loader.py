"""
Utility module for loading and validating the GateMem dataset.

This implementation satisfies the unit tests in ``tests/unit/test_data_loader.py``.
It provides functions for:
  - Directory preparation
  - Schema loading
  - Episode validation against the schema and semantic rules
  - SHA‑256 checksum computation for files and directories
  - Checksum verification stored in ``state/artifact_hashes.yaml``

All paths are confined to the project‑owned ``data/`` and ``state/`` folders.
No platform‑owned directories (e.g. ``state/``) are written to outside of the
prescribed location.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any

import yaml

# --------------------------------------------------------------------------- #
# Global paths – the tests override these globals at runtime, so they must be
# mutable module‑level variables.
# --------------------------------------------------------------------------- #

# Default locations (can be overridden by the test suite)
RAW_DATA_DIR: Path = Path("data") / "raw"
STATE_DIR: Path = Path("state")
ARTIFACT_HASHES_FILE: Path = STATE_DIR / "artifact_hashes.yaml"

# Valid domain set as required by the specification
VALID_DOMAINS = {"medical", "office", "education", "household"}

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

_log = logging.getLogger(__name__)


def ensure_dirs() -> None:
    """
    Ensure that the raw data and state directories exist.
    The function is idempotent and safe to call multiple times.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def load_schema(schema_path: Path = Path("contracts") / "dataset.schema.yaml") -> Dict[str, Any]:
    """
    Load a JSON‑Schema file (YAML format) and return the parsed dictionary.

    Parameters
    ----------
    schema_path: Path
        Path to the schema file. Defaults to the contract in the repository.

    Returns
    -------
    dict
        The parsed schema.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def compute_file_hash(file_path: Path) -> str:
    """
    Compute the SHA‑256 hash of a single file.

    Parameters
    ----------
    file_path: Path
        Path to the file.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_directory_hash(dir_path: Path) -> str:
    """
    Compute a deterministic SHA‑256 hash of an entire directory.

    The hash is built by iterating over all files (recursively),
    sorting them by their relative path, and feeding both the
    relative path (as UTF‑8 bytes) and the file contents into a
    single SHA‑256 accumulator.

    Parameters
    ----------
    dir_path: Path
        Directory to hash.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest representing the directory state.
    """
    sha256 = hashlib.sha256()
    if not dir_path.is_dir():
        raise ValueError(f"{dir_path} is not a directory")

    # Gather all file paths, sort for deterministic order
    files = sorted(p for p in dir_path.rglob("*") if p.is_file())
    for file_path in files:
        # Include the relative path to capture file renames/additions
        rel_path = file_path.relative_to(dir_path).as_posix().encode("utf-8")
        sha256.update(rel_path)
        # Include file contents
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
    return sha256.hexdigest()


def validate_checksum() -> bool:
    """
    Verify that the checksum stored in ``state/artifact_hashes.yaml`` matches
    the current hash of ``RAW_DATA_DIR``.

    Returns
    -------
    bool
        ``True`` if the checksum matches or if no checksum file exists.

    Raises
    ------
    ValueError
        If a checksum file exists but the stored hash differs from the
        freshly computed hash.
    """
    if not ARTIFACT_HASHES_FILE.exists():
        # First run – nothing to compare against
        return True

    with ARTIFACT_HASHES_FILE.open("r", encoding="utf-8") as f:
        stored_data = yaml.safe_load(f) or {}

    stored_hash = stored_data.get("gatemem_test")
    if stored_hash is None:
        # No entry – treat as first run
        return True

    current_hash = compute_directory_hash(RAW_DATA_DIR)
    if stored_hash != current_hash:
        raise ValueError("Checksum mismatch")
    return True


def validate_episode(episode: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate a single GateMem episode against the JSON‑Schema and
    additional semantic constraints (domains and role format).

    Parameters
    ----------
    episode: dict
        Episode dictionary to validate.
    schema: dict
        Loaded JSON‑Schema (used for required field list).

    Returns
    -------
    bool
        ``True`` if the episode satisfies all checks, ``False`` otherwise.
    """
    # ------------------------------------------------------------------- #
    # 1. Schema required fields
    # ------------------------------------------------------------------- #
    required_fields: List[str] = schema.get("required", [])
    for field in required_fields:
        if field not in episode:
            _log.debug(f"Missing required field: {field}")
            return False

    # ------------------------------------------------------------------- #
    # 2. Domains – accept string or list, must belong to VALID_DOMAINS
    # ------------------------------------------------------------------- #
    domains = episode.get("domains")
    if isinstance(domains, str):
        domains = [domains]
    if not isinstance(domains, list):
        _log.debug("Domains field is not a list or string")
        return False
    for d in domains:
        if d not in VALID_DOMAINS:
            _log.debug(f"Invalid domain: {d}")
            return False

    # ------------------------------------------------------------------- #
    # 3. Roles – accept string or list, each role must match a simple pattern
    # ------------------------------------------------------------------- #
    roles = episode.get("roles")
    if isinstance(roles, str):
        roles = [roles]
    if not isinstance(roles, list):
        _log.debug("Roles field is not a list or string")
        return False
    role_pattern = re.compile(r"^[A-Za-z0-9_]+$")
    for r in roles:
        if not isinstance(r, str) or not role_pattern.fullmatch(r):
            _log.debug(f"Invalid role format: {r}")
            return False

    # All checks passed
    return True


# --------------------------------------------------------------------------- #
# The module does not perform any I/O on import; all side‑effects are
# encapsulated in the functions above.  The CLI and other pipeline code
# can import this module and call the helpers as needed.
# --------------------------------------------------------------------------- #

# Exported names (for ``from code.utils.data_loader import *``)
__all__ = [
    "RAW_DATA_DIR",
    "STATE_DIR",
    "ARTIFACT_HASHES_FILE",
    "VALID_DOMAINS",
    "ensure_dirs",
    "load_schema",
    "compute_file_hash",
    "compute_directory_hash",
    "validate_checksum",
    "validate_episode",
]