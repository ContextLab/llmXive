"""Checksum generator for reproducibility artifacts.

This script generates SHA-256 checksums for all data files and writes
them to a JSON manifest. It also updates the state YAML artifact map.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Ensure the parent directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from reproducibility.logs import get_logger, log_operation

logger = get_logger(__name__)

DATA_DIR = Path("data")
CHECKSUM_FILE = DATA_DIR / "checksums.json"
STATE_DIR = Path("state")
STATE_FILE = STATE_DIR / "artifacts.yaml"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.warning(f"File not found for hashing: {file_path}")
        return ""
    except PermissionError:
        logger.error(f"Permission denied reading file: {file_path}")
        return ""

def find_data_files(base_dir: Path) -> list[Path]:
    """Find all data files to checksum."""
    files = []
    if not base_dir.exists():
        logger.warning(f"Data directory not found: {base_dir}")
        return files

    # Walk through data directory, excluding logs and temporary files
    for item in base_dir.rglob("*"):
        if item.is_file():
            # Skip log files and temporary files
            if item.suffix in [".log", ".tmp", ".swp"]:
                continue
            if "logs" in item.parts and item.suffix != ".json":
                continue
            files.append(item)

    return sorted(files)

def generate_checksums() -> Dict[str, str]:
    """Generate checksums for all data files."""
    checksums = {}
    files = find_data_files(DATA_DIR)

    if not files:
        logger.warning("No data files found to checksum.")
        return checksums

    logger.info(f"Found {len(files)} data files to checksum")

    for file_path in files:
        relative_path = file_path.relative_to(DATA_DIR)
        hash_value = compute_sha256(file_path)
        if hash_value:
            checksums[str(relative_path)] = hash_value
            logger.debug(f"Checksummed: {relative_path} -> {hash_value[:16]}...")

    return checksums

def save_checksums(checksums: Dict[str, str]) -> None:
    """Save checksums to JSON file."""
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True)

    with open(CHECKSUM_FILE, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)

    logger.info(f"Checksums saved to {CHECKSUM_FILE}")

def update_state_manifest(checksums: Dict[str, str]) -> None:
    """Update the state YAML artifact map with new hashes."""
    if not STATE_DIR.exists():
        STATE_DIR.mkdir(parents=True)

    # Read existing state if it exists
    state_data: Dict[str, Any] = {"artifacts": {}}
    if STATE_FILE.exists():
        try:
            import yaml
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state_data = yaml.safe_load(f) or state_data
        except ImportError:
            logger.warning("PyYAML not installed, skipping state update")
            return
        except Exception as e:
            logger.error(f"Error reading state file: {e}")
            return

    # Update artifact hashes
    for path, hash_value in checksums.items():
        state_data["artifacts"][path] = {"hash": hash_value}

    # Write back to YAML
    try:
        import yaml
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=True)
        logger.info(f"State manifest updated at {STATE_FILE}")
    except ImportError:
        logger.warning("PyYAML not installed, skipping state update")
    except Exception as e:
        logger.error(f"Error writing state file: {e}")

@log_operation
def main() -> int:
    """Main entry point for checksum generation."""
    logger.info("Starting checksum generation")

    checksums = generate_checksums()

    if not checksums:
        logger.error("No checksums generated. Check if data files exist.")
        return 1

    save_checksums(checksums)
    update_state_manifest(checksums)

    logger.info("Checksum generation completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())