"""
Data loading utilities for the GateMem benchmark.
Implements strict real-data fetching with no synthetic fallbacks.
Provides functions required by the test suite:
- ensure_dirs
- load_schema
- compute_file_hash
- compute_directory_hash
- validate_checksum
- validate_episode
Exposes module-level constants that can be overridden in tests:
RAW_DATA_DIR, STATE_DIR, ARTIFACT_HASHES_FILE, VALID_DOMAINS.
"""

import os
import json
import yaml
import hashlib
from pathlib import Path
from typing import Dict, Any

import jsonschema

# ----------------------------------------------------------------------
# Configuration constants (can be overridden by tests)
# ----------------------------------------------------------------------
# Default locations – may be overridden in test fixtures
RAW_DATA_DIR = Path("data/raw")
STATE_DIR = Path("state")
ARTIFACT_HASHES_FILE = STATE_DIR / "artifact_hashes.yaml"

# Valid domain names as per the specification
VALID_DOMAINS = {"medical", "office", "education", "household"}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------

def ensure_dirs() -> None:
    """
    Ensure that the raw data and state directories exist.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def load_schema() -> Dict[str, Any]:
    """
    Load the JSON‑Schema for GateMem episodes from the contracts folder.

    Returns:
        The parsed schema as a Python dictionary.
    """
    # The contracts directory lives at the project root: <repo>/contracts
    contracts_dir = Path(__file__).resolve().parents[2] / "contracts"
    schema_path = contracts_dir / "dataset.schema.yaml"
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    return schema


def compute_file_hash(file_path: Path) -> str:
    """
    Compute the SHA‑256 hash of a single file.

    Args:
        file_path: Path to the file.

    Returns:
        Hex‑encoded SHA‑256 digest.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_directory_hash(dir_path: Path) -> str:
    """
    Compute a deterministic SHA‑256 hash for all files in a directory.
    Files are processed in sorted order to ensure reproducibility.

    Args:
        dir_path: Path to the directory.

    Returns:
        Hex‑encoded SHA‑256 digest representing the directory contents.
    """
    sha256 = hashlib.sha256()
    for root, _, files in os.walk(dir_path):
        for filename in sorted(files):
            file_path = Path(root) / filename
            # Include the relative path in the hash to capture structure
            rel_path = file_path.relative_to(dir_path).as_posix()
            sha256.update(rel_path.encode())
            # Include file contents
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
    return sha256.hexdigest()


def validate_checksum() -> bool:
    """
    Validate that the current raw‑data directory hash matches the stored
    checksum in the state file.  If the checksum file does not exist,
    the function returns True (first‑run scenario).  On mismatch a
    ValueError is raised.

    Returns:
        True if the checksum matches or no checksum file is present.

    Raises:
        ValueError: If the stored checksum does not match the computed one.
    """
    # No checksum file → first run, accept as valid
    if not ARTIFACT_HASHES_FILE.is_file():
        return True

    with open(ARTIFACT_HASHES_FILE, "r", encoding="utf-8") as f:
        state_data = yaml.safe_load(f) or {}

    stored_hash = state_data.get("gatemem_test")
    if stored_hash is None:
        # No entry for our dataset yet – treat as first run
        return True

    current_hash = compute_directory_hash(RAW_DATA_DIR)
    if stored_hash != current_hash:
        raise ValueError("Checksum mismatch")
    return True


def validate_episode(episode: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate a single episode dictionary against the GateMem JSON‑Schema.

    Args:
        episode: The episode data to validate.
        schema: The JSON‑Schema dictionary loaded via ``load_schema``.

    Returns:
        True if the episode conforms to the schema, False otherwise.
    """
    try:
        jsonschema.validate(instance=episode, schema=schema)
        # Additional domain check using the allowed set
        domains = episode.get("domains")
        if isinstance(domains, str):
            domains = [domains]
        if isinstance(domains, list):
            for d in domains:
                if d not in VALID_DOMAINS:
                    return False
        return True
    except jsonschema.ValidationError:
        return False


# ----------------------------------------------------------------------
# If executed as a script, run a minimal sanity check.
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        ensure_dirs()
        schema = load_schema()
        print("Schema loaded successfully.")
        # Simple demonstration: compute hashes for the (possibly empty) raw dir
        dir_hash = compute_directory_hash(RAW_DATA_DIR)
        print(f"Current raw‑data directory hash: {dir_hash}")
    except Exception as exc:
        print(f"Error during sanity check: {exc}")
        raise
