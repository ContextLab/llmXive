import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Configure logging to write to data/logs/setup.log if it exists, otherwise stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the project directory structure based on plan.md and tasks.md
# Paths are relative to the project root (code/)
PROJECT_DIRS = [
    "src",
    "tests",
    "data",
    "data/raw",
    "data/processed",
    "data/results",
    "state",
    "data/logs",
    "contracts",
    # Additional standard directories often expected in such pipelines
    "data/human_review",
    "figures",
    "src/utils",
    "src/data",
    "src/models",
    "src/analysis",
    "src/pipeline",
    "tests/unit",
    "tests/integration",
    "code/scripts", # To match the existing API surface location
    "code/setup_project_structure.py" # Placeholder for the script itself if needed in a flat structure, but we are in code/
]

def create_structure(root_path: Path) -> Dict[str, Any]:
    """
    Creates the directory structure defined in PROJECT_DIRS.
    Returns a dictionary representing the tree created.
    """
    created_dirs = []
    errors = []

    for dir_path_str in PROJECT_DIRS:
        # Skip if it looks like a file path we aren't creating as a dir
        if dir_path_str.endswith('.py'):
            continue
        
        full_path = root_path / dir_path_str
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path.relative_to(root_path)))
            logger.info(f"Created directory: {full_path}")
        except Exception as e:
            error_msg = f"Failed to create {full_path}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)

    return {
        "created": created_dirs,
        "errors": errors,
        "root": str(root_path)
    }

def generate_tree_json(root_path: Path, output_path: Path) -> None:
    """
    Generates a JSON representation of the directory tree and saves it to output_path.
    This satisfies the verification requirement for T001a.
    """
    tree_data = {
        "generated_at": None, # Will be filled by caller or left as null if not needed
        "root": str(root_path),
        "directories": []
    }

    # Walk the directory tree to capture the exact state
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Calculate relative path
        try:
            rel_path = os.path.relpath(dirpath, root_path)
            if rel_path == '.':
                rel_path = ''
            
            # Only include directories that match our expected structure or are subdirs of them
            # To keep it clean, we just list all created dirs
            tree_data["directories"].append(rel_path)
        except ValueError:
            # Skip if path is not relative (e.g. cross-filesystem on some OS)
            continue

    # Sort directories for deterministic output
    tree_data["directories"].sort()
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tree_data, f, indent=2)
        logger.info(f"Directory tree JSON saved to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to write tree JSON: {e}")
        raise

def main():
    """
    Main entry point for the setup script.
    Determines the project root, creates the structure, and writes the verification log.
    """
    # Determine project root. Based on the task context, we are in code/
    # The task asks to create structure relative to project root.
    # Assuming the script is run from the project root or code/ directory.
    # We will assume the current working directory is the project root for simplicity,
    # or we can look for a marker file.
    # Given the existing API surface `code/setup_project_structure.py`, we assume
    # the script is executed from the project root (where `code/` is a subdirectory).
    
    # However, to be safe and robust, let's assume the script is run from the directory
    # containing `code/` if it exists, or just use the current working directory.
    cwd = Path.cwd()
    if (cwd / "code").exists():
        project_root = cwd
    else:
        project_root = cwd.parent if (cwd / "code").parent.name == "code" else cwd

    # If we are running inside the `code` directory (as per the path `code/code/scripts/...`)
    # we need to go up one level to treat `code` as the root for the project structure?
    # No, the task says "Paths are relative to the project root".
    # The existing files are in `code/`. So `code/` is likely the project root for this specific repo layout.
    # Let's assume the current working directory IS the project root.
    
    logger.info(f"Project root detected at: {project_root}")

    # 1. Create the structure
    result = create_structure(project_root)

    if result["errors"]:
        logger.warning(f"Encountered {len(result['errors'])} errors during creation.")

    # 2. Generate and save the verification log
    log_path = project_root / "data" / "logs" / "dir_tree.json"
    
    # Ensure the log directory exists before writing (it should have been created in step 1)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    generate_tree_json(project_root, log_path)

    print(f"Setup complete. Verification log written to: {log_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
