"""
Environment configuration management and checksum verification for raw downloads.

This module provides utilities for:
1. Loading environment variables from a .env file (if present) or system defaults.
2. Validating the integrity of downloaded raw data files using SHA-256 checksums.
3. Managing configuration paths for raw data directories.

Dependencies:
- python-dotenv (optional, for .env support)
- hashlib (standard library)
- pathlib (standard library)
"""
import os
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Optional dependency for .env support
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    load_dotenv = lambda: None  # type: ignore

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Default configuration keys
ENV_FILE_PATH = ".env"
CHECKSUM_MANIFEST_FILE = "data/raw/checksums.json"
DATA_RAW_DIR = "data/raw"

# Environment variable keys
ENV_KEYS = {
    "GBIF_API_KEY": "GBIF_API_KEY",
    "TRY_API_KEY": "TRY_API_KEY",
    "WORLDCLIM_BASE_URL": "WORLDCLIM_BASE_URL",
    "MAX_WORKERS": "MAX_WORKERS",
    "LOG_LEVEL": "LOG_LEVEL",
}


def load_environment_config(env_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load environment configuration from a .env file or system environment.

    Args:
        env_path: Path to the .env file. Defaults to ENV_FILE_PATH.

    Returns:
        Dictionary of configuration values.
    """
    if env_path is None:
        env_path = ENV_FILE_PATH

    config = {}

    # Attempt to load .env file if it exists
    if os.path.exists(env_path):
        if HAS_DOTENV:
            load_dotenv(env_path)
            logger.info(f"Loaded environment variables from {env_path}")
        else:
            logger.warning(
                f"Environment file {env_path} exists but python-dotenv is not installed. "
                "Please run: pip install python-dotenv"
            )
    else:
        logger.debug(f"No environment file found at {env_path}, using system defaults.")

    # Read required keys
    for key, env_var in ENV_KEYS.items():
        value = os.getenv(env_var)
        if value is None:
            # Provide defaults or log warnings for optional vars
            if key in ["GBIF_API_KEY", "TRY_API_KEY"]:
                logger.warning(f"Environment variable {env_var} is not set. "
                               "Some features requiring authentication will fail.")
            elif key == "WORLDCLIM_BASE_URL":
                value = "https://biogeo.ucdavis.edu/data/worldclim/v2.1"
            elif key == "MAX_WORKERS":
                value = "4"
            elif key == "LOG_LEVEL":
                value = "INFO"
            
        config[key] = value

    return config


def compute_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal digest string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")

    hash_obj = hashlib.new(algorithm)
    
    try:
        with open(path, "rb") as f:
            # Read in chunks to handle large files (e.g., rasters)
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path} for checksum: {e}")
        raise


def verify_checksum(file_path: str, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected hexadecimal digest.
        algorithm: Hash algorithm to use.

    Returns:
        True if checksums match, False otherwise.
    """
    try:
        actual_checksum = compute_file_checksum(file_path, algorithm)
        if actual_checksum.lower() == expected_checksum.lower():
            logger.info(f"Checksum verification passed for {file_path}")
            return True
        else:
            logger.error(
                f"Checksum verification FAILED for {file_path}. "
                f"Expected: {expected_checksum}, Got: {actual_checksum}"
            )
            return False
    except FileNotFoundError:
        logger.error(f"Cannot verify checksum: File not found {file_path}")
        return False


def register_checksum(file_path: str, checksum: Optional[str] = None, algorithm: str = "sha256") -> None:
    """
    Register a file's checksum in the manifest.

    If checksum is not provided, it is computed from the file.

    Args:
        file_path: Path to the file.
        checksum: Optional pre-computed checksum.
        algorithm: Hash algorithm to use.
    """
    manifest_path = Path(CHECKSUM_MANIFEST_FILE)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing manifest
    manifest = {}
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Corrupt checksum manifest at {manifest_path}, resetting.")
            manifest = {}

    # Compute or use provided checksum
    if checksum is None:
        checksum = compute_file_checksum(file_path, algorithm)

    # Update manifest with relative path for portability
    rel_path = str(Path(file_path).relative_to(Path(DATA_RAW_DIR)))
    manifest[rel_path] = {
        "algorithm": algorithm,
        "checksum": checksum,
        "registered_at": datetime.now().isoformat()
    }

    # Save manifest
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Registered checksum for {rel_path} in {manifest_path}")


def verify_all_downloads() -> Dict[str, bool]:
    """
    Verify all files in the raw data directory against the manifest.

    Returns:
        Dictionary mapping file paths to verification status (True/False).
    """
    manifest_path = Path(CHECKSUM_MANIFEST_FILE)
    if not manifest_path.exists():
        logger.warning("No checksum manifest found. Nothing to verify.")
        return {}

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    results = {}
    data_raw = Path(DATA_RAW_DIR)

    for rel_path, info in manifest.items():
        full_path = data_raw / rel_path
        expected = info.get("checksum")
        algo = info.get("algorithm", "sha256")

        if not full_path.exists():
            results[rel_path] = False
            logger.error(f"File missing during verification: {full_path}")
            continue

        results[rel_path] = verify_checksum(str(full_path), expected, algo)

    return results
