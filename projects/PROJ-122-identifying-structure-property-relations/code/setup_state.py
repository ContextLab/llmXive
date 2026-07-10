import os
from pathlib import Path

def create_state_structure(project_root: str) -> None:
    """
    Create the state directory structure and the initial project state YAML file.
    
    This implements task T001d:
    - Creates `state/projects/` directory
    - Creates `state/projects/PROJ-122-identifying-structure-property-relations.yaml`
    
    Args:
        project_root: The root path of the project (e.g., '.' or '/path/to/proj')
    """
    state_path = Path(project_root) / "state"
    projects_path = state_path / "projects"
    
    # Create directories if they don't exist
    projects_path.mkdir(parents=True, exist_ok=True)
    
    # Define the state file path
    project_id = "PROJ-122-identifying-structure-property-relations"
    state_file = projects_path / f"{project_id}.yaml"
    
    # Create placeholder content
    # This follows the convention of storing artifact hashes and pipeline state
    placeholder_content = f"""# Project State: {project_id}
# Generated automatically during project initialization.
# This file tracks the provenance and checksums of all major artifacts.

project_id: {project_id}
status: initialized
created_at: auto-generated
last_updated: auto-generated

# Artifact Provenance
# Keys: artifact_path -> { checksum: <sha256>, size_bytes: <int>, source: <string> }
artifacts:
  data/raw:
    status: empty
    files: []
  data/processed:
    status: empty
    files: []
  data/features:
    status: empty
    files: []
  figures:
    status: empty
    files: []

# Pipeline Execution History
# Each run will append an entry here
execution_history: []
"""
    
    # Write the file
    with open(state_file, "w", encoding="utf-8") as f:
        f.write(placeholder_content)
    
    print(f"Created state directory: {projects_path}")
    print(f"Created state file: {state_file}")

if __name__ == "__main__":
    create_state_structure(".")