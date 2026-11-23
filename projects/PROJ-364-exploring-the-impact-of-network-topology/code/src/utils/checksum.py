import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)


def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA256 checksum of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file {file_path}: {e}")


# Alias kept for backward compatibility with existing tests / code
def compute_file_sha256(file_path: str) -> str:
    """
    Alias for ``calculate_sha256`` to satisfy legacy imports.
    """
    return calculate_sha256(file_path)


def compute_string_sha256(content: str) -> str:
    """
    Calculate the SHA256 checksum of a string.

    Args:
        content: String content to hash.

    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def compute_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Calculate a checksum of a file using the specified algorithm.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm name (default: 'sha256').

    Returns:
        Hexadecimal string of the checksum.
    """
    hasher = hashlib.new(algorithm)
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_file_checksum(file_path: str, expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """
    Verify that a file's checksum matches the expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected hexadecimal checksum.
        algorithm: Hash algorithm name (default: 'sha256').

    Returns:
        True if checksums match, False otherwise.
    """
    try:
        actual_checksum = compute_file_checksum(file_path, algorithm)
        return actual_checksum.lower() == expected_checksum.lower()
    except (FileNotFoundError, IOError):
        return False


def generate_checksum_manifest(
    files: Union[list, str],
    manifest_path: Optional[str] = None,
    root_dir: Optional[str] = None
) -> Union[Dict[str, Any], Path]:
    """
    Generate a manifest of checksums for a list of files.

    This function is tolerant of different calling conventions:
    1. generate_checksum_manifest([file1, file2]) -> returns dict
    2. generate_checksum_manifest([file1], manifest_path="path") -> writes file, returns Path
    3. generate_checksum_manifest([file1], root_dir="path") -> resolves relative paths if needed

    Args:
        files: List of file paths or a single file path string.
        manifest_path: Optional path to write the manifest JSON. If provided,
                       the manifest is written to disk and the Path is returned.
        root_dir: Optional root directory to prepend to file paths (for context).
                  If provided, it is used to resolve relative paths but does not
                  alter the checksum calculation logic itself.

    Returns:
        If ``manifest_path`` is provided: a ``Path`` object pointing to the written
        manifest file. Otherwise: a dictionary representing the manifest.
    """
    if isinstance(files, str):
        files = [files]

    manifest: Dict[str, Any] = {
        "version": "1.0",
        "algorithm": "sha256",
        "files": {}
    }

    for file_path in files:
        # Resolve full path, optionally using root_dir as a base
        if root_dir:
            full_path = Path(root_dir) / file_path
        else:
            full_path = Path(file_path)

        if not full_path.exists():
            logger.warning(f"File not found for checksum: {full_path}")
            continue

        try:
            checksum = calculate_sha256(str(full_path))
            # Store both legacy ``hash`` key (expected by tests) and ``checksum`` for compatibility
            manifest_entry = {
                "hash": checksum,
                "checksum": checksum,
                "size_bytes": full_path.stat().st_size
            }
            # Preserve the original path string as the key
            manifest["files"][file_path] = manifest_entry
        except Exception as e:
            logger.error(f"Failed to checksum {full_path}: {e}")

    if manifest_path:
        manifest_path_obj = Path(manifest_path)
        # Ensure parent directories exist
        manifest_path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path_obj, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Checksum manifest written to {manifest_path_obj}")
        return manifest_path_obj

    return manifest


def load_checksum_manifest(manifest_path: str) -> Dict[str, Any]:
    """
    Load a checksum manifest from a JSON file.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        Dictionary containing the manifest data.
    """
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def verify_manifest(manifest_path: str) -> Dict[str, bool]:
    """
    Verify all files listed in a checksum manifest.

    Returns a mapping from each file path (as stored in the manifest) to a boolean
    indicating whether the file's current checksum matches the recorded one.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        Dict where keys are file paths (as strings) and values are booleans indicating
        checksum validity.
    """
    results: Dict[str, bool] = {}
    try:
        manifest = load_checksum_manifest(manifest_path)
        files = manifest.get("files", {})

        for file_path, info in files.items():
            # Prefer the legacy ``hash`` key, fall back to ``checksum`` if needed
            expected = info.get("hash") or info.get("checksum")
            if not expected:
                logger.warning(f"No checksum found for {file_path} in manifest")
                results[file_path] = False
                continue

            # ``verify_file_checksum`` works with both absolute and relative paths
            is_valid = verify_file_checksum(file_path, expected)
            results[file_path] = is_valid
            if not is_valid:
                logger.error(f"Checksum mismatch for {file_path}")
    except Exception as e:
        logger.error(f"Failed to verify manifest: {e}")
        # In case of a total failure, return an empty dict
        return {}

    return results
