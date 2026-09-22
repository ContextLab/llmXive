import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Tuple

# Configure logging to output to stdout and file if needed, but primarily for this script to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the required directory structure relative to the project root
REQUIRED_DIRS = [
    "code",
    "tests",
    "data",
    "code/lib",
    "code/data",
    "code/models",
    "code/evaluation",
    "data/results",
    "data/logs",
    "data/intermediate"
]

def create_directories(root_path: Path) -> List[str]:
    """
    Creates all required directories if they do not exist.
    Returns a list of created directory paths.
    """
    created_dirs = []
    for dir_name in REQUIRED_DIRS:
        full_path = root_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            logger.info(f"Created directory: {full_path}")
        else:
            logger.debug(f"Directory already exists: {full_path}")
    return created_dirs

def verify_structure(root_path: Path) -> Tuple[bool, str]:
    """
    Verifies that all required directories exist.
    Returns (True, "All directories verified") if successful.
    Returns (False, error_message) if any are missing.
    """
    missing_dirs = []
    for dir_name in REQUIRED_DIRS:
        full_path = root_path / dir_name
        if not full_path.is_dir():
            missing_dirs.append(str(full_path))

    if missing_dirs:
        error_msg = f"Missing directories: {', '.join(missing_dirs)}"
        return False, error_msg

    return True, "All directories verified"

def run_tree_command(root_path: Path, output_file: Path) -> None:
    """
    Runs the 'tree' command to capture directory structure and saves it to output_file.
    If 'tree' is not available, uses 'find' as a fallback to list structure.
    """
    logger.info(f"Capturing directory structure to {output_file}")
    
    # Ensure the output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Try 'tree' command first
        # -L 2 limits depth to 2 levels to keep it readable
        # -a includes hidden files if any (though we likely don't have many)
        # -I '.__pycache__|.git' ignores common noise
        result = subprocess.run(
            ["tree", "-L", "2", "-a", "-I", "__pycache__|*.pyc|.git", str(root_path)],
            capture_output=True,
            text=True,
            check=True
        )
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Project Structure Verification (tree output):\n")
            f.write("=" * 50 + "\n")
            f.write(result.stdout)
        logger.info("Successfully captured 'tree' output.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("'tree' command not found or failed. Falling back to 'find'.")
        try:
            result = subprocess.run(
                ["find", str(root_path), "-maxdepth", "2", "-type", "d"],
                capture_output=True,
                text=True,
                check=True
            )
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("Project Structure Verification (find output fallback):\n")
                f.write("=" * 50 + "\n")
                f.write(result.stdout)
            logger.info("Successfully captured 'find' output.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to capture directory structure: {e}")
            raise RuntimeError(f"Could not verify structure: {e}")

def main():
    # Determine project root (assuming script is in code/ or root)
    # We assume the script is run from the project root or the path is passed
    # For safety, we look for a marker or default to current working directory
    # Given the constraints, we assume the working directory is the project root
    project_root = Path.cwd()
    
    # If the script is in code/, we might need to go up one level
    # But usually these scripts are run from root.
    # Let's verify if 'code' is a direct child. If not, we might be in code/.
    if not (project_root / "code").exists() and (project_root / "setup_project_structure.py").exists():
        project_root = project_root.parent
        logger.info(f"Adjusted project root to: {project_root}")

    logger.info(f"Project root identified as: {project_root}")

    # 1. Create directories
    created = create_directories(project_root)
    if created:
        logger.info(f"Created {len(created)} directories.")
    else:
        logger.info("All directories already existed.")

    # 2. Verify structure
    success, message = verify_structure(project_root)
    if not success:
        logger.error(f"Verification failed: {message}")
        sys.exit(1)
    
    logger.info(f"Verification: {message}")

    # 3. Capture tree output to data/logs/structure_verification.txt
    output_path = project_root / "data" / "logs" / "structure_verification.txt"
    run_tree_command(project_root, output_path)

    logger.info(f"Structure verification complete. Report saved to: {output_path}")

if __name__ == "__main__":
    main()
