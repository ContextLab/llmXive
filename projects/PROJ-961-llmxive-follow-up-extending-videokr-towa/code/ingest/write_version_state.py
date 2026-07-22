import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from utils.config import get_project_root, get_path, ensure_dir, get_config
from utils.versioning import write_project_state_yaml
from ingest.annotate_graph import main as annotate_main

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def write_state_file(
    project_id: str, 
    task_id: str, 
    artifact_path: Path
) -> None:
    """
    Write the version state file for the project.
    
    Args:
        project_id: Project identifier.
        task_id: Task identifier.
        artifact_path: Path to the artifact to hash.
    """
    project_root = get_project_root()
    state_dir = project_root / "state" / "projects"
    ensure_dir(state_dir)
    
    state_path = state_dir / f"{project_id}.yaml"
    
    write_project_state_yaml(
        state_path=state_path,
        project_id=project_id,
        task_id=task_id,
        artifact_path=artifact_path
    )
    logger.info(f"State written to {state_path}")

def main() -> None:
    """Main entry point for writing version state."""
    project_id = "PROJ-961-llmxive-follow-up-extending-videokr-towa"
    task_id = "T013" # Assuming this task produces the annotated data
    
    project_root = get_project_root()
    artifact_path = project_root / "data" / "processed" / "annotated_videokr.csv"
    
    if not artifact_path.exists():
        logger.error("Annotated data not found. Run annotate_graph.py first.")
        sys.exit(1)
        
    write_state_file(project_id, task_id, artifact_path)

if __name__ == "__main__":
    main()