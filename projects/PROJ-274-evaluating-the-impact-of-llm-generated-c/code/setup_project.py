import os
import sys
import json
import logging
from pathlib import Path
from utils.setup_paths import ensure_project_dirs
from utils.hash_utils import calculate_directory_hash, update_project_state

def main():
    """
    T001a Implementation:
    1. Create project directory structure.
    2. Generate SHA256 hash of the directory tree.
    3. Update state/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c.yaml.
    """
    # Ensure logging is configured to avoid errors in other modules
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger = logging.getLogger(__name__)

    # Define project root relative to script location
    # Assuming script is at code/setup_project.py, project root is parent of code/
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    project_name = "PROJ-274-evaluating-the-impact-of-llm-generated-c"

    logger.info(f"Project Root: {project_root}")
    logger.info(f"Project Name: {project_name}")

    # 1. Create directory structure per implementation plan
    dirs_to_create = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs",
        "config",
        "state/projects",
        "state",
        "contracts",
        "figures"
    ]

    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory: {full_path}")

    # 2. Generate content hash (SHA256) of the entire directory tree
    # We hash the paths and a representative hash of file contents if they exist,
    # or just the structure if empty.
    logger.info("Calculating directory hash...")
    dir_hash = calculate_directory_hash(project_root, exclude_patterns=["__pycache__", "*.pyc", ".git"])
    logger.info(f"Directory Hash (SHA256): {dir_hash}")

    # 3. Update state/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c.yaml
    state_dir = project_root / "state"
    projects_state_file = state_dir / "projects" / f"{project_name}.yaml"
    
    # Ensure parent exists (already created in step 1, but good practice)
    (state_dir / "projects").mkdir(parents=True, exist_ok=True)

    # Prepare YAML content
    # Using simple string formatting for YAML to avoid dependency issues if PyYAML isn't loaded yet in this context
    # though requirements.txt says it should be.
    yaml_content = f"""project_id: {project_name}
created_at: {Path(project_root).stat().st_mtime} # Using mtime of root as proxy for creation
version: 1.0.0
status: initialized
structure_hash: {dir_hash}
last_updated: {Path(project_root).stat().st_mtime}
"""
    
    # Write the YAML file
    with open(projects_state_file, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    
    logger.info(f"Updated project state file: {projects_state_file}")
    logger.info("T001a Setup Complete.")

    return 0

if __name__ == "__main__":
    sys.exit(main())