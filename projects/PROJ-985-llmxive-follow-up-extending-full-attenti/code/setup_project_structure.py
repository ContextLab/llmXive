import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_directories() -> List[Path]:
    """
    Create the base project directory structure as defined in T001a.
    
    Returns:
        List of Path objects for created directories.
    """
    # Define all required directories relative to project root
    base_dirs = [
        "code",
        "tests",
        "data",
        "code/lib",
        "code/data",
        "code/models",
        "code/evaluation",
        "data/results",
        "data/logs",
        "data/intermediate",
        "data/config"
    ]

    # Get project root (assuming script is run from root or code/)
    # We assume the script is executed from the project root
    project_root = Path.cwd()
    
    created_dirs = []
    
    for dir_name in base_dirs:
        full_path = project_root / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(full_path)
            logger.info(f"Created directory: {full_path}")
        except Exception as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise
    
    return created_dirs

def verify_structure(dirs: List[Path]) -> Tuple[bool, List[str]]:
    """
    Verify that all specified directories exist.
    
    Args:
        dirs: List of Path objects to verify.
        
    Returns:
        Tuple of (all_exist, list_of_missing_paths)
    """
    missing = []
    for d in dirs:
        if not d.is_dir():
            missing.append(str(d))
    
    return len(missing) == 0, missing

def run_tree_command() -> str:
    """
    Run the 'tree' command to capture directory structure.
    
    Returns:
        String output of the tree command.
    """
    try:
        # Run tree command, defaulting to current directory
        result = subprocess.run(
            ["tree", "-L", "2"],  # Limit depth to 2 for readability
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            # Fallback if tree is not installed: use ls -R
            logger.warning("tree command not found, using ls -R fallback")
            result = subprocess.run(
                ["ls", "-R"],
                cwd=Path.cwd(),
                capture_output=True,
                text=True
            )
            return result.stdout
            
    except FileNotFoundError:
        logger.error("Neither 'tree' nor 'ls' command found. Cannot verify structure.")
        raise
    except subprocess.TimeoutExpired:
        logger.error("Tree command timed out.")
        raise

def main():
    """
    Main entry point for T001a: Create base project directories.
    
    1. Creates all required directories.
    2. Verifies they exist using os.path.isdir().
    3. Runs 'tree' command and saves output to data/logs/structure_verification.txt.
    """
    logger.info("Starting project structure creation (T001a)...")
    
    # Step 1: Create directories
    created_dirs = create_directories()
    
    # Step 2: Verify structure
    all_exist, missing = verify_structure(created_dirs)
    
    if not all_exist:
        error_msg = f"Verification failed. Missing directories: {missing}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    logger.info("All directories created and verified successfully.")
    
    # Step 3: Run tree and save output
    try:
        tree_output = run_tree_command()
        
        # Ensure data/logs exists before writing
        log_dir = Path.cwd() / "data" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = log_dir / "structure_verification.txt"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(tree_output)
        
        logger.info(f"Tree output saved to: {output_file}")
        
        # Final verification
        if not output_file.exists() or output_file.stat().st_size == 0:
            raise RuntimeError(f"Output file {output_file} is missing or empty.")
        
        logger.info("T001a completed successfully.")
        
    except Exception as e:
        logger.error(f"Failed to save tree output: {e}")
        raise

if __name__ == "__main__":
    main()
