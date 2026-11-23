import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the script is run from the repository root or code/scripts.
    """
    current = Path.cwd()
    # Check if we are in code/scripts
    if current.name == 'scripts' and current.parent.name == 'code':
        return current.parent.parent
    # Check if we are in code
    if current.name == 'code':
        return current.parent
    # Fallback: look for a marker file or assume cwd
    if (current / 'tasks.md').exists():
        return current
    # Last resort: go up until we find tasks.md or hit root
    for parent in current.parents:
        if (parent / 'tasks.md').exists():
            return parent
    logger.warning("Could not determine project root automatically. Using current directory.")
    return current

def create_structure(root: Path, dirs: List[str]) -> List[Path]:
    """
    Create the directory tree under root.
    Returns a list of created paths.
    """
    created_paths = []
    for d in dirs:
        target = root / d
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            created_paths.append(target)
            logger.info(f"Created directory: {target}")
        else:
            logger.debug(f"Directory already exists: {target}")
    return created_paths

def generate_tree_json(root: Path, dirs: List[str]) -> Dict[str, Any]:
    """
    Generate a JSON representation of the directory structure.
    """
    tree_data = {
        "root": str(root),
        "timestamp": str(Path(root).stat().st_mtime), # Simple timestamp
        "directories": []
    }

    for d in dirs:
        target = root / d
        if target.exists() and target.is_dir():
            # Get relative path from root
            rel_path = str(target.relative_to(root))
            tree_data["directories"].append({
                "path": rel_path,
                "absolute": str(target),
                "exists": True
            })
        else:
            tree_data["directories"].append({
                "path": d,
                "absolute": str(target),
                "exists": False,
                "error": "Directory creation failed or path invalid"
            })

    return tree_data

def main():
    """
    Main entry point for creating the project directory structure.
    """
    project_root = get_project_root()
    logger.info(f"Project root identified as: {project_root}")

    # Define the required directories as per tasks.md T001a
    # Paths are relative to the project root
    required_dirs = [
        "src",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "state",
        "data/logs",
        "contracts"
    ]

    # Create the structure
    created = create_structure(project_root, required_dirs)

    if not created:
        logger.info("No new directories were created (all exist).")
    else:
        logger.info(f"Successfully created {len(created)} directories.")

    # Generate the JSON report
    tree_json = generate_tree_json(project_root, required_dirs)
    
    # Define output path
    output_dir = project_root / "data" / "logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "dir_tree.json"

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tree_json, f, indent=2)
        logger.info(f"Successfully wrote directory tree report to: {output_file}")
    except IOError as e:
        logger.error(f"Failed to write directory tree report: {e}")
        sys.exit(1)

    # Verify the file exists
    if not output_file.exists():
        logger.error("Verification failed: Output file does not exist.")
        sys.exit(1)

    logger.info("Task T001a completed successfully.")

if __name__ == "__main__":
    main()