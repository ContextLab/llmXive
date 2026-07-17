import logging
import sys
from pathlib import Path
from utils.config import get_project_root, get_path, ensure_dir, get_config
from utils.versioning import write_project_state_yaml
from ingest.annotate_graph import main as annotate_main

def write_state_file(project_id: str, artifact_path: str, output_path: str) -> None:
    """
    Compute the hash of an artifact and write it to the project state YAML file.
    
    Args:
        project_id: The project identifier
        artifact_path: Path to the artifact to hash
        output_path: Path to the output YAML state file
    """
    from utils.versioning import compute_sha256
    
    # Ensure the artifact exists
    artifact_file = Path(artifact_path)
    if not artifact_file.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    
    # Compute hash
    artifact_hash = compute_sha256(artifact_file)
    
    # Prepare artifacts dictionary
    artifacts = {
        f"{artifact_file.name}": artifact_hash
    }
    
    # Write state file
    write_project_state_yaml(project_id, artifacts, output_path)
    logging.info(f"State file written to {output_path} with hash for {artifact_file.name}")

def main():
    """
    Main entry point for writing the project state file.
    Computes the hash of data/processed/annotated_videokr.csv and writes it to
    state/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa.yaml
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    project_root = get_project_root()
    project_id = "PROJ-961-llmxive-follow-up-extending-videokr-towa"
    
    # Define paths relative to project root
    artifact_path = project_root / "data" / "processed" / "annotated_videokr.csv"
    output_path = project_root / "state" / "projects" / f"{project_id}.yaml"
    
    try:
        write_state_file(project_id, str(artifact_path), str(output_path))
        logging.info("Successfully wrote project state file.")
    except FileNotFoundError as e:
        logging.error(f"Artifact not found: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error writing state file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
