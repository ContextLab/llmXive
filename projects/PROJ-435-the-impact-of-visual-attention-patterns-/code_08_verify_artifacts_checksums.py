"""
Utility module for verifying SHA‑256 checksums of project artifacts.

Provides functions used by the checksum verification tests and by the
ingestion pipeline to record and validate artifact hashes.
"""
import hashlib
from pathlib import Path
from typing import Union, Dict, Any

import yaml

def compute_sha256(file_or_bytes: Union[Path, bytes]) -> str:
    """
    Compute the SHA‑256 hash of a file or a bytes object.

    Args:
        file_or_bytes: Path to a file on disk or a ``bytes`` object.

    Returns:
        Hexadecimal SHA‑256 digest string.

    Raises:
        IOError: If ``file_or_bytes`` is a ``Path`` that does not exist.
    """
    if isinstance(file_or_bytes, Path):
        if not file_or_bytes.is_file():
            raise IOError(f"File not found: {file_or_bytes}")
        data = file_or_bytes.read_bytes()
    else:
        data = file_or_bytes
    return hashlib.sha256(data).hexdigest()


def get_project_root() -> Path:
    """
    Return the repository root directory.

    The function assumes it lives inside ``<project_root>/code``.
    """
    return Path(__file__).resolve().parent.parent


def _artifacts_path() -> Path:
    """Internal helper returning the path to ``state/artifacts.yaml``."""
    return get_project_root() / "state" / "artifacts.yaml"


def load_hash_registry() -> Dict[str, str]:
    """
    Load the hash registry from ``state/artifacts.yaml``.

    Returns:
        A dictionary mapping relative file paths (as strings) to their
        SHA‑256 hash strings. Returns an empty dict if the file does not
        exist.

    Raises:
        ValueError: If the YAML file exists but cannot be parsed.
    """
    path = _artifacts_path()
    if not path.is_file():
        return {}
    try:
        with path.open("r") as f:
            data = yaml.safe_load(f) or {}
            if not isinstance(data, dict):
                raise ValueError("Hash registry must be a mapping.")
            # Ensure all keys and values are strings
            return {str(k): str(v) for k, v in data.items()}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in hash registry: {exc}") from exc


def save_hash_registry(registry: Dict[str, str]) -> None:
    """
    Persist the hash registry to ``state/artifacts.yaml``.

    Args:
        registry: Mapping of relative file paths to SHA‑256 hashes.
    """
    path = _artifacts_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        yaml.safe_dump(registry, f)


def verify_artifact(file_path: Path, expected_hash: str) -> tuple[bool, str]:
    """
    Verify that a file's SHA‑256 hash matches the expected value.

    Args:
        file_path: Path to the file to verify.
        expected_hash: Expected hexadecimal SHA‑256 digest.

    Returns:
        ``(True, "OK")`` if the hashes match,
        ``(False, "<message>")`` otherwise.
    """
    try:
        actual_hash = compute_sha256(file_path)
    except IOError as exc:
        return False, f"File error: {exc}"
    if actual_hash.lower() == expected_hash.lower():
        return True, "OK"
    else:
        return (
            False,
            f"Mismatch: expected {expected_hash}, got {actual_hash}",
        )
