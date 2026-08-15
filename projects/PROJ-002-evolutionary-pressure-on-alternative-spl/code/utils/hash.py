import hashlib
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

def calculate_sha256(file_path: Path) -> str:
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
        raise FileNotFoundError(f"File not found: {file_path}")
    if file_path.is_dir():
        raise IsADirectoryError(f"Cannot hash directory: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files (e.g., BAMs)
            for chunk in iter(lambda: f.read(65536), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except PermissionError as e:
        logger.error(f"Permission denied reading file: {file_path}")
        raise PermissionError(f"Cannot read file for hashing: {file_path}") from e
    except Exception as e:
        logger.error(f"Error hashing file {file_path}: {e}")
        raise e

def generate_manifest(
    file_paths: List[Path], output_path: Optional[Path] = None
) -> Dict[str, str]:
    """
    Generate a manifest of SHA-256 checksums for a list of files.

    Args:
        file_paths: List of paths to files to include in the manifest.
        output_path: Optional path to write the JSON manifest file.
                    If None, the manifest is returned as a dict only.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.

    Raises:
        FileNotFoundError: If any file in the list does not exist.
    """
    manifest = {}
    missing_files = []

    for file_path in file_paths:
        full_path = Path(file_path)
        if not full_path.exists():
            missing_files.append(str(full_path))
            continue

        try:
            relative_path = str(full_path.relative_to(Path.cwd()))
            # Handle case where file is not under cwd
            if relative_path.startswith(".."):
                relative_path = str(full_path)
            
            hash_val = calculate_sha256(full_path)
            manifest[relative_path] = hash_val
            logger.info(f"Hashed: {relative_path} -> {hash_val[:16]}...")
        except Exception as e:
            logger.error(f"Failed to hash {file_path}: {e}")
            raise e

    if missing_files:
        logger.warning(f"Skipping {len(missing_files)} missing files: {missing_files}")

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest written to: {output_path}")

    return manifest

def verify_manifest(manifest_path: Path) -> bool:
    """
    Verify files against a stored manifest.

    Args:
        manifest_path: Path to the JSON manifest file.

    Returns:
        True if all files match their stored hashes, False otherwise.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
        json.JSONDecodeError: If the manifest file is invalid JSON.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    all_valid = True
    for relative_path, expected_hash in manifest.items():
        file_path = Path(relative_path)
        
        if not file_path.exists():
            logger.error(f"Missing file during verification: {relative_path}")
            all_valid = False
            continue

        try:
            actual_hash = calculate_sha256(file_path)
            if actual_hash != expected_hash:
                logger.error(
                    f"Hash mismatch for {relative_path}:\n"
                    f"  Expected: {expected_hash}\n"
                    f"  Actual:   {actual_hash}"
                )
                all_valid = False
            else:
                logger.debug(f"Verified: {relative_path}")
        except Exception as e:
            logger.error(f"Error verifying {relative_path}: {e}")
            all_valid = False

    if all_valid:
        logger.info("All files verified successfully.")
    else:
        logger.warning("Verification failed for one or more files.")

    return all_valid
