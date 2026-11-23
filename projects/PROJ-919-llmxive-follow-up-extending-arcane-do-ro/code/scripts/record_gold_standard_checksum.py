import hashlib
import json
import sys
from pathlib import Path

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.lib.state_tracker import generate_run_id
from src.lib.utils import get_logger

# Configure logging
logger = get_logger(__name__)


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise


def record_checksum_in_state(artifact_path: Path, checksum: str, project_id: str) -> None:
    """
    Record the checksum of an artifact in the project state directory.
    Satisfies Constitution Principle III (State Tracking).
    """
    state_dir = PROJECT_ROOT / "state" / "projects" / project_id
    state_dir.mkdir(parents=True, exist_ok=True)

    hash_file = state_dir / "artifact_hashes.json"

    # Load existing hashes or initialize
    if hash_file.exists():
        try:
            with open(hash_file, "r", encoding="utf-8") as f:
                existing_hashes = json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Corrupted hash file {hash_file}, starting fresh.")
            existing_hashes = {}
    else:
        existing_hashes = {}

    # Update with new checksum
    artifact_name = artifact_path.name
    existing_hashes[artifact_name] = {
        "checksum": checksum,
        "path": str(artifact_path.relative_to(PROJECT_ROOT)),
        "recorded_at": generate_run_id(),  # Use run_id as timestamp proxy for simplicity in this context
    }

    # Write back
    with open(hash_file, "w", encoding="utf-8") as f:
        json.dump(existing_hashes, f, indent=2)

    logger.info(f"Recorded checksum for {artifact_name} in {hash_file}")


def main():
    """Main entry point for recording Gold Standard checksum."""
    # Define paths
    gold_standard_path = PROJECT_ROOT / "data" / "gold_standard" / "human_annotations.json"
    project_id = "PROJ-919-llmxive-follow-up-extending-arcane-do-ro"

    # Verify input file exists
    if not gold_standard_path.exists():
        logger.error(f"Gold Standard file not found: {gold_standard_path}")
        logger.error("Please ensure T009a (generate_gold_standard.py) has been run successfully.")
        sys.exit(1)

    logger.info(f"Computing checksum for: {gold_standard_path}")

    try:
        checksum = compute_sha256(gold_standard_path)
        logger.info(f"SHA256 Checksum: {checksum}")

        record_checksum_in_state(gold_standard_path, checksum, project_id)

        logger.info("Checksum successfully recorded in state directory.")

    except Exception as e:
        logger.error(f"Failed to record checksum: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
