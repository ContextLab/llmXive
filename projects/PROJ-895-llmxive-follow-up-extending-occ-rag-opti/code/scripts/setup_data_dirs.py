"""
Utility script to set up the required data directory structure for the project.
It creates the following directories (if they do not already exist):
  - data/
  - data/raw/
  - data/processed/
It also initializes an empty ``data/checksums.json`` file used by other
pipeline components to record artifact checksums.

The script is idempotent – running it multiple times will not raise errors
and will leave the directory layout unchanged.
"""

import json
import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, Any


def ensure_dir(path: str) -> Path:
    """
    Ensure that a directory exists. If it does not exist, create it (including parents).

    Args:
        path: The directory path to ensure.

    Returns:
        Path object pointing to the ensured directory.
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def compute_sha256(file_path: str) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal SHA-256 digest string.
    """
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def init_checksums(checksum_file: str) -> Dict[str, Any]:
    """
    Load an existing checksums.json file or create a new empty dictionary if it does not exist.

    Args:
        checksum_file: Path to the checksums JSON file.

    Returns:
        Dictionary representing the checksum registry.
    """
    checksum_path = Path(checksum_file)
    if checksum_path.is_file():
        with checksum_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {}


def register_artifact(
    checksums: Dict[str, Any],
    artifact_name: str,
    path: str,
    source: str,
    checksum: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Register an artifact in the checksum registry.

    Args:
        checksums: Existing checksum dictionary.
        artifact_name: Human‑readable name for the artifact.
        path: Relative path to the artifact file.
        source: Description of the source (e.g., URL, manual upload).
        checksum: Optional pre‑computed checksum. If omitted, it will be computed.

    Returns:
        Updated checksum dictionary.
    """
    artifact_path = Path(path)
    if checksum is None:
        if not artifact_path.is_file():
            raise FileNotFoundError(f"Artifact not found for checksum computation: {path}")
        checksum = compute_sha256(str(artifact_path))

    checksums[artifact_name] = {
        "path": str(artifact_path),
        "source": source,
        "sha256": checksum,
    }
    return checksums


def main() -> None:
    """
    Entry point: creates the required data directories and an empty checksums file.
    """
    # Create data directories
    ensure_dir("data")
    ensure_dir(os.path.join("data", "raw"))
    ensure_dir(os.path.join("data", "processed"))

    # Initialise (or touch) the checksums.json file
    checksums_path = Path("data") / "checksums.json"
    if not checksums_path.is_file():
        # Start with an empty registry and write it to disk
        empty_registry: Dict[str, Any] = {}
        with checksums_path.open("w", encoding="utf-8") as f:
            json.dump(empty_registry, f, indent=2)
    else:
        # Ensure the file is valid JSON; if not, raise an error to surface corruption.
        try:
            with checksums_path.open("r", encoding="utf-8") as f:
                json.load(f)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON in existing checksums file: {checksums_path}") from exc

    # Log a short confirmation (stdout) for CI visibility
    print("Data directory structure ready:")
    print(f" - {Path('data').resolve()}")
    print(f" - {Path('data/raw').resolve()}")
    print(f" - {Path('data/processed').resolve()}")
    print(f" - Checksums file: {checksums_path.resolve()}")


if __name__ == "__main__":
    main()
