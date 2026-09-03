import hashlib
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from loguru import logger

from code.utils.logger import setup_logger

# Initialize logger for this module
setup_logger()

def calculate_sha256(file_path: Union[str, Path]) -> str:
    """
    Calculate the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    if file_path.is_dir():
        raise IsADirectoryError(f"Cannot hash a directory: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files (e.g., BAMs)
            for chunk in iter(lambda: f.read(4096 * 1024), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"IOError while reading {file_path} for hashing: {e}")
        raise

def generate_manifest(
    file_paths: List[Union[str, Path]],
    output_path: Union[str, Path],
    exclude_patterns: Optional[List[str]] = None,
    base_dir: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Generate a JSON manifest containing SHA-256 hashes for a list of files.

    Args:
        file_paths: List of paths to hash.
        output_path: Path where the manifest JSON will be written.
        exclude_patterns: Optional list of glob patterns to exclude.
        base_dir: Optional base directory to resolve relative paths against.

    Returns:
        The manifest dictionary.
    """
    output_path = Path(output_path)
    base_dir = Path(base_dir) if base_dir else Path.cwd()

    if exclude_patterns:
        import fnmatch
        filtered_paths = []
        for p in file_paths:
            rel_p = str(Path(p).relative_to(base_dir)) if Path(p).is_absolute() else str(p)
            if not any(fnmatch.fnmatch(rel_p, pattern) for pattern in exclude_patterns):
                filtered_paths.append(p)
        file_paths = filtered_paths

    manifest = {
        "created_at": "", # Will be set by caller or pipeline if needed, or left empty
        "files": {}
    }

    for p in file_paths:
        p_obj = Path(p)
        if not p_obj.is_absolute():
            p_obj = base_dir / p_obj

        if not p_obj.exists():
            logger.warning(f"Skipping non-existent file in manifest generation: {p_obj}")
            continue
        if p_obj.is_dir():
            logger.warning(f"Skipping directory in manifest generation: {p_obj}")
            continue

        try:
            hash_val = calculate_sha256(p_obj)
            # Store relative path from base_dir for portability
            try:
                rel_path = str(p_obj.relative_to(base_dir))
            except ValueError:
                rel_path = str(p_obj)

            manifest["files"][rel_path] = {
                "sha256": hash_val,
                "size_bytes": p_obj.stat().st_size
            }
            logger.info(f"Hashed: {rel_path} -> {hash_val[:16]}...")
        except Exception as e:
            logger.error(f"Failed to hash {p_obj}: {e}")
            # Decide whether to fail fast or continue. For manifest generation,
            # we log and continue, but the pipeline might want to abort.
            manifest["files"][str(p_obj)] = {"error": str(e)}

    # Write manifest
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Manifest written to {output_path}")
    return manifest

def verify_manifest(manifest_path: Union[str, Path]) -> bool:
    """
    Verify the integrity of files listed in a manifest against their stored hashes.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        True if all files match their hashes, False otherwise.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        try:
            manifest = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in manifest {manifest_path}: {e}")
            return False

    base_dir = manifest_path.parent
    all_valid = True

    for rel_path, entry in manifest.get("files", {}).items():
        if "error" in entry:
            logger.warning(f"Skipping {rel_path} due to previous error: {entry['error']}")
            continue

        file_path = base_dir / rel_path
        if not file_path.exists():
            logger.error(f"File missing during verification: {file_path}")
            all_valid = False
            continue

        try:
            current_hash = calculate_sha256(file_path)
            stored_hash = entry.get("sha256")
            if current_hash != stored_hash:
                logger.error(f"Hash mismatch for {file_path}: expected {stored_hash}, got {current_hash}")
                all_valid = False
            else:
                logger.debug(f"Verified: {rel_path}")
        except Exception as e:
            logger.error(f"Error verifying {file_path}: {e}")
            all_valid = False

    if all_valid:
        logger.info("Manifest verification successful: all files match.")
    else:
        logger.error("Manifest verification FAILED: some files do not match.")

    return all_valid

def log_hash_to_file(file_path: Union[str, Path], log_path: Union[str, Path]) -> str:
    """
    Calculate hash of a file and append the entry to a log file.

    Args:
        file_path: The file to hash.
        log_path: Path to the log file to append to.

    Returns:
        The calculated hash.
    """
    hash_val = calculate_sha256(file_path)
    file_path = Path(file_path)
    log_path = Path(log_path)

    entry = f"{file_path.name}\t{hash_val}\t{file_path.stat().st_size}\n"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)

    logger.info(f"Logged hash for {file_path.name} to {log_path.name}")
    return hash_val

def log_manifest_entry(manifest_path: Union[str, Path], log_path: Union[str, Path]) -> None:
    """
    Append the manifest path and its hash to a log file.

    Args:
        manifest_path: Path to the manifest file.
        log_path: Path to the log file to append to.
    """
    hash_val = calculate_sha256(manifest_path)
    manifest_path = Path(manifest_path)
    log_path = Path(log_path)

    entry = f"{manifest_path.name}\t{hash_val}\t{manifest_path.stat().st_size}\n"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)

    logger.info(f"Logged manifest hash for {manifest_path.name} to {log_path.name}")
