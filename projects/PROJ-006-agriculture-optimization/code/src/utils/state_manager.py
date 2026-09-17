import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-006-agriculture-optimization.yaml"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def scan_directory_for_artifacts(directory: Path) -> List[Path]:
    """Scan a directory recursively for all files."""
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []
    return list(directory.rglob("*"))


def load_state() -> Dict[str, Any]:
    """Load the state file or return an empty structure if missing."""
    if not STATE_FILE.exists():
        logger.warning(f"State file not found: {STATE_FILE}. Initializing empty state.")
        return {
            "project_id": "PROJ-006-agriculture-optimization",
            "artifact_hashes": {
                "data/raw": {},
                "data/processed": {}
            }
        }

    try:
        with open(STATE_FILE, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load state file: {e}")
        return {
            "project_id": "PROJ-006-agriculture-optimization",
            "artifact_hashes": {
                "data/raw": {},
                "data/processed": {}
            }
        }


def save_state(state: Dict[str, Any]) -> None:
    """Save the state dictionary to the state file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        yaml.safe_dump(state, f, default_flow_style=False)
    logger.info(f"State saved to {STATE_FILE}")


def update_artifact_hashes() -> None:
    """Scan data directories, compute hashes, and update the state file."""
    state = load_state()

    # Ensure structure exists
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {"data/raw": {}, "data/processed": {}}

    raw_hashes = {}
    processed_hashes = {}

    # Scan data/raw
    if DATA_RAW_DIR.exists():
        files = [f for f in DATA_RAW_DIR.rglob("*") if f.is_file()]
        if not files:
            logger.info("No data to hash in data/raw")
        else:
            for file_path in files:
                try:
                    rel_path = str(file_path.relative_to(DATA_RAW_DIR))
                    file_hash = compute_file_hash(file_path)
                    raw_hashes[rel_path] = file_hash
                except Exception as e:
                    logger.error(f"Error hashing {file_path}: {e}")
    else:
        logger.info("data/raw directory does not exist")

    # Scan data/processed
    if DATA_PROCESSED_DIR.exists():
        files = [f for f in DATA_PROCESSED_DIR.rglob("*") if f.is_file()]
        if not files:
            logger.info("No data to hash in data/processed")
        else:
            for file_path in files:
                try:
                    rel_path = str(file_path.relative_to(DATA_PROCESSED_DIR))
                    file_hash = compute_file_hash(file_path)
                    processed_hashes[rel_path] = file_hash
                except Exception as e:
                    logger.error(f"Error hashing {file_path}: {e}")
    else:
        logger.info("data/processed directory does not exist")

    state["artifact_hashes"]["data/raw"] = raw_hashes
    state["artifact_hashes"]["data/processed"] = processed_hashes

    save_state(state)


def verify_artifacts() -> bool:
    """Verify that current file hashes match the stored state."""
    state = load_state()
    current_hashes = {"data/raw": {}, "data/processed": {}}

    # Re-scan and hash
    if DATA_RAW_DIR.exists():
        for file_path in DATA_RAW_DIR.rglob("*"):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(DATA_RAW_DIR))
                current_hashes["data/raw"][rel_path] = compute_file_hash(file_path)

    if DATA_PROCESSED_DIR.exists():
        for file_path in DATA_PROCESSED_DIR.rglob("*"):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(DATA_PROCESSED_DIR))
                current_hashes["data/processed"][rel_path] = compute_file_hash(file_path)

    # Compare
    stored_raw = state.get("artifact_hashes", {}).get("data/raw", {})
    stored_processed = state.get("artifact_hashes", {}).get("data/processed", {})

    if current_hashes["data/raw"] != stored_raw:
        logger.warning("Hash mismatch in data/raw")
        return False

    if current_hashes["data/processed"] != stored_processed:
        logger.warning("Hash mismatch in data/processed")
        return False

    logger.info("All artifacts verified successfully.")
    return True


def main() -> int:
    """CLI entry point for state manager."""
    import argparse

    parser = argparse.ArgumentParser(description="Manage project state and artifact hashes.")
    parser.add_argument(
        "--action",
        choices=["update", "verify", "dry-run"],
        default="update",
        help="Action to perform: update hashes, verify existing, or dry-run"
    )
    parser.add_argument(
        "--create-dummy",
        action="store_true",
        help="Create a dummy file in data/raw for testing"
    )

    args = parser.parse_args()

    if args.create_dummy:
        dummy_path = DATA_RAW_DIR / "dummy.txt"
        dummy_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dummy_path, "w") as f:
            f.write("Dummy file for state manager verification.")
        logger.info(f"Created dummy file: {dummy_path}")

    if args.action == "update":
        update_artifact_hashes()
    elif args.action == "verify":
        if not verify_artifacts():
            return 1
    elif args.action == "dry-run":
        # Just scan and log without saving
        logger.info("Dry-run: Scanning directories...")
        raw_files = scan_directory_for_artifacts(DATA_RAW_DIR)
        processed_files = scan_directory_for_artifacts(DATA_PROCESSED_DIR)
        logger.info(f"Found {len(raw_files)} files in data/raw")
        logger.info(f"Found {len(processed_files)} files in data/processed")

        # Compute hashes for logging
        for f in raw_files[:5]:  # Log first 5
            logger.info(f"  {f.name}: {compute_file_hash(f)[:16]}...")
        for f in processed_files[:5]:
            logger.info(f"  {f.name}: {compute_file_hash(f)[:16]}...")

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    exit(main())
