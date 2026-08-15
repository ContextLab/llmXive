import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from src.utils.logger import get_logger, log_stage_complete, log_stage_failure
from src.utils.config import get_project_root

# Define the directory structure based on plan.md requirements
# Note: 'contracts/' is placed at root as per task description, 
# but typically in these projects it sits alongside src/. 
# We will create it relative to the project root.
DIRECTORY_STRUCTURE = [
    "src",
    "src/data",
    "src/utils",
    "src/models",
    "src/analysis",
    "tests",
    "tests/unit",
    "tests/integration",
    "data",
    "data/raw",
    "data/processed",
    "data/results",
    "data/logs",
    "data/human_review",
    "state",
    "state/projects",
    "contracts",
    "figures",
]

def create_structure(base_path: Path) -> List[str]:
    """
    Creates the directory structure defined in DIRECTORY_STRUCTURE.
    Returns a list of created paths.
    """
    created_paths = []
    for dir_name in DIRECTORY_STRUCTURE:
        target_path = base_path / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(target_path.relative_to(base_path)))
        else:
            # Ensure it is actually a directory
            if not target_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {target_path}")
    return created_paths

def generate_tree_json(base_path: Path, created_paths: List[str]) -> Dict[str, Any]:
    """
    Generates a JSON representation of the directory tree.
    Includes the root, all created directories, and a timestamp.
    """
    tree_data = {
        "project_root": str(base_path),
        "timestamp": None, # Will be set by logger or caller if needed, but here we just structure
        "directories": [],
        "structure_map": {}
    }
    
    # We need to capture the actual state of the tree at this moment
    # to satisfy the verification requirement "matches the created structure".
    # We will walk the base_path and collect all directories.
    
    all_dirs = []
    for root, dirs, files in os.walk(base_path):
        # Only include directories that are part of our structure or subdirs of them
        # We normalize paths to be relative
        rel_root = Path(root).relative_to(base_path)
        if str(rel_root) == ".":
            rel_root_str = "."
        else:
            rel_root_str = str(rel_root)
        
        for d in dirs:
            full_dir = Path(root) / d
            rel_dir = full_dir.relative_to(base_path)
            all_dirs.append(str(rel_dir))
    
    # Sort for deterministic output
    all_dirs.sort()
    
    tree_data["directories"] = all_dirs
    tree_data["total_directories"] = len(all_dirs)
    tree_data["verification_status"] = "structure_created"
    
    return tree_data

def main():
    logger = get_logger("create_project_structure")
    logger.info("Starting project structure creation for T001a")
    
    try:
        project_root = get_project_root()
        logger.info(f"Project root identified: {project_root}")
        
        # Ensure project root exists
        if not project_root.exists():
            project_root.mkdir(parents=True, exist_ok=True)
        
        # Create directories
        created = create_structure(project_root)
        logger.info(f"Created {len(created)} directories")
        
        # Generate JSON representation
        tree_json = generate_tree_json(project_root, created)
        
        # Ensure output directory exists
        logs_dir = project_root / "data" / "logs"
        if not logs_dir.exists():
            logs_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = logs_dir / "dir_tree.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(tree_json, f, indent=2)
        
        logger.info(f"Successfully wrote verification artifact to {output_file}")
        log_stage_complete(logger, "T001a", "Project structure created and logged", artifacts=[str(output_file)])
        
    except Exception as e:
        log_stage_failure(logger, "T001a", f"Failed to create structure: {e}")
        raise

if __name__ == "__main__":
    main()