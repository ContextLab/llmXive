import os
import sys
import json
import logging
from pathlib import Path
from utils.setup_paths import ensure_project_dirs
from utils.hash_utils import calculate_directory_hash, update_project_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_project_structure(project_root: Path) -> None:
    """
    Create the required directory structure for the project.
    """
    dirs_to_create = [
        'code',
        'data/raw',
        'data/processed',
        'data/reports',
        'data/logs',
        'tests/unit',
        'tests/integration',
        'tests/contract',
        'specs',
        'config',
        'state',
        'scripts',
        'figures'
    ]

    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {full_path}")

def main():
    """
    Main entry point for project setup.
    Creates directory structure and initializes project state with a hash.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Initialize project structure and state')
    parser.add_argument('--project-root', type=str, default='.', help='Root directory for the project')
    parser.add_argument('--project-id', type=str, default='PROJ-274-evaluating-the-impact-of-llm-generated-c', help='Project identifier')
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    project_id = args.project_id

    logger.info(f"Initializing project: {project_id}")
    logger.info(f"Project root: {project_root}")

    # Create directory structure
    create_project_structure(project_root)

    # Ensure project state directory exists for hash calculation
    ensure_project_dirs(project_root)

    # Calculate hash of the entire directory tree
    logger.info("Calculating initial directory hash...")
    directory_hash = calculate_directory_hash(str(project_root))
    logger.info(f"Initial Hash (SHA256): {directory_hash}")

    # Update project state file
    logger.info(f"Updating state/projects/{project_id}.yaml...")
    update_project_state(str(project_root), project_id, directory_hash, 'state')

    state_file = project_root / 'state' / f"{project_id}.yaml"
    logger.info(f"Project setup complete. State file: {state_file}")
    
    # Verify structure
    required_dirs = ['code', 'data/raw', 'data/processed', 'data/reports', 'tests/unit', 'specs', 'state']
    for d in required_dirs:
        if not (project_root / d).is_dir():
            logger.error(f"Missing required directory: {d}")
            sys.exit(1)
    
    logger.info("All required directories verified.")

if __name__ == '__main__':
    main()
