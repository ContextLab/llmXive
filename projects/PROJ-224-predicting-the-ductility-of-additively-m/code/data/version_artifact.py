import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Optional
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def ensure_state_file(state_file_path: Path) -> dict:
    """
    Ensure the state YAML file exists and load its contents.
    If it doesn't exist, create it with default structure.

    Args:
        state_file_path: Path to the state YAML file.

    Returns:
        Dictionary containing the state data.
    """
    if not state_file_path.exists():
        logger.info(f"State file not found at {state_file_path}. Creating new state file.")
        state_file_path.parent.mkdir(parents=True, exist_ok=True)
        state_data = {
            "project_id": "PROJ-224-predicting-the-ductility-of-additively-m",
            "artifact_hashes": {}
        }
        try:
            with open(state_file_path, "w") as f:
                yaml.dump(state_data, f, default_flow_style=False)
            logger.info(f"Created new state file at {state_file_path}")
        except IOError as e:
            logger.error(f"Failed to create state file {state_file_path}: {e}")
            raise
        return state_data
    else:
        try:
            with open(state_file_path, "r") as f:
                state_data = yaml.safe_load(f)
            if state_data is None:
                state_data = {"artifact_hashes": {}}
            return state_data
        except (IOError, yaml.YAMLError) as e:
            logger.error(f"Failed to read state file {state_file_path}: {e}")
            raise

def save_state(state_file_path: Path, state_data: dict) -> None:
    """
    Save the state dictionary to the YAML file.

    Args:
        state_file_path: Path to the state YAML file.
        state_data: Dictionary containing the state data.
    """
    try:
        with open(state_file_path, "w") as f:
            yaml.dump(state_data, f, default_flow_style=False)
        logger.info(f"State saved to {state_file_path}")
    except IOError as e:
        logger.error(f"Failed to save state file {state_file_path}: {e}")
        raise

def version_artifact(
    artifact_path: Path,
    state_file_path: Path,
    artifact_key: Optional[str] = None
) -> str:
    """
    Compute the SHA-256 hash of an artifact and record it in the state file.

    Args:
        artifact_path: Path to the artifact file.
        state_file_path: Path to the state YAML file.
        artifact_key: Optional key to use in the state file. If None, uses the artifact filename.

    Returns:
        The computed SHA-256 hash.

    Raises:
        FileNotFoundError: If the artifact file does not exist.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact file not found: {artifact_path}")

    # Compute hash
    hash_value = compute_sha256(artifact_path)
    logger.info(f"Computed SHA-256 for {artifact_path}: {hash_value}")

    # Determine key
    if artifact_key is None:
        artifact_key = artifact_path.name

    # Load or create state
    state_data = ensure_state_file(state_file_path)

    # Update state
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
    state_data["artifact_hashes"][artifact_key] = {
        "hash": hash_value,
        "path": str(artifact_path),
        "versioned_at": None  # Could add timestamp if needed
    }

    # Save state
    save_state(state_file_path, state_data)

    return hash_value

def main():
    """
    Main entry point for versioning the curated dataset.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    curated_data_path = project_root / "data" / "curated_builds.csv"
    state_file_path = project_root / "state" / "projects" / "PROJ-224-predicting-the-ductility-of-additively-m.yaml"

    logger.info(f"Project root: {project_root}")
    logger.info(f"Curated data path: {curated_data_path}")
    logger.info(f"State file path: {state_file_path}")

    try:
        # Version the artifact
        hash_value = version_artifact(
            artifact_path=curated_data_path,
            state_file_path=state_file_path,
            artifact_key="curated_builds_csv"
        )
        logger.info(f"Successfully versioned {curated_data_path} with hash: {hash_value}")
        print(f"Artifact versioned successfully. Hash: {hash_value}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during versioning: {e}", exc_info=True)
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
