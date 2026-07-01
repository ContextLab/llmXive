import os
import sys
import logging
import hashlib
import yaml
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_sha256(file_path: str) -> str:
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
    if not os.path.exists(file_path):
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

def version_artifact(csv_path: str, state_file_path: str) -> bool:
    """
    Compute the SHA-256 hash of the CSV artifact and record it in the project state file.
    
    Args:
        csv_path: Path to the curated_builds.csv file.
        state_file_path: Path to the project state YAML file.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        # Ensure the CSV file exists
        if not os.path.exists(csv_path):
            logger.error(f"Artifact file not found: {csv_path}")
            return False

        # Compute hash
        file_hash = compute_sha256(csv_path)
        logger.info(f"Computed SHA-256 hash for {csv_path}: {file_hash}")

        # Ensure the state directory exists
        state_dir = os.path.dirname(state_file_path)
        if state_dir and not os.path.exists(state_dir):
            os.makedirs(state_dir)
            logger.info(f"Created state directory: {state_dir}")

        # Load existing state or initialize new structure
        state_data = {}
        if os.path.exists(state_file_path):
            try:
                with open(state_file_path, 'r') as f:
                    state_data = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                logger.warning(f"Error parsing existing state file {state_file_path}: {e}. Starting fresh.")
                state_data = {}

        # Ensure 'artifact_hashes' key exists
        if 'artifact_hashes' not in state_data:
            state_data['artifact_hashes'] = {}

        # Update the hash for the specific artifact
        artifact_key = os.path.basename(csv_path)
        state_data['artifact_hashes'][artifact_key] = {
            "path": csv_path,
            "sha256": file_hash
        }

        # Write back to state file
        with open(state_file_path, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Successfully recorded hash for {artifact_key} in {state_file_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to version artifact: {e}")
        return False

def main():
    """
    Entry point for the versioning script.
    Expects environment variables or hardcoded paths for the project structure.
    """
    # Define paths relative to project root
    # Assuming this script runs from the project root or code/data/
    project_root = Path(__file__).resolve().parent.parent.parent
    csv_file = project_root / "data" / "curated_builds.csv"
    state_file = project_root / "state" / "projects" / "PROJ-224-predicting-the-ductility-of-additively-m.yaml"

    if not csv_file.exists():
        logger.error(f"Curated dataset not found at {csv_file}. Please run acquisition and cleaning pipelines first.")
        sys.exit(1)

    success = version_artifact(str(csv_file), str(state_file))
    if not success:
        sys.exit(1)

    logger.info("Versioning complete.")

if __name__ == "__main__":
    main()
